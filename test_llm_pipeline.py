"""
End-to-end test script for the tourism assistant pipeline.
Run from terminal: python test_llm_pipeline.py
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


def run_all_tests() -> None:
    collection = load_collection()

    test_queries = [
        "best religious place in Kandy",
        "cheap waterfall near Ella",
        "adventure activity in Badulla",
        "botanical garden in Kandy",
        "luxury scenic viewpoint for train view",
        "Plan a 3-day trip to Ella",
    ]

    for query in test_queries:
        print("=" * 50)
        print("QUERY:", query)
        print()

        filters = extract_filters(query)
        print("FILTERS:")
        print(filters)
        print()

        mode, filters, res = retrieve_auto(collection, query, n_results=5)
        print("RETRIEVAL MODE:")
        print(mode)
        print()

        metadatas = res.get("metadatas", [[]])
        places = metadatas[0] if metadatas else []
        print("RETRIEVED PLACES:")
        for i, meta in enumerate(places, start=1):
            name = meta.get("name", "Unknown")
            district = meta.get("district", "")
            category = meta.get("category", "")
            print(f"{i}. {name} ({district}, {category})")
        print()

        template_answer = format_answer(query, mode, filters, res)
        print("TEMPLATE ANSWER:")
        print(template_answer)
        print()

        itinerary = build_itinerary(query, filters, res, days=None)
        print("ITINERARY:")
        print(itinerary)
        print()

        try:
            llm_answer = generate_travel_response(query, places)
            print("LLM ANSWER:")
            print(llm_answer)
        except Exception as e:
            print("LLM ANSWER: ERROR -", str(e))

        print()
        print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
