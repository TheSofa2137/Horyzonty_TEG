from neo4j import GraphDatabase
from langchain_ollama import ChatOllama
import os

# Konfiguracja
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"
PROCESSED_DATA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\data\processed"

llm = ChatOllama(model="llama3.2:3b")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def add_attraction(city_name, attraction_name, attr_type):
    with driver.session() as session:
        session.run("""
            MERGE (c:City {name: $city})
            MERGE (a:Attraction {name: $attr})
            SET a.type = $type
            MERGE (a)-[:LOCATED_IN]->(c)
        """, city=city_name, attr=attraction_name, type=attr_type)

def update_prices(attraction_name, price):
    with driver.session() as session:
        session.run("""
            MATCH (a:Attraction {name: $name})
            SET a.cost = $price
        """, name=attraction_name, price=price)

# Przykład działania "półautomatycznego"
# W pełnej wersji LLM analizuje tekst, tutaj robimy fundament:
def process_files():
    for filename in os.listdir(PROCESSED_DATA_PATH):
        if filename.endswith(".txt"):
            city = filename.replace(".txt", "")
            print(f"🏙️ Przetwarzanie miasta: {city}")

            # Tu w przyszłości dodasz pętlę LLM, która wyciąga dane.
            # Na potrzeby testu dodajmy ręcznie kluczowe miejsca z plików:
            if city == "Lisbon":
                add_attraction("Lisbon", "Alfama", "District")
                add_attraction("Lisbon", "Jerónimos Monastery", "Monument")
            elif city == "Porto":
                add_attraction("Porto", "Ribeira", "District")
                add_attraction("Porto", "Livraria Lello", "Sight")


if __name__ == "__main__":
    process_files()
    driver.close()
    print("✅ Graf zasilony danymi!")