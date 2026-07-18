import sys

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

from tools import driver

load_dotenv(override=True)


def add_hotel(city_name, hotel_name, price):
    """Adds a hotel to the graph (idempotent — uses MERGE to avoid duplicates)"""
    with driver.session() as session:
        session.run("""
            MERGE (c:City {name: $city})
            MERGE (hotel:Hotel {name: $name, city: $city})
            SET hotel.price = $price
            MERGE (hotel)-[:LOCATED_IN]->(c)
        """, city=city_name, name=hotel_name, price=float(price))


def sync_hotels():
    """Seeds the graph with hotels at various prices"""

    print("🏨 Seeding graph with hotels...")

    hotels = [
        # Lisbon
        ("Lisbon", "Hotel Ibis Lisboa Centro", 250),
        ("Lisbon", "Hotel Tejo", 180),
        ("Lisbon", "Memmo Alfama Hotel", 320),

        # Porto
        ("Porto", "The Yeatman", 350),
        ("Porto", "Ribeira Tawny Porto", 150),
        ("Porto", "Livraria Lello Hotel", 280),

        # Barcelona
        ("Barcelona", "Hotel 1898", 380),
        ("Barcelona", "Apartments Barcelona Center", 280),
        ("Barcelona", "Serras Barcelona", 320),

        # Prague
        ("Prague", "Four Seasons Prague", 450),
        ("Prague", "Hotel U Prizsí", 200),
        ("Prague", "Old Town Square Hotel", 280),

        # Vienna
        ("Vienna", "Stephansdom Hotel", 380),
        ("Vienna", "Hotel Sacher", 420),
        ("Vienna", "Beethoven Hotel", 220),

        # Krakow
        ("Krakow", "Stary Hotel", 290),
        ("Krakow", "Hotel Copernicus", 350),
        ("Krakow", "Bonarka City Hotel", 160),

        # Rome
        ("Rome", "Hotel Artemide", 400),
        ("Rome", "Hassler Roma", 550),
        ("Rome", "Hotel Eden", 480),

        # Milan
        ("Milan", "Principe di Savoia", 450),
        ("Milan", "Armani Hotel Milano", 520),
        ("Milan", "Boscolo Hotel", 320),

        # Florence
        ("Florence", "Four Seasons Firenze", 480),
        ("Florence", "Brunelleschi Hotel", 350),
        ("Florence", "Hotel Continentale", 400),

        # Paris
        ("Paris", "Le Meurice", 550),
        ("Paris", "Hotel Ritz Paris", 600),
        ("Paris", "Hotel Plaza Athénée", 520),

        # Amsterdam
        ("Amsterdam", "Waldorf Astoria", 480),
        ("Amsterdam", "Hotel de l'Europe", 420),
        ("Amsterdam", "Ambassade Hotel", 350),
    ]

    for city, hotel_name, price in hotels:
        add_hotel(city, hotel_name, price)
        print(f"  ✅ {city}: {hotel_name} ({price} PLN/night)")

    print("✅ Hotels seeded!")


if __name__ == "__main__":
    sync_hotels()
    driver.close()
    print("✅ Hotels have been added to the graph!")
