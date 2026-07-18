from neo4j import GraphDatabase
from langchain_ollama import ChatOllama

# 1. Connection configuration
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
    # Ask the LLM to write a Cypher query based on the user's question
    prompt = f"""
    You are a Neo4j expert. Translate the user's question into a valid Cypher query.
    Database schema:
    - Nodes: City (name), Attraction (name, type, cost)
    - Relationship: (Attraction)-[:LOCATED_IN]->(City)

    Question: {user_query}

    Return ONLY the Cypher query code, with no preamble.
    Example: MATCH (a:Attraction)-[:LOCATED_IN]->(c:City {{name: 'Lisbon'}}) RETURN a.name, a.cost
    """
    response = llm.invoke(prompt)
    return response.content.strip().replace("```cypher", "").replace("```", "")


# 2. Main assistant loop
print("🤖 Welcome to your GraphRAG Planner! What would you like to ask?")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ['exit', 'quit']: break

    try:
        # Step A: Generate Cypher
        cypher = generate_cypher(user_input)
        print(f"🔍 Generating graph query: {cypher}")

        # Step B: Fetch data from Neo4j
        data = query_graph(cypher)

        # Step C: Final answer
        final_prompt = f"""
        The user asked: {user_input}
        Data from the database: {data}

        Based on this data, answer the user helpfully in English.
        """
        response = llm.invoke(final_prompt)
        print(f"\nAssistant: {response.content}")

    except Exception as e:
        print(f"❌ Something went wrong: {e}")

driver.close()