from tournament.engine import run_full_tournament


def main():

    print("=" * 60)
    print(" TOURNOI COMPLET OTHELLO ")
    print("=" * 60)

    n = input("Nombre total de parties pour le tournoi (défaut 50) : ").strip()

    if n.isdigit():
        total_games = int(n)
    else:
        total_games = 50

    results = run_full_tournament(total_games)

    print("\nRésultats finaux :\n")

    for result in results:

        print(
            f"{result['ia_a']} vs {result['ia_b']} → "
            f"{result['wins_a']}V / "
            f"{result['wins_b']}V / "
            f"{result['draws']}N"
        )


if __name__ == "__main__":
    main()