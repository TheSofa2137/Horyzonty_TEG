"""
Simple WebSocket echo server for testing the frontend during development.
This helps you test the UI without needing the full orchestration system.

To use:
1. Run: uvicorn test_websocket:app --reload --host 0.0.0.0 --port 8000
2. Start frontend: npm start
3. Open http://localhost:3000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

app = FastAPI()

# Add CORS middleware for HTTP requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample destinations knowledge base
DESTINATIONS = {
    "lisbon": {
        "description": "Lisbon is the capital and largest city of Portugal.",
        "attractions": ["Belém Tower", "Jerónimos Monastery", "Alfama District"],
        "food": ["Pastéis de Nata", "Grilled Fish", "Seafood Rice"],
        "neighborhoods": ["Baixa", "Príncipe Real", "Alfama", "Bairro Alto"]
    },
    "barcelona": {
        "description": "Barcelona is the capital city of Catalonia in Spain.",
        "attractions": ["Sagrada Familia", "Park Güell", "Gothic Quarter"],
        "food": ["Paella", "Jamón Ibérico", "Crema Catalana"],
        "neighborhoods": ["Eixample", "Gothic Quarter", "Montjuïc"]
    },
    "porto": {
        "description": "Porto is Portugal's second-largest city, known for port wine.",
        "attractions": ["Livraria Lello", "Dom Luís Bridge", "Ribeira District"],
        "food": ["Francesinha", "Tripeiros", "Sardines"],
        "neighborhoods": ["Ribeira", "Miragaia", "Cedofeita"]
    }
}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "").lower()

            print(f"Received: {user_message}")

            # Parse user intent and generate response
            response_content = generate_response(user_message)
            sources = extract_sources(user_message)

            # Simulate streaming with small delays
            for i, chunk in enumerate(response_content.split('. ')):
                if i > 0:
                    chunk = '. ' + chunk

                await asyncio.sleep(0.2)  # Small delay for streaming effect

            # Send complete response
            response = {
                "type": "response",
                "content": response_content,
                "sources": sources
            }

            await websocket.send_text(json.dumps(response))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Client disconnected")

def generate_response(message: str) -> str:
    """Generate a sample response based on user message."""

    # Check for destination mentions
    for dest, info in DESTINATIONS.items():
        if dest in message:
            if "plan" in message or "itinerary" in message:
                attractions = ", ".join(info["attractions"])
                food = ", ".join(info["food"])
                return f"{info['description']} Here's a suggested itinerary: Day 1 - Visit {attractions[0:20]}. Day 2 - Explore local cuisine: {food}. Day 3 - Relax and wander through {info['neighborhoods'][0]}. I found these sources for you with detailed information about each location."
            elif "food" in message or "restaurant" in message:
                food = ", ".join(info["food"])
                return f"Great question! In {dest.title()}, you should definitely try {food}. These are local specialties that will give you an authentic experience."
            elif "attraction" in message or "visit" in message:
                attractions = ", ".join(info["attractions"])
                return f"The top attractions in {dest.title()} include: {attractions}. Each offers unique historical and cultural experiences."
            else:
                return f"{info['description']} Popular neighborhoods include: {', '.join(info['neighborhoods'])}."

    # Check for flight search
    if "flight" in message:
        return "I found several flight options for you. From Warsaw to Lisbon: Option 1) Departure 10:30, Arrival 15:45 (€85), Option 2) Departure 14:00, Arrival 19:15 (€72). All prices are per person for the selected dates."

    # Check for weather
    if "weather" in message:
        return "The forecast for your trip looks great! Mostly sunny days with temperatures around 22°C. Perfect weather for outdoor activities and sightseeing."

    # Default response
    return "I'd love to help you plan your trip! You can ask me to: plan a city itinerary, search for flights, find restaurants, or get recommendations for attractions. What would you like to explore?"

def extract_sources(message: str) -> list:
    """Extract potential sources based on message."""
    sources = []

    if "lisbon" in message.lower():
        sources.extend([
            "Lisbon Travel Guide 2024 - Chapter 3: Top Attractions",
            "Portuguese Tourism Board - Food & Wine",
            "Wikitravel: Lisbon Overview",
            "TripAdvisor: Lisbon Reviews"
        ])
    elif "barcelona" in message.lower():
        sources.extend([
            "Barcelona Architecture Guide",
            "Catalan Cuisine Handbook",
            "Lonely Planet: Barcelona"
        ])
    elif "flight" in message.lower():
        sources.extend([
            "Amadeus Flight Database",
            "Current Market Pricing Data"
        ])
    else:
        sources.extend([
            "Travel Documentation Database",
            "User Reviews and Recommendations"
        ])

    return sources[:4]  # Return max 4 sources

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

