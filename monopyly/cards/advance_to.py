from .card import Card
from ..squares import Square


class AdvanceTo(Card):
    '''
    Represents an "Advance to..." card, including checking
    whether the player passes go and collects £200.
    '''

    def __init__(self, square_name):
        '''
        The 'constructor'.
        '''
        self.destination_square_name = square_name

    def play(self, game, current_player):
        '''
        We move the player to the new square, giving them
        £200 if they pass go.
        '''
        # We need to find if the player is further round the board than
        # the destination square, so we can decide whether to give them
        # £200 for passing go...
        go_square_position = game.state.board.get_index_list(Square.Name.GO)[0]
        destination_square_position = game.state.board.get_index_list(self.destination_square_name)[0]
        player_position = current_player.state.square
        if((player_position > destination_square_position) and (destination_square_position != go_square_position)):
            # The player has to pass Go to get to the destination...
            game.give_money_to_player(current_player, 200)

        # We move the player to the destination...
        current_player.state.square = destination_square_position
        game.player_has_changed_square(current_player)



