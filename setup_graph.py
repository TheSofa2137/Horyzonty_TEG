from neo4j import GraphDatabase


class TravelGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_base_data(self):
        with self.driver.session() as session:
            # Tworzymy przykładową strukturę: Lizbona i jedna atrakcja
            session.run("""
                MERGE (c:City {name: 'Lisbon'})
                MERGE (a:Attraction {name: 'Belem Tower', cost: 10, type: 'History'})
                MERGE (r:Restaurant {name: 'Time Out Market', avg_price: 25, cuisine: 'Mixed'})

                MERGE (a)-[:LOCATED_IN]->(c)
                MERGE (r)-[:LOCATED_IN]->(c)
            """)
            print("✅ Podstawowe węzły grafu zostały stworzone!")


# Ustawienia (zmień hasło na takie, jakie ustawiłaś w Neo4j Desktop)
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"

graph = TravelGraph(URI, USER, PASSWORD)
graph.create_base_data()
graph.close()