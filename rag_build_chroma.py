import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import chromadb
from answer_generator import format_answer
from itinerary_generator import build_itinerary
from query_filters import extract_filters
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

DOCS_PATH = "rag_docs.json"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "sri_lanka_tourism_places"

# Lightweight, good semantic embedding model
EMBED_MODEL = "all-MiniLM-L6-v2"

# Set True only when you want to rebuild from scratch
RESET_DB = False


def retrieve_places(
    collection,
    query: str,
    district: Optional[str] = None,
    category: Optional[str] = None,
    budget_level: Optional[str] = None,
    n_results: int = 3,
):
    """
    Retrieve top-k documents from Chroma with optional metadata filtering.
    Filtering is applied via `where`. If multiple filters exist, uses `$and`.
    Returns full query result including distances for evaluation.
    """
    conditions: List[Dict[str, Any]] = []

    # ignore empty strings
    if district:
        conditions.append({"district": district})
    if category:
        conditions.append({"category": category})
    if budget_level:
        conditions.append({"budget_level": budget_level})

    kwargs: Dict[str, Any] = {
        "query_texts": [query],
        "n_results": n_results,
        "include": ["metadatas", "distances", "documents"],
    }

    if conditions:
        kwargs["where"] = {"$and": conditions} if len(conditions) > 1 else conditions[0]

    res = collection.query(**kwargs)
    n = len(res["ids"][0])

    # Rerank: when query mentions "train" or "bridge", boost items that mention bridge (name/doc) or train (doc)
    q_lower = query.lower()
    if n and ("train" in q_lower or "bridge" in q_lower):
        metadatas_0 = res["metadatas"][0]
        documents_0 = res.get("documents", [[]])[0] if res.get("documents") else []

        def bonus(i: int) -> int:
            meta = metadatas_0[i] if i < len(metadatas_0) else {}
            doc = (documents_0[i] or "").lower() if i < len(documents_0) else ""
            name = (meta.get("name") or "").lower()
            has_bridge = "bridge" in name or "bridge" in doc
            has_train = "train" in doc
            return 1 if (has_bridge or has_train) else 0

        # Stable sort: bonus=1 first, then bonus=0; preserve relative order within each group
        indices = sorted(range(n), key=lambda i: (0 if bonus(i) else 1, i))

        for key in ("ids", "metadatas", "distances", "documents"):
            if key in res and res[key]:
                res[key][0] = [res[key][0][i] for i in indices]

    return res


def retrieve_auto(collection, query: str, n_results: int = 3):
    filters = extract_filters(query)

    # If we have any extracted filters, try filtered retrieval first
    if any(filters.values()):
        res = retrieve_places(collection, query, **filters, n_results=n_results)
        mode = "AUTO-FILTER"

        # If no results and budget_level exists, retry without budget filter
        if (not res.get("ids")) or (not res["ids"][0]):
            if filters.get("budget_level") is not None:
                filters["budget_level"] = None
                res = retrieve_places(collection, query, **filters, n_results=n_results)
                mode = "FILTER_FALLBACK_NO_BUDGET"

        # If still no results, fallback to semantic retrieval
        if (not res.get("ids")) or (not res["ids"][0]):
            res = retrieve_places(collection, query, n_results=n_results)
            mode = "SEMANTIC_FALLBACK_AFTER_FILTER"

    else:
        # No filters detected → semantic fallback
        res = retrieve_places(collection, query, n_results=n_results)
        mode = "SEMANTIC-FALLBACK"

    return mode, filters, res


def build_or_load_collection(docs: list):
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if RESET_DB:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("🧹 Deleted existing collection (RESET_DB=True).")
        except Exception:
            pass

    # If not resetting, reuse existing collection if it exists
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )
        print("✅ Loaded existing Chroma collection.")
    except Exception:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        print("✅ Created new Chroma collection.")

    # If collection is empty OR RESET_DB, ingest docs
    # We detect emptiness by a small peek query (Chroma doesn't provide direct count reliably across versions)
    # We'll just try to get by IDs if RESET_DB or if CHROMA_DIR is new.
    if RESET_DB:
        ingest_docs(collection, docs)
    else:
        # Try a lightweight check: query for anything only if there are docs.
        # If it errors or returns empty, ingest.
        try:
            probe = collection.query(
                query_texts=["probe"],
                n_results=1,
                include=["metadatas"],
            )
            if not probe.get("ids") or not probe["ids"][0]:
                ingest_docs(collection, docs)
            else:
                print("ℹ️ Collection already has embeddings; skipping ingestion.")
        except Exception:
            ingest_docs(collection, docs)

    return collection


def ingest_docs(collection, docs: list):
    ids = [str(d["metadata"]["id"]) for d in docs]
    documents = [d["text"] for d in docs]
    metadatas = [d["metadata"] for d in docs]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✅ Ingested {len(ids)} documents into Chroma at ./{CHROMA_DIR}")


def print_results(title: str, res: dict):
    print("\n==============================")
    print(title)

    metadatas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    for i, meta in enumerate(metadatas, start=1):
        dist = distances[i - 1] if i - 1 < len(distances) else None
        dist_str = f"{dist:.4f}" if isinstance(dist, (int, float)) else "N/A"
        print(f"{i}. {meta['name']} ({meta['district']}, {meta['category']})  | distance={dist_str}")


def main() -> None:
    if not Path(DOCS_PATH).exists():
        raise FileNotFoundError(f"Missing {DOCS_PATH}. Run rag_prepare_docs.py first.")

    docs = json.loads(Path(DOCS_PATH).read_text(encoding="utf-8"))

    collection = build_or_load_collection(docs)

    # --- User Queries Demo ---
    user_queries = [
        "best religious place in Kandy",
        "cheap waterfall near Ella",
        "adventure activity in Badulla",
        "botanical garden in Kandy",
        "luxury scenic viewpoint for train view",
        "Plan a 3-day trip to Ella",
    ]
    for user_query in user_queries:
        mode, filters, res_top = retrieve_auto(collection, user_query, n_results=2)
        print(f"\nMode: {mode}")
        print(f"Filters: {filters}")
        print_results(f"User query: {user_query} | filters={filters}", res_top)
        answer = format_answer(user_query, mode, filters, res_top)
        print("\n" + "=" * 40)
        print(answer)
        mode2, filters2, res_itin = retrieve_auto(collection, user_query, n_results=8)
        itinerary = build_itinerary(user_query, filters2, res_itin, days=None)
        print("\n" + "=" * 40)
        print(itinerary)

    print("\nDone.")


if __name__ == "__main__":
    main()