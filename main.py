import tkinter as tk
from tkinter import messagebox
import copy
import random

BOARD_SIZE = 8
CELL_SIZE = 70

EMPTY = 0
BLACK = 1
WHITE = -1

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

# ===============================
# LOGIQUE DU JEU
# ===============================

class Othello:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.init_board()

    def init_board(self):
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = WHITE
        self.board[mid][mid] = WHITE
        self.board[mid - 1][mid] = BLACK
        self.board[mid][mid - 1] = BLACK

    def is_on_board(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_flips(self, row, col):
        if self.board[row][col] != EMPTY:
            return []
        flips = []
        opponent = -self.current_player
        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            temp = []
            while self.is_on_board(r, c) and self.board[r][c] == opponent:
                temp.append((r, c))
                r += dr
                c += dc
            if self.is_on_board(r, c) and self.board[r][c] == self.current_player:
                flips.extend(temp)
        return flips

    def valid_moves(self):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.get_flips(r, c):
                    moves.append((r, c))
        return moves

    def make_move(self, row, col):
        flips = self.get_flips(row, col)
        if not flips:
            return False
        self.board[row][col] = self.current_player
        for r, c in flips:
            self.board[r][c] = self.current_player
        self.current_player *= -1
        return True

    def game_over(self):
        if self.valid_moves():
            return False
        self.current_player *= -1
        if self.valid_moves():
            self.current_player *= -1
            return False
        return True

    def score(self):
        black = sum(row.count(BLACK) for row in self.board)
        white = sum(row.count(WHITE) for row in self.board)
        return black, white

# ===============================
# IA TRÈS PERFORMANTE
# ===============================

# Table de poids stratégique pour chaque case
WEIGHTS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -2, 5, 1, 1, 5, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
]

def evaluate(game, player):
    board = game.board
    score = 0

    # Poids par position
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                score += WEIGHTS[r][c]
            elif board[r][c] == -player:
                score -= WEIGHTS[r][c]

    # Mobilité
    current = game.current_player
    game.current_player = player
    my_moves = len(game.valid_moves())
    game.current_player = -player
    opp_moves = len(game.valid_moves())
    game.current_player = current
    score += (my_moves - opp_moves) * 10

    # Différence de pions (pour fin de partie)
    black, white = game.score()
    diff = (black - white) if player == BLACK else (white - black)
    score += diff * 2

    return score

def minimax(game, depth, alpha, beta, maximizing, player):
    if depth == 0 or game.game_over():
        return evaluate(game, player), None

    moves = game.valid_moves()
    if not moves:
        game.current_player *= -1
        val, _ = minimax(game, depth-1, alpha, beta, not maximizing, player)
        game.current_player *= -1
        return val, None

    best_move = None

    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move[0], move[1])
            eval_score, _ = minimax(new_game, depth-1, alpha, beta, False, player)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move[0], move[1])
            eval_score, _ = minimax(new_game, depth-1, alpha, beta, True, player)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def ai_move(game, depth):
    _, move = minimax(game, depth, float('-inf'), float('inf'),
                      True, game.current_player)
    return move

# ===============================
# INTERFACE GRAPHIQUE
# ===============================

class OthelloGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Othello Deluxe")
        self.root.geometry("1000x800")
        self.root.configure(bg="#0f0f1a")

        self.mode = None
        self.difficulty = None

        self.show_home()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def modern_button(self, parent, text, command):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 16, "bold"),
            bg="#1f1f2e",
            fg="white",
            activebackground="#3a3a5a",
            bd=0,
            padx=30,
            pady=15,
            cursor="hand2",
            command=command
        )
        btn.pack(pady=15)
        return btn

    # -------------------------
    # PAGE D'ACCUEIL
    # -------------------------
    def show_home(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        tk.Label(frame,
                 text="OTHELLO",
                 font=("Segoe UI", 60, "bold"),
                 fg="#00f5d4",
                 bg="#0f0f1a").pack(pady=40)

        self.modern_button(frame, "👥 Humain vs Humain",
                           lambda: self.start_game("HUMAN"))

        self.modern_button(frame, "🤖 Humain vs IA",
                           self.show_difficulty_menu)

        self.modern_button(frame, "🤖 IA vs IA (50 parties)",
                           self.start_tournament)

    # -------------------------
    def show_difficulty_menu(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        tk.Label(frame,
                 text="Choisissez la difficulté",
                 font=("Segoe UI", 32, "bold"),
                 fg="white",
                 bg="#0f0f1a").pack(pady=40)

        self.modern_button(frame, "Facile (profondeur 2)",
                           lambda: self.start_game("AI", 2))

        self.modern_button(frame, "Moyen (profondeur 4)",
                           lambda: self.start_game("AI", 4))

        self.modern_button(frame, "Difficile (profondeur 6)",
                           lambda: self.start_game("AI", 6))

        self.modern_button(frame, "Retour", self.show_home)

    # -------------------------
    def start_game(self, mode, difficulty=None):
        self.mode = mode
        self.difficulty = difficulty

        self.clear_window()
        self.game = Othello()

        main = tk.Frame(self.root, bg="#0f0f1a")
        main.pack(expand=True)

        self.score_label = tk.Label(main,
                                    font=("Segoe UI", 18),
                                    fg="white",
                                    bg="#0f0f1a")
        self.score_label.pack(pady=10)

        self.canvas = tk.Canvas(main,
                                width=BOARD_SIZE * CELL_SIZE,
                                height=BOARD_SIZE * CELL_SIZE,
                                bg="#006400",
                                highlightthickness=0)
        self.canvas.pack(pady=20)

        self.canvas.bind("<Button-1>", self.click)

        self.update_ui()

    # -------------------------
    def update_ui(self):
        self.canvas.delete("all")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")
                if self.game.board[r][c] == BLACK:
                    self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill="black")
                elif self.game.board[r][c] == WHITE:
                    self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill="white")

        black, white = self.game.score()
        player = "Noir" if self.game.current_player == BLACK else "Blanc"
        self.score_label.config(
            text=f"Tour: {player}    ⚫ {black}   ⚪ {white}"
        )

    # -------------------------
    def click(self, event):
        if self.mode == "AI" and self.game.current_player == WHITE:
            return
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if self.game.make_move(row, col):
            self.update_ui()
            self.check_end()
            if self.mode == "AI":
                self.root.after(500, self.ai_play)

    # -------------------------
    def ai_play(self):
        move = ai_move(self.game, self.difficulty)
        if move:
            self.game.make_move(move[0], move[1])
            self.update_ui()
            self.check_end()

    # -------------------------
    def check_end(self):
        if self.game.game_over():
            black, white = self.game.score()
            if black > white:
                result = "⚫ Noir gagne !"
            elif white > black:
                result = "⚪ Blanc gagne !"
            else:
                result = "Match nul !"
            messagebox.showinfo("Fin de partie",
                                f"{result}\nNoir: {black}\nBlanc: {white}")
            self.show_home()

    # -------------------------
    def start_tournament(self):
        self.clear_window()
        results = {"Noir": 0, "Blanc": 0}

        for _ in range(50):
            game = Othello()
            while not game.game_over():
                move = ai_move(game, 4)  # IA moyenne vs moyenne
                if move:
                    game.make_move(move[0], move[1])
                else:
                    game.current_player *= -1
            black, white = game.score()
            if black > white:
                results["Noir"] += 1
            elif white > black:
                results["Blanc"] += 1

        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)
        tk.Label(frame,
                 text="Résultats Tournoi (50 parties)",
                 font=("Segoe UI", 26, "bold"),
                 fg="white",
                 bg="#0f0f1a").pack(pady=30)
        tk.Label(frame,
                 text=f"Noir: {results['Noir']} victoires",
                 font=("Segoe UI", 18),
                 fg="#00f5d4",
                 bg="#0f0f1a").pack(pady=10)
        tk.Label(frame,
                 text=f"Blanc: {results['Blanc']} victoires",
                 font=("Segoe UI", 18),
                 fg="#ff4d6d",
                 bg="#0f0f1a").pack(pady=10)
        self.modern_button(frame, "Retour", self.show_home)

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = OthelloGUI(root)
    root.mainloop()