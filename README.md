# 🧠 Othello IA — Jeu, IA & Tournois en Temps Réel

Application complète du jeu **Othello/Reversi** développée en Python avec :

- 🎮 Interface graphique moderne (Tkinter)
- 🤖 Plusieurs intelligences artificielles
- 🏆 Tournois IA vs IA
- ⚡ Exécution parallèle avec multiprocessing
- 🧵 Communication thread-safe avec threading + queue
- 🧪 Système de tests unitaires

---

# 🚀 Fonctionnalités

## 🎮 Modes de jeu

### 👥 Humain vs Humain
Deux joueurs jouent sur le même plateau.

### 🤖 Humain vs IA
Affrontez plusieurs niveaux d’intelligence artificielle.

### 🏆 Tournoi IA vs IA
Les IA s’affrontent automatiquement dans un tournoi :

- parties générées aléatoirement
- alternance Noir/Blanc
- exécution parallèle
- classement dynamique en direct

---

# 🤖 Niveaux d’IA

## 🎲 Aléatoire
Choisit un coup valide au hasard.

## 😊 Facile
Minimax profondeur 2.

## 😐 Moyen
Minimax + heuristique de mobilité.

## 😈 Difficile
Minimax avancé :

- poids positionnels
- mobilité
- contrôle des coins
- profondeur adaptative

---

# 🧠 Algorithmes utilisés

## Minimax avec Alpha-Beta Pruning

Le moteur IA utilise :

- recherche Minimax
- optimisation Alpha-Beta
- fonctions d’évaluation heuristiques

---

# 📊 Système de tournoi IA

Le tournoi utilise :

- `multiprocessing.Pool`
- exécution parallèle des parties
- génération aléatoire des matchs
- équilibrage des couleurs

## Affichage temps réel

L’interface affiche :

- résultats des parties
- gagnants
- scores
- progression
- classement cumulé

---

# ⚡ Concurrence & Parallélisme

Le projet combine :

## multiprocessing
Pour jouer plusieurs parties simultanément.

## threading
Pour éviter de bloquer l’interface Tkinter.

## queue.Queue
Pour transmettre les résultats des workers vers l’UI.

---

# 🎨 Interface Graphique

Interface développée avec Tkinter :

- thème sombre moderne
- plateau interactif
- coups valides affichés
- classement dynamique
- barre de progression tournoi
- résultats en direct

---

# 🧩 Architecture du projet

```text
project/
│
├── main.py
│
├── core/
│   ├── constants.py
│   └── game.py
│
├── ai/
│   ├── evaluation.py
│   ├── minimax.py
│   └── players.py
│
├── tournament/
│   ├── engine.py
│   └── workers.py
│
├── ui/
│   ├── gui.py
│   └── cli.py
│
└── tests/
    └── test_othello.py
```

---

# 🧠 Logique du jeu

## Règles implémentées

- validation des coups
- capture des pions
- retournement automatique
- gestion des passes
- détection de fin de partie

---

# 🔁 Gestion du PASS automatique

Lorsqu’un joueur n’a aucun coup valide :

```python
if not self.game.valid_moves():
    self.game.current_player *= -1
```

Si les deux joueurs sont bloqués :

➡️ la partie se termine automatiquement.

---

# 🧪 Tests unitaires

Le projet contient un système de tests permettant de vérifier :

- initialisation du plateau
- coups valides
- retournement des pions
- copie du jeu
- détection fin de partie
- système de PASS

---

# ⚙️ Installation

## Prérequis

- Python 3.10+
- Tkinter

---

# ▶️ Exécution

## Interface graphique

```bash
python main.py
```

## Mode CLI

```bash
python main.py cli
```

## Tournoi CLI

```bash
python main.py tournament
```

---

# 📈 Exemple de tournoi

```text
#    Noir         Blanc        Score   Gagnant

1    Facile       Moyen        34-30   Facile
2    Difficile    Facile       45-19   Difficile
3    Moyen        Aléatoire    40-24   Moyen
...
```

---

# 🛠️ Technologies utilisées

- Python 3
- Tkinter
- multiprocessing
- threading
- queue
- Minimax
- Alpha-Beta pruning

---

# 💡 Améliorations possibles

- IA Monte Carlo Tree Search
- sauvegarde/replay des parties
- statistiques avancées
- mode réseau multijoueur
- animations plus avancées
- IA par apprentissage

---

# 👨‍💻 Objectifs pédagogiques

Projet développé pour pratiquer :

- algorithmique
- intelligence artificielle
- théorie des jeux
- concurrence
- multiprocessing
- architecture logicielle Python
- développement desktop

---

# 📜 Licence

Projet libre d’utilisation à des fins éducatives.