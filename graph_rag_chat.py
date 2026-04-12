from neo4j import GraphDatabase
from langchain_ollama import ChatOllama

# 1. Konfiguracja połączeń
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
llm = ChatOllama(model="llama3.2:3b")


def query_graph(cypher_query):
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]


def generate_cypher(user_query):
    # Prosimy LLM o napisanie zapytania Cypher na podstawie pytania użytkownika
    prompt = f"""
    Jesteś ekspertem Neo4j. Przetłumacz pytanie użytkownika na poprawne zapytanie Cypher.
    Schemat bazy:
    - Węzły: City (name), Attraction (name, type, cost)
    - Relacja: (Attraction)-[:LOCATED_IN]->(City)

    Pytanie: {user_query}

    Zwróć TYLKO kod zapytania Cypher, bez żadnego wstępu.
    Przykład: MATCH (a:Attraction)-[:LOCATED_IN]->(c:City {{name: 'Lisbon'}}) RETURN a.name, a.cost
    """
    response = llm.invoke(prompt)
    return response.content.strip().replace("```cypher", "").replace("```", "")


# 2. Główna pętla asystenta
print("🤖 Witaj w Twoim GraphRAG Plannerze! O co chcesz zapytać?")

while True:
    user_input = input("\nTy: ")
    if user_input.lower() in ['exit', 'quit']: break

    try:
        # Krok A: Generowanie Cypher
        cypher = generate_cypher(user_input)
        print(f"🔍 Generuję zapytanie do grafu: {cypher}")

        # Krok B: Pobieranie danych z Neo4j
        data = query_graph(cypher)

        # Krok C: Finalna odpowiedź
        final_prompt = f"""
        Użytkownik zapytał: {user_input}
        Dane z bazy danych: {data}

        Na podstawie tych danych, odpowiedz użytkownikowi uprzejmie po polsku.
        """
        response = llm.invoke(final_prompt)
        print(f"\nAsystent: {response.content}")

    except Exception as e:
        print(f"❌ Coś poszło nie tak: {e}")

driver.close()