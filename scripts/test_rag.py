import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=os.getenv("OLLAMA_BASE_URL"),
)

vectorstore = Chroma(
    persist_directory=os.getenv("CHROMA_PATH"),
    embedding_function=embeddings,
)

llm = OllamaLLM(
    model="llama3.2",
    base_url=os.getenv("OLLAMA_BASE_URL"),
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 6})

prompt = ChatPromptTemplate.from_template("""
Answer the question using only the context below.

Context:
{context}

Question:
{question}
""")

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

query = "What are the best neighbourhoods to visit in Lisbon?"
print(f"Query: {query}\n")
result = chain.invoke(query)
print(f"Answer:\n{result}")