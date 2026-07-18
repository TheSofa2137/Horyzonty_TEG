import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=True)
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PW")))

def patch_graph():
    with driver.session() as session:
        session.run("""
        // 1. Dzielnica
        MERGE (c:City {name: 'Lisbon'})
        MERGE (n:Neighbourhood {name: 'Parque das Nações'})
        MERGE (n)-[:PART_OF]->(c)

        // 2. Dni tygodnia (jako osobne węzły do skoków OPEN_ON)
        MERGE (sat:Day {name: 'Saturday'})
        MERGE (sun:Day {name: 'Sunday'})

        // 3. Atrakcja 1 (Przyjazna rodzinom, otwarta w weekend)
        MERGE (a1:Attraction {name: 'Oceanário de Lisboa'})
        SET a1.category = 'Aquarium', a1.family_friendly = true, a1.cost = 80, a1.free = false, a1.description = 'Huge aquarium.'
        MERGE (a1)-[:LOCATED_IN]->(n)
        MERGE (a1)-[:OPEN_ON]->(sat)
        MERGE (a1)-[:OPEN_ON]->(sun)

        // 4. Atrakcja 2 (Przyjazna rodzinom, otwarta w weekend)
        MERGE (a2:Attraction {name: 'Pavilhão do Conhecimento'})
        SET a2.category = 'Science Museum', a2.family_friendly = true, a2.cost = 45, a2.free = false, a2.description = 'Interactive science museum.'
        MERGE (a2)-[:LOCATED_IN]->(n)
        MERGE (a2)-[:OPEN_ON]->(sat)
        MERGE (a2)-[:OPEN_ON]->(sun)

        // 5. Atrakcja 3 (PUPŁAPKA: Otwarta w weekend, ale NIE DLA RODZIN)
        MERGE (a3:Attraction {name: 'Casino Lisboa'})
        SET a3.category = 'Entertainment', a3.family_friendly = false, a3.cost = 0, a3.free = true, a3.description = 'Adults only casino.'
        MERGE (a3)-[:LOCATED_IN]->(n)
        MERGE (a3)-[:OPEN_ON]->(sat)
        MERGE (a3)-[:OPEN_ON]->(sun)
        """)
        print("✅ Dane testowe dla ES-02 dodane do Neo4j!")

if __name__ == "__main__":
    patch_graph()
    driver.close()