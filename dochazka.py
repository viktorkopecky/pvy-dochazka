
import csv
import json
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

console = Console()

SLOUPCE = ["číslo čipu", "zaměstnanec", "příchod", "odchod"]
FORMAT_CASU = "%Y-%m-%d %H:%M"


# Načtení docházky z CSV
def nacti_dochazku(nazev_souboru):
    dochazka = []

    with open(nazev_souboru, "r", encoding="utf-8-sig", newline="") as soubor:
        reader = csv.DictReader(soubor, delimiter=";")

        if reader.fieldnames != SLOUPCE:
            raise ValueError("CSV nemá správné názvy sloupců.")

        for row in reader:
            prichod = datetime.strptime(row["příchod"], FORMAT_CASU)
            odchod = datetime.strptime(row["odchod"], FORMAT_CASU)

            if odchod < prichod:
                raise ValueError("Odchod nesmí být před příchodem.")

            delka = odchod - prichod
            hodiny = delka.total_seconds() / 3600

            row["hodiny"] = hodiny
            row["datum"] = prichod.date().isoformat()

            dochazka.append(row)

    return dochazka


# Výpis všech záznamů
def vypis_dochazky(dochazky):
    table = Table(title="Seznam docházky")

    table.add_column("Číslo čipu", justify="right")
    table.add_column("Zaměstnanec")
    table.add_column("Příchod")
    table.add_column("Odchod")
    table.add_column("Hodiny", justify="right")

    for zaznam in dochazky:
        table.add_row(
            zaznam["číslo čipu"],
            zaznam["zaměstnanec"],
            zaznam["příchod"],
            zaznam["odchod"],
            f"{zaznam['hodiny']:.2f}"
        )

    console.print(table)


# Vyhledávání podle jména nebo čísla čipu
def vyhledej_zamestnance(dochazka):
    hledany = input("Zadej jméno nebo číslo čipu: ").strip().lower()
    vysledky = []

    for zaznam in dochazka:
        jmeno = zaznam["zaměstnanec"].lower()
        cip = zaznam["číslo čipu"]

        if hledany in jmeno or hledany == cip:
            vysledky.append(zaznam)

    if vysledky:
        vypis_dochazky(vysledky)
    else:
        console.print("[red]Zaměstnanec nebyl nalezen.[/red]")


# Výpočet souhrnných statistik zaměstnanců
def statistiky_zamestnancu(dochazka):
    statistiky = {}

    for zaznam in dochazka:
        cip = zaznam["číslo čipu"]

        if cip not in statistiky:
            statistiky[cip] = {
                "číslo čipu": cip,
                "zaměstnanec": zaznam["zaměstnanec"],
                "počet_směn": 0,
                "celkem_hodin": 0
            }

        statistiky[cip]["počet_směn"] += 1
        statistiky[cip]["celkem_hodin"] += zaznam["hodiny"]

    for zamestnanec in statistiky.values():
        pocet = zamestnanec["počet_směn"]
        celkem = zamestnanec["celkem_hodin"]

        zamestnanec["průměrná_směna"] = round(celkem / pocet, 2)
        zamestnanec["celkem_hodin"] = round(celkem, 2)

    return statistiky


# Žebříček podle odpracovaných hodin
def vypis_hodiny(dochazka):
    statistiky = statistiky_zamestnancu(dochazka)

    serazeni = sorted(
        statistiky.values(),
        key=lambda x: x["celkem_hodin"],
        reverse=True
    )

    table = Table(title="Odpracované hodiny zaměstnanců")

    table.add_column("Zaměstnanec")
    table.add_column("Počet směn", justify="right")
    table.add_column("Celkem hodin", justify="right")
    table.add_column("Průměrná směna", justify="right")

    for zamestnanec in serazeni:
        table.add_row(
            zamestnanec["zaměstnanec"],
            str(zamestnanec["počet_směn"]),
            f"{zamestnanec['celkem_hodin']:.2f}",
            f"{zamestnanec['průměrná_směna']:.2f}"
        )

    console.print(table)


