import sys
import os
from typing import Any, cast

# ── Windows compatibility ─────────────────────────────────────────────────────
# MUST be before ALL other imports: orchestrator.py runs module-level print()
# calls with emoji the moment it is imported, before any later fix can apply.
# Ensure emojis and Unicode in print() work on Windows cmd / PowerShell.
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# asyncio ProactorEventLoop (Windows default in Python 3.8+) does not support
# all socket operations that uvicorn + WebSockets require.
if sys.platform == "win32":
    import asyncio as _asyncio
    if sys.version_info < (3, 14):
        _selector_policy = getattr(_asyncio, "WindowsSelectorEventLoopPolicy", None)
        if _selector_policy is not None:
            _asyncio.set_event_loop_policy(_selector_policy())

import warnings
# Suppress LangGraph's pending deprecation warning about JsonPlusSerializer's
# `allowed_objects` default changing in a future version.  The warning fires
# inside langgraph/cache/base/__init__.py at import time and cannot be
# addressed in user code until LangGraph exposes the parameter publicly.
warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change",
)

from dotenv import load_dotenv
load_dotenv(override=True)

import json
import re
import datetime as dt
from functools import lru_cache
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from langchain_ollama import ChatOllama
from orchestrator import app_graph, is_input_safe


@lru_cache(maxsize=1)
def _get_llm():
    return ChatOllama(model="llama3.2:3b")


_AMBIGUOUS_ENGLISH_CITY_NAMES: frozenset[str] = frozenset({"nice"})

