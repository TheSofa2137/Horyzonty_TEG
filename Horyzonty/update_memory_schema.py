from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration from your .env
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PW = os.getenv("NEO4J_PW")

def apply_memory_schema():
    driver = GraphDatabase.driver(URI, auth=(USER, PW))
    with driver.session() as session:
        print("🛠️ Applying Persistent Memory Schema...")

        # 1. Ensure User IDs are unique
        session.run("""
            CREATE CONSTRAINT user_id_unique IF NOT EXISTS 
            FOR (u:User) REQUIRE u.id IS UNIQUE
        """)

        # 2. Ensure Session IDs are unique
        session.run("""
            CREATE CONSTRAINT session_id_unique IF NOT EXISTS 
            FOR (s:Session) REQUIRE s.id IS UNIQUE
        """)

        # 3. Create an index on Message timestamps for fast history loading
        session.run("""
            CREATE INDEX message_timestamp_index IF NOT EXISTS 
            FOR (m:Message) ON (m.timestamp)
        """)

        print("✅ Constraints and Indexes for memory are active.")
    driver.close()

if __name__ == "__main__":
    apply_memory_schema()