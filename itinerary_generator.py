"""
Rule-based itinerary generator using retrieved Chroma results (metadatas only).
"""

import re


def parse_duration_to_hours(duration_str: str) -> float:
    """
    Convert common duration strings to approximate hours.
    Unknown formats default to 2.
    """
    if not duration_str or not isinstance(duration_str, str):
        return 2.0
    s = duration_str.strip().lower()
    if s in ("1 hour", "1 hr"):
        return 1.0
    if s in ("2 hours", "2 hrs"):
        return 2.0
    if s in ("half day", "half-day"):
        return 4.0
    if s in ("full day", "full-day"):
        return 8.0
    # Optional: "3 hours" etc.
    m = re.match(r"^(\d+)\s*hours?$", s)
    if m:
        return float(int(m.group(1)))
    return 2.0


def _slot_type_for_hours(hours: float) -> str:
    """Return 'full_day', 'half_day', or 'short' for slot assignment."""
    if hours >= 6:
        return "full_day"
    if hours >= 3:
        return "half_day"
    return "short"


def extract_days(query: str, default_days: int = 2) -> int:
    """
    Extract number of days from the user query.
    Supports patterns like:
    - "3-day", "3 day", "3days", "for 3 days"
    - "weekend" -> 2
    Defaults to 2 if not found.
    """
    if not query or not isinstance(query, str):
        return default_days
    q = query.lower().strip()
    if "weekend" in q:
        return 2
    patterns = [
        r"(\d+)\s*-?\s*day",   # 3-day, 3 day
        r"(\d+)\s*days",      # 3days, 3 days
        r"for\s*(\d+)\s*days?",  # for 3 days
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            n = int(m.group(1))
            return max(1, min(7, n))
    return default_days


def build_itinerary(
    user_query: str,
    filters: dict,
    res: dict,
    days: int | None = None,
) -> str:
    """
    Build a day-by-day itinerary from retrieved places.
    Uses only res["metadatas"][0]; no invented places.
    If days is None, it is inferred from user_query via extract_days().
    """
    if days is None:
        days = extract_days(user_query, default_days=2)
    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]
    if not metadatas:
        return (
            "I couldn't find any places to build an itinerary. "
            "Try specifying a district (Kandy/Badulla) or category "
            "(waterfall/adventure/nature/religious/scenic)."
        )

    # Rank by vector distance (lower = better); fallback dist=999 if missing
    if len(distances) == len(metadatas):
        items = [{"meta": m, "dist": d} for m, d in zip(metadatas, distances)]
    else:
        items = [{"meta": m, "dist": 999} for m in metadatas]
    items.sort(key=lambda x: x["dist"])

    # Preferred district: from filter or top-ranked result (fallback to other districts when preferred runs out)
    if filters.get("district"):
        preferred_district = filters["district"]
    else:
        if items:
            preferred_district = items[0]["meta"].get("district")
        else:
            preferred_district = None

    places = []
    for it in items:
        meta = it["meta"]
        dur_str = (meta.get("recommended_duration") or "").strip()
        hours = parse_duration_to_hours(meta.get("recommended_duration", ""))
        slot_type = _slot_type_for_hours(hours)
        is_full_day = dur_str.lower() == "full day"
        name = meta.get("name", "Unknown")
        category = meta.get("category", "")
        district = (meta.get("district") or "").strip()
        places.append({
            "name": name,
            "hours": hours,
            "slot_type": slot_type,
            "is_full_day": is_full_day,
            "category": category,
            "district": district,
            "meta": meta,
        })

    # Build slots: 2 per day (Morning, Afternoon). full_day uses both slots then next day; prefer preferred_district + diversity.
    slots_per_day = ["Morning", "Afternoon"]
    total_slots = days * 2
    slot_assignments = [None] * total_slots
    remaining_places = list(places)
    categories_used = [set() for _ in range(days)]
    s = 0

    def choose_place(remaining, day, preferred):
        # a) preferred_district + diversity  b) preferred_district  c) any + diversity  d) any (fallback when preferred runs out)
        for p in remaining:
            if preferred and p["district"] == preferred and p["category"] not in categories_used[day]:
                return p
        for p in remaining:
            if preferred and p["district"] == preferred:
                return p
        for p in remaining:
            if p["category"] not in categories_used[day]:
                return p
        return remaining[0] if remaining else None

    while s < total_slots and remaining_places:
        day = s // 2
        slot_name = slots_per_day[s % 2]

        chosen = choose_place(remaining_places, day, preferred_district)
        if chosen is None:
            break

        if chosen["is_full_day"] or chosen["slot_type"] == "full_day":
            # Full-day: Morning shows "place — full day", Afternoon shows "(continued) place"
            slot_assignments[s] = (chosen, "Morning", "full_day")
            if s + 1 < total_slots:
                slot_assignments[s + 1] = (chosen, "Afternoon", "continued")
            categories_used[day].add(chosen["category"])
            remaining_places.remove(chosen)
            s += 2
            continue

        slot_assignments[s] = (chosen, slot_name, None)
        categories_used[day].add(chosen["category"])
        remaining_places.remove(chosen)
        s += 1

    def slot_display(place_or_none, slot_label, suffix=None):
        if place_or_none is None:
            return f"{slot_label} - Free time / local exploration"
        name = place_or_none.get("name", "Unknown")
        meta = place_or_none.get("meta", {})
        district = (meta.get("district") or "").strip()
        duration = (meta.get("recommended_duration") or "").strip()
        if suffix == "full_day":
            base = f"{name} ({district})" if district else name
            return f"{slot_label} - {base} — full day"
        if suffix == "continued":
            return f"{slot_label} - (continued) {name}"
        if district:
            base = f"{name} ({district})"
        else:
            base = name
        if duration:
            base += f" — {duration}"
        return f"{slot_label} - {base}"

    # Fill empty slots (store triple for consistency)
    for i in range(total_slots):
        if slot_assignments[i] is None:
            slot_assignments[i] = (None, slots_per_day[i % 2], None)

    # Format output: if filters["district"] was None but we have preferred_district, show "district=Badulla preferred"
    if filters.get("district"):
        district_display = filters["district"]
    elif preferred_district:
        district_display = f"{preferred_district} preferred"
    else:
        district_display = "—"
    budget = filters.get("budget_level") or "—"
    category = filters.get("category") or "—"
    header = (
        f"Itinerary for {days}-day trip (district={district_display}, budget={budget}, category={category})\n\n"
    )
    lines = []
    for d in range(days):
        start = d * 2
        parts = []
        for i in range(2):
            entry = slot_assignments[start + i]
            place = entry[0] if len(entry) > 0 else None
            label = entry[1] if len(entry) > 1 else slots_per_day[i]
            suffix = entry[2] if len(entry) > 2 else None
            parts.append(slot_display(place, label, suffix))
        lines.append(f"Day {d + 1}: " + "; ".join(parts))
    return header + "\n".join(lines)


