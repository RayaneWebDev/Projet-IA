import tkinter as tk
from tkinter import messagebox
import copy
import random
import time

# ================================================================
#  CONSTANTES GLOBALES
# ================================================================

BOARD_SIZE = 8  # Taille du plateau (8x8)
CELL_SIZE = 70  # Taille en pixels de chaque case

EMPTY = 0       # Case vide
BLACK = 1       # Joueur Noir (commence toujours)
WHITE = -1      # Joueur Blanc


# Les 8 directions possibles sur le plateau (haut, bas, gauche, droite, diagonales)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

# ================================================================
#  TABLE DE POIDS POSITIONNELS
#  Chaque case a une valeur stratégique :
#    - Coins (100)       : très forts, impossibles à retourner
#    - Adjacents coins (-50/-20) : dangereux car offrent le coin à l'adversaire
#    - Bords (10/5)      : relativement stables
#    - Centre (0/1)      : neutres
# ================================================================
WEIGHTS = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,   5,   1,   1,   5,  -2,  10],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [ 10,  -2,   5,   1,   1,   5,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
]


# ================================================================
#  SECTION 1 : LOGIQUE DU JEU
#  (Code de ton binôme — non modifié)
# ================================================================

class Othello:
    """
    Représente l'état complet d'une partie d'Othello.
    Contient le plateau, le joueur courant, et toutes les règles du jeu.
    """

    def __init__(self):
        # Plateau 8x8 rempli de cases vides
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK   # Noir commence toujours
        self.init_board()

    def init_board(self):
        """Place les 4 pions initiaux au centre du plateau."""
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = WHITE
        self.board[mid    ][mid    ] = WHITE
        self.board[mid - 1][mid    ] = BLACK
        self.board[mid    ][mid - 1] = BLACK

    def is_on_board(self, row, col):
        """Vérifie qu'une case (row, col) est bien dans les limites du plateau."""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_flips(self, row, col):
        """
        Retourne la liste des pions qui seraient retournés si le joueur
        courant jouait en (row, col). Liste vide = coup invalide.
        """
        if self.board[row][col] != EMPTY:
            return []
        flips    = []
        opponent = -self.current_player

        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            temp  = []
            # On avance dans la direction tant qu'on rencontre des pions adverses
            while self.is_on_board(r, c) and self.board[r][c] == opponent:
                temp.append((r, c))
                r += dr
                c += dc
            # Si on finit sur un pion allié, on valide le retournement
            if self.is_on_board(r, c) and self.board[r][c] == self.current_player:
                flips.extend(temp)

        return flips

    def valid_moves(self):
        """Retourne la liste de tous les coups valides pour le joueur courant."""
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.get_flips(r, c):
                    moves.append((r, c))
        return moves

    def make_move(self, row, col):
        """
        Joue le coup (row, col) pour le joueur courant.
        Retourne True si le coup est valide et a été joué, False sinon.
        """
        flips = self.get_flips(row, col)
        if not flips:
            return False
        self.board[row][col] = self.current_player
        for r, c in flips:
            self.board[r][c] = self.current_player
        self.current_player *= -1   # Change de joueur
        return True

    def game_over(self):
        """
        Vérifie si la partie est terminée.
        La partie s'arrête quand AUCUN des deux joueurs ne peut jouer.
        """
        if self.valid_moves():
            return False
        # Le joueur courant ne peut pas jouer → on teste l'autre joueur
        self.current_player *= -1
        if self.valid_moves():
            self.current_player *= -1   # On remet comme avant
            return False
        return True  # Ni l'un ni l'autre ne peut jouer → fin de partie

    def score(self):
        """Retourne le nombre de pions (noir, blanc) sur le plateau."""
        black = sum(row.count(BLACK) for row in self.board)
        white = sum(row.count(WHITE) for row in self.board)
        return black, white

# ================================================================
#  SECTION 2 : FONCTIONS D'ÉVALUATION
#
#  Une fonction d'évaluation estime la "valeur" d'un état de jeu
#  du point de vue d'un joueur donné (score positif = avantage).
#
#  Trois fonctions de difficulté croissante :
#    1. evaluate_naive    → compte juste les pions (IA facile)
#    2. evaluate_mobility → mobilité + coins (IA moyenne)
#    3. evaluate_advanced → poids + mobilité + pions (IA difficile)
# ================================================================

