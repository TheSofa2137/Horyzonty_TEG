import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=True)
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PW")))


def patch_edinburgh_hotel():
    with driver.session() as session:
        session.run("""
        MERGE (c:City {name: 'Edinburgh'})

        MERGE (h:Hotel {name: 'The Balmoral', city: 'Edinburgh'})
        SET h.price = 200
        MERGE (h)-[:LOCATED_IN]->(c)

        MERGE (h2:Hotel {name: 'Edinburgh Castle Budget Inn', city: 'Edinburgh'})
        SET h2.price = 80
        MERGE (h2)-[:LOCATED_IN]->(c)
        """)
        print("✅ Hotele w Edynburgu dodane do Neo4j!")


if __name__ == "__main__":
    patch_edinburgh_hotel()
    driver.close()