# Polish inflected city forms → canonical English names.
# "Praga" = Prague (Czech Republic), NOT the Praga district of Warsaw.
POLISH_TO_ENGLISH_CITIES: dict[str, str] = {
    # Poland
    "warszawa": "Warsaw", "warszawy": "Warsaw", "warszawie": "Warsaw",
    "kraków": "Krakow", "krakow": "Krakow", "krakowa": "Krakow", "krakowie": "Krakow",
    "wrocław": "Wroclaw", "wroclaw": "Wroclaw", "wrocławia": "Wroclaw", "wrocławiu": "Wroclaw",
    "gdańsk": "Gdansk", "gdansk": "Gdansk", "gdańska": "Gdansk", "gdańsku": "Gdansk",
    "poznań": "Poznan", "poznan": "Poznan", "poznania": "Poznan", "poznaniu": "Poznan",
    "łódź": "Lodz", "lodz": "Lodz", "łodzi": "Lodz",
    "katowice": "Katowice", "katowicach": "Katowice",
    "lublin": "Lublin", "lublina": "Lublin", "lublinie": "Lublin",
    "białystok": "Bialystok", "białegostoku": "Bialystok",
    "szczecin": "Szczecin", "szczecina": "Szczecin", "szczecinie": "Szczecin",
    "bydgoszcz": "Bydgoszcz", "bydgoszczy": "Bydgoszcz",
    "gdynia": "Gdynia", "gdyni": "Gdynia",
    "toruń": "Torun", "torun": "Torun", "torunia": "Torun", "toruniu": "Torun",
    "zakopane": "Zakopane", "zakopanem": "Zakopane",
    "trójmiasto": "Tricity",

    # Western Europe
    "praga": "Prague", "pragi": "Prague", "pradze": "Prague",
    "paryż": "Paris", "paryża": "Paris", "paryżu": "Paris",
    "londyn": "London", "londynu": "London", "londynie": "London",
    "rzym": "Rome", "rzymu": "Rome", "rzymie": "Rome",
    "wiedeń": "Vienna", "wiednia": "Vienna", "wiedniu": "Vienna",
    "madryt": "Madrid", "madrytu": "Madrid", "madrycie": "Madrid",
    "barcelona": "Barcelona", "barcelony": "Barcelona", "barcelonie": "Barcelona",
    "amsterdam": "Amsterdam", "amsterdamu": "Amsterdam", "amsterdamie": "Amsterdam",
    "bruksela": "Brussels", "brukseli": "Brussels",
    "berlin": "Berlin", "berlina": "Berlin", "berlinie": "Berlin",
    "monachium": "Munich",
    "frankfurt": "Frankfurt", "frankfurtu": "Frankfurt", "frankfurcie": "Frankfurt",
    "hamburg": "Hamburg", "hamburga": "Hamburg", "hamburgu": "Hamburg",
    "drezno": "Dresden", "drezna": "Dresden", "dreźnie": "Dresden",
    "kopenhaga": "Copenhagen", "kopenhagi": "Copenhagen", "kopenhadze": "Copenhagen",
    "sztokholm": "Stockholm", "sztokholmu": "Stockholm", "sztokholmie": "Stockholm",
    "oslo": "Oslo",
    "helsinki": "Helsinki",
    "ateny": "Athens", "aten": "Athens", "atenach": "Athens",
    "stambuł": "Istanbul", "stambułu": "Istanbul", "stambule": "Istanbul",
    "lizbona": "Lisbon", "lizbony": "Lisbon", "lizbonie": "Lisbon",
    "porto": "Porto",
    "sewilla": "Seville", "sewilli": "Seville",
    "walencja": "Valencia", "walencji": "Valencia",
    "lyon": "Lyon", "lyonu": "Lyon", "lyonie": "Lyon",
    "marsylia": "Marseille", "marsylii": "Marseille",
    "nicea": "Nice", "nicei": "Nice",
    "strasburg": "Strasbourg", "strasburga": "Strasbourg", "strasburgu": "Strasbourg",
    "mediolan": "Milan", "mediolanu": "Milan", "mediolanie": "Milan",
    "florencja": "Florence", "florencji": "Florence",
    "wenecja": "Venice", "wenecji": "Venice",
    "neapol": "Naples", "neapolu": "Naples",
    "dubrownik": "Dubrovnik", "dubrownika": "Dubrovnik", "dubrowniku": "Dubrovnik",
    "zurych": "Zurich", "zurychu": "Zurich",
    "genewa": "Geneva", "genewy": "Geneva", "genewie": "Geneva",
    "berno": "Bern", "berna": "Bern", "bernie": "Bern",
    "edinburgh": "Edinburgh",
    "edynburg": "Edinburgh", "edynburga": "Edinburgh", "edynburgu": "Edinburgh",
    "reykjavik": "Reykjavik",

    # Eastern / Central Europe
    "budapeszt": "Budapest", "budapesztu": "Budapest", "budapeszcie": "Budapest",
    "bratysława": "Bratislava", "bratysławy": "Bratislava", "bratysławie": "Bratislava",
    "bratislava": "Bratislava",
    "lublana": "Ljubljana", "lublany": "Ljubljana", "lublanie": "Ljubljana",
    "zagrzeb": "Zagreb", "zagrzebia": "Zagreb", "zagrzebiu": "Zagreb",
    "belgrad": "Belgrade", "belgradu": "Belgrade", "belgradzie": "Belgrade",
    "bukareszt": "Bucharest", "bukaresztu": "Bucharest", "bukareszcie": "Bucharest",
    "sofia": "Sofia", "sofii": "Sofia",
    "tallinn": "Tallinn",
    "ryga": "Riga", "rygi": "Riga", "rydze": "Riga",
    "wilno": "Vilnius", "wilna": "Vilnius", "wilnie": "Vilnius",
    "moskwa": "Moscow", "moskwy": "Moscow", "moskwie": "Moscow",
    "kijów": "Kyiv", "kijowa": "Kyiv", "kijowie": "Kyiv",

    # Asia
    "tokio": "Tokyo",
    "pekin": "Beijing", "pekinu": "Beijing", "pekinie": "Beijing",
    "szanghaj": "Shanghai", "szanghaju": "Shanghai",
    "hongkong": "Hong Kong", "hong kong": "Hong Kong",
    "seul": "Seoul", "seulu": "Seoul",
    "bangkok": "Bangkok", "bangkoku": "Bangkok",
    "singapur": "Singapore", "singapuru": "Singapore", "singapurze": "Singapore",
    "bali": "Bali",
    "dubaj": "Dubai", "dubaju": "Dubai", "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "mumbaj": "Mumbai", "mumbaju": "Mumbai",
    "delhi": "Delhi",
    "nowe delhi": "New Delhi",
    "kair": "Cairo", "kairu": "Cairo", "kairze": "Cairo",
    "kapsztad": "Cape Town", "kapsztadu": "Cape Town",
    "nairobi": "Nairobi",
    "marrakesz": "Marrakech", "marrakeszu": "Marrakech", "marrakech": "Marrakech",
    "casablanca": "Casablanca",

    # Americas
    "nowy jork": "New York", "nowego jorku": "New York", "nowym jorku": "New York",
    "los angeles": "Los Angeles",
    "chicago": "Chicago",
    "miami": "Miami",
    "las vegas": "Las Vegas",
    "san francisco": "San Francisco",
    "toronto": "Toronto",
    "montreal": "Montreal",
    "vancouver": "Vancouver",
    "meksyk": "Mexico City", "meksyku": "Mexico City",
    "buenos aires": "Buenos Aires",
    "rio de janeiro": "Rio de Janeiro",
    "sao paulo": "São Paulo",
    "lima": "Lima",
    "bogota": "Bogotá", "bogotá": "Bogotá",

    # Australia / Oceania
    "sydney": "Sydney",
    "melbourne": "Melbourne",
    "brisbane": "Brisbane",
    "auckland": "Auckland",
}

