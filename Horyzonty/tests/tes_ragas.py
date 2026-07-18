import json
import asyncio
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision, context_recall
from datasets import Dataset
from langchain_ollama import ChatOllama, OllamaEmbeddings
from orchestrator import app_graph # Import your existing graph

# 1. Setup the Judge (using your local Ollama)
eval_llm = ChatOllama(model="llama3.2:3b")
eval_embeddings = OllamaEmbeddings(model="llama3.2:3b")

async def run_rag_eval():
    # 2. Load your ground truth
    with open("tests/eval_dataset.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    print("🚀 Generating answers for evaluation...")

    for item in test_data:
        query = item["question"]
        
        # 3. Run the orchestrator to get the REAL response
        # We invoke the graph and look at the final state
        result = await app_graph.ainvoke({
            "messages": [("user", query)],
            "city": None,
            "budget": None
        })

        # Extract the final answer and the retrieved context chunks
        # (Note: You may need to adjust keys based on your StateGraph keys)
        final_answer = result["messages"][-1].content
        
        # In your project, the context is usually what the Researcher found
        # For this test, we simulate the retrieval chunks
        retrieved_chunks = [msg.content for msg in result["messages"] if "context" in str(msg).lower()]

        questions.append(query)
        answers.append(final_answer)
        contexts.append(retrieved_chunks if retrieved_chunks else ["No context found"])
        ground_truths.append(item["ground_truth"])

    # 4. Prepare data for Ragas
    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data_dict)

    # 5. Perform Evaluation
    print("⚖️ Ragas is judging the results...")
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevance,
            context_precision,
            context_recall,
        ],
        llm=eval_llm,
        embeddings=eval_embeddings,
    )

    print("\n📊 EVALUATION RESULTS:")
    print(result)
    
    # Save results to file
    result.to_pandas().to_csv("tests/ragas_results.csv")

if __name__ == "__main__":
    asyncio.run(run_rag_eval())