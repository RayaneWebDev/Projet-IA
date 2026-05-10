import copy

def minimax(game, depth, alpha, beta, maximizing, player, eval_fn):
    if depth == 0 or game.game_over():
        return eval_fn(game, player), None
    moves = game.valid_moves()
    if not moves:
        game.current_player *= -1
        val, _ = minimax(game, depth, alpha, beta, not maximizing, player, eval_fn)
        game.current_player *= -1
        return val, None
    best = None
    if maximizing:
        mx = float('-inf')
        for m in moves:
            ng = game.copy(); ng.make_move(*m)
            ev, _ = minimax(ng, depth-1, alpha, beta, False, player, eval_fn)
            if ev > mx: mx = ev; best = m
            alpha = max(alpha, ev)
            if beta <= alpha: break
        return mx, best
    else:
        mn = float('inf')
        for m in moves:
            ng = game.copy(); ng.make_move(*m)
            ev, _ = minimax(ng, depth-1, alpha, beta, True, player, eval_fn)
            if ev < mn: mn = ev; best = m
            beta = min(beta, ev)
            if beta <= alpha: break
        return mn, best
