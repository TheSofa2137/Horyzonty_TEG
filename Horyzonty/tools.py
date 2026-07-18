import sys

# ── Windows compatibility ─────────────────────────────────────────────────────
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
tools.py — I/O helpers for Neo4j, Duffel, OpenWeatherMap and on-demand graph enrichment.

Public API used by orchestrator.py:
    city_exists_in_graph, city_has_neighbourhoods, enrich_city_in_graph,
    search_flights, search_hotels, get_weather
"""

import json
import os
import random
import requests as http_requests
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, cast, TypedDict
from collections import Counter
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_ollama import ChatOllama

load_dotenv()

def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def _get_driver_instance():
    return GraphDatabase.driver(
        _require_env("NEO4J_URI"),
        auth=(_require_env("NEO4J_USER"), _require_env("NEO4J_PW")),
    )


def _build_chat_model(**kwargs: Any):
    return ChatOllama(**cast(Any, kwargs))


@lru_cache(maxsize=1)
def _get_llm_instance():
    return _build_chat_model(model="llama3.2:3b")


class _LazyNeo4jDriver:
    def session(self, *args: Any, **kwargs: Any):
        return _get_driver_instance().session(*args, **kwargs)

    def close(self) -> None:
        _get_driver_instance().close()


class _LazyChatModel:
    def __getattr__(self, name: str) -> Any:
        return getattr(_get_llm_instance(), name)


driver = _LazyNeo4jDriver()
llm = _LazyChatModel()

_FX_RATES_TO_PLN: dict[str, float] = {
    "PLN": 1.0,
    "EUR": 4.35,
    "USD": 4.0,
    "GBP": 5.1,
}


def price_to_pln(amount: float | int, currency: str | None) -> float:
    """Converts a known currency amount to PLN using conservative static rates."""
    code = (currency or "PLN").upper().strip()
    rate = _FX_RATES_TO_PLN.get(code, 1.0)
    return round(float(amount) * rate, 2)


class _DailyWeatherBucket(TypedDict):
    temps: list[float]
    descriptions: list[str]
    rain_probs: list[float]


def city_exists_in_graph(city: str) -> bool:
    """Checks whether the city already exists in the Neo4j graph."""
    with driver.session() as session:
        result = session.run(
            "MATCH (c:City {name: $city}) RETURN count(c) as count",
            city=city
        )
        record = result.single()
        return bool(record and record["count"] > 0)


def city_has_neighbourhoods(city: str) -> bool:
    """Checks whether the city already has neighbourhoods in the graph."""
    with driver.session() as session:
        result = session.run(
            "MATCH (nb:Neighbourhood)-[:PART_OF]->(c:City {name: $city}) RETURN count(nb) as count",
            city=city
        )
        record = result.single()
        return bool(record and record["count"] > 0)


def _generate_city_data_via_llm(city: str) -> dict:
    """
    Asks the LLM to produce structured travel data for *city*.
    Raises an exception (caught by the caller) when the response is not valid JSON.
    """
    prompt = f"""Generate complete travel data for the CITY: {city}

⚠️ IMPORTANT DISAMBIGUATION:
- "{city}" refers to the CITY named {city} (a standalone travel destination with its own airport/transport hub)
- Do NOT confuse it with any district or neighbourhood of another city
- For example: "Praga" = Prague (capital of Czech Republic), NOT Praga district of Warsaw
- Generate data appropriate for a CITY-LEVEL travel destination

