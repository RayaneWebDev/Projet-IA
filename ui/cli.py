# =========================================
# ui/cli.py
# =========================================

import time

from core.game import Othello
from core.constants import (
    BLACK,
    WHITE,
    BOARD_SIZE
)

from ai.players import AI_PLAYERS

from tournament.engine import run_full_tournament


def print_board(game):

    print("\n    " + "  ".join(str(c) for c in range(BOARD_SIZE)))
    print("   " + "─" * (BOARD_SIZE * 3))

    for r in range(BOARD_SIZE):

        row_str = f" {r} │"

        for c in range(BOARD_SIZE):

            cell = game.board[r][c]

            if cell == BLACK:
                row_str += " ● "

            elif cell == WHITE:
                row_str += " ○ "

            else:
                row_str += " · "

        print(row_str)

    black, white = game.score()

    print(f"\n⚫ Noir : {black} | ⚪ Blanc : {white}")


def cli_play_human_vs_ai(ai_name="Difficile"):

    game = Othello()

    ai_fn = AI_PLAYERS[ai_name]

    while not game.game_over():

        print_board(game)

        valid_moves = game.valid_moves()

        # ==================================
        # TOUR HUMAIN
        # ==================================
        if game.current_player == BLACK:

            print("\nVotre tour")
            print("Coups possibles :", valid_moves)

            while True:

                try:

                    move = input("ligne colonne : ").split()

                    row = int(move[0])
                    col = int(move[1])

                    if (row, col) in valid_moves:

                        game.make_move(row, col)
                        break

                    else:
                        print("Coup invalide")

                except:
                    print("Erreur de saisie")

        # ==================================
        # TOUR IA
        # ==================================
        else:

            print(f"\nTour IA ({ai_name})...")

            start = time.time()

            move = ai_fn(game)

            elapsed = time.time() - start

            if move:

                game.make_move(*move)

                print(f"IA joue : {move}")
                print(f"Temps : {elapsed:.2f}s")

            else:

                game.current_player *= -1

    print_board(game)

    black, white = game.score()

    print("\nFIN")

    if black > white:
        print("⚫ Noir gagne")

    elif white > black:
        print("⚪ Blanc gagne")

    else:
        print("🤝 Match nul")


def cli_run_tournament_report(n_games=50):

    print("\nTOURNOI IA")

    results = run_full_tournament(n_games)

    for result in results:

        print(
            f"{result['ia_a']} vs {result['ia_b']} : "
            f"{result['wins_a']}V "
            f"{result['wins_b']}V "
            f"{result['draws']}N"
        )