# Districts misidentified as cities (e.g. "Praga" as Warsaw district instead of Prague)
KNOWN_DISTRICTS_NOT_CITIES = {
    "praga-północ", "praga-południe", "mokotów", "żoliborz", "wola",
    "ursynów", "targówek", "bemowo", "ochota", "śródmieście", "bielany",
    "wilanów", "białołęka", "rembertów", "wesoła", "wawer",
    "ursus", "włochy", "bairro alto", "alfama", "belém", "chiado",
    "baixa", "mouraria",
}

app = FastAPI(title="Horyzonty API")

app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket node sets (module-level — immutable, evaluated once) ───────────
_STREAMING_NODES: frozenset[str] = frozenset(
    {"Planner", "Refine", "Justify", "Attractions", "OffTopic"}
)
_KNOWN_NODES: frozenset[str] = frozenset({
    "IntentClassifier", "Researcher", "Booking", "Planner", "Refine",
    "FlightSearch", "HotelSearch", "Attractions", "Justify",
    "GraphQuery", "Weather", "OffTopic",
})

# ── Default session values (single source of truth for init and reset) ───────
_DEFAULT_SESSION: dict = {
    "conversation_history": [],
    "current_plan": "",
    "city": "Lisbon",
    "budget": 2000.0,
    "duration": 2,
    "departure_date": "",
}


def _sync_session_from_output(session: dict, output: dict) -> None:
    """Updates mutable session state from a completed node's output dict (in-place)."""
    if "current_plan" in output:
        session["current_plan"] = output.get("current_plan", "")
    if "conversation_history" in output:
        session["conversation_history"] = output.get("conversation_history", [])


def _has_city_context(message_lower: str, city_lower: str) -> bool:
    escaped = re.escape(city_lower)
    patterns = (
        rf"\b(?:to|in|for|visit|visiting|trip to|holiday in|vacation in|go to|fly to)\s+{escaped}\b",
        rf"\b{escaped}\s+(?:trip|holiday|vacation|getaway|city break)\b",
    )
    return any(re.search(pattern, message_lower) for pattern in patterns)


def _format_flight_price_label(flight: dict) -> str:
    price = flight.get("price", "?")
    currency = str(flight.get("currency", "PLN")).upper()
    price_pln = flight.get("price_pln")
    if currency == "PLN" or price_pln in (None, "", price):
        return f"{price} {currency}"
    return f"{price} {currency} (~{int(round(float(price_pln))):,} PLN)"


