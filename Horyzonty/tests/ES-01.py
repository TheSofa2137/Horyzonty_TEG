import os
import sys
from dotenv import load_dotenv

# 1. Ścieżka do głównego folderu projektu (Horyzonty)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

# 2. Wymuszenie wczytania pliku .env z głównego folderu
dotenv_path = os.path.join(ROOT_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

# 3. Szybki test czy klucz na pewno się wczytał
api_key = os.environ.get("LANGCHAIN_API_KEY")
if not api_key:
    print("❌ BŁĄD: Nie znaleziono klucza LANGCHAIN_API_KEY w pliku .env!")
    sys.exit(1)
elif not api_key.startswith("lsv2_pt_"):
    print("⚠️ OSTRZEŻENIE: Twój klucz wygląda podejrzanie. Powinien zaczynać się od 'lsv2_pt_'.")

from langsmith import Client
from langsmith.evaluation import evaluate
from orchestrator import get_best_context

# Podajemy klucz jawnie, aby ominąć problemy z plikiem .env
client = Client()
# ... (reszta kodu bez zmian, zaczynając od definicji dataset_name)

load_dotenv(override=True)
client = Client()

# 1. Definicja zbioru danych dla ES-01
dataset_name = "ES-01-Neighbourhoods"
if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(dataset_name=dataset_name)
    client.create_example(
        inputs={"question": "What are the best neighbourhoods to stay in Lisbon for a first-time visitor?"},
        outputs={"expected": ["Baixa", "Príncipe Real", "Alfama", "Chiado"]},
        dataset_id=dataset.id,
    )


def predict_rag(inputs: dict):
    query = inputs["question"]
    # Wymuszamy na systemie szukanie TYLKO w dokumentach z Lizbony
    context, sources = get_best_context(query, city="Lisbon", k=8)
    return {"retrieved_context": context}


# 3. Własny ewaluator (działa lokalnie, bez OpenAI!)
def exact_match_evaluator(run, example):
    retrieved_text = run.outputs.get("retrieved_context", "")
    expected_hoods = example.outputs.get("expected", [])

    # Sprawdzamy, ile z oczekiwanych dzielnic fizycznie znajduje się w kontekście
    found = [hood for hood in expected_hoods if hood.lower() in retrieved_text.lower()]
    score = len(found) / len(expected_hoods) if expected_hoods else 0.0

    return {
        "key": "context_precision",
        "score": score,
        "comment": f"Znaleziono {len(found)}/{len(expected_hoods)} dzielnic: {', '.join(found)}"
    }


if __name__ == "__main__":
    print("🚀 Uruchamianie ewaluacji RAG...")
    experiment_results = evaluate(
        predict_rag,
        data=dataset_name,
        evaluators=[exact_match_evaluator],
        experiment_prefix="es-01-retrieval-test",
    )
    print("✅ Gotowe! Sprawdź wyniki w dashboardzie LangSmith.")