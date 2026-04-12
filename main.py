# main.py
from flights import sync_flights_from_radar
from itinerary_agent import generate_itinerary

# 1. Pobierz świeże dane z API i wrzuć do grafu
sync_flights_from_radar('WAW', 'LIS')

# 2. Na podstawie tego, co JEST W GRAFIE, wygeneruj plan
budzet = 2000
plan = generate_itinerary("Plan podróży do Lizbony", budzet)

print(plan)