async def extract_city(user_msg: str) -> str | None:
    """
    Extracts the travel destination city from a user message.
    Step 1: deterministic dictionary lookup (longest key first, word-boundary match).
    Step 2: LLM fallback with anti-hallucination prompt (async — does not block event loop).
    """
    msg_lower = user_msg.lower().strip()

    # Check longest keys first so "nowy jork" matches before "york"
    for pl_name in sorted(POLISH_TO_ENGLISH_CITIES, key=len, reverse=True):
        # Word-boundary pattern prevents "hamburg" matching inside "hamburger"
        pattern = r'(?<![a-ząćęłńóśźż])' + re.escape(pl_name) + r'(?![a-ząćęłńóśźż])'
        if re.search(pattern, msg_lower):
            en_name = POLISH_TO_ENGLISH_CITIES[pl_name]
            if pl_name in KNOWN_DISTRICTS_NOT_CITIES:
                print(f"⚠️ '{pl_name}' is a district, not a city — ignoring")
                continue
            print(f"🏙️ Dictionary: '{pl_name}' → '{en_name}'")
            return en_name

    # Also try direct English city names (e.g. "Lisbon", "Prague")
    # Use word-boundary regex (same as Polish lookup) to avoid "nice" matching "a nice hotel"
    english_cities_lower = {v.lower(): v for v in POLISH_TO_ENGLISH_CITIES.values()}
    for en_lower, en_proper in sorted(english_cities_lower.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = r'(?<![a-z])' + re.escape(en_lower) + r'(?![a-z])'
        if re.search(pattern, msg_lower):
            if en_lower in _AMBIGUOUS_ENGLISH_CITY_NAMES and not _has_city_context(msg_lower, en_lower):
                continue
            print(f"🏙️ English name matched: '{en_proper}'")
            return en_proper

    # LLM fallback — async so it doesn't block the WebSocket event loop
    prompt = f"""You are a city name extractor. Extract ONLY the travel DESTINATION CITY from the message below.

CRITICAL RULES:
- Return ONLY the city name in English (e.g. "Prague", "Paris", "Lisbon")
- "Praga" in Polish = "Prague" (capital of Czech Republic) — NOT a Warsaw district
- Do NOT return district/neighbourhood names (Bairro Alto, Alfama, Mokotów, etc.)
- Do NOT return region names (Alentejo, Tuscany, etc.) unless asked
- Do NOT add any explanation, punctuation or extra words
- If no city is mentioned, return: unknown

Examples:
- "zaplanuj wyjazd do Pragi" → Prague
- "let's go to Barcelona for 3 days" → Barcelona
- "chcę pojechać do nowego jorku" → New York
- "wycieczka do Marrakeszu" → Marrakech
- "co zwiedzić w centrum" → unknown

Message: "{user_msg}"
City:"""

    try:
        response = await _get_llm().ainvoke(prompt)         # ← non-blocking
        city = response.content.strip().strip('"').strip("'").strip(".")
        if city.lower() != "unknown" and len(city.split()) <= 4 and len(city) > 1:
            city_lower = city.lower()
            if city_lower in POLISH_TO_ENGLISH_CITIES:
                city = POLISH_TO_ENGLISH_CITIES[city_lower]
            if city_lower not in KNOWN_DISTRICTS_NOT_CITIES:
                print(f"🏙️ LLM extracted city: '{city}'")
                return city
    except Exception as e:
        print(f"⚠️ City extraction error: {e}")

    print("🏙️ Could not extract city — no change")
    return None


def extract_budget(user_msg: str) -> float | None:
    """
    Extracts budget from user message using 3-pass strategy:
      1. Number directly followed by currency keyword (PLN, zł, etc.)
      2. Number after context words (for / za / budget / max …)
      3. First number ≥ 100 (avoids "1 person", "3 adults" false positives)
    Duration patterns are stripped first to avoid confusion with day counts.
    """
    msg_clean = re.sub(
        r'\d+\s*-?\s*(?:dni|dniowy|dniowa|noce|noc|day|days|night|nights|tygodni|tydzień|week|weeks)',
        '', user_msg, flags=re.IGNORECASE
    )

    currency_pattern = r'(\d[\d\s]*(?:[.,]\d+)?)\s*(?:PLN|zł|zloty|złotych|zl|pln|EUR|euro|USD|usd|dollars?|GBP|pounds?)\b'
    m = re.search(currency_pattern, msg_clean, re.IGNORECASE)
    if m:
        try:
            budget = float(m.group(1).strip().replace(' ', '').replace(',', '.'))
            if budget >= 50:
                print(f"💰 Extracted budget (currency match): {budget}")
                return budget
        except ValueError:
            pass

    context_pattern = r'(?:for|za|budget|within|up to|do|max|maksymalnie|około|okolo|around)\s+(\d[\d\s]*(?:[.,]\d+)?)'
    m = re.search(context_pattern, msg_clean, re.IGNORECASE)
    if m:
        try:
            budget = float(m.group(1).strip().replace(' ', '').replace(',', '.'))
            if budget >= 50:
                print(f"💰 Extracted budget (context match): {budget}")
                return budget
        except ValueError:
            pass

    for num_str in re.findall(r'\d+(?:[.,]\d+)?', msg_clean):
        try:
            budget = float(num_str.replace(',', '.'))
            if budget >= 100:
                print(f"💰 Extracted budget (fallback ≥100): {budget}")
                return budget
        except ValueError:
            pass

    print("💰 No budget found in message — no change")
    return None


def extract_duration(user_msg: str) -> int | None:
    """Extracts trip length in days from user message."""
    patterns = [
        r'(\d+)\s*-?\s*(?:dni|dniowy|dniowa)',
        r'(\d+)\s*-?\s*(?:noce|noc)',
        r'(\d+)\s*(?:day|days)',
        r'(\d+)\s*(?:night|nights)',
    ]
    for pattern in patterns:
        match = re.search(pattern, user_msg, re.IGNORECASE)
        if match:
            try:
                duration = int(match.group(1))
                if 1 <= duration <= 30:
                    print(f"📅 Extracted trip length: {duration} days")
                    return duration
            except (ValueError, IndexError):
                pass
    print("📅 No trip length found in message — no change")
    return None


def extract_date(user_msg: str) -> str | None:
    """
    Extracts departure date from user message.
    Handles: '10 June', 'around 15 July', '5 maja', 'on June 10'.
    Returns ISO date YYYY-MM-DD, or None. Advances to next year if date has passed.
    """
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4,
        "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
        "września": 9, "października": 10, "listopada": 11, "grudnia": 12,
        "styczeń": 1, "luty": 2, "marzec": 3, "kwiecień": 4,
        "maj": 5, "czerwiec": 6, "lipiec": 7, "sierpień": 8,
        "wrzesień": 9, "październik": 10, "listopad": 11, "grudzień": 12,
    }

    msg = user_msg.lower()
    today = dt.date.today()
    year = today.year

    if re.search(r'\btomorrow\b', msg):
        return (today + dt.timedelta(days=1)).isoformat()

    if re.search(r'\bnext week\b', msg):
        return (today + dt.timedelta(days=7)).isoformat()

    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    for label, extra_weeks in (("this", 0), ("next", 1)):
        for weekday_name, weekday_num in weekday_map.items():
            if re.search(rf'\b{label}\s+{weekday_name}\b', msg):
                days_ahead = (weekday_num - today.weekday()) % 7
                if days_ahead == 0 and label == "next":
                    days_ahead = 7
                elif label == "next":
                    days_ahead += 7
                return (today + dt.timedelta(days=days_ahead + (extra_weeks * 0))).isoformat()

    for month_word, month_num in month_map.items():
        # "10 June" / "around 10 June"
        m = re.search(rf'\b(\d{{1,2}})\s+{re.escape(month_word)}(?:\s+(\d{{4}}))?\b', msg)
        if m:
            try:
                parsed_year = int(m.group(2)) if m.group(2) else year
                d = dt.date(parsed_year, month_num, int(m.group(1)))
                if not m.group(2) and d < today:
                    d = dt.date(year + 1, month_num, int(m.group(1)))
                print(f"📅 Extracted departure date: {d.isoformat()}")
                return d.isoformat()
            except ValueError:
                pass
        # "June 10"
        m = re.search(rf'\b{re.escape(month_word)}\s+(\d{{1,2}})(?:\s+(\d{{4}}))?\b', msg)
        if m:
            try:
                parsed_year = int(m.group(2)) if m.group(2) else year
                d = dt.date(parsed_year, month_num, int(m.group(1)))
                if not m.group(2) and d < today:
                    d = dt.date(year + 1, month_num, int(m.group(1)))
                print(f"📅 Extracted departure date: {d.isoformat()}")
                return d.isoformat()
            except ValueError:
                pass

    print("📅 No departure date found in message — no change")
    return None


