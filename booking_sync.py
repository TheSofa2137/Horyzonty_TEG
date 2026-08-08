import requests
from neo4j import GraphDatabase

# --- KONFIGURACJA ---
RAPID_API_KEY = "8e6dfd68femshdfa437a5181dbb4p172746jsn521e3e39dd2b"  # Wklej tu swój klucz (zaczyna się pewnie od 8e6dfd...)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PW = "12345678"  # Upewnij się, że to dobre hasło

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW))


def sync_hotels_from_booking15(city_name):
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

    querystring = {
        "dest_id": "-2167973",
        "search_type": "CITY",
        "arrival_date": "2026-06-15",
        "departure_date": "2026-06-17",
        "adults": "1",
        "room_qty": "1",
        "currency_code": "PLN"
    }

    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "booking-com15.p.rapidapi.com"
    }

    print(f"🏨 Pobieram hotele w {city_name} z API booking-com15...")
    try:
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code == 200:
            data = response.json()
            hotels_list = data.get('data', {}).get('hotels', [])[:3]

            if not hotels_list:
                print("⚠️ Brak hoteli. Wydruk struktury, by sprawdzić błąd:")
                print(data)
                return

            with driver.session() as session:
                for h in hotels_list:
                    name = h.get('property', {}).get('name', 'Nieznany Hotel')
                    price = h.get('property', {}).get('priceBreakdown', {}).get('grossPrice', {}).get('value', 500.0)

                    session.run("""
                        MERGE (c:City {name: $city})
                        CREATE (hotel:Hotel {name: $name, price: $price})
                        CREATE (hotel)-[:LOCATED_IN]->(c)
                    """, city=city_name, name=name, price=float(price))

            print("✅ Hotele zapisane w grafie Neo4j!")
        else:
            print(f"❌ Błąd API: {response.status_code}")
            print(response.text)  # To pokaże dokładnie DLACZEGO jest 403

    except Exception as e:
        print(f"❌ Błąd skryptu: {e}")


if __name__ == "__main__":
    sync_hotels_from_booking15("Lisbon")
    driver.close()