import sys
import os

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from neo4j import GraphDatabase
from dotenv import load_dotenv

# --- CONFIGURATION ---
#dane z env
load_dotenv(override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PW = os.getenv("NEO4J_PW")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PW:
    raise EnvironmentError("Missing required Neo4j env vars: NEO4J_URI, NEO4J_USER, NEO4J_PW")

_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW))


def add_flight(from_city, to_city, airline, price, date="2026-06-15"):
    """Adds a flight to the graph (idempotent — uses MERGE to avoid duplicates)"""
    with _driver.session() as session:
        session.run("""
            MERGE (c:City {name: $to_city})
            MERGE (f:Flight {origin: $origin, airline: $airline, date: $date})
            SET f.price = $price
            MERGE (f)-[:FLIES_TO]->(c)
        """, origin=from_city, to_city=to_city, airline=airline, price=float(price), date=date)


def sync_flights():
    """Seeds the graph with flights at various prices"""

    print("✈️ Seeding graph with flights...")

    flights = [
        # WAW -> Lisbon
        ("WAW", "Lisbon", "LOT Polish Airlines", 550),
        ("WAW", "Lisbon", "TAP Portugal", 680),
        ("WAW", "Lisbon", "Ryanair", 320),

        # WAW -> Porto
        ("WAW", "Porto", "TAP Portugal", 620),
        ("WAW", "Porto", "LOT Polish Airlines", 600),
        ("WAW", "Porto", "Ryanair", 350),

        # WAW -> Barcelona
        ("WAW", "Barcelona", "Vueling", 450),
        ("WAW", "Barcelona", "Ryanair", 320),
        ("WAW", "Barcelona", "LOT Polish Airlines", 680),

        # WAW -> Prague
        ("WAW", "Prague", "LOT Polish Airlines", 280),
        ("WAW", "Prague", "Czech Airlines", 320),
        ("WAW", "Prague", "Ryanair", 180),

        # WAW -> Vienna
        ("WAW", "Vienna", "LOT Polish Airlines", 350),
        ("WAW", "Vienna", "Austrian Airlines", 380),
        ("WAW", "Vienna", "Wizz Air", 240),

        # WAW -> Krakow (domestic!)
        ("WAW", "Krakow", "LOT Polish Airlines", 150),
        ("WAW", "Krakow", "Wizz Air", 80),
        ("WAW", "Krakow", "Ryanair", 120),

        # WAW -> Rome
        ("WAW", "Rome", "Alitalia", 480),
        ("WAW", "Rome", "LOT Polish Airlines", 550),
        ("WAW", "Rome", "Ryanair", 380),

        # WAW -> Milan
        ("WAW", "Milan", "Alitalia", 450),
        ("WAW", "Milan", "Lufthansa", 520),
        ("WAW", "Milan", "Ryanair", 320),

        # WAW -> Florence
        ("WAW", "Florence", "Alitalia", 480),
        ("WAW", "Florence", "LOT Polish Airlines", 580),
        ("WAW", "Florence", "Ryanair", 400),

        # WAW -> Paris
        ("WAW", "Paris", "LOT Polish Airlines", 420),
        ("WAW", "Paris", "Air France", 480),
        ("WAW", "Paris", "Ryanair", 240),

        # WAW -> Amsterdam
        ("WAW", "Amsterdam", "KLM", 350),
        ("WAW", "Amsterdam", "LOT Polish Airlines", 380),
        ("WAW", "Amsterdam", "Ryanair", 200),
    ]

    for origin, destination, airline, price in flights:
        add_flight(origin, destination, airline, price)
        print(f"  ✅ {origin} → {destination}: {airline} ({price} PLN)")

    print("✅ Flights seeded!")


if __name__ == "__main__":
    sync_flights()
    _driver.close()
    print("✅ Flights have been added to the graph!")