_SUMMARY_TRIGGER = 10
_MESSAGES_TO_COMPRESS = 8


async def _maybe_summarise_history(history: list) -> list:
    """
    Compresses the oldest _MESSAGES_TO_COMPRESS messages into a single summary
    once conversation history exceeds _SUMMARY_TRIGGER entries.
    Keeps recent messages intact; silently skips on LLM failure.
    Async — does not block the WebSocket event loop.
    """
    if len(history) < _SUMMARY_TRIGGER:
        return history

    to_compress = history[:_MESSAGES_TO_COMPRESS]
    to_keep = history[_MESSAGES_TO_COMPRESS:]

    transcript = "\n".join(
        f"{str(m.get('role', 'unknown')).upper()}: {str(m.get('content', ''))[:300]}"
        for m in to_compress
        if isinstance(m, dict)
    )

    prompt = f"""Summarise this travel assistant conversation into 3–5 concise bullet points.
Focus on: destination city, budget, trip length, user preferences, confirmed bookings or plans.
This summary replaces the original messages to save context — be specific and compact.

Conversation:
{transcript}

Summary (bullet points):"""

    try:
        summary_text = str((await _get_llm().ainvoke(prompt)).content).strip()   # ← non-blocking
        print(f"📝 History summarised: {_MESSAGES_TO_COMPRESS} messages → 1 summary entry")
    except Exception as e:
        print(f"⚠️ Summarisation failed ({e}) — keeping original history")
        return history

    summary_entry = {
        "role": "system",
        "content": f"[Earlier conversation compressed]\n{summary_text}",
    }
    return [summary_entry] + to_keep