Return ONLY a valid JSON object (no markdown) in this EXACT format:
{{
  "neighbourhoods": [
    {{"name": "Old Town", "description": "Historic center with main attractions", "near_to": ["City Center"]}},
    {{"name": "City Center", "description": "Modern shopping and business area", "near_to": ["Old Town"]}}
  ],
  "attractions": [
    {{"name": "Main Cathedral", "category": "church", "free": true, "cost": 0,
      "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
      "neighbourhood": "Old Town", "description": "Historic cathedral from 12th century"}},
    {{"name": "City Museum", "category": "museum", "free": false, "cost": 12,
      "open_days": ["Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
      "neighbourhood": "Old Town", "description": "Main city museum with history exhibits"}}
  ],
  "hotels": [
    {{"name": "Hotel Name", "price": 200}},
    {{"name": "Budget Inn", "price": 120}}
  ],
  "flights": [
    {{"airline": "LOT Polish Airlines", "price": 450}},
    {{"airline": "Ryanair", "price": 280}}
  ]
}}

Rules for {city}:
- Include 3-5 REAL neighbourhoods of the CITY {city} (use actual district names of THIS city)
- Include 8-12 REAL attractions that are located IN THE CITY {city}
- category must be ONE of: gallery, museum, monument, church, park, viewpoint, landmark, attraction
- open_days: array of day names in English (Monday, Tuesday, etc.)
- near_to: list of neighbouring district names from the same list
- free: boolean (true if free entry)
- cost: integer in PLN (0 if free)
- neighbourhood: must match one of the neighbourhood names above
- Include 2-3 hotels (prices 100-500 PLN/night)
- Include 2-3 flights from Warsaw (prices 200-900 PLN)
- Return ONLY the JSON, no explanation"""

    response = llm.invoke(prompt)
    raw = response.content.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(raw)


def _fallback_city_data(city: str) -> dict:
    """Returns minimal placeholder data used when LLM generation fails."""
    rng = random.Random(city.casefold())
    return {
        "neighbourhoods": [
            {"name": f"{city} Old Town", "description": "Historic city centre", "near_to": [f"{city} Center"]},
            {"name": f"{city} Center",   "description": "Modern city centre",   "near_to": [f"{city} Old Town"]},
        ],
        "attractions": [
            {"name": f"{city} Cathedral",     "category": "church",   "free": True,  "cost": 0,
             "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
             "neighbourhood": f"{city} Old Town", "description": "Main cathedral"},
            {"name": f"{city} Main Museum",   "category": "museum",   "free": False, "cost": 12,
             "open_days": ["Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
             "neighbourhood": f"{city} Old Town", "description": "City history museum"},
            {"name": f"{city} Central Park",  "category": "park",     "free": True,  "cost": 0,
             "open_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
             "neighbourhood": f"{city} Center", "description": "Main city park"},
            {"name": f"{city} Art Gallery",   "category": "gallery",  "free": True,  "cost": 0,
             "open_days": ["Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
             "neighbourhood": f"{city} Center", "description": "Contemporary art gallery"},
            {"name": f"{city} Historic Castle","category": "monument","free": False, "cost": 10,
             "open_days": ["Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
             "neighbourhood": f"{city} Old Town", "description": "Historic castle"},
        ],
        "hotels": [
            {"name": f"Hotel {city} Center", "price": rng.randint(150, 250)},
            {"name": f"{city} Budget Inn",   "price": rng.randint(80, 150)},
        ],
        "flights": [
            {"airline": "LOT Polish Airlines", "price": rng.randint(300, 600)},
            {"airline": "Ryanair",             "price": rng.randint(150, 400)},
        ],
    }


def _persist_city_to_graph(city: str, data: dict) -> tuple[int, int]:
    """
    Writes all city data (neighbourhoods, attractions, hotels, flights) to Neo4j.
    Returns (neighbourhood_count, attraction_count).
    """
    seed_date = (date.today() + timedelta(days=30)).isoformat()

    with driver.session() as session:
        session.run("MERGE (c:City {name: $city})", city=city)

        for nb in data.get("neighbourhoods", []):
            session.run("""
                MATCH (c:City {name: $city})
                MERGE (nb:Neighbourhood {name: $name, city: $city})
                SET nb.description = $description
                MERGE (nb)-[:PART_OF]->(c)
            """, city=city, name=nb["name"], description=nb.get("description", ""))

        for nb in data.get("neighbourhoods", []):
            for near in nb.get("near_to", []):
                session.run("""
                    MATCH (a:Neighbourhood {name: $a, city: $city}), (b:Neighbourhood {name: $b, city: $city})
                    MERGE (a)-[:NEAR_TO]->(b)
                    MERGE (b)-[:NEAR_TO]->(a)
                """, city=city, a=nb["name"], b=near)

        for attr in data.get("attractions", []):
            nb_name = attr.get("neighbourhood", "")
            session.run("""
                MATCH (c:City {name: $city})
                MERGE (a:Attraction {name: $name, city: $city})
                SET a.category    = $category,
                    a.free        = $free,
                    a.cost        = $cost,
                    a.open_days   = $open_days,
                    a.description = $description
                MERGE (a)-[:LOCATED_IN]->(c)
            """, city=city, name=attr["name"], category=attr.get("category", "attraction"),
                       free=bool(attr.get("free", False)), cost=int(attr.get("cost", 0)),
                       open_days=attr.get("open_days", []), description=attr.get("description", ""))
            if nb_name:
                session.run("""
                    MATCH (a:Attraction {name: $name, city: $city})
                    MATCH (nb:Neighbourhood {name: $nb, city: $city})
                    MERGE (a)-[:LOCATED_IN]->(nb)
                """, city=city, name=attr["name"], nb=nb_name)

        for hotel in data.get("hotels", []):
            session.run("""
                MATCH (c:City {name: $city})
                MERGE (h:Hotel {name: $name, city: $city})
                SET h.price = $price
                MERGE (h)-[:LOCATED_IN]->(c)
            """, city=city, name=hotel["name"], price=float(hotel.get("price", 200)))

        for flight in data.get("flights", []):
            session.run("""
                MATCH (c:City {name: $city})
                MERGE (f:Flight {origin: 'WAW', airline: $airline, date: $date, destination_city: $city})
                SET f.price = $price
                MERGE (f)-[:FLIES_TO]->(c)
            """, city=city, airline=flight["airline"], date=seed_date, price=float(flight.get("price", 400)))

    return len(data.get("neighbourhoods", [])), len(data.get("attractions", []))


def enrich_city_in_graph(city: str) -> dict:
    """
    Populates Neo4j with LLM-generated travel data for an unknown city.
    Falls back to minimal placeholder data when the LLM response cannot be parsed.
    """
    print(f"🌍 [Graph Enrichment] Generating data for '{city}'...")
    try:
        data = _generate_city_data_via_llm(city)
        print(f"  ✅ LLM generated: {len(data.get('neighbourhoods', []))} neighbourhoods, "
              f"{len(data.get('attractions', []))} attractions")
    except Exception as e:
        print(f"  ⚠️ LLM parse error ({e}). Using fallback data.")
        data = _fallback_city_data(city)

    nb_count, attr_count = _persist_city_to_graph(city, data)
    print(f"  🗄️ Saved to Neo4j: {nb_count} neighbourhoods, {attr_count} attractions, hotels, flights")
    return data


CITY_TO_IATA: dict[str, str] = {
    "Lisbon": "LIS", "Porto": "OPO", "Barcelona": "BCN",
    "Prague": "PRG", "Vienna": "VIE", "Rome": "FCO",
    "Milan": "MXP", "Florence": "FLR", "Paris": "CDG",
    "Amsterdam": "AMS", "Krakow": "KRK", "Warsaw": "WAW",
    "London": "LHR", "Madrid": "MAD", "Athens": "ATH",
    "Istanbul": "IST", "Budapest": "BUD", "Berlin": "BER",
    "Munich": "MUC", "Edinburgh": "EDI", "Dubrovnik": "DBV",
    "Brussels": "BRU", "Copenhagen": "CPH", "Stockholm": "ARN",
    "Oslo": "OSL", "Helsinki": "HEL", "Zurich": "ZRH",
    "Geneva": "GVA", "Venice": "VCE", "Naples": "NAP",
    "Seville": "SVQ", "Valencia": "VLC", "Nice": "NCE",
    "Lyon": "LYS", "Marseille": "MRS", "Riga": "RIX",
    "Tallinn": "TLL", "Vilnius": "VNO", "Bratislava": "BTS",
    "Ljubljana": "LJU", "Zagreb": "ZAG", "Bucharest": "OTP",
    "Sofia": "SOF", "Belgrade": "BEG", "Reykjavik": "KEF",
    "Dubai": "DXB", "Cairo": "CAI",
    "Tokyo": "NRT", "Bangkok": "BKK", "Singapore": "SIN",
    "New York": "JFK", "Miami": "MIA", "Los Angeles": "LAX",
}

CARRIER_NAMES: dict[str, str] = {
    "FR": "Ryanair", "LO": "LOT Polish Airlines", "TP": "TAP Portugal",
    "VY": "Vueling", "W6": "Wizz Air", "U2": "easyJet",
    "OS": "Austrian Airlines", "LH": "Lufthansa", "AF": "Air France",
    "KL": "KLM", "BA": "British Airways", "IB": "Iberia",
    "AZ": "Alitalia / ITA", "SK": "SAS", "FI": "Icelandair",
    "EK": "Emirates", "QR": "Qatar Airways", "TK": "Turkish Airlines",
    "AY": "Finnair", "SN": "Brussels Airlines",
}

BOOKING_URLS: dict[str, str] = {
    "Ryanair":             "https://www.ryanair.com/gb/en/cheap-flights",
    "LOT Polish Airlines": "https://www.lot.com/pl/en",
    "TAP Portugal":        "https://www.flytap.com/en-gb",
    "TAP Air Portugal":    "https://www.flytap.com/en-gb",
    "Vueling":             "https://www.vueling.com/en",
    "Wizz Air":            "https://wizzair.com",
    "easyJet":             "https://www.easyjet.com/en",
    "EasyJet":             "https://www.easyjet.com/en",
    "Austrian Airlines":   "https://www.austrian.com/global/en",
    "Austrian":            "https://www.austrian.com/global/en",
    "Lufthansa":           "https://www.lufthansa.com/gb/en",
    "Air France":          "https://www.airfrance.com",
    "KLM":                 "https://www.klm.com/en",
    "British Airways":     "https://www.britishairways.com/en-gb",
    "Iberia":              "https://www.iberia.com/web/portal",
    "Alitalia / ITA":      "https://www.ita-airways.com/en_gb",
    "ITA Airways":         "https://www.ita-airways.com/en_gb",
    "SAS":                 "https://www.flysas.com/en",
    "Icelandair":          "https://www.icelandair.com",
    "Emirates":            "https://www.emirates.com/english",
    "Qatar Airways":       "https://www.qatarairways.com/en",
    "Turkish Airlines":    "https://www.turkishairlines.com",
    "Finnair":             "https://www.finnair.com/en",
    "Brussels Airlines":   "https://www.brusselsairlines.com/en",
    "Swiss":               "https://www.swiss.com/gb/en",
    "SWISS":               "https://www.swiss.com/gb/en",
    "Eurowings":           "https://www.eurowings.com/en",
    "Transavia":           "https://www.transavia.com/en-EU",
    "Volotea":             "https://www.volotea.com/en",
    "Norwegian":           "https://www.norwegian.com/en",
    "Corendon Airlines":   "https://www.corendon.com",
    "Aegean Airlines":     "https://en.aegeanair.com",
    "Olympic Air":         "https://www.olympicair.com/en",
    "Croatia Airlines":    "https://www.croatiaairlines.com/en",
    "Duffel Airways":      "https://duffel.com",   # linia testowa Duffel
}


def _booking_url_for(airline: str) -> str:
    """Returns a direct booking URL for the given airline.
    Tries exact match first, then case-insensitive partial match, then Google Flights fallback.
    """
    # Exact match
    if airline in BOOKING_URLS:
        return BOOKING_URLS[airline]
    # Case-insensitive partial match (e.g. "Austrian" matches "Austrian Airlines")
    airline_lower = airline.lower()
    for key, url in BOOKING_URLS.items():
        if airline_lower in key.lower() or key.lower() in airline_lower:
            return url
    # Fallback: Google Flights search
    return f"https://www.google.com/flights#search;q={airline.replace(' ', '+')}"


DUFFEL_BASE = "https://api.duffel.com"


def _duffel_headers() -> dict:
    """Returns Duffel API request headers using the key from env."""
    api_key = os.environ.get("DUFFEL_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Duffel-Version": "v2",
    }


def _parse_iso_duration(iso: str) -> str:
    """Converts ISO 8601 duration (PT4H14M) to human-readable string (4h 14m)."""
    if not iso:
        return ""
    iso = iso.replace("PT", "")
    result = ""
    if "H" in iso:
        parts = iso.split("H")
        result += parts[0] + "h "
        iso = parts[1]
    if "M" in iso:
        result += iso.replace("M", "") + "m"
    return result.strip()


def search_flights_duffel(city: str, origin: str = "WAW",
                          departure_date: str | None = None) -> list:
    """
    Searches live flight offers via Duffel Flights API (offer_requests endpoint).
    Returns [] when Duffel is unavailable or the city has no IATA mapping.
    """
    dest_iata = CITY_TO_IATA.get(city)
    if not dest_iata:
        print(f"  ⚠️ No IATA code for '{city}' — skipping Duffel flights")
        return []

    api_key = os.environ.get("DUFFEL_API_KEY", "")
    if not api_key:
        print("  ⚠️ DUFFEL_API_KEY not set — skipping live flight search")
        return []

    dep_date = departure_date or (date.today() + timedelta(days=30)).isoformat()

    try:
        resp = http_requests.post(
            f"{DUFFEL_BASE}/air/offer_requests",
            headers=_duffel_headers(),
            json={
                "data": {
                    "slices": [
                        {
                            "origin": origin,
                            "destination": dest_iata,
                            "departure_date": dep_date,
                        }
                    ],
                    "passengers": [{"type": "adult"}],
                    "cabin_class": "economy",
                }
            },
            timeout=20,
        )

        if resp.status_code not in (200, 201):
            print(f"  ⚠️ Duffel offer_requests {resp.status_code}: {resp.text[:200]}")
            return []

        body = resp.json()
        offers = body.get("data", {}).get("offers", [])

        if not offers:
            print(f"  ⚠️ Duffel returned no offers for {origin}→{dest_iata}")
            return []

        # Sort by price, keep cheapest 6
        offers.sort(key=lambda o: float(o.get("total_amount", 9999)))
        flights = []

        for offer in offers[:6]:
            try:
                price_raw = float(offer["total_amount"])
                currency = offer.get("total_currency", "EUR")
                offer_id = offer.get("id", "")

                slice0 = offer["slices"][0]
                segments = slice0.get("segments", [])
                if not segments:
                    continue
                first_seg = segments[0]
                last_seg = segments[-1]

                airline = first_seg["marketing_carrier"]["name"]
                iata_code = first_seg["marketing_carrier"]["iata_code"]
                dep_time = first_seg["departing_at"][11:16]
                arr_time = last_seg["arriving_at"][11:16]
                duration = _parse_iso_duration(slice0.get("duration", ""))
                stops = max(0, len(segments) - 1)
                fare_brand = slice0.get("fare_brand_name") or "Economy"

                # Build Duffel booking link (deep-link via offer id when available)
                booking_url = _booking_url_for(airline)
                price_pln = price_to_pln(price_raw, currency)

                flights.append({
                    "airline": airline,
                    "iata_code": iata_code,
                    "price": round(price_raw, 2),
                    "currency": currency,
                    "price_pln": price_pln,
                    "departure": dep_time,
                    "arrival": arr_time,
                    "duration": duration,
                    "stops": stops,
                    "fare_class": fare_brand,
                    "date": dep_date,
                    "offer_id": offer_id,
                    "source": "Duffel",
                    "booking_url": booking_url,
                })
            except (KeyError, IndexError, ValueError, TypeError):
                continue

        print(f"  ✈️ Duffel: {len(flights)} flights {origin}→{dest_iata} on {dep_date}")
        return flights

    except Exception as e:
        print(f"  ⚠️ Duffel flight search exception: {e}")
        return []


def search_flights(city: str, departure_date: str | None = None, budget: float | None = None):
    """Tries Duffel live data first, falls back to Neo4j seed data, with optional budget filtering."""
    print(f"🛠️ Tool 'search_flights' called for city: {city}, date: {departure_date}")

    live_enabled_raw = os.getenv("ENABLE_LIVE_FLIGHTS", "1").strip().lower()
    live_enabled = live_enabled_raw not in {"0", "false", "no"}
    # Keep test runs deterministic and offline unless explicitly enabled.
    if "PYTEST_CURRENT_TEST" in os.environ and "ENABLE_LIVE_FLIGHTS" not in os.environ:
        live_enabled = False

    if live_enabled:
        duffel_flights = search_flights_duffel(city, departure_date=departure_date)
        if duffel_flights:
            if budget is not None:
                return [f for f in duffel_flights if float(f.get("price_pln", f.get("price", 0))) <= float(budget)]
            return duffel_flights

    print(f"  📋 Duffel returned no data — falling back to Neo4j for {city}")
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Flight)-[:FLIES_TO]->(c:City {name: $city})
            WHERE f.price IS NOT NULL
            RETURN f.airline as airline, f.price as price
            ORDER BY f.price ASC
        """, city=city)
        flights = [
            {
                "airline": record["airline"],
                "price": record["price"],
                "currency": "PLN",
                "price_pln": float(record["price"]),
                "source": "Neo4j",
                "booking_url": _booking_url_for(record["airline"]),
            }
            for record in result
        ]
        if budget is not None:
            flights = [f for f in flights if float(f.get("price_pln", f.get("price", 0))) <= float(budget)]
        print(f"  ✈️ Neo4j flights found: {len(flights)}")
        return flights


