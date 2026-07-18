# main.py
from flights import sync_flights
from itinerary_agent import generate_itinerary

# 1. Seed graph with predefined flight data
sync_flights()

# 2. Based on what IS IN THE GRAPH, generate a plan
budget = 2000
plan = generate_itinerary("Trip plan to Lisbon", budget)

print(plan)