if __name__ == "__main__":
    # Sample with distances: lower distance = better match, chosen first. Repeated categories show diversity.
    sample_res = {
        "metadatas": [
            [
                {"name": "Temple of the Tooth", "recommended_duration": "2 hours", "category": "religious", "district": "Kandy"},
                {"name": "Royal Botanic Gardens", "recommended_duration": "half day", "category": "nature", "district": "Kandy"},
                {"name": "Ravana Falls", "recommended_duration": "2 hours", "category": "waterfall", "district": "Badulla"},
                {"name": "Nine Arches Bridge", "recommended_duration": "1 hour", "category": "scenic", "district": "Badulla"},
                {"name": "Sri Dalada Museum", "recommended_duration": "1 hour", "category": "religious", "district": "Kandy"},
                {"name": "Hanthana Range", "recommended_duration": "half day", "category": "nature", "district": "Kandy"},
            ]
        ],
        "distances": [[0.25, 0.31, 0.42, 0.38, 0.55, 0.48]],  # lower = better; Temple first, then Gardens, etc.
    }
    filters = {"district": "Kandy", "category": "religious", "budget_level": "low"}
    out = build_itinerary("religious and nature in Kandy", filters, sample_res, days=2)
    print("--- Itinerary (sample: distance-ranked + diversity) ---")
    print(out)