def search_hotels(city: str, budget: float | None = None):
    """Returns hotels in the given city from Neo4j, ordered by price, with optional budget filtering."""
    print(f"🛠️ Tool 'search_hotels' called for city: {city}")
    with driver.session() as session:
        result = session.run("""
            MATCH (h:Hotel)-[:LOCATED_IN]->(c:City {name: $city})
            WHERE h.price IS NOT NULL
            RETURN h.name as name, h.price as price
            ORDER BY h.price ASC
        """, city=city)
        hotels = [{"name": record["name"], "price": record["price"]} for record in result]
        if budget is not None:
            hotels = [h for h in hotels if float(h.get("price", 0)) <= float(budget)]
        print(f"  🏨 Hotels found: {len(hotels)}")
        return hotels


def _rain_level(rain_probability: float) -> str:
    """Maps rain probability (0–100) to outdoor suitability level."""
    if rain_probability < 20:
        return "perfect"
    elif rain_probability < 40:
        return "good"
    elif rain_probability < 70:
        return "mixed"
    else:
        return "rainy"


def _mock_weather(city: str, days: int, reason: str = "no API key") -> dict:
    """Returns a plausible simulated forecast when the API key is absent."""
    rng = random.Random(f"{city.casefold()}|{days}|{reason}")
    conditions = [
        ("sunny",          10),
        ("partly cloudy",  30),
        ("cloudy",         55),
        ("light rain",     65),
        ("heavy rain",     85),
    ]
    today = date.today()
    forecast = []
    for i in range(days):
        desc, rain = rng.choice(conditions)
        forecast.append({
            "date": (today + timedelta(days=i)).isoformat(),
            "temp_avg": rng.randint(14, 26),
            "description": desc,
            "rain_probability": rain,
            "outdoor_level": _rain_level(rain),
            "outdoor_friendly": rain < 70,
        })
    return {"city": city, "forecast": forecast, "source": f"Demo forecast ({reason})"}


