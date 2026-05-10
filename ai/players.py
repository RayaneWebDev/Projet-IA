from .minimax import minimax
from .evaluation import *
import random

def ai_random(game):
    moves = game.valid_moves()
    return random.choice(moves) if moves else None

def ai_easy(game):
    _, m = minimax(game, 2, float('-inf'), float('inf'), True, game.current_player, evaluate_naive)
    return m

def ai_medium(game):
    _, m = minimax(game, 3, float('-inf'), float('inf'), True, game.current_player, evaluate_mobility)
    return m

def ai_hard(game):
    d = 3 if game.empty_count() > 50 else 5
    _, m = minimax(game, d, float('-inf'), float('inf'), True, game.current_player, evaluate_advanced)
    return m

AI_PLAYERS = {
    "Aléatoire": ai_random,
    "Facile":    ai_easy,
    "Moyen":     ai_medium,
    "Difficile": ai_hard,
}