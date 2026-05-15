import json

# Load your pipeline output
input_file = "mine_output.jsonl"
output_file = "my_pipeline_kgs.json"

my_kgs = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        item = json.loads(line)

        # Extract entities (keys of the "nodes" dict)
        entities = list(item["nodes"].keys())

        # Extract edges (unique relation types from "relations" dict)
        edges = list(item["relations"].keys())

        # Extract triples as [subject, predicate, object]
        relations = [
            [t["subject"], t["relation"], t["object"]]
            for t in item["triples"]
        ]

        my_kgs.append({
            "entities": entities,
            "edges": edges,
            "relations": relations
        })

# Save to output file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(my_kgs, f, indent=2)

print(f"Total KGs converted: {len(my_kgs)}")
print(f"Saved to: {output_file}")

# Quick sanity check on first item
print("\n--- Sanity Check (first KG) ---")
print(f"Entities ({len(my_kgs[0]['entities'])}): {my_kgs[0]['entities'][:5]} ...")
print(f"Edges ({len(my_kgs[0]['edges'])}): {my_kgs[0]['edges'][:5]} ...")
print(f"Relations ({len(my_kgs[0]['relations'])}): {my_kgs[0]['relations'][:3]} ...")