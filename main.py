from monopyly import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--ai_dir",
                    default="AIs_dev")
parser.add_argument("-t", "--tournament",
                    action='store_true')
parser.add_argument("-b", "--brett",
                    action='store_true')

args = parser.parse_args()

# True to play a tournament, False to play a single game
# with selected players...
play_tournament = args.tournament
play_brett = args.brett

# We find the collection of AIs from the AIs folder...
ais = load_ais(args.ai_dir)

if play_tournament:
    # We play a tournament. This plays all the permutations of
    # AIs against each other.

    # Logging at INFO_PLUS level shows game results, but does not
    # show verbose information...
    Logger.add_handler(ConsoleLogHandler(Logger.INFO_PLUS))
    Logger.add_handler(FileLogHandler("tournament.log", Logger.INFO_PLUS))
    Logger.log("Number of AIs: {0}".format(len(ais)), Logger.INFO_PLUS)

    our_player = "MLBaseline"
    brett_players = ["Bretts AI","Xander","Buffy","Cordie","Willow"]

    if play_brett:
        for p in brett_players:
            ais_for_game = [a for a in ais if a.get_name() not in set(brett_players) and a.get_name() != our_player]
            desired_player = [a for a in ais if a.get_name()==p][0]
            ais_for_game.append(desired_player)
            tournament = IncludeTournament(
                player_ais=ais_for_game,
                desired_player=desired_player,
                min_players_per_game=3,
                max_players_per_game=3,
                number_of_rounds=30,
                maximum_games=100,
                permutations_or_combinations=Tournament.PERMUTATIONS)
            tournament.play()
            tournament.log_results(final=True)

    else:
        # We set up and play a tournament with MC player and all of Bretts AIS
        mc_player = our_player
        mc_ais = brett_players
        tournament = MCTournament(
            player_ais=[a for a in ais if a.get_name() != mc_player and a.get_name() not in set(mc_ais)],
            mc_player=[a for a in ais if a.get_name() == mc_player][0],
            mc_ais=[a for a in ais if a.get_name() in set(mc_ais)],
            min_players_per_game=3,
            max_players_per_game=3,
            number_of_rounds=30,
            maximum_games=100,
            permutations_or_combinations=Tournament.PERMUTATIONS)

        # Sends updates to the C# GUI...
        #tournament.messaging_server = MessagingServer(update_every_n_turns=10, sleep_between_turns_seconds=0.0)

        # We play the tournament...
        tournament.play()
        tournament.log_results(final=True)

else:
    # We play a single game with selected players.
    #
    # This can be useful for testing your AI in a single game without
    # having to play a full multi-player tournament.
    #
    # To test with your own players, change the AI selections below.

    # Logging at INFO level shows verbose information about each
    # turn in the game...
    Logger.add_handler(ConsoleLogHandler(Logger.INFO))

    # We select specific AIs from the ones loaded...

    kk_ai = next(ai for ai in ais if ai.get_name() == "KKBaseline")
    ml_ai = next(ai for ai in ais if ai.get_name() == "MLBaseline")
    xander_ai = next(ai for ai in ais if ai.get_name() == "Xander")
    #bigbrick_ai = next(ai for ai in ais if ai.get_name() == "The Big Brick")
    brill_ai = next(ai for ai in ais if ai.get_name() == "Brill")
    #rimpo_ai = next(ai for ai in ais if ai.get_name() == "RimpoAI")

    
    # We set up and play a single game...
    game = Game()
    # game.add_player(ml_ai)
    # game.add_player(kk_ai,oracle_ai)
    # game.add_player(xander_ai)
    
    #game.add_player((rimpo_ai,0))
    game.add_player(ml_ai,mc_ais=[xander_ai,brill_ai])
    #game.add_player((bigbrick_ai,2))
    game.add_player(kk_ai)

    #game.add_player(kk_ai2)
    game.play_game()