def evaluate_naive(game, player):
    """
    ÉVALUATION NAÏVE — utilisée par l'IA Facile.

    Stratégie : maximiser simplement le nombre de ses pions sur le plateau.
    C'est la stratégie la plus basique et souvent mauvaise à Othello,
    car avoir beaucoup de pions en milieu de partie peut être un désavantage.

    Retourne : (mes_pions - pions_adversaire)
    """
    black, white = game.score()
    if player == BLACK:
        return black - white
    else:
        return white - black


def evaluate_mobility(game, player):
    """
    ÉVALUATION PAR MOBILITÉ — utilisée par l'IA Moyenne.

    Stratégie : favoriser la liberté de mouvement (avoir plus de coups
    disponibles que l'adversaire) et capturer les coins (valeur 50 chacun).

    La mobilité est importante à Othello : plus on a de choix, moins
    on est contraint par l'adversaire.

    Retourne : score basé sur (mobilité + bonus coins)
    """
    score = 0

    # --- Bonus pour les coins capturés  ---
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in corners:
        if game.board[r][c] == player:
            score += 50
        elif game.board[r][c] == -player:
            score -= 50

    # --- Mobilité : comparer le nombre de coups disponibles ---
    # On sauvegarde le joueur courant pour ne pas perturber l'état du jeu
    saved = game.current_player

    game.current_player = player
    my_moves = len(game.valid_moves())

    game.current_player = -player
    opp_moves = len(game.valid_moves())

    game.current_player = saved   # Restauration du joueur courant

    # Formule : différence de mobilité, pondérée par 10
    if my_moves + opp_moves > 0:
        score += 10 * (my_moves - opp_moves)

    return score


def evaluate_advanced(game, player):
    """
    ÉVALUATION AVANCÉE — utilisée par l'IA Difficile.

    Combine trois critères :
      1. Poids positionnels (table WEIGHTS) : valorise coins, bords, etc.
      2. Mobilité : liberté de mouvement
      3. Différence de pions : utile en fin de partie

    C'est la fonction la plus complète et la plus efficace.
    """
    board = game.board
    score = 0

    # --- 1. Score positionnel (table WEIGHTS) ---
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == player:
                score += WEIGHTS[r][c]
            elif board[r][c] == -player:
                score -= WEIGHTS[r][c]

    # --- 2. Mobilité ---
    saved = game.current_player

    game.current_player = player
    my_moves = len(game.valid_moves())

    game.current_player = -player
    opp_moves = len(game.valid_moves())

    game.current_player = saved

    score += (my_moves - opp_moves) * 10

    # --- 3. Différence de pions (utile surtout en fin de partie) ---
    black, white = game.score()
    diff = (black - white) if player == BLACK else (white - black)
    score += diff * 2

    return score

def minimax(game, depth, alpha, beta, maximizing, player, eval_fn):
    """
    Algorithme Minimax avec élagage Alpha-Bêta.

    Paramètres :
      game        : état actuel du jeu (objet Othello)
      depth       : profondeur restante à explorer (0 = feuille)
      alpha       : meilleur score garanti pour MAX (initialement -inf)
      beta        : meilleur score garanti pour MIN (initialement +inf)
      maximizing  : True si c'est le tour de MAX (notre IA)
      player      : le joueur pour lequel on optimise (BLACK ou WHITE)
      eval_fn     : la fonction d'évaluation à utiliser

    Retourne : (score, meilleur_coup)
    """

    # Cas de base : profondeur 0 ou partie terminée → on évalue l'état
    if depth == 0 or game.game_over():
        return eval_fn(game, player), None

    moves = game.valid_moves()

    # Si aucun coup disponible → le joueur passe son tour
    if not moves:
        game.current_player *= -1
        val, _ = minimax(game, depth - 1, alpha, beta, not maximizing, player, eval_fn)
        game.current_player *= -1
        return val, None

    best_move = None

    if maximizing:
        # MAX cherche le score le plus élevé
        max_eval = float('-inf')
        for move in moves:
            new_game = copy.deepcopy(game)           # Copie pour ne pas modifier l'état réel
            new_game.make_move(move[0], move[1])
            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, False, player, eval_fn)
            if eval_score > max_eval:
                max_eval  = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:                         # Coupure β : branche inutile
                break
        return max_eval, best_move

    else:
        # MIN cherche le score le plus bas (il joue contre nous)
        min_eval = float('inf')
        for move in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(move[0], move[1])
            eval_score, _ = minimax(new_game, depth - 1, alpha, beta, True, player, eval_fn)
            if eval_score < min_eval:
                min_eval  = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:                         # Coupure α : branche inutile
                break
        return min_eval, best_move

