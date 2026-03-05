"""
Extract district, category, and budget_level filters from a natural-language query.
"""

from typing import Optional

# District: keywords (lower) -> canonical name
DISTRICT_KEYWORDS = [
    (["kandy"], "Kandy"),
    (["badulla", "ella"], "Badulla"),
]

# Category: priority order waterfall > adventure > religious > nature > scenic
CATEGORY_KEYWORDS = [
    (["waterfall", "falls", "cascade"], "waterfall"),
    (["adventure", "zip", "zipline", "zip line", "thrill"], "adventure"),
    (["temple", "religious", "buddha", "tooth", "maligawa"], "religious"),
    (["garden", "botanic", "nature", "mountain", "hike", "hiking", "forest"], "nature"),
    (["scenic", "view", "viewpoint", "bridge", "train"], "scenic"),
]

# Budget: keywords -> canonical budget_level
BUDGET_KEYWORDS = [
    (["budget", "cheap", "low cost"], "low"),
    (["medium", "mid"], "medium"),
    (["luxury", "expensive", "high end"], "high"),
]


def extract_filters(query: str) -> dict[str, Optional[str]]:
    """
    Extract district, category, and budget_level from a natural-language query.
    Case-insensitive. Category uses priority: waterfall > adventure > religious > nature > scenic.
    Returns None for any field not detected.
    """
    q = query.lower().strip()
    result: dict[str, Optional[str]] = {
        "district": None,
        "category": None,
        "budget_level": None,
    }

    # District
    for keywords, district in DISTRICT_KEYWORDS:
        if any(kw in q for kw in keywords):
            result["district"] = district
            break

    # Category (first match wins; order = priority)
    for keywords, category in CATEGORY_KEYWORDS:
        if any(kw in q for kw in keywords):
            result["category"] = category
            break

    # Budget
    for keywords, budget in BUDGET_KEYWORDS:
        if any(kw in q for kw in keywords):
            result["budget_level"] = budget
            break

    return result


if __name__ == "__main__":
    test_queries = [
        "cheap waterfall near Ella",
        "best religious place in Kandy",
        "adventure activity in Badulla",
        "scenic bridge to watch a train",
        "botanical garden in Kandy",
    ]

    print("Extracted filters:\n")
    for q in test_queries:
        filters = extract_filters(q)
        print(f"Query: {q}")
        print(f"  -> {filters}\n")
