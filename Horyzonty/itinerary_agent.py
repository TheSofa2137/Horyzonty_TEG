import os
import numpy as np
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tools import driver as shared_driver

# --- CONFIGURATION ---
load_dotenv(override=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")

# Initialise models
embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3.2:3b")
driver = shared_driver

# --- RAG ENGINE (text search) ---
print("📂 Initialising Wikivoyage knowledge base...")
loader = DirectoryLoader(PROCESSED_DATA_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
chunks = [doc.page_content for doc in splitter.split_documents(docs)]
chunk_embeddings = embeddings_model.embed_documents(chunks)


def get_best_context(query, k=2):
    query_embedding = embeddings_model.embed_query(query)
    similarities = [np.dot(query_embedding, chunk_emb) for chunk_emb in chunk_embeddings]
    best_indices = np.argsort(similarities)[-k:][::-1]
    selected_chunks = [str(chunks[int(i)]) for i in best_indices]
    return "\n---\n".join(selected_chunks)


# --- GRAPH ENGINE (Prices and Facts) ---
def get_budget_plan(city_name, max_budget):
    with driver.session() as session:
        query = """
        MATCH (f:Flight)-[:FLIES_TO]->(c:City {name: $city})
        MATCH (h:Hotel)-[:LOCATED_IN]->(c)
        MATCH (a:Attraction)-[:LOCATED_IN]->(c)
        WHERE f.price IS NOT NULL AND h.price IS NOT NULL AND a.cost IS NOT NULL
        WITH f, h, a, (f.price + h.price + a.cost) as total
        WHERE total <= $budget
        RETURN f, h, collect(a) as attractions, total
        ORDER BY total ASC LIMIT 1
        """
        result = session.run(query, city=city_name, budget=max_budget)
        return result.single()


# --- PLANNER AGENT ---
def generate_itinerary(user_query, budget):
    print(f"🕵️ Analysing options for budget {budget} PLN...")

    plan_data = get_budget_plan("Lisbon", budget)
    if not plan_data:
        return "Sorry, I couldn't find flights and attractions within this budget. Try increasing the amount!"

    attraction_names = ", ".join([a['name'] for a in plan_data['attractions']])
    print(f"🔍 Fetching descriptions for: {attraction_names}...")

    # Call helper function
    extra_info = get_best_context(f"Information about {attraction_names} in Lisbon", k=2)

    flight_node = plan_data['f']
    hotel_node = plan_data['h']

    prompt = f"""
    You are a professional travel guide. Create a 2-day itinerary for Lisbon.

    GRAPH DATA:
    - Flight: {flight_node['airline']} ({flight_node['price']} PLN)
    - Hotel: {hotel_node['name']} ({hotel_node['price']} PLN/night)
    - Attractions: {plan_data['attractions']}

    GUIDEBOOK CONTEXT:
    {extra_info}

    BUDGET: {budget} PLN
    Rules: Answer in English. Lisbon is in Portugal. Break it down into Day 1 and Day 2.
    """

    response = llm.invoke(prompt)
    return response.content


# --- ENTRY POINT ---
if __name__ == "__main__":
    print("🌍 Welcome to Travel-Graph Agent!")
    my_budget = 1500
    plan = generate_itinerary("I want to fly to Lisbon", my_budget)
    print("\n" + "=" * 40)
    print(plan)
    print("=" * 40)
    driver.close()