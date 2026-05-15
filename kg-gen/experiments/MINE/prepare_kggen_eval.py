import pandas as pd
import json
import ast
from tqdm import tqdm

# ========================= CONFIG =========================
CSV_PATH = "mine1final - mine_dataset_unfixed.csv"  # your fixed CSV

# Essays to skip (empty kggen output)
SKIP_TOPICS = {
    "Unusual Animal Adaptations",
    "How Languages Die",
    "The History of Protests and Revolutions",
    "The Art of Calligraphy",
    "The Development of Renewable Energy Sources",
}
# ==========================================================

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} rows from CSV")

kggen_list = []
queries_list = []
skipped = []
errors = []

for idx, row in tqdm(df.iterrows(), total=len(df)):
    topic = str(row["essay_topic"]).strip()

    # --- Skip missing/bad kggen rows ---
    if (
        topic in SKIP_TOPICS
        or pd.isna(row["kggen"])
        or str(row["kggen"]).strip() in ["{}", "nan", ""]
    ):
        skipped.append(f"row {idx}: {topic}")
        continue

    # --- Parse kggen KG ---
    try:
        kggen_str = row["kggen"]
        kggen_dict = ast.literal_eval(kggen_str) if isinstance(kggen_str, str) else kggen_str

        entities = kggen_dict.get("entities", []) or kggen_dict.get("nodes", [])
        edges    = kggen_dict.get("edges", [])
        relations = kggen_dict.get("relations", []) or kggen_dict.get("triples", [])

        pipeline_item = {
            "entities": entities,
            "edges": edges,
            "relations": relations,
        }
        kggen_list.append(pipeline_item)

    except Exception as e:
        errors.append(f"row {idx} ({topic}): {e}")
        continue  # don't add queries either if KG parse failed

    # --- Parse queries (must stay aligned with KG) ---
    try:
        queries_raw = row["generated_queries"]
        if isinstance(queries_raw, str):
            queries_parsed = ast.literal_eval(queries_raw)
        else:
            queries_parsed = queries_raw  # already a list
        queries_list.append(queries_parsed)
    except Exception as e:
        # If queries fail, remove the KG we just appended to keep alignment
        kggen_list.pop()
        errors.append(f"row {idx} ({topic}) - queries parse error: {e}")
        continue

# --- Sanity check ---
assert len(kggen_list) == len(queries_list), (
    f"ALIGNMENT ERROR: {len(kggen_list)} KGs vs {len(queries_list)} query sets!"
)

# --- Save outputs ---
with open("kggen_pipeline_kgs.json", "w", encoding="utf-8") as f:
    json.dump(kggen_list, f, indent=2, ensure_ascii=False)

with open("kggen_queries.json", "w", encoding="utf-8") as f:
    json.dump(queries_list, f, indent=2, ensure_ascii=False)

# --- Summary ---
print(f"\n✅ kggen_pipeline_kgs.json  → {len(kggen_list)} entries")
print(f"✅ kggen_queries.json        → {len(queries_list)} entries")
print(f"⏭️  Skipped ({len(skipped)}):")
for s in skipped:
    print(f"   {s}")
if errors:
    print(f"\n❌ Errors ({len(errors)}):")
    for e in errors:
        print(f"   {e}")