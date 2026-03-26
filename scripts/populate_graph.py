from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def populate(tx):
    tx.run("""
        MERGE (c:City {name: 'Lisbon', country: 'Portugal'})
        MERGE (n1:Neighbourhood {name: 'Alfama'})
        MERGE (n2:Neighbourhood {name: 'Bairro Alto'})
        MERGE (n1)-[:LOCATED_IN]->(c)
        MERGE (n2)-[:LOCATED_IN]->(c)
    """)
    tx.run("""
        MERGE (a:Attraction {id: 'azulejo-museum', name: 'Museu Nacional do Azulejo',
               category: 'museum', free: false})
        MERGE (n:Neighbourhood {name: 'Alfama'})
        MERGE (a)-[:LOCATED_IN]->(n)
        SET a.open_days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    """)
    tx.run("""
        MERGE (a:Attraction {id: 'castelo-sao-jorge', name: 'Castelo de São Jorge',
               category: 'landmark', free: false})
        MERGE (n:Neighbourhood {name: 'Alfama'})
        MERGE (a)-[:LOCATED_IN]->(n)
        SET a.open_days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    """)

with driver.session() as session:
    session.execute_write(populate)
    print("Graph populated.")

driver.close()