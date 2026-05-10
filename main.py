# =========================================
# main.py
# =========================================

import sys
import tkinter as tk
import multiprocessing as mp

from ui.gui import OthelloGUI
from ui.cli import (
    cli_play_human_vs_ai,
    cli_run_tournament_report
)


def main():

    # ==============================
    # MODE CLI
    # ==============================
    if len(sys.argv) > 1:

        if sys.argv[1] == "cli":
            cli_play_human_vs_ai()

        elif sys.argv[1] == "tournament":
            cli_run_tournament_report()

    # ==============================
    # MODE GUI
    # ==============================
    else:

        root = tk.Tk()

        app = OthelloGUI(root)

        root.mainloop()


if __name__ == "__main__":

    mp.freeze_support()

    main()