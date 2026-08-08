import os
import numpy as np
from neo4j import GraphDatabase
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

# --- 1. KONFIGURACJA BAZ I MODELI ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PW = "12345678"  # Upewnij się, że to Twoje aktualne hasło!
PROCESSED_DATA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\data\processed"

# Inicjalizacja sterowników i LLM
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW))
embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3.2:3b")

# --- 2. SILNIK RAG (Wiedza z Wikivoyage) ---
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


# --- 3. STAN APLIKACJI (LangGraph State) ---
class TripState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    city: str
    budget: float
    research_data: dict
    flights_hotels: dict
    final_plan: str


# --- 4. AGENTY (Węzły LangGraph) ---
def researcher_agent(state: TripState):
    city = state["city"]
    print(f"🔍 [Researcher] Przeszukuję bazę grafową i teksty dla: {city}...")

    with driver.session() as session:
        result = session.run("MATCH (a:Attraction)-[:LOCATED_IN]->(c:City {name: $city}) RETURN a.name AS name",
                             city=city)
        attractions = [record["name"] for record in result]

    if not attractions:
        attractions = ["Brak zapisanych atrakcji w grafie"]
        context = "Brak informacji z przewodnika."
    else:
        attractions_str = ", ".join(attractions)
        context = get_best_context(f"Tell me about {attractions_str} in {city}", k=2)

    return {"research_data": {"attractions": attractions, "context": context}}


def booking_agent(state: TripState):
    city = state["city"]
    budget = state["budget"]
    print(f"💳 [Booking] Sprawdzam loty i hotele do {budget} PLN...")

    with driver.session() as session:
        query = """
        MATCH (f:Flight)-[:FLIES_TO]->(c:City {name: $city})
        MATCH (h:Hotel)-[:LOCATED_IN]->(c)
        WHERE f.price IS NOT NULL AND h.price IS NOT NULL
        WITH f, h, (f.price + h.price) as base_cost
        WHERE base_cost <= $budget
        RETURN f.airline as airline, f.price as flight_price,
               h.name as hotel_name, h.price as hotel_price
        ORDER BY base_cost DESC LIMIT 1
        """
        result = session.run(query, city=city, budget=budget).single()

        if result:
            booking_info = dict(result)
        else:
            booking_info = {"error": "Zbyt mały budżet na lot i hotel!"}

    return {"flights_hotels": booking_info}


def planner_agent(state: TripState):
    print("📅 [Planner] Generuję finałowy plan...")

    research = state.get("research_data", {})
    booking = state.get("flights_hotels", {})
    budget = state["budget"]

    if "error" in booking:
        return {"final_plan": f"Przykro mi, ale nie znalazłem lotu i hotelu w budżecie {budget} PLN."}

    attractions_list = ", ".join(research.get('attractions', []))
    context = research.get('context', '')

    prompt = f"""
    Jesteś profesjonalnym przewodnikiem. Stwórz 2-dniowy plan wycieczki do {state['city']} w Portugalii.

    DANE Z REZERWACJI:
    - Lot: {booking.get('airline')} ({booking.get('flight_price')} PLN)
    - Nocleg: {booking.get('hotel_name')} ({booking.get('hotel_price')} PLN)
    - Budżet max: {budget} PLN

    WIEDZA O MIEJSCU:
    - Atrakcje z bazy: {attractions_list}
    - Kontekst z Wikivoyage: {context}

    WYMAGANIA:
    Napisz po polsku. Rozpisz plan na Dzień 1 i Dzień 2. Uwzględnij powyższe koszty w budżecie.
    """

    response = llm.invoke(prompt)
    return {"final_plan": response.content}


# --- 5. BUDOWA GRAFU ---
workflow = StateGraph(TripState)

workflow.add_node("Researcher", researcher_agent)
workflow.add_node("Booking", booking_agent)
workflow.add_node("Planner", planner_agent)

workflow.set_entry_point("Researcher")
workflow.add_edge("Researcher", "Booking")
workflow.add_edge("Booking", "Planner")
workflow.add_edge("Planner", END)

app_graph = workflow.compile()

# --- 6. URUCHOMIENIE ---
if __name__ == "__main__":
    print("🚀 Test LangGraph Orchestrator...")
    initial_state = {
        "messages": [],
        "city": "Lisbon",
        "budget": 2000.0
    }

    result = app_graph.invoke(initial_state)
    print("\n" + "=" * 50)
    print("✅ FINAŁOWY PLAN:")
    print(result['final_plan'])
    print("=" * 50)
    driver.close()