def get_weather(city: str, days: int = 5) -> dict:
    """
    Fetches 5-day forecast from OpenWeatherMap (3h slots aggregated to daily).
    Falls back to mock data when OPENWEATHERMAP_API_KEY is not set.
    """
    days_count = int(days)
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        print(f"  ⚠️ OPENWEATHERMAP_API_KEY not set — using demo forecast for '{city}'")
        return _mock_weather(city, days_count, reason="set OPENWEATHERMAP_API_KEY in .env")

    try:
        cnt = min(days_count, 5) * 8  # free tier: 5 days × 8 three-hour slots
        params = {"q": city, "appid": api_key, "units": "metric", "cnt": cnt}
        resp = http_requests.get("https://api.openweathermap.org/data/2.5/forecast",
                                 params=params, timeout=10)
        data = resp.json()

        if str(data.get("cod")) != "200":
            msg = data.get("message", "unknown error")
            print(f"  ⚠️ OpenWeatherMap API error: {msg} — using demo forecast")
            reason = ("key not yet activated — new keys take up to 2h"
                      if "Invalid API key" in msg else f"API error: {msg}")
            return _mock_weather(city, days_count, reason=reason)

        # Aggregate 3-h slots → daily buckets
        daily: dict[str, _DailyWeatherBucket] = {}
        for slot in data["list"]:
            d = slot["dt_txt"][:10]
            if d not in daily:
                daily[d] = {"temps": [], "descriptions": [], "rain_probs": []}
            daily[d]["temps"].append(float(slot["main"]["temp"]))
            daily[d]["descriptions"].append(str(slot["weather"][0]["description"]))
            daily[d]["rain_probs"].append(float(slot.get("pop", 0.0)))

        forecast = []
        for idx, (day_date, info) in enumerate(daily.items()):
            if idx >= days_count:
                break
            temps = info["temps"]
            rain_probs = info["rain_probs"]
            descriptions = info["descriptions"]
            avg_temp = round(sum(temps) / len(temps), 1) if temps else 0.0
            max_rain = 0.0
            for value in rain_probs:
                if value > max_rain:
                    max_rain = value
            main_desc = Counter(descriptions).most_common(1)[0][0] if descriptions else "unknown"
            rain_pct = max_rain * 100.0
            forecast.append({
                "date": day_date,
                "temp_avg": avg_temp,
                "description": main_desc,
                "rain_probability": int(rain_pct),
                "outdoor_level": _rain_level(rain_pct),
                "outdoor_friendly": max_rain < 0.7,
            })

        print(f"  ✅ Weather fetched for '{city}': {len(forecast)} days")
        return {"city": city, "forecast": forecast, "source": "OpenWeatherMap"}

    except Exception as e:
        print(f"  ⚠️ Weather fetch error: {e} — using demo forecast")
        return _mock_weather(city, days_count, reason=str(e))

def save_chat_message(user_id: str, session_id: str, role: str, content: str):
    """Saves a single message to the Neo4j graph linked to a user and session."""
    with driver.session() as session:
        session.run("""
            MERGE (u:User {id: $user_id})
            MERGE (s:Session {id: $session_id})
            MERGE (u)-[:STARTED]->(s)
            CREATE (m:Message {role: $role, content: $content, timestamp: datetime()})
            CREATE (s)-[:HAS_MESSAGE]->(m)
        """, user_id=user_id, session_id=session_id, role=role, content=content)

def load_chat_history(user_id: str, session_id: str, limit: int = 10):
    """Retrieves the last N messages for a specific user and session."""
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {id: $user_id})-[:STARTED]->(s:Session {id: $session_id})-[:HAS_MESSAGE]->(m:Message)
            RETURN m.role as role, m.content as content
            ORDER BY m.timestamp ASC
            LIMIT $limit
        """, user_id=user_id, session_id=session_id, limit=limit)
        return [{"role": record["role"], "content": record["content"]} for record in result]