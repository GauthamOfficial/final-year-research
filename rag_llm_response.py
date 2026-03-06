"""
Generate a natural travel recommendation using Gemini based on retrieved places.
Reads the Gemini API key from the GEMINI_API_KEY environment variable.
"""

import os
from typing import List, Dict, Any

import google.generativeai as genai

# Read API key from environment (set GEMINI_API_KEY before running)
_api_key = os.environ.get("GEMINI_API_KEY")
if _api_key:
    genai.configure(api_key=_api_key)

model = genai.GenerativeModel("gemini-1.5-flash")


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

    prompt = f"""User query: {query}

Relevant places:
{relevant_block}

Write a short helpful travel recommendation."""

    response = model.generate_content(prompt)
    return response.text.strip() if response.text else ""
