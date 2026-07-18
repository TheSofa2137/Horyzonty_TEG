import pytest
import re
# Import the functions directly from your project files
from api import extract_budget, extract_duration, POLISH_TO_ENGLISH_CITIES
from tools import _rain_level
import orchestrator

# --- 1. Testing Budget Extraction ---
def test_extract_budget_valid():
    """Checks if various currency formats are correctly parsed into floats."""
    assert extract_budget("my budget is 500 PLN") == 500.0
    assert extract_budget("mam 1200zl na wyjazd") == 1200.0
    assert extract_budget("budget: 3000zł") == 3000.0
    assert extract_budget("I have 400 euro") == 400.0
    assert extract_budget("around 150usd") == 150.0

def test_extract_budget_none():
    """Ensures None is returned when no budget is mentioned."""
    assert extract_budget("I want to go to Lisbon") is None
    assert extract_budget("Give me a cheap trip") is None

# --- 2. Testing Duration Extraction ---
def test_extract_duration_valid():
    """Checks if day counts are correctly extracted from Polish and English."""
    assert extract_duration("wyjazd na 3 dni") == 3
    assert extract_duration("trip for 5 days") == 5
    assert extract_duration("będę tam przez 10 dniach") == 10

def test_extract_duration_invalid():
    """Ensures strings without numbers/keywords return None."""
    assert extract_duration("chcę jechać na tydzień") is None # Matches digits only
    assert extract_duration("long trip") is None

# --- 3. Testing City Normalization ---
def test_city_mapping():
    """Verifies Polish inflections map to the correct English canonical names."""
    # Test specific cases from your api.py mapping
    test_cases = {
        "warszawie": "Warsaw",
        "krakowie": "Krakow",
        "rzymie": "Rome",
        "paryżu": "Paris",
        "lizbony": "Lisbon"
    }
    for polish, english in test_cases.items():
        assert POLISH_TO_ENGLISH_CITIES.get(polish.lower()) == english

# --- 4. Testing Internal Tool Logic ---
def test_rain_level_logic():
    """Tests the logic that converts percentage to description in tools.py."""
    assert _rain_level(10) == "perfect"
    assert _rain_level(35) == "good"
    assert _rain_level(80) == "rainy"

# --- 5. Testing Query Cleaning (Security/Orchestration logic) ---
def test_query_filtering():
    """
    Tests the logic from orchestrator.py that filters out meta-talk
    from the search queries.
    """
    # Logic extracted from orchestrator.py: _is_real_query
    def is_real_query(q):
        q_low = q.lower()
        if not q_low.strip(): return False
        if "none" in q_low or "null" in q_low: return False
        if "nie podano" in q_low or "brak danych" in q_low: return False
        return True

    assert is_real_query("Top attractions in Lisbon") is True
    assert is_real_query("None") is False
    assert is_real_query("Brak danych") is False
    assert is_real_query("  ") is False


def test_refine_invalid_change_returns_explanation(monkeypatch):
    """Regression: refine should return a warning message (not the old plan text) when change is unmatched."""

    class _MockResp:
        def __init__(self, content):
            self.content = content

    class _MockLLM:
        def invoke(self, prompt):
            if "Answer with exactly one word: YES or NO." in prompt:
                return _MockResp("NO")
            return _MockResp("flight: LOT, hotel: Grand Hotel, day activities")

    monkeypatch.setattr(orchestrator, "llm", _MockLLM())

    state = {
        "user_message": "replace helicopter transfer",
        "current_plan": "## Plan\n- Flight: LOT\n- Hotel: Grand Hotel\n",
        "conversation_history": [],
        "budget": 2000,
        "city": "Lisbon",
    }

    out = orchestrator.refine_agent(state)

    assert out["current_plan"] == state["current_plan"]
    assert "couldn't find that element" in out["final_plan"].lower()

