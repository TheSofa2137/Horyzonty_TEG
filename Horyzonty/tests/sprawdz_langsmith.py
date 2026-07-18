import os
from langsmith import Client

import os
langsmith_token = os.environ.get("LANGSMITH_API_KEY")

# 2. Wymuszamy nadpisanie wszelkich zmiennych środowiskowych,
# żeby odciąć się od potencjalnie zepsutego pliku .env
os.environ["LANGCHAIN_API_KEY"] = MOJ_KLUCZ
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "test-project"

print(f"Próbuję połączyć się z kluczem zaczynającym się od: {MOJ_KLUCZ[:12]}...")

try:
    # Tworzymy klienta
    client = Client()
    # Próbujemy wykonać najprostszą operację odczytu (pobranie listy projektów)
    projects = list(client.list_projects())
    print("✅ SUKCES! Połączono z serwerem LangSmith.")
    print(f"Znalazłem {len(projects)} projektów na Twoim koncie.")
except Exception as e:
    print("❌ BŁĄD POŁĄCZENIA:")
    print(e)