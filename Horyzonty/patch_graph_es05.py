import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=True)
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PW")))


def patch_edinburgh():
    with driver.session() as session:
        session.run("""
        MERGE (c:City {name: 'Edinburgh'})

        // --- OUTDOOR (Na zewnątrz) ---
        MERGE (a1:Attraction {name: 'Arthur\\'s Seat'})
        SET a1.category = 'Park', a1.cost = 0, a1.free = true, a1.description = 'OUTDOOR: An extinct volcano offering panoramic views of the city.'
        MERGE (a1)-[:LOCATED_IN]->(c)

        MERGE (a2:Attraction {name: 'Princes Street Gardens'})
        SET a2.category = 'Park', a2.cost = 0, a2.free = true, a2.description = 'OUTDOOR: Beautiful public park in the center of Edinburgh.'
        MERGE (a2)-[:LOCATED_IN]->(c)

        MERGE (a3:Attraction {name: 'Royal Botanic Garden'})
        SET a3.category = 'Garden', a3.cost = 0, a3.free = true, a3.description = 'OUTDOOR: Stunning 70-acre botanical garden.'
        MERGE (a3)-[:LOCATED_IN]->(c)

        // --- INDOOR (Pod dachem) ---
        MERGE (i1:Attraction {name: 'National Museum of Scotland'})
        SET i1.category = 'Museum', i1.cost = 0, i1.free = true, i1.description = 'INDOOR: Vast museum of Scottish history and culture.'
        MERGE (i1)-[:LOCATED_IN]->(c)

        MERGE (i2:Attraction {name: 'Camera Obscura'})
        SET i2.category = 'Museum', i2.cost = 20, i2.free = false, i2.description = 'INDOOR: Museum of optical illusions.'
        MERGE (i2)-[:LOCATED_IN]->(c)

        MERGE (i3:Attraction {name: 'Scottish National Gallery'})
        SET i3.category = 'Gallery', i3.cost = 0, i3.free = true, i3.description = 'INDOOR: National art gallery of Scotland.'
        MERGE (i3)-[:LOCATED_IN]->(c)
        """)
        print("✅ Dane testowe dla ES-05 (Edynburg: Indoor/Outdoor) dodane!")


if __name__ == "__main__":
    patch_edinburgh()
    driver.close()