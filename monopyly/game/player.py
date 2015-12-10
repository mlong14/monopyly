from .player_state import PlayerState
from ..squares import Property, Street
import time

class Player(object):
    '''
    Holds the PlayerState and a player AI (an object
    derived from PlayerAIBase).
    '''

    def __init__(self, ai, player_number, board):
        '''
        The 'constructor'.
        '''
        self.state = PlayerState()
        self.ai = ai
        self.board = board
        self.player_number = player_number

    def is_mcp(self):
        return False


    def owns_properties(self, properties):
        '''
        Returns True if this player owns all the properties passed in,
        False if not (or if any of the squares passed in are no properties).
        '''
        # We check each property...
        for square in properties:
            # We check that the square is a property...
            if not isinstance(square, Property):
                return False

            if square.owner is not self:
                return False

        return True

    @property
    def net_worth(self):
        '''
        Returns the player's net worth, which includes their
        cash, properties and houses.
        '''
        # Net worth includes cash...
        total = self.state.cash

        for property in self.state.properties:
            # We add the mortgage value of properties...
            if not property.is_mortgaged:
                total += property.mortgage_value

            # We add the resale value of houses...
            if type(property) == Street:
                total += int(property.house_price/2 * property.number_of_houses)

        return total

    @property
    def name(self):
        '''
        Returns the player name.
        '''
        return self.ai.get_name()


    def is_same_player(self, other):
        '''
        Returns true if the other player is the same as this one.

        'other' can be either a Player object or a Player AI object.
        '''
        if other is self:
            return True

        if other is self.ai:
            return True

        return False

    def call_ai(self, function, *args):
        '''
        Calls the function passed in, times it and updates the
        total time used by this player.

        The functions will be the AI methods.
        '''
        # We call the function and time how long the AI spends processing it...
        start = time.clock()
        result = function(*args)
        end = time.clock()
        elapsed_seconds = end - start
 
        # We update the time the AI has remaining for the current game...
        self.state.ai_processing_seconds_remaining -= elapsed_seconds
        self.state.ai_processing_seconds_used += elapsed_seconds

        # And return what the function returned...
        return result

    # def __str__(self):
    #     return self.state.__str__()


#TODO
#Data analysis packages that compares all moves to oracle, and makes numbers


class OraclePlayer(Player):

    def __init__(self, ai, player_number, board, oracle_ai):
        super().__init__(ai, player_number, board)
        self.oracle_ai = oracle_ai
        self.oracle_ai.set_name(self.ai.get_name())

        self.oracle_moves = {}
        self.ai_moves = {}

        self.f = open("logging/oracle_logs_{0}".format(board.game_id),"w")
        self.call_count = 0

    def call_ai(self, function, *args):

        self.call_count+=1

        start = time.clock()
        result = function(*args)

        funcToCall = getattr(self.oracle_ai, function.__name__)
        or_result = funcToCall(*args)

        self.log(function,result,or_result,*args)

        end = time.clock()
        elapsed_seconds = end - start

        # We update the time the AI has remaining for the current game...
        self.state.ai_processing_seconds_remaining -= elapsed_seconds
        self.state.ai_processing_seconds_used += elapsed_seconds

        # And return what the function returned...
        return result

    def args2tuple(self,*args):
        arg_l = []
        for a in args:
            try:
                arg_l.append(a.name)
            except:
                arg_l.append(a.__str__())
        return tuple(arg_l)

    def log(self,function,result,or_result,*args):

        fn = function.__name__

        self.f.write("{2}. Function: {0}, Args: {1}\n".format(fn,self.args2tuple(*args),self.call_count))
        self.f.write("Baseline: {0}\n".format(result))
        self.f.write("Oracle: {0}\n".format(or_result))

        if fn not in self.ai_moves:
            self.ai_moves[fn] = []
            self.oracle_moves[fn] = []

        self.ai_moves[fn].append(result.__str__())
        self.oracle_moves[fn].append(or_result.__str__())


    def basic_analysis(self):

        print("")
        print("BASIC ANALYSIS")

        for k in sorted(self.ai_moves.keys()):
            diff = 0
            for i in range(len(self.ai_moves[k])):
                if self.ai_moves[k][i] != self.oracle_moves[k][i]:
                    diff+=1
            print("Move: {0}, Similarity: {1}".format(k,100*(1-float(diff)/len(self.ai_moves[k]))))

        print("")


    def __str__(self):

        ai_state = self.state.__str__()

        return "(Oracle) {0}".format(ai_state)



class MonteCarloPlayer(Player):

    def __init__(self, ai, player_number, board, ai_list):
        super().__init__(ai, player_number, board)
        self.ai_list = ai_list
        self.ai_names = [a.get_name() for a in ai_list]

        self.ai_players = [Player(ai_mc, player_number, board) for ai_mc in self.ai_list]        

        self.ai_moves = {}
        self.curr_ai = 0
        self.num_ais = len(ai_list)

        self.call_count = 0

    def change_names(self):
        for ais in self.ai_list:
            ais.set_name(self.ai.get_name())

    def is_mcp(self):
        return True

    def get_ais(self):
        return self.ai_list

    def set_ai(self,ai_ind):
        self.curr_ai = ai_ind
        return self.ai_names[ai_ind]

    def call_ai(self, function, *args):

        self.call_count+=1

        start = time.clock()
        results = []

        args = list(args)
        for ai in self.ai_list:
            funcToCall = getattr(ai, function.__name__)
            ai_result = funcToCall(*args)
            results.append(ai_result)
            if ai_result is not None:
                print("RESULT: ",ai_result)
        #print("NARGS",args,self)
        # if current_player:
        #     print("CP",current_player)
        # for ai in self.ai_players:
        #     ai_result = ai.call_ai(function,*tuple(args))
        #     results.append(ai_result)
        #     if ai_result is not None:
        #         print("RESULT: ",ai_result)

        result = results[self.curr_ai]


        end = time.clock()
        elapsed_seconds = end - start

        # We update the time the AI has remaining for the current game...
        self.state.ai_processing_seconds_remaining -= elapsed_seconds
        self.state.ai_processing_seconds_used += elapsed_seconds

        # And return what the function returned...
        return result


    # def __str__(self):

    #     ai_state = self.state.__str__()

    #     return "(MC Player) {0}, {1}".format(self.ai.get_name(),ai_state) 

