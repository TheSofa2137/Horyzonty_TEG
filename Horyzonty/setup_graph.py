import sys

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from neo4j import GraphDatabase


class TravelGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_base_data(self):
        """Creates the base city structure and relationships"""
        with self.driver.session() as session:
            # Clear all existing data (clean start)
            session.run("MATCH (n) DETACH DELETE n")
            print("🧹 Old data cleared")

            # Create city nodes
            cities = [
                "Lisbon", "Porto", "Barcelona",  # Portugal and Spain
                "Prague", "Vienna", "Krakow",    # Central Europe
                "Rome", "Milan", "Florence",     # Italy
                "Paris", "Amsterdam"             # Western Europe
            ]
            for city in cities:
                session.run("MERGE (c:City {name: $name})", name=city)

            print("✅ Cities created:", cities)


# Settings
#dane z env
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PW")

if __name__ == "__main__":
    graph = TravelGraph(URI, USER, PASSWORD)
    graph.create_base_data()
    graph.close()
    print("✅ Base graph structure ready!")
