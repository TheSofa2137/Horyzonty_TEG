import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=True)
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PW")))


def patch_porto():
    with driver.session() as session:
        session.run("""
        MERGE (c:City {name: 'Porto'})

        // Architektura
        MERGE (a1:Attraction {name: 'Clérigos Tower'})
        SET a1.category = 'Architecture', a1.cost = 8, a1.free = false, a1.description = 'Iconic baroque bell tower with city views.'
        MERGE (a1)-[:LOCATED_IN]->(c)

        MERGE (a2:Attraction {name: 'Livraria Lello'})
        SET a2.category = 'Architecture', a2.cost = 5, a2.free = false, a2.description = 'Historic bookstore with an incredible wooden staircase.'
        MERGE (a2)-[:LOCATED_IN]->(c)

        MERGE (a3:Attraction {name: 'Dom Luís I Bridge'})
        SET a3.category = 'Architecture', a3.cost = 0, a3.free = true, a3.description = 'Double-deck metal arch bridge designed by a student of Eiffel.'
        MERGE (a3)-[:LOCATED_IN]->(c)

        // Wino
        MERGE (w1:Attraction {name: 'Sandeman Cellars'})
        SET w1.category = 'Wine', w1.cost = 15, w1.free = false, w1.description = 'Famous Port wine cellar offering guided tours and tastings.'
        MERGE (w1)-[:LOCATED_IN]->(c)

        MERGE (w2:Attraction {name: 'Taylor\\'s Port'})
        SET w2.category = 'Wine', w2.cost = 20, w2.free = false, w2.description = 'Historic wine lodge with tastings and a panoramic restaurant.'
        MERGE (w2)-[:LOCATED_IN]->(c)
        """)
        print("✅ Dane testowe dla ES-03 (Porto: Wino i Architektura) dodane!")


if __name__ == "__main__":
    patch_porto()
    driver.close()