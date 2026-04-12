import os
import numpy as np
from neo4j import GraphDatabase
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- KONFIGURACJA ---
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"  # Upewnij się, że hasło jest poprawne
PROCESSED_DATA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\data\processed"

# Inicjalizacja modeli
embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3.2:3b")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# --- SILNIK RAG (Wyszukiwanie tekstowe) ---
print("📂 Inicjalizacja bazy wiedzy Wikivoyage...")
loader = DirectoryLoader(PROCESSED_DATA_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
chunks = [doc.page_content for doc in splitter.split_documents(docs)]
chunk_embeddings = embeddings_model.embed_documents(chunks)


def get_best_context(query, k=2):
    query_embedding = embeddings_model.embed_query(query)
    similarities = [np.dot(query_embedding, chunk_emb) for chunk_emb in chunk_embeddings]
    best_indices = np.argsort(similarities)[-k:][::-1]
    return "\n---\n".join([chunks[i] for i in best_indices])


# --- SILNIK GRAFOWY (Ceny i Fakty) ---
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


# --- AGENT PLANISTA ---
def generate_itinerary(user_query, budget):
    print(f"🕵️ Analizuję możliwości dla budżetu {budget} PLN...")

    plan_data = get_budget_plan("Lisbon", budget)
    if not plan_data:
        return "Niestety, nie znalazłem lotów i atrakcji w tym budżecie. Spróbuj zwiększyć kwotę!"

    attraction_names = ", ".join([a['name'] for a in plan_data['attractions']])
    print(f"🔍 Pobieram opisy dla: {attraction_names}...")

    # Wywołanie naprawionej funkcji
    extra_info = get_best_context(f"Information about {attraction_names} in Lisbon", k=2)

    prompt = f"""
    Jesteś profesjonalnym przewodnikiem. Stwórz 2-dniowy plan wycieczki do Lizbony.

    DANE Z GRAFU:
    - Lot: {plan_data['airline']} ({plan_data['flight_price']} PLN)
    - Atrakcje: {plan_data['attractions']}

    KONTEKST Z PRZEWODNIKA:
    {extra_info}

    BUDŻET: {budget} PLN
    Zasady: Odpowiedz po polsku. Lizbona jest w Portugalii. Rozpisz Dzień 1 i Dzień 2.
    """

    response = llm.invoke(prompt)
    return response.content


# --- START ---
if __name__ == "__main__":
    print("🌍 Witaj w Travel-Graph Agent!")
    moj_budzet = 1500
    plan = generate_itinerary("Chcę lecieć do Lizbony", moj_budzet)
    print("\n" + "=" * 40)
    print(plan)
    print("=" * 40)
    driver.close()