# ── WebSocket node event handlers ────────────────────────────────────────────
# Each handler owns exactly one node's on_chain_end logic, keeping the main
# event loop short and easy to follow.

async def _on_intent_classifier(output: dict, city: str, websocket: WebSocket) -> None:
    """Sends a progress message and switches the UI mode after intent classification."""
    intent = output.get("intent", "new_trip")
    progress_msg = (
        "✏️ Got it, modifying your plan..."
        if intent == "refine"
        else f"🔍 Searching for information about **{city}**..."
    )
    await websocket.send_json({"type": "response", "content": progress_msg})
    await websocket.send_json({"type": "mode_update", "mode": intent, "city": city})


async def _on_researcher(output: dict, city: str, websocket: WebSocket) -> None:
    """Forwards found attractions and RAG source excerpts to the frontend."""
    rd = output.get("research_data", {})
    attractions = rd.get("attractions", [])
    attractions_str = ", ".join(attractions)
    rag_sources = rd.get("rag_sources", [])
    context_snippet = rd.get("context", "")[:150] + "..." if rd.get("context") else ""
    await websocket.send_json({
        "type": "response",
        "content": (
            f"📚 Found attractions: {attractions_str}"
            if attractions_str
            else f"📚 I couldn't find structured attraction data for {city} yet, but I checked the travel knowledge base."
        ),
        "sources": rag_sources or [f"Neo4j Graph: {city}", f"RAG: {context_snippet}"],
    })


async def _on_booking(
    output: dict, city: str, budget: float, websocket: WebSocket
) -> str:
    """
    Handles Booking node output: sends flight/hotel summary to the frontend.
    Returns a budget-banner markdown string (may be empty) for the Planner prefix.
    """
    booking_data = output.get("flights_hotels", {})
    all_flights = booking_data.get("all_flights", [])
    selected = booking_data.get("flight_info", {})
    hotel = booking_data.get("hotel_info", {})

    pending_banner = ""
    if booking_data.get("budget_exceeded"):
        cheapest = booking_data.get("cheapest_possible", 0)
        gap = booking_data.get("budget_gap", 0)
        pending_banner = (
            f"> ⚠️ **Budget Alert** — The cheapest available option "
            f"costs **{int(cheapest):,} PLN**, which is **{int(gap):,} PLN over your budget** "
            f"of {int(budget):,} PLN.\n"
            f"> The plan below uses the most affordable option found.\n\n"
        )
    elif booking_data.get("budget_tight"):
        remaining = booking_data.get("remaining_budget", 0)
        pending_banner = (
            f"> 💡 **Heads up** — After flights and hotel you have only "
            f"**{max(0, int(remaining)):,} PLN** left for food and activities.\n\n"
        )

    if "error" not in booking_data and all_flights:
        flights_list = "\n".join([
            f"  ✈️ {f['airline']} — {f['price']} {f.get('currency', 'PLN')}"
            for f in all_flights
        ])
        await websocket.send_json({
            "type": "response",
            "content": (
                f"**Available flights WAW → {city}:**\n{flights_list}\n\n"
                f"✅ Selected: **{selected.get('airline')}** for **{_format_flight_price_label(selected)}**\n"
                f"🏨 Hotel: **{hotel.get('name')}** for **{hotel.get('price')} PLN/night**"
            ),
        })
        await websocket.send_json({
            "type": "state_update",
            "state": {
                "flights": [
                    {"airline": f["airline"], "price": f["price"], "price_pln": f.get("price_pln"), "currency": f.get("currency", "PLN"), "booking_url": f.get("booking_url", "")}
                    for f in all_flights
                ],
                "selected_hotel": hotel,
                "budget": budget,
                "destination": city,
            },
        })
    return pending_banner


async def _on_graph_query(output: dict, session: dict, websocket: WebSocket) -> None:
    """Sends the graph query answer as a complete response (no streaming to avoid Cypher leaking)."""
    _sync_session_from_output(session, output)
    text = output.get("final_plan", "")
    sources = output.get("research_data", {}).get("rag_sources", []) or ["Neo4j Graph"]
    await websocket.send_json({"type": "response", "content": text, "sources": sources})


