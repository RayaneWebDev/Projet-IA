# 🧠 Othello IA — Jeu, IA & Tournois en Temps Réel

Application complète du jeu **Othello** avec :

* Interface graphique interactive (Tkinter)
* Plusieurs niveaux d’intelligence artificielle
* Tournoi IA vs IA 

---

## 🚀 Fonctionnalités

### 🎮 Modes de jeu

* 👥 **Humain vs Humain**
* 🤖 **Humain vs IA**
* 🏆 **IA vs IA (tournoi automatisé)**

### 🤖 Niveaux d’IA

* 🎲 **Aléatoire**
* 😊 **Facile** (Minimax profondeur 2)
* 😐 **Moyen** (Minimax + mobilité)
* 😈 **Difficile** (Minimax avancé + heuristiques)

### 📊 Tournoi IA

* Matchs générés aléatoirement
* Alternance des couleurs (équité)
* Exécution **en parallèle** (multiprocessing)
* Affichage **en temps réel** :

  * Résultats des parties
  * Classement dynamique
  * Barre de progression

### 🧪 Tests unitaires

* Vérification des règles du jeu
* Validation des IA
* Test du système de **PASS (aucun coup valide)**

---

## 🧱 Structure du projet

```
.
├── Othello (logique du jeu)
├── IA (minimax + heuristiques)
├── GUI (Tkinter)
├── Tournoi (multiprocessing)
├── Tests (run_tests)
└── Main (lancement app ou CLI)
```

---

## ⚙️ Installation & Exécution

### ▶️ Lancer l’interface graphique

```bash
python main.py
```


## 🧠 Logique du jeu

### Règles implémentées

* Placement valide avec capture
* Retournement des pions
* Gestion du **PASS automatique**
* Fin de partie si aucun joueur ne peut jouer

---

## 🤖 Intelligence Artificielle

### Algorithme utilisé

* **Minimax avec Alpha-Beta pruning**

### Fonctions d’évaluation

* `evaluate_naive` → différence de score
* `evaluate_mobility` → mobilité + coins
* `evaluate_advanced` → poids positionnels + mobilité + score

---

## ⚡ Parallélisme

* Utilisation de `multiprocessing.Pool`
* Exécution des parties en parallèle
* Communication via `queue` vers l’interface

---

## 🎨 Interface graphique

* Tkinter moderne (design custom)
* Plateau interactif
* Indication des coups valides
* Animation des tours IA
* Tableau de classement dynamique

---

## 🔁 Gestion du PASS (important)

Quand un joueur n’a **aucun coup valide** :

```python
if not self.game.valid_moves():
    self.game.current_player *= -1
```

✔️ Si les deux joueurs sont bloqués → fin de partie

---

## 🧪 Tests unitaires

Lancer depuis le menu ou automatiquement :

### Tests couverts :

* Initialisation du plateau
* Coups valides
* Retournement
* IA
* Copie du jeu
* ✅ **PASS automatique**

---

## 📈 Exemple de résultat tournoi

```
#    Noir         Blanc        Score   Gagnant
1    Facile       Moyen        34-30   Facile
2    Difficile    Facile       45-19   Difficile
...
```

---

## 🛠️ Technologies utilisées

* Python 3
* Tkinter
* multiprocessing
* threading
* queue

---

## 💡 Améliorations possibles

* Ajouter une IA avec **Monte Carlo Tree Search**
* Sauvegarde des parties
* Mode réseau (multijoueur)
* Replay des parties
* Graphiques statistiques

---

## 👨‍💻 Auteur

Projet développé dans le cadre d’un apprentissage avancé :

* Algorithmique (Minimax)
* IA de jeu
* Concurrence (threads + multiprocessing)
* UI Desktop

---

## 📜 Licence

Projet libre d’utilisation à des fins éducatives.

---
