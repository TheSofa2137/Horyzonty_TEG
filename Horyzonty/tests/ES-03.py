import os
import sys
import re
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

from orchestrator import app_graph, llm

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)
client = Client()

dataset_name = "ES-03-Itinerary"
if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(dataset_name=dataset_name)
    client.create_example(
        inputs={"user_message": "Plan 3 days in Porto for a couple who love wine and architecture, budget €100/day."},
        outputs={"expected": "Valid 3-day plan with wine, architecture, and budget limits."},
        dataset_id=dataset.id,
    )


def predict_itinerary(inputs: dict):
    # Symulujemy przepuszczenie zapytania przez cały Twój LangGraph
    print("⏳ Generowanie planu przez agentów (to chwilę potrwa)...")
    result = app_graph.invoke({
        "messages": [], "city": "Porto", "budget": 800.0, "duration": 3,
        "conversation_history": [], "current_plan": "", "intent": "new_trip",
        "user_message": inputs["user_message"]
    })
    return {"final_plan": result['final_plan']}


def llm_as_judge_evaluator(run, example):
    plan = run.outputs.get("final_plan", "")

    prompt = f"""You are an impartial judge evaluating a travel itinerary. 
    Review the following itinerary based on these 4 STRICT criteria:
    1. Completeness: Covers exactly 3 days with morning, afternoon, and evening slots.
    2. Theme (Wine): Includes at least 2 wine-related activities (e.g. cellars, tastings).
    3. Theme (Architecture): Includes at least 2 architectural landmarks.
    4. Budget: No single activity mentioned exceeds 50 in cost per person.

    ITINERARY:
    {plan}

    Rate the itinerary from 1 to 5, where 5 means ALL criteria are perfectly met.
    Start your response with the number. Example: "5 - because..."
    """

    print("⚖️ Sędzia LLM ocenia plan...")
    evaluation = llm.invoke(prompt).content.strip()

    # Wyciągamy pierwszą cyfrę z odpowiedzi sędziego
    match = re.search(r'\d+', evaluation)
    score = int(match.group()) if match else 1
    normalized_score = score / 5.0  # LangSmith preferuje skalę 0.0 - 1.0 (gdzie 0.8 to 4/5)

    return {
        "key": "rubric_score",
        "score": normalized_score,
        "comment": evaluation[:200] + "..."
    }


if __name__ == "__main__":
    print("🚀 Uruchamianie ewaluacji ES-03 (End-to-end)...")
    experiment_results = evaluate(
        predict_itinerary,
        data=dataset_name,
        evaluators=[llm_as_judge_evaluator],
        experiment_prefix="es-03-itinerary-eval",
    )
    print("✅ Gotowe! Sprawdź wynik w LangSmith.")