async def _on_streaming_node_end(
    output: dict, session: dict, stream_bubble_open: bool, websocket: WebSocket
) -> None:
    """
    Finalizes a streaming node:
    - If the bubble is open (tokens were streamed) → sends stream_end.
    - Otherwise → sends a plain response (no-LLM fallback path, e.g. GraphQuery error).
    """
    _sync_session_from_output(session, output)
    final_text = output.get("final_plan", "")
    rag_sources = output.get("research_data", {}).get("rag_sources", [])
    default_sources = ["Llama 3.2 + Neo4j + RAG"]

    if stream_bubble_open:
        await websocket.send_json({"type": "stream_end", "sources": rag_sources or default_sources})
    else:
        await websocket.send_json({
            "type": "response",
            "content": final_text,
            "sources": rag_sources or default_sources,
        })


async def _on_weather(
    output: dict, city: str, session: dict, websocket: WebSocket
) -> None:
    """Sends the weather forecast state update, then the formatted forecast message."""
    weather = output.get("weather_data", {})
    if weather and weather.get("forecast"):
        await websocket.send_json({
            "type": "state_update",
            "state": {"weather_forecast": weather["forecast"][:5], "destination": city},
        })
    _sync_session_from_output(session, output)
    await websocket.send_json({
        "type": "response",
        "content": output.get("final_plan", ""),
        "sources": output.get("research_data", {}).get("rag_sources", []) or ["OpenWeatherMap"],
    })


async def _on_flight_search(
    output: dict, city: str, budget: float, session: dict, websocket: WebSocket
) -> None:
    """Sends flight list state update and the final message for FlightSearch node."""
    fh = output.get("flights_hotels", {})
    flights_data = fh.get("flights_data", [])
    if flights_data:
        await websocket.send_json({
            "type": "state_update",
            "state": {
                "flights_list": [
                    {
                        "airline": f["airline"],
                        "price": f["price"],
                        "departure": f.get("departure", ""),
                        "arrival": f.get("arrival", ""),
                        "duration": f.get("duration", ""),
                        "source": f.get("source", ""),
                        "booking_url": f.get("booking_url", ""),
                    }
                    for f in flights_data[:5]
                ],
                "budget": budget,
                "destination": city,
            },
        })
    _sync_session_from_output(session, output)
    await websocket.send_json({"type": "response", "content": output.get("final_plan", ""), "sources": []})


