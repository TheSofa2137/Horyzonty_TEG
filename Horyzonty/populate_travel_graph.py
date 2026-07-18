import sys

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from neo4j import GraphDatabase
import os

# Configuration
#dane z env
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PW")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def add_attraction(city_name, attraction_name, attr_type, cost=0, description=""):
    """Adds an attraction (idempotent — uses MERGE). Sets both 'category' and 'free' fields."""
    with driver.session() as session:
        session.run("""
            MERGE (c:City {name: $city})
            MERGE (a:Attraction {name: $attr})
            SET a.category = $category,
                a.cost = $cost,
                a.free = ($cost = 0),
                a.description = $description
            MERGE (a)-[:LOCATED_IN]->(c)
        """, city=city_name, attr=attraction_name, category=attr_type.lower(), cost=cost,
             description=description or attraction_name)


def populate_attractions():
    """Seeds the graph with attractions and prices"""

    print("🌍 Seeding graph with attractions...")

    # Lisbon
    lisbon_attractions = [
        ("Lisbon", "Alfama", "District", 5),
        ("Lisbon", "Jerónimos Monastery", "Monument", 15),
        ("Lisbon", "Belem Tower", "Monument", 12),
        ("Lisbon", "Sintra Palaces", "Palace", 20),
        ("Lisbon", "Castelo de São Jorge", "Castle", 10),
        ("Lisbon", "Belém Cultural Complex", "Museum", 8),
        ("Lisbon", "Oceanário de Lisboa", "Aquarium", 18),
    ]

    # Porto
    porto_attractions = [
        ("Porto", "Ribeira", "District", 0),
        ("Porto", "Livraria Lello", "Bookstore", 5),
        ("Porto", "Torre dos Clérigos", "Tower", 8),
        ("Porto", "Dom Luís Bridge", "Bridge", 0),
        ("Porto", "Palác da Bolsa", "Palace", 10),
        ("Porto", "Igreja Clérigos", "Church", 3),
        ("Porto", "Museu do Vinho do Porto", "Museum", 7),
    ]

    # Barcelona
    barcelona_attractions = [
        ("Barcelona", "Sagrada Familia", "Cathedral", 25),
        ("Barcelona", "Park Güell", "Park", 14),
        ("Barcelona", "Casa Batlló", "Building", 22),
        ("Barcelona", "La Rambla", "Street", 0),
        ("Barcelona", "Gothic Quarter", "District", 0),
        ("Barcelona", "Montjuïc", "Area", 5),
        ("Barcelona", "Picasso Museum", "Museum", 15),
    ]

    # Prague
    prague_attractions = [
        ("Prague", "Charles Bridge", "Bridge", 0),
        ("Prague", "Prague Castle", "Castle", 18),
        ("Prague", "Old Town Square", "Square", 0),
        ("Prague", "Jewish Quarter", "District", 10),
        ("Prague", "Petřín Lookout Tower", "Tower", 8),
        ("Prague", "St. Vitus Cathedral", "Cathedral", 12),
        ("Prague", "Municipal House", "Museum", 6),
    ]

    # Vienna
    vienna_attractions = [
        ("Vienna", "Schönbrunn Palace", "Palace", 16),
        ("Vienna", "St. Stephen's Cathedral", "Cathedral", 8),
        ("Vienna", "Hofburg Palace", "Palace", 14),
        ("Vienna", "Belvedere Palace", "Palace", 15),
        ("Vienna", "Prater Park", "Park", 5),
        ("Vienna", "Giant Ferris Wheel", "Landmark", 12),
        ("Vienna", "St. Karl's Church", "Church", 6),
    ]

    # Krakow
    krakow_attractions = [
        ("Krakow", "Wawel Castle", "Castle", 12),
        ("Krakow", "Main Market Square", "Square", 0),
        ("Krakow", "St. Mary's Basilica", "Church", 5),
        ("Krakow", "Kazimierz District", "District", 0),
        ("Krakow", "Cloth Hall", "Market", 8),
        ("Krakow", "Underground Museum", "Museum", 10),
        ("Krakow", "Rynek Underground", "Museum", 9),
    ]

    # Rome
    rome_attractions = [
        ("Rome", "Colosseum", "Landmark", 18),
        ("Rome", "Roman Forum", "Historic", 14),
        ("Rome", "Pantheon", "Temple", 10),
        ("Rome", "Vatican City", "Religious", 20),
        ("Rome", "Trevi Fountain", "Fountain", 5),
        ("Rome", "Spanish Steps", "Landmark", 0),
        ("Rome", "Sistine Chapel", "Church", 22),
    ]

    # Milan
    milan_attractions = [
        ("Milan", "Duomo", "Cathedral", 15),
        ("Milan", "Galleria Vittorio Emanuele II", "Gallery", 0),
        ("Milan", "Sforza Castle", "Castle", 8),
        ("Milan", "The Last Supper", "Museum", 12),
        ("Milan", "Navigli District", "District", 0),
        ("Milan", "Pinacoteca di Brera", "Museum", 10),
        ("Milan", "Monumental Cemetery", "Cemetery", 3),
    ]

    # Florence
    florence_attractions = [
        ("Florence", "Florence Cathedral", "Cathedral", 8),
        ("Florence", "Uffizi Gallery", "Museum", 18),
        ("Florence", "Accademia Gallery", "Museum", 16),
        ("Florence", "Ponte Vecchio", "Bridge", 0),
        ("Florence", "Palazzo Pitti", "Palace", 10),
        ("Florence", "Boboli Gardens", "Garden", 12),
        ("Florence", "Piazzale Michelangelo", "Square", 0),
    ]

    # Paris
    paris_attractions = [
        ("Paris", "Eiffel Tower", "Landmark", 20),
        ("Paris", "Louvre Museum", "Museum", 18),
        ("Paris", "Notre-Dame", "Cathedral", 10),
        ("Paris", "Arc de Triomphe", "Monument", 12),
        ("Paris", "Champs-Élysées", "Street", 0),
        ("Paris", "Sacré-Cœur", "Basilica", 8),
        ("Paris", "Versailles Palace", "Palace", 25),
    ]

    # Amsterdam
    amsterdam_attractions = [
        ("Amsterdam", "Anne Frank House", "Museum", 14),
        ("Amsterdam", "Canal Cruise", "Tour", 15),
        ("Amsterdam", "Van Gogh Museum", "Museum", 20),
        ("Amsterdam", "Rijksmuseum", "Museum", 22),
        ("Amsterdam", "Dam Square", "Square", 0),
        ("Amsterdam", "Vondelpark", "Park", 0),
        ("Amsterdam", "Old Church", "Church", 5),
    ]

    all_attractions = (lisbon_attractions + porto_attractions + barcelona_attractions +
                      prague_attractions + vienna_attractions + krakow_attractions +
                      rome_attractions + milan_attractions + florence_attractions +
                      paris_attractions + amsterdam_attractions)

    for city, attr, type_, cost in all_attractions:
        add_attraction(city, attr, type_, cost)
        print(f"  ✅ {city}: {attr} ({cost} PLN)")

    print("✅ Attractions seeded!")


if __name__ == "__main__":
    populate_attractions()
    driver.close()
    print("✅ Graf zasilony danymi!")