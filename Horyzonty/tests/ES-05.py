import os
import sys
import re
from unittest.mock import patch
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)


# 1. Tworzymy fałszywą prognozę pogody dla Edynburga
def mock_get_weather(city, days=5):
    return {
        "city": city,
        "source": "Mock Forecast (ES-05)",
        "forecast": [
            {"date": "Day 1", "description": "Sunny", "temp_avg": 12, "rain_probability": 10, "outdoor_friendly": True,
             "outdoor_level": "perfect"},
            {"date": "Day 2", "description": "Heavy Rain", "temp_avg": 8, "rain_probability": 85,
             "outdoor_friendly": False, "outdoor_level": "rainy"},  # ⚠️ DESZCZ
            {"date": "Day 3", "description": "Cloudy", "temp_avg": 10, "rain_probability": 20, "outdoor_friendly": True,
             "outdoor_level": "good"},
            {"date": "Day 4", "description": "Storm", "temp_avg": 6, "rain_probability": 95, "outdoor_friendly": False,
             "outdoor_level": "rainy"},  # ⚠️ DESZCZ
            {"date": "Day 5", "description": "Clear", "temp_avg": 11, "rain_probability": 5, "outdoor_friendly": True,
             "outdoor_level": "perfect"},
        ]
    }


load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)

# 2. Patchujemy funkcję get_weather przed importem orchestratora
with patch('tools.get_weather', side_effect=mock_get_weather):
    from orchestrator import app_graph, llm


    def test_es05():
        query = "Plan 5 days in Edinburgh in November — I want to visit outdoor attractions."

        print("🚀 Uruchamiam test ES-05 (Weather-aware scheduling)...")
        print("🌦️ Wstrzyknięto fałszywą pogodę: Dzień 2 i 4 to ulewy (>80% deszczu).")

        result = app_graph.invoke({
            "messages": [], "city": "Edinburgh", "budget": 3000.0, "duration": 5,
            "conversation_history": [], "current_plan": "", "intent": "new_trip",
            "user_message": query
        })

        plan = result.get("final_plan", "")

        print("-" * 50)
        print("📋 WYGENEROWANY PLAN (fragment):")
        # Wyświetlamy tylko plan dni
        import re
        days_only = re.search(r'(## 📅 Day 1.*?)(## 💰 Cost Summary|$)', plan, re.DOTALL)
        if days_only:
            print(days_only.group(1))
        else:
            print(plan)
        print("-" * 50)

        # 3. LLM-as-a-judge ocenia przestrzeganie pogody
        prompt = f"""You are a strict QA evaluator for a travel planning system.
        Look at the travel plan below. The weather forecast for this trip was:
        Day 1: Sunny
        Day 2: HEAVY RAIN
        Day 3: Cloudy
        Day 4: STORM
        Day 5: Clear

        Rule to evaluate: Zero outdoor activities (like Arthur's Seat, Princes Street Gardens, Royal Botanic Garden) should be scheduled on Day 2 and Day 4. 
        Only INDOOR activities (like Museums or Galleries) are allowed on Day 2 and Day 4.

        ITINERARY TO EVALUATE:
        {plan}

        Did the system successfully keep Day 2 and Day 4 free of ANY outdoor attractions?
        Rate it from 1 to 5, where 5 means NO outdoor attractions were scheduled on Days 2 and 4.
        Start your response with the number. Example: "5 - because..."
        """

        print("⚖️ Sędzia LLM sprawdza, czy nikt nie zmókł na wycieczce...")
        evaluation = llm.invoke(prompt).content.strip()
        print(f"📝 OCYNA SĘDZIEGO:\n{evaluation}")

        match = re.search(r'^\d+', evaluation)
        score = int(match.group()) if match else 1

        if score >= 4:
            print("\n🎯 ES-05: SUCCESS CRITERIA MET! (Agent uniknął deszczu)")
        else:
            print("\n⚠️ ES-05: EWALUACJA OBLANA. Agent wysłał użytkownika na deszcz.")

if __name__ == "__main__":
    test_es05()