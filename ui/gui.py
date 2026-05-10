import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

import multiprocessing as mp
import threading
import queue

from core.game import Othello

from core.constants import *

from ai.players import (
    ai_random,
    ai_easy,
    ai_medium,
    ai_hard
)

from tournament.workers import (
    _play_game_worker,
    build_game_list,
    AI_ORDER
)

from tests.test_othello import run_tests


P = {
    "bg": "#0d0d1a",
    "panel": "#14142b",
    "card": "#1c1c3a",
    "accent": "#00e5c0",
    "accent2": "#7c3aed",
    "warn": "#f59e0b",
    "danger": "#ef4444",
    "success": "#22c55e",
    "text": "#e2e8f0",
    "muted": "#64748b",
    "board": "#1a6b3a",
    "board_ln": "#145c30",
}
class OthelloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Othello IA — Tournoi en direct")
        self.root.geometry("1100x860")
        self.root.configure(bg=P["bg"])
        self.mode = None;
        self.ai_fn = None
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
        b.pack(pady=5);
        return b

    def lbl(self, parent, text, size=13, color=None, bold=False):
        l = tk.Label(parent, text=text,
                     font=("Consolas", size, "bold" if bold else "normal"),
                     fg=color or P["text"], bg=parent.cget("bg"))
        l.pack();
        return l

    # ── Accueil ──────────────────────────────────────────────────────────────

    def show_home(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]);
        f.pack(expand=True)
        tk.Label(f, text="◈  OTHELLO  ◈", font=("Consolas", 50, "bold"),
                 fg=P["accent"], bg=P["bg"]).pack(pady=28)
        tk.Label(f, text="Moteur IA  ·  Analyse  ·  Tournois en direct",
                 font=("Consolas", 13), fg=P["muted"], bg=P["bg"]).pack()
        tk.Frame(f, height=2, bg=P["accent2"]).pack(fill="x", padx=80, pady=18)
        self.btn(f, "  👥  Humain vs Humain", lambda: self.start_game("HUMAN"))
        self.btn(f, "  🤖  Humain vs IA", self.show_difficulty)
        self.btn(f, "  🏆  Tournoi IA vs IA", self.show_tournament_menu)
        self.btn(f, "  🧪  Tests unitaires", self.show_tests)

    # ── Difficulté ───────────────────────────────────────────────────────────

    def show_difficulty(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]);
        f.pack(expand=True)
        self.lbl(f, "Choisissez la difficulté", 24, bold=True)
        tk.Frame(f, height=2, bg=P["accent"]).pack(fill="x", padx=60, pady=14)
        for text, fn in [("🎲  Aléatoire — baseline", ai_random),
                         ("😊  Facile    — profondeur 2", ai_easy),
                         ("😐  Moyen     — profondeur 3", ai_medium),
                         ("😈  Difficile — profondeur 5", ai_hard)]:
            self.btn(f, text, lambda fn=fn: self.start_game("AI", fn))
        self.btn(f, "↩  Retour", self.show_home, small=True)

    # ── Menu tournoi ─────────────────────────────────────────────────────────

    def show_tournament_menu(self):
        self.clear()
        f = tk.Frame(self.root, bg=P["bg"]);
        f.pack(expand=True)
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
        row = tk.Frame(f, bg=P["bg"]);
        row.pack(pady=10)
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
        top = tk.Frame(root, bg=P["bg"]);
        top.pack(fill="x", padx=20, pady=(14, 4))
        tk.Label(top, text=f"🏆  Tournoi  —  {n_total} parties",
                 font=("Consolas", 18, "bold"), fg=P["accent"], bg=P["bg"]).pack(side="left")

        # Barre de progression
        prog_frame = tk.Frame(root, bg=P["bg"]);
        prog_frame.pack(fill="x", padx=20, pady=4)
        self.prog_var = tk.IntVar(value=0)
        style = ttk.Style();
        style.theme_use("clam")
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
        cols = tk.Frame(root, bg=P["bg"]);
        cols.pack(fill="both", expand=True, padx=20, pady=6)

        # --- Colonne gauche : log des parties ---
        left = tk.Frame(cols, bg=P["bg"]);
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Résultats des parties",
                 font=("Consolas", 12, "bold"), fg=P["accent2"], bg=P["bg"]).pack(anchor="w")

        log_frame = tk.Frame(left, bg=P["panel"]);
        log_frame.pack(fill="both", expand=True)
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
        self.log_text.tag_configure("win", foreground=P["success"])
        self.log_text.tag_configure("draw", foreground=P["warn"])
        self.log_text.tag_configure("num", foreground=P["muted"])
        self.log_text.tag_configure("black_lbl", foreground="#aaaaff")
        self.log_text.tag_configure("white_lbl", foreground="#ffddaa")

        # En-tête log
        self._log_write(f"{'#':>3}  {'Noir':<12} {'Blanc':<12} {'Score':>9}  {'Gagnant'}\n", "header")

        # --- Colonne droite : classement cumulé ---
        right = tk.Frame(cols, bg=P["bg"], width=320);
        right.pack(side="right", fill="y", padx=(14, 0))
        right.pack_propagate(False)
        tk.Label(right, text="Classement cumulé",
                 font=("Consolas", 12, "bold"), fg=P["accent2"], bg=P["bg"]).pack(anchor="w")

        self.rank_frame = tk.Frame(right, bg=P["panel"]);
        self.rank_frame.pack(fill="both", expand=True)

        # ── Stats internes ───────────────────────────────────────
        self._stats = {name: {"wins": 0, "losses": 0, "draws": 0, "played": 0}
                       for name in AI_ORDER}
        self._done = 0
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
        hrow = tk.Frame(self.rank_frame, bg=P["card"]);
        hrow.pack(fill="x")
        for text, width in [("IA", 11), ("J", 4), ("V", 4), ("D", 4), ("N", 4), ("%V", 6)]:
            tk.Label(hrow, text=text, width=width, anchor="w",
                     font=("Consolas", 10, "bold"), fg=P["accent"], bg=P["card"]
                     ).pack(side="left", padx=4, pady=3)

        self._rank_rows = {}
        for i, name in enumerate(AI_ORDER):
            bg = P["bg"] if i % 2 == 0 else P["panel"]
            row = tk.Frame(self.rank_frame, bg=bg);
            row.pack(fill="x")
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
            s = self._stats[name]
            row = self._rank_rows[name]
            wr = f"{100 * s['wins'] / s['played']:.0f}%" if s['played'] > 0 else "—"

            # Couleur de fond selon le rang
            bg = bgs[rank % 2]
            for lbl in row.values():
                lbl.config(bg=bg)
            row["name"].master.config(bg=bg)

            row["name"].config(text=name, fg=P["accent"] if rank == 0 else P["text"])
            row["played"].config(text=str(s["played"]))
            row["wins"].config(text=str(s["wins"]), fg=P["success"])
            row["losses"].config(text=str(s["losses"]), fg=P["danger"])
            row["draws"].config(text=str(s["draws"]), fg=P["warn"])
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
        num = f"{r['game_num']:>3}"
        black = r["name_black"]
        white = r["name_white"]
        score = f"{r['score_b']}-{r['score_w']}"
        winner = r["winner"]

        if winner is None:
            result_text = "Nul"
            result_tag = "draw"
        elif winner == black:
            result_text = f"● {black}"
            result_tag = "win"
        else:
            result_text = f"○ {white}"
            result_tag = "win"

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
                    self._stats[name]["wins"] += 1
                    self._stats[name]["played"] += 1
                elif name == l:
                    self._stats[name]["losses"] += 1
                    self._stats[name]["played"] += 1
                elif result["name_black"] == name or result["name_white"] == name:
                    self._stats[name]["draws"] += 1
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

        self._log_write(f"\n{'─' * 46}\n", "header")
        winner = sorted(AI_ORDER, key=lambda n: self._stats[n]["wins"], reverse=True)[0]
        wins = self._stats[winner]["wins"]
        draws = self._stats[winner]["draws"]
        self._log_write(f"Champion du tournoi : {winner}  —  {wins} victoires, {draws} nuls\n", "win")

        # Active le bouton retour
        self.back_btn.config(state="normal", fg="white", bg=P["accent2"])

    # ── Partie humain ─────────────────────────────────────────────────────────

    def start_game(self, mode, ai_fn=None):
        self.mode = mode;
        self.ai_fn = ai_fn
        self.clear();
        self.game = Othello()
        main = tk.Frame(self.root, bg=P["bg"]);
        main.pack(expand=True)
        self.score_label = tk.Label(main, font=("Consolas", 15, "bold"),
                                    fg=P["text"], bg=P["bg"])
        self.score_label.pack(pady=8)
        self.canvas = tk.Canvas(main, width=BOARD_SIZE * CELL_SIZE,
                                height=BOARD_SIZE * CELL_SIZE,
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
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE;
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                fill = "#1e7a42" if ((r, c) in valid and human_turn) else P["board"]
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=P["board_ln"], fill=fill, width=1)
                cell = self.game.board[r][c]
                if cell == BLACK:
                    self.canvas.create_oval(x1 + 6, y1 + 6, x2 - 6, y2 - 6,
                                            fill="#111", outline="#444", width=2)
                elif cell == WHITE:
                    self.canvas.create_oval(x1 + 6, y1 + 6, x2 - 6, y2 - 6,
                                            fill="#f0f0f0", outline="#aaa", width=2)
                elif (r, c) in valid and human_turn:
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    self.canvas.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill=P["accent"], outline="")
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
        f = tk.Frame(self.root, bg=P["bg"]);
        f.pack(expand=True)
        col = P["success"] if passed == total else P["danger"]
        tk.Label(f, text=f"Tests : {passed}/{total} réussis",
                 font=("Consolas", 24, "bold"), fg=col, bg=P["bg"]).pack(pady=18)
        txt = tk.Text(f, font=("Consolas", 10), bg=P["panel"], fg=P["text"],
                      width=74, height=22, bd=0, padx=10, pady=10)
        txt.insert("1.0", output);
        txt.config(state="disabled");
        txt.pack(padx=20)
        self.btn(f, "↩  Retour", self.show_home, small=True)