"""
Generate a natural travel recommendation using Gemini based on retrieved places.
Reads the Gemini API key from the GEMINI_API_KEY variable in a .env file or environment.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

from google import genai
from dotenv import load_dotenv

# Load .env from project root (directory containing this file)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key or not _api_key.strip():
    raise ValueError(
        "GEMINI_API_KEY is not set. Add it to your .env file or set the environment variable."
    )

client = genai.Client(api_key=_api_key.strip())


def generate_travel_response(query: str, retrieved_places: List[Dict[str, Any]]) -> str:
    """
    Build a prompt from the query and retrieved places, then return the model's
    short travel recommendation. Each place dict should contain at least:
    name, district, category, best_time, visit_duration, budget_level
    (best_season / recommended_duration used as fallbacks if present).
    """
    lines = []
    for p in retrieved_places:
        name = p.get("name", "")
        district = p.get("district", "")
        category = p.get("category", "")
        best_time = p.get("best_time") or p.get("best_season", "")
        visit_duration = p.get("visit_duration") or p.get("recommended_duration", "")
        budget_level = p.get("budget_level", "")
        lines.append(
            f"{name} in {district} - category {category}, best time {best_time}, "
            f"visit duration {visit_duration}, budget {budget_level}"
        )
    relevant_block = "\n".join(lines) if lines else "(No places provided.)"

    prompt = f"""You are a travel assistant. Answer using ONLY the information in the retrieved places below.

RULES (strict):
- Use ONLY the information provided in the retrieved places context.
- Do NOT invent additional facts.
- Do NOT add travel times, ticket prices, train schedules, hotel suggestions, food suggestions, or historical details unless they are explicitly present in the retrieved context.
- If some detail is missing, say: "This information is not available in the current knowledge base."
- For itinerary-style queries, you may reorganize the retrieved places into a natural explanation, but do NOT introduce new attractions or unsupported travel advice.
- Keep your answer concise and practical.

User query: {query}

Retrieved places (your only source of facts):
{relevant_block}

Write a short, helpful travel recommendation that follows the rules above."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception:
        raise


if __name__ == "__main__":
    query = "cheap waterfall near Ella"
    retrieved_places = [
        {
            "name": "Ravana Falls (Ravana Ella)",
            "district": "Badulla",
            "category": "waterfall",
            "best_season": "Year-round",
            "recommended_duration": "1 hour",
            "budget_level": "low",
        },
        {
            "name": "Diyaluma Falls",
            "district": "Badulla",
            "category": "waterfall",
            "best_season": "February to July",
            "recommended_duration": "half day",
            "budget_level": "low",
        },
    ]
    response = generate_travel_response(query, retrieved_places)
    print(response)
