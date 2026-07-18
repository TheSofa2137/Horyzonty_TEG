import os
import numpy as np
from functools import lru_cache
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama

# 1. Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")


@lru_cache(maxsize=1)
def _build_knowledge_base():
    print("📂 Loading and splitting documents...")
    loader = DirectoryLoader(
        PROCESSED_DATA_PATH,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    docs = loader.load()
    print(f"✅ Loaded {len(docs)} documents.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = [doc.page_content for doc in splitter.split_documents(docs)]

    embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
    print(f"🧠 Generating knowledge for {len(chunks)} chunks (this may take a moment)...")
    chunk_embeddings = embeddings_model.embed_documents(chunks)
    llm = ChatOllama(model="llama3.2:3b")
    return embeddings_model, llm, chunks, chunk_embeddings


def get_best_context(query, k=3):
    embeddings_model, _, chunks, chunk_embeddings = _build_knowledge_base()
    # Convert question to a vector
    query_embedding = embeddings_model.embed_query(query)

    # Calculate similarity (cosine similarity)
    similarities = [np.dot(query_embedding, chunk_emb) for chunk_emb in chunk_embeddings]

    # Select k best indices
    best_indices = np.argsort(similarities)[-k:][::-1]
    selected_chunks = [str(chunks[int(i)]) for i in best_indices]
    return "\n---\n".join(selected_chunks)


def main() -> None:
    _, llm, _, _ = _build_knowledge_base()
    print("\n✅ SYSTEM READY! Your Wikivoyage data has been loaded.")
    while True:
        query = input("\nYour question (or 'exit'): ")
        if query.lower() == 'exit':
            break

        print("🔍 Searching documents...")
        context = get_best_context(query)

        full_prompt = f"""
            You are a helpful travel assistant. 
            Use the CONTEXT below to answer the user's QUESTION in English.

            CONTEXT:
            {context}

            QUESTION: 
            {query}

            ANSWER:
            """

        print("\n🤖 ANSWER:")
        for chunk in llm.stream(full_prompt):
            print(chunk.content, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()

