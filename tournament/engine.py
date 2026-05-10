# =========================================
# tournament/engine.py
# =========================================

from core.game import Othello
from core.constants import BLACK, WHITE, EMPTY

from ai.players import AI_PLAYERS


def play_one_game(ai_black_fn, ai_white_fn):

    game = Othello()

    while not game.game_over():

        if game.current_player == BLACK:
            move = ai_black_fn(game)

        else:
            move = ai_white_fn(game)

        if move:
            game.make_move(*move)

        else:
            game.current_player *= -1

    black_score, white_score = game.score()

    if black_score > white_score:
        winner = BLACK

    elif white_score > black_score:
        winner = WHITE

    else:
        winner = EMPTY

    return winner, black_score, white_score


def run_tournament(ai_name_a, ai_name_b, n_games=50):

    ai_fn_a = AI_PLAYERS[ai_name_a]
    ai_fn_b = AI_PLAYERS[ai_name_b]

    wins_a = 0
    wins_b = 0
    draws = 0

    half = n_games // 2

    for i in range(n_games):

        # A joue Noir
        if i < half:

            winner, _, _ = play_one_game(
                ai_fn_a,
                ai_fn_b
            )

            if winner == BLACK:
                wins_a += 1

            elif winner == WHITE:
                wins_b += 1

            else:
                draws += 1

        # A joue Blanc
        else:

            winner, _, _ = play_one_game(
                ai_fn_b,
                ai_fn_a
            )

            if winner == WHITE:
                wins_a += 1

            elif winner == BLACK:
                wins_b += 1

            else:
                draws += 1

    return {

        "ia_a": ai_name_a,
        "ia_b": ai_name_b,

        "wins_a": wins_a,
        "wins_b": wins_b,

        "draws": draws,

        "total_games": n_games
    }


def run_full_tournament(total_games=50):

    ai_names = list(AI_PLAYERS.keys())

    # Calculer le nombre de paires
    n_pairs = len(ai_names) * (len(ai_names) - 1) // 2
    
    # Diviser le nombre total de parties par le nombre de paires
    games_per_pair = max(1, total_games // n_pairs)
    remaining_games = total_games % n_pairs

    results = []
    pair_index = 0

    for i in range(len(ai_names)):

        for j in range(i + 1, len(ai_names)):

            # Les premières paires reçoivent une partie supplémentaire
            games = games_per_pair
            if pair_index < remaining_games:
                games += 1
            
            result = run_tournament(
                ai_names[i],
                ai_names[j],
                games
            )

            results.append(result)
            pair_index += 1

    return results