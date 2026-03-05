"""
Build a paragraph-style assistant reply from retrieved RAG results.
Uses only metadata; avoids hallucination.
"""


def format_answer(user_query: str, mode: str, filters: dict, res: dict) -> str:
    """
    Build a paragraph-style assistant reply using retrieved results.
    Uses only res["metadatas"][0] (top-k places) and the filters/mode.
    Avoid hallucination: do not add facts not present in metadata.
    """
    metadatas = res.get("metadatas", [[]])[0]

    if not metadatas:
        return (
            "I couldn't find a match in the current knowledge base. "
            "Try specifying a district (Kandy/Badulla) or a category "
            "(waterfall/adventure/nature/religious/scenic)."
        )

    def normalize(s: str) -> str:
        return " ".join(s.split())

    # Intro sentence (one paragraph)
    intro = f"For your query '{user_query}', here are the most relevant places from the current knowledge base."

    # Optional fallback explanation (separate paragraph)
    fallback_para = None
    if "FALLBACK" in mode or "fallback" in mode.lower():
        fallback_para = "I didn't find an exact match for budget, so I relaxed the budget filter."
    if mode == "FILTER_FALLBACK_NO_BUDGET" or "FALLBACK" in mode:
        extra = "These matches are relevant by theme, but they may not meet the original budget preference in the current dataset."
        fallback_para = (fallback_para + " " + extra) if fallback_para else extra

    # Options paragraph: natural descriptions using only metadata
    top = metadatas[:2]
    unique_districts = sorted(set(m.get("district", "") for m in top if (m.get("district") or "").strip()))
    if len(unique_districts) == 1:
        loc_phrase = f"in {unique_districts[0]}"
    else:
        loc_phrase = "across " + " and ".join(unique_districts) if unique_districts else ""
    descriptions = []
    for meta in top:
        name = meta.get("name", "Unknown")
        district = meta.get("district", "")
        category = meta.get("category", "")
        best_season = meta.get("best_season", "")
        duration = meta.get("recommended_duration", "")
        budget = meta.get("budget_level", "")
        transport = meta.get("transport_options", "")

        parts = [f"{name} is a {category} in {district}"]
        if best_season or duration:
            mid = []
            if best_season:
                mid.append(f"that can be visited {best_season.lower()}")
            if duration:
                mid.append(f"usually takes about {duration} to explore")
            parts[0] += " " + " and ".join(mid) + "."
        else:
            parts[0] += "."
        if budget or transport:
            tail = []
            if budget:
                tail.append(f"It is generally a {budget}-budget stop")
            if transport:
                tail.append(f"can be reached by {transport}")
            parts[0] += " " + " and ".join(tail) + "."
        descriptions.append(parts[0])

    if len(descriptions) == 1:
        options_para = descriptions[0]
    else:
        names = [meta.get("name", "Unknown") for meta in top]
        lead = f"The top options are {names[0]} and {names[1]} {loc_phrase}."
        second_desc = descriptions[1].replace(f"{names[1]} is a ", f"{names[1]} is another ", 1)
        options_para = lead + " " + descriptions[0] + " " + second_desc

    # Assemble with spacing: intro, optional fallback, options
    out = normalize(intro)
    if fallback_para:
        out += "\n\n" + normalize(fallback_para)
    out += "\n\n" + normalize(options_para)
    return out


if __name__ == "__main__":
    # Sample res with hardcoded metadatas
    sample_res = {
        "metadatas": [
            [
                {
                    "name": "Ravana Falls",
                    "district": "Badulla",
                    "category": "waterfall",
                    "best_season": "October to January",
                    "recommended_duration": "2 hours",
                    "budget_level": "low",
                    "transport_options": "tuk-tuk, car",
                },
                {
                    "name": "Diyaluma Falls",
                    "district": "Badulla",
                    "category": "waterfall",
                    "best_season": "Year-round",
                    "recommended_duration": "half day",
                    "budget_level": "low",
                    "transport_options": "car, bus",
                },
            ]
        ]
    }

    answer = format_answer(
        "cheap waterfall near Ella",
        "AUTO-FILTER",
        {"district": "Badulla", "category": "waterfall", "budget_level": "low"},
        sample_res,
    )
    print("--- Formatted answer (sample) ---")
    print(answer)
