from core.constants import *

def evaluate_naive(game, player):
    b, w = game.score()
    return (b - w) if player == BLACK else (w - b)

def evaluate_mobility(game, player):
    score = 0; board = game.board
    for r, c in [(0,0),(0,7),(7,0),(7,7)]:
        if board[r][c] == player:    score += 50
        elif board[r][c] == -player: score -= 50
    saved = game.current_player
    game.current_player = player;   my = len(game.valid_moves())
    game.current_player = -player;  op = len(game.valid_moves())
    game.current_player = saved
    if my + op > 0: score += 10 * (my - op)
    return score

def evaluate_advanced(game, player):
    board = game.board; score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = board[r][c]
            if cell == player:       score += WEIGHTS[r][c]
            elif cell == -player:    score -= WEIGHTS[r][c]
    saved = game.current_player
    game.current_player = player;   my = len(game.valid_moves())
    game.current_player = -player;  op = len(game.valid_moves())
    game.current_player = saved
    score += (my - op) * 10
    b, w = game.score()
    score += ((b-w) if player == BLACK else (w-b)) * 2
    return score
