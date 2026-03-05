"""
Create RAG-ready documents from sri_lanka_tourism_dataset_kandy_badulla_v1.csv
Output: a list of dicts with 'text' and 'metadata'
"""

import csv
from pathlib import Path

CSV_PATH = "sri_lanka_tourism_dataset_kandy_badulla_v1.csv"
OUT_PATH = "rag_docs.json"


def load_docs(csv_path: str):
    docs = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = (row.get("full_text") or "").strip()
            if not text:
                continue

            metadata = {
                "id": int(row["id"]),
                "name": row["name"].strip(),
                "district": row["district"].strip(),
                "category": row["category"].strip(),
                "budget_level": row["budget_level"].strip(),
                "recommended_duration": row["recommended_duration"].strip(),
                "best_season": row["best_season"].strip(),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }

            docs.append({"text": text, "metadata": metadata})
    return docs


if __name__ == "__main__":
    import json

    if not Path(CSV_PATH).exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    docs = load_docs(CSV_PATH)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(docs)} documents to {OUT_PATH}")
