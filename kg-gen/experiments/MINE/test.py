from datasets import load_dataset

dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
data = dataset.to_list()

# Check if kggen KG entities match essay topic keywords
# Simple heuristic: check if essay topic words appear in entities
mismatched = []
for i, item in enumerate(data):
    topic = item["essay_topic"].lower()
    kg = item["kggen"]
    if kg is None or len(kg["entities"]) == 0:
        continue
    # Get first keyword from topic
    first_word = topic.split()[0] if topic else ""
    entities_text = " ".join(kg["entities"]).lower()
    if first_word and first_word not in entities_text:
        mismatched.append((i, item["essay_topic"]))

print(f"Potentially mismatched: {len(mismatched)}")
for i, topic in mismatched[:10]:
    print(f"[{i}] {topic}")