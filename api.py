import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from orchestrator import app_graph, TripState  # Importujemy Twój graf!

app = FastAPI(title="Travel-Graph LangGraph API")


@app.websocket("/ws/plan")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # 1. Czekamy na dane od użytkownika (miasto, budżet)
        data_text = await websocket.receive_text()
        request_data = json.loads(data_text)

        city = request_data.get("city", "Lisbon")
        budget = float(request_data.get("budget", 2000.0))

        initial_state = {
            "messages": [],
            "city": city,
            "budget": budget
        }

        # 2. STRUMIENIOWANIE (Magia LangGraph)
        # app_graph.stream() zwraca informacje po każdym zakończonym agencie!
        for output in app_graph.stream(initial_state):
            # output to słownik, np. {"Researcher": {"research_data": ...}}
            for node_name, state_update in output.items():

                # Wysyłamy do frontendu informację, który agent właśnie skończył pracę
                await websocket.send_json({
                    "type": "agent_update",
                    "agent": node_name,
                    "message": f"Agent [{node_name}] zakończył zadanie."
                })

                # Jeśli to był ostatni agent (Planner), wysyłamy gotowy tekst
                if node_name == "Planner":
                    await websocket.send_json({
                        "type": "final_plan",
                        "content": state_update.get("final_plan", "Brak planu.")
                    })

                # Dajemy serwerowi chwilę na "oddech" (asynchroniczność)
                await asyncio.sleep(0.5)

        await websocket.send_json({"type": "done", "message": "Proces zakończony."})

    except WebSocketDisconnect:
        print("Klient się rozłączył.")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


if __name__ == "__main__":
    print("🚀 Uruchamiam serwer WebSocket na porcie 8000...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)