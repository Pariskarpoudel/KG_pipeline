import json
from pathlib import Path
import numpy as np


import json
from pathlib import Path
import numpy as np

results_dir = Path("results/hf-mypipeline")
accuracies = []

for f in sorted(results_dir.glob("results_*.json")):
    data = json.load(open(f))
    last = data[-1]
    if "accuracy" in last:
        accuracies.append(float(last["accuracy"].replace("%", "")))

print(f"Essays evaluated: {len(accuracies)}")
print(f"Your MINE-1 Score: {np.mean(accuracies):.2f}%")
# print(f"Compare to: KGGen=66.07%, GraphRAG=47.80%, OpenIE=29.84%")