# ================================================================
#  SECTION 4 : LES 4 NIVEAUX D'IA
#
#  Chaque IA est une fonction qui reçoit un état de jeu
#  et retourne le coup à jouer sous forme (row, col).
# ================================================================

def ai_random(game):
    """
    IA ALÉATOIRE (Niveau 0 — Baseline).
    Choisit un coup légal au hasard.
    Utile comme référence dans les tournois : toute IA sérieuse doit la battre.
    """
    moves = game.valid_moves()
    if moves:
        return random.choice(moves)
    return None


def ai_easy(game):
    """
    IA FACILE (Niveau 1 — Profondeur 2).
    Utilise Minimax avec évaluation naïve (compte les pions).
    Joue de façon médiocre : prend des pions sans réfléchir aux coins/bords.
    """
    _, move = minimax(
        game,
        depth=2,
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing=True,
        player=game.current_player,
        eval_fn=evaluate_naive          # Fonction d'évaluation simple
    )
    return move


def ai_medium(game):
    """
    IA MOYENNE (Niveau 2 — Profondeur 4).
    Utilise Minimax avec évaluation par mobilité + coins.
    Comprend l'importance des coins et essaie d'avoir plus de choix.
    """
    _, move = minimax(
        game,
        depth=4,
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing=True,
        player=game.current_player,
        eval_fn=evaluate_mobility       # Fonction d'évaluation intermédiaire
    )
    return move


def ai_hard(game):
    """
    IA DIFFICILE (Niveau 3 — Profondeur 6).
    Utilise Minimax avec évaluation avancée (poids + mobilité + pions).
    Joue de façon très stratégique, difficile à battre pour un humain.
    """
    # Compter les cases vides
    empty_cells = sum(row.count(EMPTY) for row in game.board)

    # Adapter la profondeur
    if empty_cells > 50:  # Début de partie : on baisse à 4 pour aller vite
        d = 4
    else:  # Reste de la partie
        d = 6

    _, move = minimax(
        game,
        depth=d,
        alpha=float('-inf'),
        beta=float('inf'),
        maximizing=True,
        player=game.current_player,
        eval_fn=evaluate_advanced       # Fonction d'évaluation complète
    )
    return move


# Dictionnaire pratique pour accéder aux IA par nom
AI_PLAYERS = {
    "Aléatoire": ai_random,
    "Facile":    ai_easy,
    "Moyen":     ai_medium,
    "Difficile": ai_hard,
}

# ================================================================
#  SECTION 5 : MOTEUR DE TOURNOI
#
#  Fait s'affronter deux IA un certain nombre de fois et
#  retourne les statistiques (victoires, défaites, nuls, temps).
# ================================================================

def play_one_game(ai_black_fn, ai_white_fn):
    """
    Joue une partie complète entre deux fonctions IA.

    ai_black_fn : fonction IA qui joue Noir (ex: ai_easy)
    ai_white_fn : fonction IA qui joue Blanc (ex: ai_hard)

    Retourne : (gagnant, score_noir, score_blanc)
      gagnant = BLACK, WHITE, ou EMPTY (nul)
    """
    game = Othello()

    while not game.game_over():
        # Sélection de la fonction IA en fonction du joueur courant
        if game.current_player == BLACK:
            move = ai_black_fn(game)
        else:
            move = ai_white_fn(game)

        if move:
            game.make_move(move[0], move[1])
        else:
            # Aucun coup disponible → passage de tour
            game.current_player *= -1

    black_score, white_score = game.score()

    if black_score > white_score:
        return BLACK, black_score, white_score
    elif white_score > black_score:
        return WHITE, black_score, white_score
    else:
        return EMPTY, black_score, white_score   # Match nul


