import json
from pathlib import Path
from typing import List, Dict, Any

from rag_build_chroma import (
    DOCS_PATH,
    build_or_load_collection,
    retrieve_auto,
)


def load_collection() -> Any:
    docs_path = Path(DOCS_PATH)
    if not docs_path.exists():
        raise FileNotFoundError(f"Missing {DOCS_PATH}. Run rag_prepare_docs.py first.")

    docs = json.loads(docs_path.read_text(encoding="utf-8"))
    collection = build_or_load_collection(docs)
    return collection


def load_evaluation_queries(path: str = "evaluation_queries.json") -> List[Dict[str, Any]]:
    eval_path = Path(path)
    if not eval_path.exists():
        raise FileNotFoundError(f"Missing {path}.")
    return json.loads(eval_path.read_text(encoding="utf-8"))


def evaluate_retrieval(collection, queries: List[Dict[str, Any]]) -> None:
    hit_at_1_list: List[float] = []
    precision_at_2_list: List[float] = []
    k = 2

    for item in queries:
        query_text: str = item["query"]
        relevant: List[str] = item.get("relevant", [])

        mode, filters, res = retrieve_auto(collection, query_text, n_results=k)
        metadatas_list = res.get("metadatas", [[]])
        metadatas = metadatas_list[0] if metadatas_list else []

        predicted_names = [meta.get("name", "") for meta in metadatas]

        # Hit@1: 1 if first predicted result is in relevant, else 0
        hit_at_1 = 1.0 if (predicted_names and predicted_names[0] in relevant) else 0.0
        hit_at_1_list.append(hit_at_1)

        # Precision@2: (# relevant in top 2) / 2
        relevant_retrieved = sum(1 for name in predicted_names if name in relevant)
        precision_at_2 = relevant_retrieved / 2.0
        precision_at_2_list.append(precision_at_2)

        predicted_str = ", ".join(predicted_names) if predicted_names else "(no results)"
        relevant_str = ", ".join(relevant) if relevant else "(none specified)"

        print(f"Query: {query_text}")
        print(f"Predicted: {predicted_str}")
        print(f"Relevant: {relevant_str}")
        print(f"Hit@1 = {hit_at_1:.3f}")
        print(f"Precision@2 = {precision_at_2:.3f}")
        print()

    if hit_at_1_list:
        avg_hit_at_1 = sum(hit_at_1_list) / len(hit_at_1_list)
        avg_precision_at_2 = sum(precision_at_2_list) / len(precision_at_2_list)
        print(f"Average Hit@1 = {avg_hit_at_1:.3f}")
        print(f"Average Precision@2 = {avg_precision_at_2:.3f}")


def main() -> None:
    collection = load_collection()
    queries = load_evaluation_queries()
    evaluate_retrieval(collection, queries)


if __name__ == "__main__":
    main()

