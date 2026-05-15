import pandas as pd
import json
import ast
from tqdm import tqdm

# ========================= CONFIG =========================
GRAPHRAG_CSV_PATH = "graphrag_dataset.csv"   # change to your actual filename
OPENIE_CSV_PATH   = "openie_dataset.csv"     # change to your actual filename

# Column names for KG output in each CSV
GRAPHRAG_COL = "graphrag_kg"
OPENIE_COL   = "openie_kg"
# ==========================================================


def extract_aligned(csv_path: str, kg_col: str, label: str):
    """
    Reads a CSV, skips rows where kg_col is NaN/empty,
    and returns two aligned lists: kg_list and queries_list.
    """
    df = pd.read_csv(csv_path)
    print(f"\n[{label}] Loaded {len(df)} rows from {csv_path}")

    kg_list      = []
    queries_list = []
    skipped      = []
    errors       = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc=label):
        topic = str(row["essay_topic"]).strip()

        # --- Skip missing/empty KG ---
        if pd.isna(row[kg_col]) or str(row[kg_col]).strip() in ["{}", "nan", ""]:
            skipped.append(f"row {idx}: {topic}")
            continue

        # --- Parse KG ---
        try:
            kg_str  = row[kg_col]
            kg_dict = ast.literal_eval(kg_str) if isinstance(kg_str, str) else kg_str

            entities  = kg_dict.get("entities", []) or kg_dict.get("nodes", [])
            edges     = kg_dict.get("edges", [])
            relations = kg_dict.get("relations", []) or kg_dict.get("triples", [])

            if not relations:
                skipped.append(f"row {idx}: {topic} (empty relations)")
                continue

            kg_item = {"entities": entities, "edges": edges, "relations": relations}
            kg_list.append(kg_item)

        except Exception as e:
            errors.append(f"row {idx} ({topic}) - KG parse error: {e}")
            continue

        # --- Parse queries (only if KG succeeded) ---
        try:
            queries_raw = row["generated_queries"]
            queries_parsed = ast.literal_eval(queries_raw) if isinstance(queries_raw, str) else queries_raw
            queries_list.append(queries_parsed)
        except Exception as e:
            # Remove the KG we just appended to keep alignment
            kg_list.pop()
            errors.append(f"row {idx} ({topic}) - queries parse error: {e}")
            continue

    # --- Sanity check ---
    assert len(kg_list) == len(queries_list), (
        f"ALIGNMENT ERROR: {len(kg_list)} KGs vs {len(queries_list)} query sets!"
    )

    # --- Summary ---
    print(f"  ✅ Kept:    {len(kg_list)} entries")
    print(f"  ⏭️  Skipped: {len(skipped)}")
    for s in skipped:
        print(f"     {s}")
    if errors:
        print(f"  ❌ Errors:  {len(errors)}")
        for e in errors:
            print(f"     {e}")

    return kg_list, queries_list


# ── GraphRAG ──────────────────────────────────────────────
graphrag_kgs, graphrag_queries = extract_aligned(GRAPHRAG_CSV_PATH, GRAPHRAG_COL, "GraphRAG")

with open("graphrag_pipeline_kgs.json", "w", encoding="utf-8") as f:
    json.dump(graphrag_kgs, f, indent=2, ensure_ascii=False)

with open("graphrag_queries.json", "w", encoding="utf-8") as f:
    json.dump(graphrag_queries, f, indent=2, ensure_ascii=False)

print(f"\n✅ graphrag_pipeline_kgs.json → {len(graphrag_kgs)} entries")
print(f"✅ graphrag_queries.json       → {len(graphrag_queries)} entries")


# ── OpenIE ────────────────────────────────────────────────
openie_kgs, openie_queries = extract_aligned(OPENIE_CSV_PATH, OPENIE_COL, "OpenIE")

with open("openie_pipeline_kgs.json", "w", encoding="utf-8") as f:
    json.dump(openie_kgs, f, indent=2, ensure_ascii=False)

with open("openie_queries.json", "w", encoding="utf-8") as f:
    json.dump(openie_queries, f, indent=2, ensure_ascii=False)

print(f"\n✅ openie_pipeline_kgs.json → {len(openie_kgs)} entries")
print(f"✅ openie_queries.json       → {len(openie_queries)} entries")