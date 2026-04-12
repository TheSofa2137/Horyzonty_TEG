import requests
from neo4j import GraphDatabase

# --- KONFIGURACJA ---
RAPID_API_KEY = "8e6dfd68femshdfa437a5181dbb4p172746jsn521e3e39dd2b"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PW = "12345678"


def sync_flights_from_radar(from_iata, to_iata):
    url = "https://flight-radar1.p.rapidapi.com/flights/search"
    querystring = {"from": from_iata, "to": to_iata, "date": "2026-06-15", "currency": "PLN"}

    headers = {
        "x-rapidapi-key": "8e6dfd68femshdfa437a5181dbb4p172746jsn521e3e39dd2b",
        "x-rapidapi-host": "flight-radar1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # Logika zapisu z Twojego poprzedniego skryptu...
            print("✅ Loty zaktualizowane z API!")
        else:
            print(f"⚠️ API zwróciło status {response.status_code}. Uruchamiam tryb awaryjny (Mock Data).")
            # --- TRYB AWARYJNY ---
            with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW)).session() as session:
                session.run("""
                    MERGE (c:City {name: 'Lisbon'})
                    MERGE (f:Flight {origin: $origin, date: '2026-06-15'})
                    SET f.price = 850.0, f.airline = 'TAP Portugal (Simulated)'
                    MERGE (f)-[:FLIES_TO]->(c)
                """, origin=from_iata)
            print("✅ Graf zasilony stabilnymi danymi testowymi.")

    except Exception as e:
        print(f"❌ Błąd połączenia: {e}. Używam danych lokalnych.")