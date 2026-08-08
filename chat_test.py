import os
import numpy as np
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama

# 1. Konfiguracja
PROCESSED_DATA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\data\processed"
embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="llama3.2:3b")

print("📂 Ładowanie i dzielenie dokumentów...")
# Dodaliśmy loader_kwargs={'encoding': 'utf-8'}
loader = DirectoryLoader(
    PROCESSED_DATA_PATH,
    glob="*.txt",
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'}
)

try:
    docs = loader.load()
    print(f"✅ Załadowano {len(docs)} dokumentów.")
except Exception as e:
    print(f"❌ Nadal występuje błąd ładowania: {e}")
    exit()

splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
chunks = [doc.page_content for doc in splitter.split_documents(docs)]

# 2. Generujemy wektory (embeddingi) dla wszystkich fragmentów
print(f"🧠 Generowanie wiedzy dla {len(chunks)} fragmentów (to potrwa chwilę)...")
chunk_embeddings = embeddings_model.embed_documents(chunks)


def get_best_context(query, k=3):
    # Zamień pytanie na wektor
    query_embedding = embeddings_model.embed_query(query)

    # Oblicz podobieństwo (cosinus similarity) - prosta matematyka
    similarities = [np.dot(query_embedding, chunk_emb) for chunk_emb in chunk_embeddings]

    # Wybierz k najlepszych indeksów
    best_indices = np.argsort(similarities)[-k:][::-1]
    return "\n---\n".join([chunks[i] for i in best_indices])


# 3. Pętla czatu
print("\n✅ SYSTEM GOTOWY! Twoje dane z Wikivoyage są załadowane.")
while True:
    query = input("\nTwoje pytanie (lub 'exit'): ")
    if query.lower() == 'exit':
        break

    print("🔍 Szukam w dokumentach...")
    context = get_best_context(query)

    full_prompt = f"""
        Jesteś pomocnym asystentem podróży. 
        Użyj poniższego KONTEKSTU (który jest po angielsku), aby odpowiedzieć na PYTANIE użytkownika w języku POLSKIM.

        KONTEKST:
        {context}

        PYTANIE: 
        {query}

        ODPOWIEDŹ (po polsku):
        """

    print("\n🤖 ODPOWIEDŹ:")
    for chunk in llm.stream(full_prompt):
        print(chunk.content, end="", flush=True)
    print("\n")