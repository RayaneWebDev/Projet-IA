"""
Othello IA — Version 3
=======================
Tournoi modifié :
  • N parties TOTALES (20 ou 50), paires tirées aléatoirement à chaque partie
  • Résultat de chaque partie affiché en temps réel dans un log scrollable
  • Classement cumulé mis à jour après chaque partie
  • Multiprocessing conservé pour la vitesse
  • Vérification de la hiérarchie en fin de tournoi
"""

import tkinter as tk
from tkinter import messagebox, ttk
import random, time, threading, queue
import multiprocessing as mp

# ─── Constantes ──────────────────────────────────────────────────────────────

BOARD_SIZE = 8
CELL_SIZE  = 70
EMPTY = 0; BLACK = 1; WHITE = -1

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WEIGHTS = [
    [100,-20, 10,  5,  5, 10,-20,100],
    [-20,-50, -2, -2, -2, -2,-50,-20],
    [ 10, -2,  5,  1,  1,  5, -2, 10],
    [  5, -2,  1,  0,  0,  1, -2,  5],
    [  5, -2,  1,  0,  0,  1, -2,  5],
    [ 10, -2,  5,  1,  1,  5, -2, 10],
    [-20,-50, -2, -2, -2, -2,-50,-20],
    [100,-20, 10,  5,  5, 10,-20,100]
]

# ─── Logique du jeu ───────────────────────────────────────────────────────────

