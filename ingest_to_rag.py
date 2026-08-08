import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# 1. Konfiguracja ścieżek
PROCESSED_DATA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\data\processed"
CHROMA_PATH = r"C:\Users\zuzan\Desktop\Horyzonty\backend\chroma_db"

def ingest_data():
    # 2. Załadowanie plików .txt wygenerowanych wcześniej
    print("Ładowanie dokumentów")
    loader = DirectoryLoader(PROCESSED_DATA_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    documents = loader.load()

    # 3. Podział tekstu na fragmenty (Chunking)
    # LLM lepiej radzi sobie z mniejszymi blokami tekstu
    print("Dzielenie tekstu na fragmenty")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(documents)

    # 4. Inicjalizacja modelu Embedding (Ollama musi być włączona!)
    print("Generowanie embeddingów i zapis do ChromaDB")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # 5. Tworzenie bazy danych
    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f"Sukces! Baza RAG została zapisana w: {CHROMA_PATH}")

if __name__ == "__main__":
    ingest_data()