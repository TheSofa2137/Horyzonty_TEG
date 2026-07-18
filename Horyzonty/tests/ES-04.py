import os
import sys
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

from orchestrator import app_graph, driver

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)


def test_es04():
    query = "Find flights from Warsaw to Porto on 5 July, returning 8 July."

    print(f"🚀 Uruchamiam test ES-04 dla zapytania:\n'{query}'")

    # Wywołujemy graf z intencją flight_search
    result = app_graph.invoke({
        "messages": [],
        "city": "Porto",
        "budget": 5000.0,
        "duration": 3,
        "conversation_history": [],
        "current_plan": "",
        "intent": "flight_search",
        "user_message": query
    })

    plan = result.get("final_plan", "")
    flights_metadata = result.get("flights_hotels", {})
    extracted_params = flights_metadata.get("flight_params", {})

    print("-" * 50)
    print("💬 ODPOWIEDŹ AGENTA LOTÓW:")
    print(plan)
    print("-" * 50)

    # WERYFIKACJA KRYTERIÓW AKCEPTACJI
    passed = True

    # 1. Sprawdzenie ekstrakcji parametrów
    origin = extracted_params.get("origin_code", "").upper()
    dest = extracted_params.get("destination_code", "").upper()
    dep = extracted_params.get("departure_date", "")
    ret = extracted_params.get("return_date", "")

    if "WAW" in origin or origin == "WARSAW":
        print("✅ PARAMETR: Miejsce wylotu sparsowane poprawnie (WAW/Warsaw).")
    else:
        print(f"❌ BŁĄD PARAMETRU: Niepoprawny punkt wylotu (Sparsowano: {origin}).")
        passed = False

    if "OPO" in dest or dest == "PORTO":
        print("✅ PARAMETR: Miejsce docelowe sparsowane poprawnie (OPO/Porto).")
    else:
        print(f"❌ BŁĄD PARAMETRU: Niepoprawne miejsce docelowe (Sparsowano: {dest}).")
        passed = False

    if dep == "2026-07-05":
        print("✅ PARAMETR: Data wylotu sformatowana poprawnie (2026-07-05).")
    else:
        print(f"❌ BŁĄD PARAMETRU: Niepoprawna data wylotu (Sparsowano: {dep}).")
        passed = False

    if ret == "2026-07-08":
        print("✅ PARAMETR: Data powrotu sformatowana poprawnie (2026-07-08).")
    else:
        print(f"❌ BŁĄD PARAMETRU: Niepoprawna data powrotu (Sparsowano: {ret}).")
        passed = False

    # 2. Sprawdzenie liczby i struktury opcji w tekście odpowiedzi
    options_count = plan.count("\n") - plan.count("\n\n")  # szacowanie linii z wynikami
    # Prostszy test: szukamy kropek numeracji "1.", "2.", "3."
    has_enough_options = "1." in plan and "2." in plan and "3." in plan

    if has_enough_options:
        print("✅ WYNIKI: Zwrócono co najmniej 3 opcje lotów.")
    else:
        print("❌ BŁĄD WYNIKÓW: Odpowiedź zawiera mniej niż 3 opcje lotów.")
        passed = False

    # 3. Weryfikacja pól (Airline, Price, Departure Time)
    if "Departs:" in plan and ("PLN" in plan or "EUR" in plan):
        print("✅ STRUKTURA: Wyniki zawierają linię lotniczą, cenę oraz czas wylotu.")
    else:
        print("❌ BŁĄD STRUKTURY: Brak wymaganych pól (Airline, Price, Departure Time) w tekście.")
        passed = False

    if passed:
        print("\n🎯 ES-04: SUCCESS CRITERIA MET! (Wszystko na zielono)")
    else:
        print("\n⚠️ ES-04: EWALUACJA OBLANA.")


if __name__ == "__main__":
    test_es04()
    driver.close()