# Nejkratší, nejdelší a průměrná směna
def vypis_statistiky_smen(dochazka):
    nejkratsi = min(dochazka, key=lambda x: x["hodiny"])
    nejdelsi = max(dochazka, key=lambda x: x["hodiny"])

    celkem = sum(zaznam["hodiny"] for zaznam in dochazka)
    prumer = celkem / len(dochazka)

    console.print("\n[bold]Statistiky směn[/bold]")
    console.print(f"Počet směn: {len(dochazka)}")
    console.print(f"Průměrná délka: {prumer:.2f} hodin")

    console.print(
        f"Nejkratší směna: {nejkratsi['zaměstnanec']} "
        f"({nejkratsi['datum']}) - {nejkratsi['hodiny']:.2f} h"
    )

    console.print(
        f"Nejdelší směna: {nejdelsi['zaměstnanec']} "
        f"({nejdelsi['datum']}) - {nejdelsi['hodiny']:.2f} h"
    )


# První příchod a poslední odchod každého dne
def prichody_odchody(dochazka):
    dny = {}

    for zaznam in dochazka:
        datum = zaznam["datum"]

        if datum not in dny:
            dny[datum] = []

        dny[datum].append(zaznam)

    table = Table(title="První příchody a poslední odchody")

    table.add_column("Datum")
    table.add_column("První příchod")
    table.add_column("Čas")
    table.add_column("Poslední odchod")
    table.add_column("Čas")

    for datum in sorted(dny):
        zaznamy = dny[datum]

        prvni = min(zaznamy, key=lambda x: x["příchod"])
        posledni = max(zaznamy, key=lambda x: x["odchod"])

        table.add_row(
            datum,
            prvni["zaměstnanec"],
            prvni["příchod"][11:16],
            posledni["zaměstnanec"],
            posledni["odchod"][11:16]
        )

    console.print(table)


# Uložení statistik do JSON
def uloz_json(data, nazev_souboru):
    try:
        with open(nazev_souboru, "w", encoding="utf-8") as soubor:
            json.dump(data, soubor, indent=4, ensure_ascii=False)

        console.print(f"[green]Data byla uložena do {nazev_souboru}[/green]")

    except OSError as error:
        console.print(f"[bold red]Chyba: {error}[/bold red]")


# menu
def menu():
    console.print()
    console.print("[bold blue]========================================[/bold blue]")
    console.print("[bold white]          ANALÝZA DOCHÁZKY[/bold white]")
    console.print("[bold blue]========================================[/bold blue]")
    console.print()
    console.print("1 - Zobrazit všechny záznamy")
    console.print("2 - Vyhledat zaměstnance")
    console.print("3 - Odpracované hodiny zaměstnanců")
    console.print("4 - Statistiky směn")
    console.print("5 - První příchody a poslední odchody")
    console.print("6 - Export statistik do JSON")
    console.print("0 - Konec")


def main():
    if len(sys.argv) != 2:
        console.print("[red]Použití: python dochazka.py dochazka.csv[/red]")
        return

    nazev_souboru = sys.argv[1]

    try:
        dochazka = nacti_dochazku(nazev_souboru)

    except (OSError, ValueError, KeyError, csv.Error) as error:
        console.print(f"[red]Chyba při načítání souboru: {error}[/red]")
        return

    if not dochazka:
        console.print("[red]Soubor neobsahuje žádné záznamy.[/red]")
        return

    console.print(f"[green]Načteno {len(dochazka)} záznamů.[/green]")

    while True:
        menu()
        volba = input("\nVolba: ").strip()

        if volba == "1":
            vypis_dochazky(dochazka)

        elif volba == "2":
            vyhledej_zamestnance(dochazka)

        elif volba == "3":
            vypis_hodiny(dochazka)

        elif volba == "4":
            vypis_statistiky_smen(dochazka)

        elif volba == "5":
            prichody_odchody(dochazka)

        elif volba == "6":
            statistiky = statistiky_zamestnancu(dochazka)
            uloz_json(list(statistiky.values()), "vysledek.json")

        elif volba == "0":
            console.print("[blue]Program ukončen.[/blue]")
            break

        else:
            console.print("[red]Neplatná volba.[/red]")


if __name__ == "__main__":
    main()
