# =========================================
# tests/test_othello.py
# =========================================

from core.game import Othello
from core.constants import BLACK, WHITE


def test_initial_setup():

    game = Othello()

    b, w = game.score()

    assert b == 2, "Initial Black score should be 2"
    assert w == 2, "Initial White score should be 2"

    print("✓ test_initial_setup")


def test_valid_moves_initial():

    game = Othello()

    moves = game.valid_moves()

    assert len(moves) > 0, "There should be valid moves at start"

    print("✓ test_valid_moves_initial")


def test_move_execution():

    game = Othello()

    moves = game.valid_moves()

    r, c = moves[0]

    ok = game.make_move(r, c)

    assert ok, "Move should be valid"

    b, w = game.score()

    assert b + w > 4, "Board should change after move"

    print("✓ test_move_execution")


def test_copy_game():

    game = Othello()

    clone = game.copy()

    assert clone.board == game.board
    assert clone.current_player == game.current_player

    print("✓ test_copy_game")


def test_game_over_detection():

    game = Othello()

    # Force a near-end situation
    for r in range(8):
        for c in range(8):
            game.board[r][c] = BLACK

    game.board[0][0] = WHITE

    assert game.game_over(), "Game should be over"

    print("✓ test_game_over_detection")


def run_tests():

    output = []
    passed = 0
    total = 5

    tests = [
        test_initial_setup,
        test_valid_moves_initial,
        test_move_execution,
        test_copy_game,
        test_game_over_detection,
    ]

    for t in tests:

        try:
            t()
            passed += 1
            output.append(f"{t.__name__} : OK")

        except Exception as e:

            output.append(f"{t.__name__} : FAIL -> {e}")

    return passed, total, "\n".join(output)


# =========================================
# CLI direct run
# =========================================

if __name__ == "__main__":

    passed, total, output = run_tests()

    print("\nRESULTATS TESTS\n")
    print(output)
    print(f"\n{passed}/{total} tests réussis")