class Othello:
    __slots__ = ['board', 'current_player']

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        mid = BOARD_SIZE // 2
        self.board[mid-1][mid-1] = WHITE;  self.board[mid][mid]   = WHITE
        self.board[mid-1][mid]   = BLACK;  self.board[mid][mid-1] = BLACK

    def copy(self):
        g = Othello.__new__(Othello)
        g.board = [row[:] for row in self.board]
        g.current_player = self.current_player
        return g

    def is_on_board(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get_flips(self, row, col):
        if self.board[row][col] != EMPTY:
            return []
        flips = []; opp = -self.current_player; cp = self.current_player; board = self.board
        for dr, dc in DIRECTIONS:
            r, c = row+dr, col+dc; temp = []
            while 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==opp:
                temp.append((r,c)); r+=dr; c+=dc
            if temp and 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE and board[r][c]==cp:
                flips.extend(temp)
        return flips

    def valid_moves(self):
        moves = []; board = self.board; cp = self.current_player; opp = -cp
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != EMPTY: continue
                for dr, dc in DIRECTIONS:
                    nr, nc = r+dr, c+dc
                    if not (0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==opp):
                        continue
                    nr+=dr; nc+=dc
                    while 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==opp:
                        nr+=dr; nc+=dc
                    if 0<=nr<BOARD_SIZE and 0<=nc<BOARD_SIZE and board[nr][nc]==cp:
                        moves.append((r,c)); break
        return moves

    def make_move(self, row, col):
        flips = self.get_flips(row, col)
        if not flips: return False
        self.board[row][col] = self.current_player
        for r, c in flips: self.board[r][c] = self.current_player
        self.current_player *= -1
        return True

    def game_over(self):
        if self.valid_moves(): return False
        self.current_player *= -1
        has = bool(self.valid_moves())
        self.current_player *= -1
        return not has

    def score(self):
        b = w = 0
        for row in self.board:
            for cell in row:
                if cell == BLACK: b += 1
                elif cell == WHITE: w += 1
        return b, w

    def empty_count(self):
        return sum(row.count(EMPTY) for row in self.board)

# ─── Évaluations ─────────────────────────────────────────────────────────────

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

# ─── Minimax ─────────────────────────────────────────────────────────────────

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

# ─── Fonctions IA ─────────────────────────────────────────────────────────────

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
AI_ORDER = ["Aléatoire", "Facile", "Moyen", "Difficile"]

# ─── Worker multiprocessing ───────────────────────────────────────────────────

def _play_game_worker(args):
    """
    Joue une partie complète entre deux IA.
    args = (name_black, name_white, game_number)
    Retourne un dict avec toutes les infos pour l'affichage.
    """
    name_black, name_white, game_num = args
    fn_black = AI_PLAYERS[name_black]
    fn_white = AI_PLAYERS[name_white]

    game = Othello()
    while not game.game_over():
        fn   = fn_black if game.current_player == BLACK else fn_white
        move = fn(game)
        if move: game.make_move(*move)
        else:    game.current_player *= -1

    b, w = game.score()
    if   b > w: winner = name_black; loser = name_white
    elif w > b: winner = name_white; loser = name_black
    else:       winner = None;       loser = None

    return {
        "game_num":   game_num,
        "name_black": name_black,
        "name_white": name_white,
        "score_b":    b,
        "score_w":    w,
        "winner":     winner,   # None = nul
        "loser":      loser,
    }

# ─── Lancement du tournoi ─────────────────────────────────────────────────────

def build_game_list(n_total):
    """
    Construit la liste de N parties avec paires tirées aléatoirement.
    Chaque paire a des couleurs alternées pour l'équité.
    """
    all_pairs = [
        (AI_ORDER[i], AI_ORDER[j])
        for i in range(len(AI_ORDER))
        for j in range(i+1, len(AI_ORDER))
    ]
    tasks = []
    color_counter = {}  # suit qui a joué Noir pour chaque paire

    for k in range(n_total):
        a, b = random.choice(all_pairs)
        key  = (a, b)
        cnt  = color_counter.get(key, 0)
        # Alterne : tour pair → a=Noir, tour impair → b=Noir
        if cnt % 2 == 0:
            black, white = a, b
        else:
            black, white = b, a
        color_counter[key] = cnt + 1
        tasks.append((black, white, k + 1))

    return tasks

# ─── Interface graphique ──────────────────────────────────────────────────────

P = {
    "bg":      "#0d0d1a",
    "panel":   "#14142b",
    "card":    "#1c1c3a",
    "accent":  "#00e5c0",
    "accent2": "#7c3aed",
    "warn":    "#f59e0b",
    "danger":  "#ef4444",
    "success": "#22c55e",
    "text":    "#e2e8f0",
    "muted":   "#64748b",
    "board":   "#1a6b3a",
    "board_ln":"#145c30",
}

class OthelloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Othello IA — Tournoi en direct")
        self.root.geometry("1100x860")
        self.root.configure(bg=P["bg"])
        self.mode = None; self.ai_fn = None
        self.show_home()

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def btn(self, parent, text, cmd, accent=False, small=False):
        size = 11 if small else 14
        b = tk.Button(parent, text=text, font=("Consolas", size, "bold"),
                      bg=P["accent2"] if accent else P["card"], fg="white",
                      activebackground=P["accent"], activeforeground=P["bg"],
                      bd=0, padx=18, pady=8 if small else 12,
                      cursor="hand2", relief="flat", command=cmd)
        b.pack(pady=5); return b

    def lbl(self, parent, text, size=13, color=None, bold=False):
        l = tk.Label(parent, text=text,
                     font=("Consolas", size, "bold" if bold else "normal"),
                     fg=color or P["text"], bg=parent.cget("bg"))
        l.pack(); return l

    # ── Accueil ──────────────────────────────────────────────────────────────

    def show_home(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]); f.pack(expand=True)
        tk.Label(f, text="◈  OTHELLO  ◈", font=("Consolas", 50, "bold"),
                 fg=P["accent"], bg=P["bg"]).pack(pady=28)
        tk.Label(f, text="Moteur IA  ·  Analyse  ·  Tournois en direct",
                 font=("Consolas", 13), fg=P["muted"], bg=P["bg"]).pack()
        tk.Frame(f, height=2, bg=P["accent2"]).pack(fill="x", padx=80, pady=18)
        self.btn(f, "  👥  Humain vs Humain",  lambda: self.start_game("HUMAN"))
        self.btn(f, "  🤖  Humain vs IA",       self.show_difficulty)
        self.btn(f, "  🏆  Tournoi IA vs IA",   self.show_tournament_menu)
        self.btn(f, "  🧪  Tests unitaires",     self.show_tests)

    # ── Difficulté ───────────────────────────────────────────────────────────

    def show_difficulty(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]); f.pack(expand=True)
        self.lbl(f, "Choisissez la difficulté", 24, bold=True)
        tk.Frame(f, height=2, bg=P["accent"]).pack(fill="x", padx=60, pady=14)
        for text, fn in [("🎲  Aléatoire — baseline",     ai_random),
                         ("😊  Facile    — profondeur 2", ai_easy),
                         ("😐  Moyen     — profondeur 3", ai_medium),
                         ("😈  Difficile — profondeur 5", ai_hard)]:
            self.btn(f, text, lambda fn=fn: self.start_game("AI", fn))
        self.btn(f, "↩  Retour", self.show_home, small=True)

    # ── Menu tournoi ─────────────────────────────────────────────────────────

    def show_tournament_menu(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]); f.pack(expand=True)
        self.lbl(f, "Tournoi IA vs IA", 26, bold=True)
        tk.Label(f,
            text=(
                "À chaque partie, deux IA sont tirées au sort.\n"
                "Les couleurs alternent pour chaque paire (équité).\n\n"
                "Les résultats s'affichent en direct, partie par partie.\n"
                "Un classement cumulé est mis à jour en temps réel."
            ),
            font=("Consolas", 12), fg=P["muted"], bg=P["bg"], justify="center"
        ).pack(pady=12)
        row = tk.Frame(f, bg=P["bg"]); row.pack(pady=10)
        for label, n in [("⚡  20 parties", 20), ("🏆  50 parties", 50)]:
            tk.Button(row, text=label, font=("Consolas", 13, "bold"),
                      bg=P["accent2"], fg="white",
                      activebackground=P["accent"], activeforeground=P["bg"],
                      bd=0, padx=22, pady=12, cursor="hand2", relief="flat",
                      command=lambda n=n: self.launch_tournament(n)
                      ).pack(side="left", padx=14)
        self.btn(f, "↩  Retour", self.show_home, small=True)

    # ── Écran de tournoi en direct ────────────────────────────────────────────

    def launch_tournament(self, n_total):
        self.clear()
        root = self.root

        # ── Layout principal ─────────────────────────────────────
        top = tk.Frame(root, bg=P["bg"]); top.pack(fill="x", padx=20, pady=(14,4))
        tk.Label(top, text=f"🏆  Tournoi  —  {n_total} parties",
                 font=("Consolas", 18, "bold"), fg=P["accent"], bg=P["bg"]).pack(side="left")

        # Barre de progression
        prog_frame = tk.Frame(root, bg=P["bg"]); prog_frame.pack(fill="x", padx=20, pady=4)
        self.prog_var = tk.IntVar(value=0)
        style = ttk.Style(); style.theme_use("clam")
        style.configure("T.Horizontal.TProgressbar",
                        troughcolor=P["panel"], background=P["accent"],
                        bordercolor=P["panel"], lightcolor=P["accent"],
                        darkcolor=P["accent"])
        ttk.Progressbar(prog_frame, variable=self.prog_var, maximum=n_total,
                        length=1040, style="T.Horizontal.TProgressbar").pack()
        self.prog_lbl = tk.Label(prog_frame, text="Démarrage...",
                                 font=("Consolas", 11), fg=P["muted"], bg=P["bg"])
        self.prog_lbl.pack(anchor="w")

        # ── Deux colonnes : log | classement ─────────────────────
        cols = tk.Frame(root, bg=P["bg"]); cols.pack(fill="both", expand=True, padx=20, pady=6)

        # --- Colonne gauche : log des parties ---
        left = tk.Frame(cols, bg=P["bg"]); left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Résultats des parties",
                 font=("Consolas", 12, "bold"), fg=P["accent2"], bg=P["bg"]).pack(anchor="w")

        log_frame = tk.Frame(left, bg=P["panel"]); log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(
            log_frame, font=("Consolas", 10), bg=P["panel"], fg=P["text"],
            width=52, bd=0, padx=8, pady=6, state="disabled",
            wrap="none", spacing1=2
        )
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Tags de couleur pour le log
        self.log_text.tag_configure("header", foreground=P["accent"], font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("win",    foreground=P["success"])
        self.log_text.tag_configure("draw",   foreground=P["warn"])
        self.log_text.tag_configure("num",    foreground=P["muted"])
        self.log_text.tag_configure("black_lbl", foreground="#aaaaff")
        self.log_text.tag_configure("white_lbl", foreground="#ffddaa")

        # En-tête log
        self._log_write(f"{'#':>3}  {'Noir':<12} {'Blanc':<12} {'Score':>9}  {'Gagnant'}\n", "header")

        # --- Colonne droite : classement cumulé ---
        right = tk.Frame(cols, bg=P["bg"], width=320); right.pack(side="right", fill="y", padx=(14,0))
        right.pack_propagate(False)
        tk.Label(right, text="Classement cumulé",
                 font=("Consolas", 12, "bold"), fg=P["accent2"], bg=P["bg"]).pack(anchor="w")

        self.rank_frame = tk.Frame(right, bg=P["panel"]); self.rank_frame.pack(fill="both", expand=True)

        # ── Stats internes ───────────────────────────────────────
        self._stats = {name: {"wins": 0, "losses": 0, "draws": 0, "played": 0}
                       for name in AI_ORDER}
        self._done   = 0
        self._n_total = n_total

        self._init_ranking_table()

        # Bouton retour (désactivé pendant le tournoi)
        self.back_btn = tk.Button(root, text="↩  Retour au menu", font=("Consolas", 11, "bold"),
                                  bg=P["card"], fg=P["muted"], bd=0, padx=16, pady=8,
                                  cursor="hand2", relief="flat", state="disabled",
                                  command=self.show_home)
        self.back_btn.pack(pady=(4, 10))

        # Queue pour recevoir les résultats depuis le thread
        self._result_queue = queue.Queue()

        # Construit la liste des parties
        tasks = build_game_list(n_total)

        # Lance le worker dans un thread (qui utilise multiprocessing en interne)
        threading.Thread(target=self._tournament_worker, args=(tasks,), daemon=True).start()

        # Démarre la boucle de polling (toutes les 80 ms)
        root.after(80, self._poll_results)

    # ── Construction du tableau de classement ────────────────────────────────

    def _init_ranking_table(self):
        for w in self.rank_frame.winfo_children(): w.destroy()

        # En-tête
        hrow = tk.Frame(self.rank_frame, bg=P["card"]); hrow.pack(fill="x")
        for text, width in [("IA", 11), ("J", 4), ("V", 4), ("D", 4), ("N", 4), ("%V", 6)]:
            tk.Label(hrow, text=text, width=width, anchor="w",
                     font=("Consolas", 10, "bold"), fg=P["accent"], bg=P["card"]
                     ).pack(side="left", padx=4, pady=3)

        self._rank_rows = {}
        for i, name in enumerate(AI_ORDER):
            bg = P["bg"] if i % 2 == 0 else P["panel"]
            row = tk.Frame(self.rank_frame, bg=bg); row.pack(fill="x")
            labels = {}
            for key, width, anchor in [
                ("name", 11, "w"), ("played", 4, "e"), ("wins", 4, "e"),
                ("losses", 4, "e"), ("draws", 4, "e"), ("wr", 6, "e")
            ]:
                lbl = tk.Label(row, text="—", width=width, anchor=anchor,
                               font=("Consolas", 10), fg=P["text"], bg=bg)
                lbl.pack(side="left", padx=4, pady=2)
                labels[key] = lbl
            labels["name"].config(text=name)
            self._rank_rows[name] = labels

        self._update_ranking_table()

    def _update_ranking_table(self):
        """Met à jour les valeurs du tableau de classement, trié par victoires."""
        sorted_names = sorted(AI_ORDER,
                              key=lambda n: self._stats[n]["wins"],
                              reverse=True)
        bgs = [P["bg"], P["panel"]]

        for rank, name in enumerate(sorted_names):
            s   = self._stats[name]
            row = self._rank_rows[name]
            wr  = f"{100*s['wins']/s['played']:.0f}%" if s['played'] > 0 else "—"

            # Couleur de fond selon le rang
            bg = bgs[rank % 2]
            for lbl in row.values():
                lbl.config(bg=bg)
            row["name"].master.config(bg=bg)

            row["name"].config(text=name, fg=P["accent"] if rank == 0 else P["text"])
            row["played"].config(text=str(s["played"]))
            row["wins"].config(text=str(s["wins"]),   fg=P["success"])
            row["losses"].config(text=str(s["losses"]), fg=P["danger"])
            row["draws"].config(text=str(s["draws"]),  fg=P["warn"])
            row["wr"].config(text=wr)

    # ── Log helper ────────────────────────────────────────────────────────────

    def _log_write(self, text, tag=None):
        self.log_text.config(state="normal")
        if tag:
            self.log_text.insert("end", text, tag)
        else:
            self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log_game_result(self, r):
        """Formate et ajoute une ligne de résultat dans le log."""
        num    = f"{r['game_num']:>3}"
        black  = r["name_black"]
        white  = r["name_white"]
        score  = f"{r['score_b']}-{r['score_w']}"
        winner = r["winner"]

        if winner is None:
            result_text = "Nul"
            result_tag  = "draw"
        elif winner == black:
            result_text = f"● {black}"
            result_tag  = "win"
        else:
            result_text = f"○ {white}"
            result_tag  = "win"

        self._log_write(f"{num}  ", "num")
        self._log_write(f"{black:<12}", "black_lbl")
        self._log_write(f"{white:<12}", "white_lbl")
        self._log_write(f"{score:>9}  ")
        self._log_write(f"{result_text}\n", result_tag)

    # ── Worker thread ─────────────────────────────────────────────────────────

    def _tournament_worker(self, tasks):
        """
        Tourne dans un thread séparé.
        Utilise un Pool multiprocessing pour jouer les parties en parallèle,
        mais envoie les résultats un par un via la queue pour l'affichage.
        """
        n_cores = max(1, mp.cpu_count())
        with mp.Pool(processes=n_cores) as pool:
            for result in pool.imap_unordered(_play_game_worker, tasks):
                self._result_queue.put(result)
        # Signal de fin
        self._result_queue.put(None)

    # ── Polling des résultats (dans le thread UI) ─────────────────────────────

    def _poll_results(self):
        """
        Appelée toutes les 80 ms depuis le thread UI (after).
        Vide la queue de résultats et met à jour l'interface.
        """
        finished = False
        # On traite tous les résultats disponibles d'un coup
        while True:
            try:
                result = self._result_queue.get_nowait()
            except queue.Empty:
                break

            if result is None:
                finished = True
                break

            # Met à jour les stats
            w = result["winner"]
            l = result["loser"]
            for name in AI_ORDER:
                if name == w:
                    self._stats[name]["wins"]   += 1
                    self._stats[name]["played"] += 1
                elif name == l:
                    self._stats[name]["losses"] += 1
                    self._stats[name]["played"] += 1
                elif result["name_black"] == name or result["name_white"] == name:
                    self._stats[name]["draws"]  += 1
                    self._stats[name]["played"] += 1

            self._done += 1
            self._log_game_result(result)
            self._update_ranking_table()

            pct = int(100 * self._done / self._n_total)
            self.prog_var.set(self._done)
            self.prog_lbl.config(text=f"Partie {self._done} / {self._n_total}  ({pct}%)")

        if finished:
            self._on_tournament_done()
        else:
            self.root.after(80, self._poll_results)

    # ── Fin de tournoi ────────────────────────────────────────────────────────

    def _on_tournament_done(self):
        self.prog_lbl.config(text=f"Terminé — {self._n_total} parties jouées",
                             fg=P["success"])

        self._log_write(f"\n{'─'*46}\n", "header")
        winner = sorted(AI_ORDER, key=lambda n: self._stats[n]["wins"], reverse=True)[0]
        wins = self._stats[winner]["wins"]
        draws = self._stats[winner]["draws"]
        self._log_write(f"Champion du tournoi : {winner}  —  {wins} victoires, {draws} nuls\n", "win")

        # Active le bouton retour
        self.back_btn.config(state="normal", fg="white", bg=P["accent2"])

    # ── Partie humain ─────────────────────────────────────────────────────────

    def start_game(self, mode, ai_fn=None):
        self.mode = mode; self.ai_fn = ai_fn
        self.clear(); self.game = Othello()
        main = tk.Frame(self.root, bg=P["bg"]); main.pack(expand=True)
        self.score_label = tk.Label(main, font=("Consolas", 15, "bold"),
                                    fg=P["text"], bg=P["bg"])
        self.score_label.pack(pady=8)
        self.canvas = tk.Canvas(main, width=BOARD_SIZE*CELL_SIZE,
                                height=BOARD_SIZE*CELL_SIZE,
                                bg=P["board"], highlightthickness=2,
                                highlightbackground=P["accent2"])
        self.canvas.pack(pady=8)
        self.canvas.bind("<Button-1>", self.on_click)
        self.btn(main, "↩  Quitter", self.show_home, small=True)
        self.update_ui()

    def update_ui(self):
        self.canvas.delete("all")
        valid = self.game.valid_moves()
        human_turn = not (self.mode == "AI" and self.game.current_player == WHITE)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1,y1 = c*CELL_SIZE, r*CELL_SIZE; x2,y2 = x1+CELL_SIZE, y1+CELL_SIZE
                fill = "#1e7a42" if ((r,c) in valid and human_turn) else P["board"]
                self.canvas.create_rectangle(x1,y1,x2,y2, outline=P["board_ln"], fill=fill, width=1)
                cell = self.game.board[r][c]
                if cell == BLACK:
                    self.canvas.create_oval(x1+6,y1+6,x2-6,y2-6,
                                            fill="#111", outline="#444", width=2)
                elif cell == WHITE:
                    self.canvas.create_oval(x1+6,y1+6,x2-6,y2-6,
                                            fill="#f0f0f0", outline="#aaa", width=2)
                elif (r,c) in valid and human_turn:
                    cx,cy = (x1+x2)//2,(y1+y2)//2
                    self.canvas.create_oval(cx-7,cy-7,cx+7,cy+7, fill=P["accent"], outline="")
        b, w = self.game.score()
        cur = "Noir ○" if self.game.current_player == BLACK else "Blanc ●"
        self.score_label.config(text=f"Tour : {cur}    ⚫ {w}   ⚪ {b}")
        
    

    def on_click(self, event):
        if self.mode == "AI" and self.game.current_player == WHITE:
            return

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE

        if self.game.make_move(row, col):
            self.update_ui()

            # Vérifie si le joueur suivant peut jouer
            if not self.game.valid_moves():
                self.game.current_player *= -1

                # Si personne ne peut jouer → fin
                if not self.game.valid_moves():
                    self.root.after(400, self.check_end)
                    return

            if self.mode == "AI":
                self.root.after(300, self.ai_play)

    def ai_play(self):
        move = self.ai_fn(self.game)

        if move:
            self.game.make_move(*move)
        else:
            self.game.current_player *= -1

        self.update_ui()

        # Vérifie si le joueur suivant peut jouer
        if not self.game.valid_moves():
            self.game.current_player *= -1

            # Si personne ne peut jouer → fin
            if not self.game.valid_moves():
                self.root.after(400, self.check_end)
                return

        # Si c'est encore à l'IA (cas rare mais possible)
        if self.mode == "AI" and self.game.current_player == WHITE:
            self.root.after(300, self.ai_play)

    def check_end(self):
        if self.game.game_over():
            b, w = self.game.score()
            msg = ("⚫ Noir gagne !" if b > w else
                   "⚪ Blanc gagne !" if w > b else "🤝 Match nul !")
            messagebox.showinfo("Fin de partie", f"{msg}\nNoir: {b}  |  Blanc: {w}")
            self.show_home()

    # ── Tests ─────────────────────────────────────────────────────────────────

    def show_tests(self):
        passed, total, output = run_tests()
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]); f.pack(expand=True)
        col = P["success"] if passed == total else P["danger"]
        tk.Label(f, text=f"Tests : {passed}/{total} réussis",
                 font=("Consolas", 24, "bold"), fg=col, bg=P["bg"]).pack(pady=18)
        txt = tk.Text(f, font=("Consolas", 10), bg=P["panel"], fg=P["text"],
                      width=74, height=22, bd=0, padx=10, pady=10)
        txt.insert("1.0", output); txt.config(state="disabled"); txt.pack(padx=20)
        self.btn(f, "↩  Retour", self.show_home, small=True)


