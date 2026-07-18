import os
import sys
from dotenv import load_dotenv

# Konfiguracja ścieżek, by skrypt widział orchestrator
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

from orchestrator import run_nl_graph_query, driver

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)


def test_es02():
    query = "Find family-friendly attractions near Parque das Nações that are open on weekends."
    city = "Lisbon"

    print(f"🚀 Uruchamiam ES-02 Text-to-Cypher dla pytania:\n'{query}'")
    answer, cypher = run_nl_graph_query(query, city)

    print("-" * 50)
    print("📋 WYGENEROWANY CYPHER:")
    print(cypher)
    print("-" * 50)
    print("💬 ODPOWIEDŹ LLM:")
    print(answer)
    print("-" * 50)

    # WERYFIKACJA KRYTERIÓW AKCEPTACYJNYCH
    passed = True

    # 1. Minimum 2 hop-y relacyjne
    if "LOCATED_IN" not in cypher or "OPEN_ON" not in cypher:
        print("❌ BŁĄD: Cypher nie zawiera obu wymaganych relacji (LOCATED_IN, OPEN_ON).")
        passed = False
    else:
        print("✅ ZNALEZIONO: 2+ relacje (Multi-hop) w Cypherze.")

    # 2. Brak false-positives (wymuszony wariant family_friendly)
    if "family_friendly" not in cypher and "family_friendly = true" not in cypher.lower():
        print("❌ BŁĄD: Cypher nie filtruje poprawnie flagi family_friendly.")
        passed = False
    else:
        print("✅ ZNALEZIONO: Filtr family_friendly.")

    # 3. Sprawdzenie samych wyników w Neo4j
    with driver.session() as session:
        rows = list(session.run(cypher))

    if len(rows) < 2:
        print(f"❌ BŁĄD: Oczekiwano co najmniej 2 atrakcji, znaleziono {len(rows)}.")
        passed = False
    else:
        names = [r.get('name') for r in rows] if 'name' in rows[0] else [str(r) for r in rows]
        print(f"✅ BAZA ZWRÓCIŁA {len(rows)} TRAFNE WYNIKI: {names}")

        # Upewniamy się, że LLM nie ściągnął kasyna!
        if any("casino" in name.lower() for name in names):
            print("❌ BŁĄD: Znaleziono false positive (Kasyno zostało zwrócone).")
            passed = False

    if passed:
        print("\n🎯 ES-02: SUCCESS CRITERIA MET! (Wszystko na zielono)")
    else:
        print("\n⚠️ ES-02: EWALUACJA OBLANA. Wymagane poprawki w prompcie.")


if __name__ == "__main__":
    test_es02()