def run_tournament(ai_name_a, ai_name_b, n_games=50):
    """
    Tournoi entre deux IA : chaque IA joue n_games/2 fois en Noir et n_games/2 fois en Blanc
    pour neutraliser l'avantage du premier joueur.

    Retourne un dictionnaire avec :
      - wins_a, wins_b : victoires de chaque IA
      - draws          : matchs nuls
      - avg_time_a     : temps moyen de réflexion par coup de l'IA A
      - total_games    : nombre total de parties jouées
    """
    ai_fn_a = AI_PLAYERS[ai_name_a]
    ai_fn_b = AI_PLAYERS[ai_name_b]

    wins_a  = 0
    wins_b  = 0
    draws   = 0
    half    = n_games // 2

    print(f"\n  Tournoi : {ai_name_a} vs {ai_name_b} ({n_games} parties)...")

    for i in range(n_games):
        # On alterne les couleurs pour un tournoi équitable
        if i < half:
            # IA_A joue Noir, IA_B joue Blanc
            winner, bs, ws = play_one_game(ai_fn_a, ai_fn_b)
            if   winner == BLACK: wins_a += 1
            elif winner == WHITE: wins_b += 1
            else:                 draws  += 1
        else:
            # IA_A joue Blanc, IA_B joue Noir
            winner, bs, ws = play_one_game(ai_fn_b, ai_fn_a)
            if   winner == WHITE: wins_a += 1
            elif winner == BLACK: wins_b += 1
            else:                 draws  += 1

    return {
        "ia_a":        ai_name_a,
        "ia_b":        ai_name_b,
        "wins_a":      wins_a,
        "wins_b":      wins_b,
        "draws":       draws,
        "total_games": n_games,
    }


def run_full_tournament(n_games=50):
    """
    Lance le tournoi complet entre TOUTES les paires d'IA.
    Retourne la liste de tous les résultats.
    """
    ai_names = list(AI_PLAYERS.keys())   # ["Aléatoire", "Facile", "Moyen", "Difficile"]
    results  = []

    # Génère tous les couples uniques (sans répétition ni auto-affrontement)
    for i in range(len(ai_names)):
        for j in range(i + 1, len(ai_names)):
            result = run_tournament(ai_names[i], ai_names[j], n_games)
            results.append(result)

    return results

# ================================================================
#  SECTION 6 : TESTS UNITAIRES
#
#  Vérifient que la logique du jeu est correcte.
#  Chaque test affiche OK ou ERREUR.
# ================================================================

def run_tests():
    """
    Lance tous les tests unitaires du moteur de jeu.
    Retourne (tests_réussis, tests_totaux).
    """
    passed = 0
    total  = 0

    def test(name, condition):
        """Affiche le résultat d'un test et incrémente les compteurs."""
        nonlocal passed, total
        total += 1
        if condition:
            print(f"  [OK]    {name}")
            passed += 1
        else:
            print(f"  [ERREUR] {name}")

    print("\n" + "="*50)
    print("  TESTS UNITAIRES")
    print("="*50)

    # --- TEST 1 : Initialisation du plateau ---
    g = Othello()
    mid = BOARD_SIZE // 2
    test(
        "Initialisation : 2 pions noirs au centre",
        g.board[mid-1][mid] == BLACK and g.board[mid][mid-1] == BLACK
    )
    test(
        "Initialisation : 2 pions blancs au centre",
        g.board[mid-1][mid-1] == WHITE and g.board[mid][mid] == WHITE
    )
    test(
        "Initialisation : joueur courant = Noir",
        g.current_player == BLACK
    )

    # --- TEST 2 : Coups valides en début de partie ---
    moves = g.valid_moves()
    test(
        "Début de partie : exactement 4 coups valides pour Noir",
        len(moves) == 4
    )
    test(
        "Début de partie : le coup (2,3) est valide",
        (2, 3) in moves
    )
    test(
        "Début de partie : le coup (0,0) est invalide",
        (0, 0) not in moves
    )

    # --- TEST 3 : Retournement de pions ---
    g2 = Othello()
    g2.make_move(2, 3)    # Noir joue en (2,3)
    test(
        "Après (2,3) : le pion en (3,3) est retourné en Noir",
        g2.board[3][3] == BLACK
    )
    test(
        "Après (2,3) : c'est maintenant au tour de Blanc",
        g2.current_player == WHITE
    )

    # --- TEST 4 : Coup invalide ---
    g3  = Othello()
    res = g3.make_move(0, 0)   # Case d'angle vide sans retournement possible
    test(
        "Le coup invalide (0,0) retourne False",
        res == False
    )
    test(
        "Après coup invalide : le plateau n'a pas changé",
        g3.board[0][0] == EMPTY
    )

    # --- TEST 5 : Détection de fin de partie ---
    g4 = Othello()
    test(
        "Partie fraîche : game_over() retourne False",
        g4.game_over() == False
    )

    # --- TEST 6 : Calcul du score ---
    g5 = Othello()
    b, w = g5.score()
    test(
        "Score initial : 2 noirs et 2 blancs",
        b == 2 and w == 2
    )

    # --- TEST 7 : is_on_board ---
    test(
        "is_on_board(0,0) = True (coin valide)",
        g.is_on_board(0, 0) == True
    )
    test(
        "is_on_board(-1,0) = False (hors plateau)",
        g.is_on_board(-1, 0) == False
    )
    test(
        "is_on_board(8,8) = False (hors plateau)",
        g.is_on_board(8, 8) == False
    )

    # --- TEST 8 : Les IA retournent bien un coup valide ---
    g6 = Othello()
    move_random = ai_random(g6)
    test(
        "IA Aléatoire : retourne un coup valide",
        move_random in g6.valid_moves()
    )
    move_easy = ai_easy(g6)
    test(
        "IA Facile : retourne un coup valide",
        move_easy in g6.valid_moves()
    )

    print("="*50)
    print(f"  Résultat : {passed}/{total} tests réussis")
    print("="*50 + "\n")

    return passed, total