async def _on_hotel_search(
    output: dict, city: str, budget: float, session: dict, websocket: WebSocket
) -> None:
    """Sends hotel list state update and the final message for HotelSearch node."""
    fh = output.get("flights_hotels", {})
    hotels_data = fh.get("hotels_data", [])
    if hotels_data:
        await websocket.send_json({
            "type": "state_update",
            "state": {"hotels_list": hotels_data[:5], "budget": budget, "destination": city},
        })
    _sync_session_from_output(session, output)
    await websocket.send_json({"type": "response", "content": output.get("final_plan", ""), "sources": []})


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ WebSocket connected")

    session: dict[str, Any] = {**_DEFAULT_SESSION, "conversation_history": []}

    try:
        while True:
            data_text = await websocket.receive_text()

            try:
                request_data = json.loads(data_text)
            except json.JSONDecodeError as je:
                print(f"⚠️ Received invalid JSON: {je}")
                await websocket.send_json({"type": "response", "content": "⚠️ Invalid request format — please send a JSON message."})
                continue

            if request_data.get("type") == "reset":
                session = {**_DEFAULT_SESSION, "conversation_history": []}
                print("🔄 Session reset")
                await websocket.send_json({
                    "type": "session_reset",
                    "content": "Session has been reset. You can start a new conversation!"
                })
                continue

            user_msg = str(request_data.get("message") or request_data.get("content") or "")
            if not user_msg.strip():
                await websocket.send_json({
                    "type": "response",
                    "content": "⚠️ Please send a non-empty travel message.",
                })
                continue
            user_msg_lower = user_msg.lower()
            print(f"📨 Received message: {user_msg}")

            session["conversation_history"].append({"role": "user", "content": user_msg})
            #GUARDRAIL
            if not await is_input_safe(user_msg):
                await websocket.send_json({
                    "type": "response", 
                    "content": "⚠️ **Security Alert**: Your message was flagged as unsafe. Please rephrase your travel request."
                })
                # Remove the unsafe message from history so it doesn't pollute the context
                session["conversation_history"].pop()
                continue

            new_city = await extract_city(user_msg_lower)           # ← async
            new_budget = extract_budget(user_msg_lower)
            new_duration = extract_duration(user_msg_lower)
            new_date = extract_date(user_msg)

            if new_city is not None:
                session["city"] = new_city
            if new_budget is not None:
                session["budget"] = new_budget
            if new_duration is not None:
                session["duration"] = new_duration
            if new_date is not None:
                session["departure_date"] = new_date

            city = session["city"]
            budget = session["budget"]
            duration = session["duration"]
            departure_date = session["departure_date"]

            print(f"🏙️ City: {city}, Budget: {budget}, Days: {duration}, Date: {departure_date or 'not set'}")
            print(f"📜 History: {len(session['conversation_history'])} messages, Plan: {'YES' if session['current_plan'] else 'NONE'}")

            initial_state = {
                "messages": [],
                "city": city,
                "budget": budget,
                "duration": duration,
                "departure_date": departure_date,
                "user_message": user_msg,
                "conversation_history": session["conversation_history"],
                "current_plan": session["current_plan"],
                "intent": "",
                "research_data": {},
                "flights_hotels": {},
                "weather_data": {},
                "final_plan": "",
            }

            await websocket.send_json({
                "type": "state_update",
                "state": {
                    "destination": city,
                    "budget": f"{budget} PLN",
                    "duration": duration,
                    "departure_date": departure_date or None,
                }
            })

            print("🚀 Starting orchestration...")

            _pending_banner = ""    # budget banner shown before Planner starts streaming
            _had_stream_tokens = False  # True once first LLM token arrives for current node
            _stream_bubble_open = False  # True after stream_start has been sent
            _handled_chain_end_nodes: set[str] = set()  # guard against duplicated LangGraph chain-end events

            async for event in app_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event", "")
                node = event.get("metadata", {}).get("langgraph_node", "")

                if not node or node not in _KNOWN_NODES:
                    continue

                # ── Token streaming (any node in _STREAMING_NODES) ─────────────
                if kind == "on_chat_model_stream" and node in _STREAMING_NODES:
                    chunk = event["data"].get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        if not _stream_bubble_open:
                            # ── LAZY stream_start: open the bubble only on the FIRST token.
                            # Avoids an empty blinking cursor while Neo4j / Cypher / Chroma
                            # pre-processing runs (can take 10-30 s on slow hardware).
                            # Also avoids duplicate bubbles if on_chain_start fires multiple
                            # times for the same node (LangGraph internal chain nesting).
                            _stream_bubble_open = True
                            _had_stream_tokens = True
                            prefix = _pending_banner if node == "Planner" else ""
                            _pending_banner = ""
                            print(f"  🌊 [{node}] first token — opening stream bubble")
                            await websocket.send_json({
                                "type": "stream_start",
                                "node": node,
                                "prefix": prefix,
                            })
                        await websocket.send_json({
                            "type": "stream_chunk",
                            "content": chunk.content,
                        })
                    continue

                # ── Node start for streaming nodes — reset flags only ──────────
                if kind == "on_chain_start" and node in _STREAMING_NODES:
                    # Don't open the bubble here; wait for the first token above.
                    # Reset per-node flags so multiple streaming nodes in a single
                    # request don't bleed state into each other.
                    _had_stream_tokens = False
                    _stream_bubble_open = False
                    continue

                # ── Only process node completions from here ────────────────────
                if kind != "on_chain_end":
                    continue

                if node in _handled_chain_end_nodes:
                    print(f"  ↩️ Skipping duplicate on_chain_end for [{node}]")
                    continue

                output = event.get("data", {}).get("output", {})
                if not isinstance(output, dict):
                    continue

                _handled_chain_end_nodes.add(node)

                print(f"  📊 Node: [{node}]")

                if node == "IntentClassifier":
                    await _on_intent_classifier(output, city, websocket)

                elif node == "Researcher":
                    await _on_researcher(output, city, websocket)

                elif node == "GraphQuery":
                    await _on_graph_query(output, session, websocket)

                elif node == "Booking":
                    _pending_banner = await _on_booking(output, city, budget, websocket)

                elif node in _STREAMING_NODES:
                    await _on_streaming_node_end(output, session, _stream_bubble_open, websocket)

                elif node == "Weather":
                    await _on_weather(output, city, session, websocket)

                elif node == "FlightSearch":
                    await _on_flight_search(output, city, budget, session, websocket)

                elif node == "HotelSearch":
                    await _on_hotel_search(output, city, budget, session, websocket)

            print("✅ Orchestration complete")
            session["conversation_history"] = await _maybe_summarise_history(  # ← async
                session["conversation_history"]
            )

    except WebSocketDisconnect:
        print("❌ Client disconnected.")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "response", "content": f"❌ Backend error: {str(e)}"})
        except Exception:
            pass

if __name__ == "__main__":
    print("🚀 Starting FastAPI server on port 8000...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)