# ─── Tests unitaires ──────────────────────────────────────────────────────────

def run_tests():
    passed = 0; total = 0; lines = []
    def test(name, cond):
        nonlocal passed, total; total += 1
        lines.append(f"  {'[OK]   ' if cond else '[ERREUR]'} {name}")
        if cond: passed += 1

    g = Othello(); mid = BOARD_SIZE // 2
    test("Init : 2 noirs au centre",    g.board[mid-1][mid]==BLACK and g.board[mid][mid-1]==BLACK)
    test("Init : 2 blancs au centre",   g.board[mid-1][mid-1]==WHITE and g.board[mid][mid]==WHITE)
    test("Tour initial = Noir",         g.current_player == BLACK)
    mv = g.valid_moves()
    test("4 coups valides au départ",   len(mv) == 4)
    test("(2,3) est valide",            (2,3) in mv)
    test("(0,0) est invalide",          (0,0) not in mv)
    g2 = Othello(); g2.make_move(2,3)
    test("Retournement (3,3) → Noir",   g2.board[3][3] == BLACK)
    test("Tour passe à Blanc",          g2.current_player == WHITE)
    g3 = Othello(); res = g3.make_move(0,0)
    test("Coup invalide retourne False", res == False)
    test("Plateau inchangé",            g3.board[0][0] == EMPTY)
    test("game_over() = False au départ", not Othello().game_over())
    b, w = Othello().score()
    test("Score initial 2 noirs / 2 blancs", b==2 and w==2)
    test("is_on_board(0,0) = True",     g.is_on_board(0,0))
    test("is_on_board(-1,0) = False",   not g.is_on_board(-1,0))
    test("is_on_board(8,8) = False",    not g.is_on_board(8,8))
    g6 = Othello(); vm = g6.valid_moves()
    test("IA Aléatoire : coup valide",  ai_random(g6) in vm)
    test("IA Facile    : coup valide",  ai_easy(g6)   in vm)
    g7 = Othello(); gc = g7.copy(); gc.make_move(2,3)
    test("copy() : original intact",    g7.board[2][3] == EMPTY)
    g8 = Othello()

    # Situation où BLACK ne peut pas jouer
    g8.board = [[WHITE]*8 for _ in range(8)]
    g8.board[0][0] = BLACK
    g8.board[0][1] = EMPTY

    g8.current_player = BLACK

    no_moves = (len(g8.valid_moves()) == 0)

    if no_moves:
        g8.current_player *= -1  # simulation du PASS

    test("PASS : si aucun coup → changement de joueur", g8.current_player == WHITE)

    return passed, total, "\n".join(lines)