# ================================================================
#  SECTION 7 : INTERFACE EN LIGNE DE COMMANDE (CLI)
#
#  Permet de jouer sans interface graphique (compatible Linux).
# ================================================================

def print_board(game):
    """Affiche le plateau dans le terminal avec coordonnées."""
    print("\n    " + "  ".join(str(c) for c in range(BOARD_SIZE)))
    print("   " + "─" * (BOARD_SIZE * 3))
    for r in range(BOARD_SIZE):
        row_str = f" {r} │"
        for c in range(BOARD_SIZE):
            cell = game.board[r][c]
            if   cell == BLACK: row_str += " ● "   # Pion noir
            elif cell == WHITE: row_str += " ○ "   # Pion blanc
            else:               row_str += " · "   # Case vide
        print(row_str)
    black, white = game.score()
    print(f"\n  Score → ● Noir: {black}  |  ○ Blanc: {white}")


def cli_play_human_vs_ai(ai_name="Difficile"):
    """
    Lance une partie Humain (Noir) vs IA dans le terminal.
    L'humain entre ses coups sous la forme : ligne colonne
    """
    print("\n" + "="*50)
    print("  OTHELLO — Humain vs IA")
    print(f"  IA choisie : {ai_name}")
    print("  Entrez vos coups sous la forme : ligne colonne")
    print("="*50)

    game   = Othello()
    ai_fn  = AI_PLAYERS[ai_name]

    while not game.game_over():
        print_board(game)
        valid = game.valid_moves()

        if game.current_player == BLACK:
            # Tour du joueur humain
            print(f"\n  Votre tour (●Noir). Coups valides : {valid}")
            while True:
                try:
                    inp = input("  Votre coup (ligne colonne) : ").strip().split()
                    row, col = int(inp[0]), int(inp[1])
                    if (row, col) in valid:
                        game.make_move(row, col)
                        break
                    else:
                        print("  ❌ Coup invalide, réessayez.")
                except (ValueError, IndexError):
                    print("  ❌ Format incorrect (exemple : 2 3)")
        else:
            # Tour de l'IA
            print(f"\n  Tour de l'IA ({ai_name})...")
            t_start = time.time()
            move    = ai_fn(game)
            elapsed = time.time() - t_start

            if move:
                game.make_move(move[0], move[1])
                print(f"  IA joue en {move} (réflexion : {elapsed:.2f}s)")
            else:
                print("  IA passe son tour.")
                game.current_player *= -1

    # Fin de partie
    print_board(game)
    black, white = game.score()
    print("\n  ══════════ FIN DE PARTIE ══════════")
    if   black > white: print("  ● Noir gagne !")
    elif white > black: print("  ○ Blanc gagne !")
    else:               print("  Match nul !")
    print(f"  Score final → Noir: {black}  |  Blanc: {white}")


