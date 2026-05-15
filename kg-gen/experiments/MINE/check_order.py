import json

with open("my_pipeline_kgs.json") as f:
    kgs = json.load(f)

print("Problematic KGs in my pipeline:")
for i, kg in enumerate(kgs):
    if kg is None:
        print(f"[{i}] None")
    elif len(kg["relations"]) == 0:
        print(f"[{i}] Empty relations")

print(f"\nTotal: {len(kgs)} KGs")


# from datasets import load_dataset

# dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
# data = dataset.to_list()

# print("Essays with empty relations in kggen KG:")
# empty_count = 0
# for i, item in enumerate(data):
#     kg = item["kggen"]
#     if kg is None:
#         print(f"[{i}] {item['essay_topic']} → None")
#         empty_count += 1
#     elif len(kg["relations"]) == 0:
#         print(f"[{i}] {item['essay_topic']} → 0 relations (entities: {len(kg['entities'])})")
#         empty_count += 1

# print(f"\nTotal problematic essays: {empty_count}/101")





# from datasets import load_dataset

# dataset = load_dataset("josancamon/kg-gen-MINE-evaluation-dataset")["train"]
# for i, item in enumerate(dataset):
#     print(i, item["essay_topic"])