import os
import sys
import difflib
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

from orchestrator import app_graph

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)


def test_es06():
    # Surowy plan "przed" zmianą
    original_plan = """## 📅 Day 1 — Arrival
**🌅 Morning (9:00–12:00)**
- 9:00 → City Walk | OUTDOOR | free

## 📅 Day 2 — Sightseeing
**🌅 Morning (9:00–12:00)**
- 9:00 → National Museum | INDOOR | free

**☀️ Midday (12:00–14:00)**
- Lunch nearby: Traditional Steakhouse, ~80 PLN

**🌇 Afternoon (14:00–18:00)**
- 14:00 → Royal Castle | OUTDOOR | 50 PLN

## 📅 Day 3 — Departure
**🌅 Morning (9:00–12:00)**
- 9:00 → Souvenir Shopping | INDOOR | free"""

    query = "Replace the Day 2 lunch with a vegetarian option under €15."

    print("🚀 Uruchamiam test ES-06 (Itinerary refinement)...")

    # Wywołujemy LangGraph omijając planistę - celujemy prosto w refinement
    result = app_graph.invoke({
        "messages": [],
        "city": "Lisbon",
        "budget": 3000.0,
        "duration": 3,
        "conversation_history": [{"role": "assistant", "content": original_plan}],
        "current_plan": original_plan,
        "intent": "refine",
        "user_message": query
    })

    new_plan = result.get("final_plan", "")

    print("-" * 50)
    print("📋 ZMODYFIKOWANY PLAN:")
    print(new_plan)
    print("-" * 50)

    # WERYFIKACJA MUTACJI:
    passed = True

    # Odcinamy nagłówek (ze znacznikiem ✏️), żeby nie szukać starych słów w logu zmian
    plan_body = new_plan.split("## 📅 Day 1")[1] if "## 📅 Day 1" in new_plan else new_plan

    # 1. Czy stary element zniknął z SAMEGO PLANU?
    if "Traditional Steakhouse" in plan_body:
        print("❌ BŁĄD: 'Traditional Steakhouse' nadal istnieje w planie.")
        passed = False
    else:
        print("✅ MUTACJA: 'Traditional Steakhouse' zostało poprawnie usunięte z harmonogramu.")

    # 2. Czy dodano opcję wegetariańską?
    if "vegetarian" not in new_plan.lower() and "veg " not in new_plan.lower():
        print("❌ BŁĄD: Nie znaleziono opcji wegetariańskiej w nowym planie.")
        passed = False
    else:
        print("✅ MUTACJA: Dodano posiłek wegetariański.")

    # 3. Zabezpieczenie przed Side-Effects (Czy Dzień 1 i 3 przetrwały?)
    if "City Walk" not in plan_body or "Souvenir Shopping" not in plan_body:
        print("❌ BŁĄD (SIDE EFFECT): Agent skrócił/zepsuł inne dni zamiast skopiować je 1:1.")
        passed = False
    else:
        print("✅ SIDE-EFFECTS: Inne dni i aktywności (City Walk, Souvenir Shopping) pozostały nienaruszone!")

    if passed:
        print("\n🎯 ES-06: SUCCESS CRITERIA MET! (Agent chirurgicznie podmienił lunch bez uszkadzania planu)")
    else:
        print("\n⚠️ ES-06: EWALUACJA OBLANA.")

if __name__ == "__main__":
    test_es06()