# ─── Point d'entrée ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mp.freeze_support()   # nécessaire sur Windows
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        tasks = build_game_list(n)
        print(f"\nTournoi — {n} parties (paires aléatoires)\n{'='*55}")
        print(f"{'#':>3}  {'Noir':<12} {'Blanc':<12} {'Score':>7}  Gagnant")
        print("─"*55)
        stats = {name: {"wins":0,"losses":0,"draws":0,"played":0} for name in AI_ORDER}
        for task in tasks:
            r = _play_game_worker(task)
            score = f"{r['score_b']}-{r['score_w']}"
            winner = r['winner'] or "Nul"
            print(f"{r['game_num']:>3}  {r['name_black']:<12} {r['name_white']:<12} {score:>7}  {winner}")
            w, l = r['winner'], r['loser']
            for name in AI_ORDER:
                if name == w:
                    stats[name]["wins"] += 1; stats[name]["played"] += 1
                elif name == l:
                    stats[name]["losses"] += 1; stats[name]["played"] += 1
                elif r['name_black'] == name or r['name_white'] == name:
                    stats[name]["draws"] += 1; stats[name]["played"] += 1
        print(f"\n{'─'*55}\nClassement final :")
        for name in sorted(AI_ORDER, key=lambda n: stats[n]["wins"], reverse=True):
            s = stats[name]
            wr = f"{100*s['wins']/s['played']:.0f}%" if s['played'] else "—"
            print(f"  {name:<12}  J={s['played']}  V={s['wins']}  D={s['losses']}  N={s['draws']}  WR={wr}")
    else:
        root = tk.Tk()
        OthelloGUI(root)
        root.mainloop()