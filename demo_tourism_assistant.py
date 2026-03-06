"""
Simple terminal demo of the tourism AI assistant.
Run: python demo_tourism_assistant.py
"""

import json
from pathlib import Path

from query_filters import extract_filters
from rag_build_chroma import DOCS_PATH, build_or_load_collection, retrieve_auto
from answer_generator import format_answer
from itinerary_generator import build_itinerary
from rag_llm_response import generate_travel_response


def load_collection():
    docs_path = Path(DOCS_PATH)
    if not docs_path.exists():
        raise FileNotFoundError(f"Missing {DOCS_PATH}. Run rag_prepare_docs.py first.")
    docs = json.loads(docs_path.read_text(encoding="utf-8"))
    return build_or_load_collection(docs)


def main() -> None:
    query = input("Enter your travel query: ").strip()
    if not query:
        print("No query entered. Exiting.")
        return

    collection = load_collection()
    filters = extract_filters(query)
    mode, filters, res = retrieve_auto(collection, query, n_results=5)
    metadatas = res.get("metadatas", [[]])
    places = metadatas[0] if metadatas else []

    format_answer(query, mode, filters, res)  # pipeline step (not shown in demo)
    itinerary = build_itinerary(query, filters, res, days=None)

    try:
        llm_response = generate_travel_response(query, places)
    except Exception as e:
        llm_response = f"Sorry, the AI recommendation could not be generated: {e}"

    # Clean presentation output
    sep = "-" * 33
    print()
    print(sep)
    print("QUERY")
    print(sep)
    print(query)
    print()

    print("FILTERS")
    print(sep)
    print(filters)
    print()

    print("RETRIEVED PLACES")
    print(sep)
    for i, meta in enumerate(places, start=1):
        name = meta.get("name", "Unknown")
        district = meta.get("district", "")
        category = meta.get("category", "")
        print(f"{i}. {name} ({district}, {category})")
    print()

    print("ITINERARY")
    print(sep)
    print(itinerary)
    print()

    print("AI TRAVEL RECOMMENDATION")
    print(sep)
    print(llm_response)
    print()


if __name__ == "__main__":
    main()