def cli_run_tournament_report(n_games=50):
    """
    Lance le tournoi complet en CLI et affiche un rapport détaillé.
    """
    print("\n" + "="*60)
    print("  TOURNOI COMPLET — TOUTES LES IAs")
    print(f"  {n_games} parties par paire")
    print("="*60)

    results = run_full_tournament(n_games)

    print("\n  RÉSULTATS :")
    print(f"  {'Matchup':<30} {'IA_A':>6} {'IA_B':>6} {'Nuls':>6}")
    print("  " + "─"*52)

    for r in results:
        matchup = f"{r['ia_a']} vs {r['ia_b']}"
        print(
            f"  {matchup:<30} "
            f"{r['wins_a']:>5}V "
            f"{r['wins_b']:>5}V "
            f"{r['draws']:>5}N"
        )

    print("="*60)
# ================================================================
#  SECTION 8 : INTERFACE GRAPHIQUE (tkinter)
#  (Code de ton binôme — conservé et étendu)
# ================================================================

class OthelloGUI:
    """
    Interface graphique complète du jeu Othello.
    Gère le menu principal, les parties Humain/IA, et les tournois.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Othello Deluxe")
        self.root.geometry("1000x800")
        self.root.configure(bg="#0f0f1a")

        self.mode       = None
        self.ai_fn      = None   # Fonction IA choisie

        self.show_home()

    # ----------------------------------------------------------
    # UTILITAIRES UI
    # ----------------------------------------------------------

    def clear_window(self):
        """Supprime tous les widgets de la fenêtre."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def modern_button(self, parent, text, command):
        """Crée un bouton stylisé réutilisable."""
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

    # ----------------------------------------------------------
    # PAGE D'ACCUEIL
    # ----------------------------------------------------------

    def show_home(self):
        """Affiche le menu principal."""
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        tk.Label(
            frame, text="OTHELLO",
            font=("Segoe UI", 60, "bold"),
            fg="#00f5d4", bg="#0f0f1a"
        ).pack(pady=40)

        self.modern_button(frame, "👥 Humain vs Humain",
                           lambda: self.start_game("HUMAN"))
        self.modern_button(frame, "🤖 Humain vs IA",
                           self.show_difficulty_menu)
        self.modern_button(frame, "🏆 Tournoi IA vs IA",
                           self.show_tournament_menu)
        self.modern_button(frame, "🧪 Lancer les Tests",
                           self.show_test_results)

    # ----------------------------------------------------------
    # MENU DIFFICULTÉ
    # ----------------------------------------------------------

    def show_difficulty_menu(self):
        """Affiche le menu de sélection de la difficulté."""
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        tk.Label(
            frame, text="Choisissez la difficulté",
            font=("Segoe UI", 32, "bold"),
            fg="white", bg="#0f0f1a"
        ).pack(pady=40)

        self.modern_button(frame, "🎲 Aléatoire (baseline)",
                           lambda: self.start_game("AI", ai_random))
        self.modern_button(frame, "😊 Facile  (profondeur 2, naïf)",
                           lambda: self.start_game("AI", ai_easy))
        self.modern_button(frame, "😐 Moyen   (profondeur 4, mobilité)",
                           lambda: self.start_game("AI", ai_medium))
        self.modern_button(frame, "😈 Difficile (profondeur 6, avancé)",
                           lambda: self.start_game("AI", ai_hard))
        self.modern_button(frame, "↩ Retour", self.show_home)

    # ----------------------------------------------------------
    # MENU TOURNOI
    # ----------------------------------------------------------

    def show_tournament_menu(self):
        """Affiche le menu de lancement de tournoi."""
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        tk.Label(
            frame, text="Tournoi IA vs IA",
            font=("Segoe UI", 32, "bold"),
            fg="white", bg="#0f0f1a"
        ).pack(pady=40)

        tk.Label(
            frame,
            text="Toutes les IA s'affrontent.\nChaque paire joue 50 parties (25 par couleur).",
            font=("Segoe UI", 14),
            fg="#aaaaaa", bg="#0f0f1a", justify="center"
        ).pack(pady=10)

        # Avertissement sur le temps
        tk.Label(
            frame,
            text="⚠️  Peut prendre plusieurs minutes.",
            font=("Segoe UI", 12, "italic"),
            fg="#ff9900", bg="#0f0f1a"
        ).pack(pady=5)

        self.modern_button(frame, "▶ Lancer le tournoi (50 parties/paire)",
                           lambda: self.run_gui_tournament(50))
        self.modern_button(frame, "⚡ Tournoi rapide (10 parties/paire)",
                           lambda: self.run_gui_tournament(10))
        self.modern_button(frame, "↩ Retour", self.show_home)

    # ----------------------------------------------------------
    # LANCEMENT D'UNE PARTIE
    # ----------------------------------------------------------

    def start_game(self, mode, ai_fn=None):
        """
        Lance une partie.
        mode   : "HUMAN" (H vs H) ou "AI" (H vs IA)
        ai_fn  : la fonction IA à utiliser (si mode == "AI")
        """
        self.mode  = mode
        self.ai_fn = ai_fn

        self.clear_window()
        self.game = Othello()

        main = tk.Frame(self.root, bg="#0f0f1a")
        main.pack(expand=True)

        self.score_label = tk.Label(
            main, font=("Segoe UI", 18),
            fg="white", bg="#0f0f1a"
        )
        self.score_label.pack(pady=10)

        self.canvas = tk.Canvas(
            main,
            width=BOARD_SIZE * CELL_SIZE,
            height=BOARD_SIZE * CELL_SIZE,
            bg="#006400",
            highlightthickness=0
        )
        self.canvas.pack(pady=20)
        self.canvas.bind("<Button-1>", self.click)

        self.modern_button(main, "↩ Quitter la partie", self.show_home)

        self.update_ui()

    # ----------------------------------------------------------
    # MISE À JOUR DE L'INTERFACE
    # ----------------------------------------------------------

    def update_ui(self):
        """Redessine le plateau et met à jour le score."""
        self.canvas.delete("all")

        valid = self.game.valid_moves()   # Coups valides du joueur courant

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE

                # Surligne les coups valides en vert clair
                if (r, c) in valid and not (self.mode == "AI" and self.game.current_player == WHITE):
                    self.canvas.create_rectangle(x1, y1, x2, y2,
                                                 outline="black", fill="#228B22")
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")

                # Dessine les pions
                if self.game.board[r][c] == BLACK:
                    self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill="black")
                elif self.game.board[r][c] == WHITE:
                    self.canvas.create_oval(x1+8, y1+8, x2-8, y2-8, fill="white")

        black, white = self.game.score()
        current = "Noir ●" if self.game.current_player == BLACK else "Blanc ○"
        self.score_label.config(
            text=f"Tour : {current}    ⚫ {black}   ⚪ {white}"
        )

    # ----------------------------------------------------------
    # GESTION DES CLICS
    # ----------------------------------------------------------

    def click(self, event):
        """Gère le clic du joueur humain sur le plateau."""
        # En mode IA, bloque le clic quand c'est le tour de l'IA (Blanc)
        if self.mode == "AI" and self.game.current_player == WHITE:
            return

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE

        if self.game.make_move(row, col):
            self.update_ui()
            # On vérifie immédiatement si la partie est finie
            if self.game.game_over():
                self.root.after(500, self.check_end)
                return

            # Si c'est au tour de l'IA
            if self.mode == "AI":
                self.root.after(500, self.ai_play)

    def ai_play(self):
        """Fait jouer l'IA et met à jour l'interface."""
        move = self.ai_fn(self.game)
        if move:
            self.game.make_move(move[0], move[1])
        else:
            # L'IA doit passer son tour
            self.game.current_player *= -1
        self.update_ui()
        # On vérifie la fin de partie après le coup de l'IA
        if self.game.game_over():
            self.root.after(500, self.check_end)

    # ----------------------------------------------------------
    # FIN DE PARTIE
    # ----------------------------------------------------------

    def check_end(self):
        """Vérifie si la partie est terminée et affiche le résultat."""
        if self.game.game_over():
            black, white = self.game.score()
            if   black > white: result = "⚫ Noir gagne !"
            elif white > black: result = "⚪ Blanc gagne !"
            else:               result = "🤝 Match nul !"
            messagebox.showinfo(
                "Fin de partie",
                f"{result}\nNoir: {black}  |  Blanc: {white}"
            )
            self.show_home()

    # ----------------------------------------------------------
    # TOURNOI GRAPHIQUE
    # ----------------------------------------------------------

    def run_gui_tournament(self, n_games):
        """
        Lance le tournoi complet et affiche les résultats dans l'interface.
        Un label de chargement est affiché pendant l'exécution.
        """
        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        loading = tk.Label(
            frame,
            text="⏳ Tournoi en cours...\nCela peut prendre plusieurs minutes.",
            font=("Segoe UI", 18),
            fg="#ffcc00", bg="#0f0f1a", justify="center"
        )
        loading.pack(pady=40)
        self.root.update()   # Force le rafraîchissement de l'interface

        # Lance le tournoi (bloquant)
        results = run_full_tournament(n_games)

        # Efface le label de chargement
        loading.destroy()

        tk.Label(
            frame,
            text=f"🏆 Résultats Tournoi ({n_games} parties/paire)",
            font=("Segoe UI", 26, "bold"),
            fg="white", bg="#0f0f1a"
        ).pack(pady=20)

        # En-tête du tableau
        header = tk.Frame(frame, bg="#1f1f2e")
        header.pack(fill="x", padx=40, pady=5)
        for text, w in [("Matchup", 28), ("Victoires A", 12), ("Victoires B", 12), ("Nuls", 8)]:
            tk.Label(
                header, text=text, width=w,
                font=("Segoe UI", 13, "bold"),
                fg="#00f5d4", bg="#1f1f2e", anchor="w"
            ).pack(side="left", padx=5)

        # Lignes de résultats
        colors = ["#1a1a2e", "#16213e"]
        for idx, r in enumerate(results):
            row_frame = tk.Frame(frame, bg=colors[idx % 2])
            row_frame.pack(fill="x", padx=40)

            matchup = f"{r['ia_a']} vs {r['ia_b']}"
            data    = [
                (matchup,               28),
                (f"{r['wins_a']} V",    12),
                (f"{r['wins_b']} V",    12),
                (f"{r['draws']} N",      8),
            ]
            for text, w in data:
                tk.Label(
                    row_frame, text=text, width=w,
                    font=("Segoe UI", 12),
                    fg="white", bg=colors[idx % 2], anchor="w"
                ).pack(side="left", padx=5, pady=4)

        self.modern_button(frame, "↩ Retour au menu", self.show_home)

    # ----------------------------------------------------------
    # AFFICHAGE DES TESTS
    # ----------------------------------------------------------

    def show_test_results(self):
        """Lance les tests unitaires et affiche le résultat dans une fenêtre."""
        # On redirige la sortie pour capturer les résultats
        import io, sys
        buffer      = io.StringIO()
        sys.stdout  = buffer
        passed, total = run_tests()
        sys.stdout  = sys.__stdout__
        output      = buffer.getvalue()

        self.clear_window()
        frame = tk.Frame(self.root, bg="#0f0f1a")
        frame.pack(expand=True)

        color = "#00f5d4" if passed == total else "#ff4d6d"
        tk.Label(
            frame,
            text=f"Tests : {passed}/{total} réussis",
            font=("Segoe UI", 28, "bold"),
            fg=color, bg="#0f0f1a"
        ).pack(pady=20)

        # Affiche le détail dans une zone de texte scrollable
        text_widget = tk.Text(
            frame,
            font=("Courier New", 12),
            bg="#1a1a2e", fg="white",
            width=55, height=20,
            bd=0, padx=10, pady=10
        )
        text_widget.insert("1.0", output)
        text_widget.config(state="disabled")
        text_widget.pack(padx=20)

        self.modern_button(frame, "↩ Retour", self.show_home)
# ================================================================
#  SECTION 9 : POINT D'ENTRÉE DU PROGRAMME
# ================================================================

if __name__ == "__main__":
    import sys

    # Si on passe l'argument "cli" → mode terminal
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        print("Mode CLI sélectionné.")
        print("1) Jouer contre l'IA")
        print("2) Lancer les tests")
        print("3) Lancer le tournoi complet")
        choice = input("Votre choix : ").strip()

        if choice == "1":
            print("Niveaux : Aléatoire, Facile, Moyen, Difficile")
            level = input("Choisissez le niveau : ").strip()
            if level not in AI_PLAYERS:
                level = "Difficile"
            cli_play_human_vs_ai(level)

        elif choice == "2":
            run_tests()

        elif choice == "3":
            n = input("Nombre de parties par paire (défaut 50) : ").strip()
            n = int(n) if n.isdigit() else 50
            cli_run_tournament_report(n)

    else:
        # Mode graphique (comportement par défaut)
        root = tk.Tk()
        app  = OthelloGUI(root)
        root.mainloop()