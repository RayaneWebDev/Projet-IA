# =========================================
# tournament/workers.py
# =========================================

import random

from core.game import Othello
from core.constants import BLACK
from ai.players import AI_PLAYERS

AI_ORDER = [
    "Aléatoire",
    "Facile",
    "Moyen",
    "Difficile"
]


def _play_game_worker(args):
    """
    Worker multiprocessing :
    joue une partie complète entre deux IA.
    """

    name_black, name_white, game_num = args

    fn_black = AI_PLAYERS[name_black]
    fn_white = AI_PLAYERS[name_white]

    game = Othello()

    while not game.game_over():

        fn = (
            fn_black
            if game.current_player == BLACK
            else fn_white
        )

        move = fn(game)

        if move:
            game.make_move(*move)

        else:
            game.current_player *= -1

    black_score, white_score = game.score()

    if black_score > white_score:

        winner = name_black
        loser = name_white

    elif white_score > black_score:

        winner = name_white
        loser = name_black

    else:

        winner = None
        loser = None

    return {
        "game_num": game_num,
        "name_black": name_black,
        "name_white": name_white,
        "score_b": black_score,
        "score_w": white_score,
        "winner": winner,
        "loser": loser,
    }


def build_game_list(n_total):
    """
    Génère les parties du tournoi
    avec alternance des couleurs.
    """

    all_pairs = [

        (AI_ORDER[i], AI_ORDER[j])

        for i in range(len(AI_ORDER))
        for j in range(i + 1, len(AI_ORDER))
    ]

    tasks = []

    color_counter = {}

    for k in range(n_total):

        a, b = random.choice(all_pairs)

        key = (a, b)

        cnt = color_counter.get(key, 0)

        # alternance Noir / Blanc
        if cnt % 2 == 0:
            black, white = a, b
        else:
            black, white = b, a

        color_counter[key] = cnt + 1

        tasks.append((black, white, k + 1))

    return tasks