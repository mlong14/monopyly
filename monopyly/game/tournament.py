import itertools
import random
from .game import Game
from ..utility import Logger


class Tournament(object):
    '''
    Manages a tournament.

    A tournament is a number of games between a collection of players.

    You specify:
    - The collection of player AIs.
    - The maximum number of players in each game.
    - The number of rounds to play.

    Each round plays all permutations of the players against each other. This
    includes the same set of players playing in different orders.

    So a round may consist of a large number of games. For example, if there
    are 15 players playing in groups of 4, there are 32760 games in a round.
    '''

    class _PlayerInfo(object):
        '''
        Holds info about one player including games won, player number
        timing info etc.
        '''
        def __init__(self):
            '''
            The 'constructor'.
            '''
            self.ai = None
            self.games_won = 0
            self.turns_played = 0
            self.processing_seconds = 0.0
            self.name = ""
            self.player_number = -1

    # An 'enum' for whether we should play permutations or combinations
    # of AIs when playing a tournament...
    PERMUTATIONS = 1
    COMBINATIONS = 2

    def __init__(
            self,
            player_ais,
            mc_player,
            mc_ais,
            min_players_per_game,
            max_players_per_game,
            number_of_rounds,
            maximum_games,
            permutations_or_combinations):
        '''
        The 'constructor'
        '''
        # We hold a list of _PlayerInfo objects - one for each plater...
        self.player_infos = dict()
        number_of_player_ais = len(player_ais)+1
        for player_number in range(number_of_player_ais-1):
            player_info = Tournament._PlayerInfo()
            player_info.ai = player_ais[player_number]
            player_info.name = player_info.ai.get_name()
            player_info.player_number = player_number
            self.player_infos[player_number] = player_info

        player_info = Tournament._PlayerInfo()
        player_info.ai = mc_player
        player_info.name = player_info.ai.get_name()
        player_info.player_number = number_of_player_ais-1
        self.player_infos[number_of_player_ais-1] = player_info

        self.mc_player = mc_player
        self.mc_ais = mc_ais

        self.number_of_rounds = number_of_rounds

        # We check that there are enough players...
        if number_of_player_ais >= max_players_per_game:
            self.max_players_per_game = max_players_per_game
        else:
            self.max_players_per_game = number_of_player_ais

        if min_players_per_game < self.max_players_per_game:
            self.min_players_per_game = min_players_per_game
        else:
            self.min_players_per_game = self.max_players_per_game

        # If the messaging_server is set up, we send updates to
        # the C# GUI when game events occur...
        self.messaging_server = None

        # Whether we are playing permutations or combinations
        # of players...
        self.permutations_or_combinations = permutations_or_combinations

        # The maximum number of games to play per round...
        player_number_variations = max_players_per_game - min_players_per_game + 1
        variations = number_of_rounds * 2 * player_number_variations
        self.max_games_per_round = int(maximum_games / variations)

        # The number of games played...
        self.game_count = 0

    def play(self):
        '''
        Plays the tournament and returns the results as a dictionary of
        AI names to the number of games each won.
        '''
        self.game_count = 0

        # We send the start-of-tournament message...
        if self.messaging_server is not None:
            # We send a list of (player-name, player-number)...
            players = [(p.name, p.player_number) for p in self.player_infos.values()]
            self.messaging_server.send_start_of_tournament_message(players)

        # We play the specified number of rounds...
        for round in range(self.number_of_rounds):
            Logger.log("Playing round {0}".format(round+1), Logger.INFO_PLUS)
            Logger.indent()

            # We play one round with each number of plays in the range specified...
            for number_of_players in range(self.min_players_per_game, self.max_players_per_game+1):
                # We play one round with the eminent-domain rule and one without...
                self._play_round(number_of_players, True)
                self._play_round(number_of_players, False)
            Logger.dedent()

    def log_results(self):
        '''
        Logs the results, ie games won per player, sorted from high to low.
        '''
        results = [(p.name, p.games_won) for p in self.player_infos.values()]
        results.sort(key=lambda r: r[1], reverse=True)
        Logger.log("Results: {0}".format(results), Logger.INFO_PLUS)

    def turn_played(self, game):
        '''
        Called at the end of each turn in a game.

        We notify the GUI of the current game state.
        '''
        # We send the player-info message...
        if self.messaging_server is not None:
            self.messaging_server.send_end_of_turn_messages(tournament=self, game=game, force_send=False)

    def get_ms_per_turn(self, player):
        '''
        We calculate the ms/turn taken by the player over the whole
        tournament so far.
        '''
        player_info = self.player_infos[player.player_number]

        total_seconds = player_info.processing_seconds + player.state.ai_processing_seconds_used
        total_turns = player_info.turns_played + player.state.turns_played
        if total_turns == 0:
            milliseconds_per_turn = 0.0
        else:
            milliseconds_per_turn = 1000.0 * total_seconds / total_turns

        return milliseconds_per_turn

    def _play_round(self, number_of_players, eminent_domain):
        '''
        We play one round and store the results.
        '''
        # We loop through all permutations or combinations of the players...
        ais = [(p.ai, p.player_number) for p in self.player_infos.values()]
        if self.permutations_or_combinations == Tournament.PERMUTATIONS:
            ais_per_game =itertools.permutations(ais, number_of_players)
        else:
            ais_per_game =itertools.combinations(ais, number_of_players)

        # We may want to choose a random subset of these games...
        ais_per_game = list(ais_per_game)
        if self.max_games_per_round < len(ais_per_game):
            ais_per_game = random.sample(ais_per_game, self.max_games_per_round)

        for ais_for_this_game in ais_per_game:

            if any([ai[0]==self.mc_player for ai in ais_for_this_game]):
                # Each permutation is a collection of player AIs. We play a game with these AIs...
                game = Game()
                game.tournament = self
                game.eminent_domain = eminent_domain
                for ai in ais_for_this_game:
                    if ai[0] == self.mc_player:
                        game.add_player(ai,mc_ais=self.mc_ais)
                    else:
                        game.add_player(ai)

                # We notify the GUI that the game has started...
                if self.messaging_server is not None:
                    self.messaging_server.send_start_of_game_message()

                # We play the game...
                game.play_game()

                # We add the winner to the results...
                winner = game.winner
                if winner is None:
                    winner_name = "Game drawn"
                else:
                    winner_name = winner.name

                # We update the player infos...
                for player in itertools.chain(game.state.players, game.state.bankrupt_players):
                    player_info = self.player_infos[player.player_number]

                    # Did this player win?
                    if player_info.name == winner_name:
                        player_info.games_won += 1

                    # We update the processing stats...
                    player_info.turns_played += player.state.turns_played
                    player_info.processing_seconds += player.state.ai_processing_seconds_used

                # We log the results...
                self.game_count += 1
                player_names = [ai[0].get_name() for ai in ais_for_this_game]
                message = "Game {0}:  Winner was: {3} ({1} eminent-domain: {2})".format(
                    self.game_count, player_names, eminent_domain, winner_name)
                Logger.log(message, Logger.INFO_PLUS)

                # We show interim results every 10 games...
                if self.game_count % 10 == 0:
                    self.log_results()

                # We update the GUI...
                if self.messaging_server is not None:
                    self.messaging_server.send_end_of_turn_messages(tournament=self, game=game, force_send=True)

