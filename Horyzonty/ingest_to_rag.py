import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import shutil

# 1. Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")
CHROMA_PATH = os.path.join(BASE_DIR, "backend", "chroma_db")

def ingest_data():
    print("Loading documents")
    loader = DirectoryLoader(PROCESSED_DATA_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    documents = loader.load()

    # NOWE: Dodanie metadanych miasta na podstawie nazwy pliku
    for doc in documents:
        # np. z "Lisbon.txt" robi "Lisbon"
        city_name = os.path.basename(doc.metadata['source']).replace('.txt', '').replace('_', ' ')
        doc.metadata['city'] = city_name
        # Opcjonalnie: wzmocnienie kontekstu w samym tekście
        doc.page_content = f"[{city_name}] {doc.page_content}"

    print("Splitting text into chunks")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    print("Generating embeddings and saving to ChromaDB")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # NOWE: Usunięcie starej bazy (bez tagów), aby zrobić miejsce na nową
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH, ignore_errors=True)

    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
    print(f"Success! RAG database saved at: {CHROMA_PATH}")

if __name__ == "__main__":
    ingest_data()