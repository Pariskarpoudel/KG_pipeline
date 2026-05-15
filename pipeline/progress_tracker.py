import os
import json
import logging

logger = logging.getLogger(__name__)

PROGRESS_FILE = "progress.json"


def load_progress(output_dir: str) -> set:
    """
    Load set of already processed keys from progress.json.
    Returns empty set if no progress file exists.
    """
    path = os.path.join(output_dir, PROGRESS_FILE)
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    processed = set(data.get("processed", []))
    logger.info(f"Resuming — {len(processed)} articles already processed")
    return processed


def save_progress(output_dir: str, key: str, kg: dict, output_filename: str):
    """
    Mark article as processed:
      1. Append KG to combined JSONL output file
      2. Update progress.json with new key
    """
    os.makedirs(output_dir, exist_ok=True)

    # Append KG to combined JSONL output
    jsonl_path = os.path.join(output_dir, output_filename)
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(kg, ensure_ascii=False) + "\n")

    # Update progress.json
    progress_path = os.path.join(output_dir, PROGRESS_FILE)
    processed = []
    if os.path.exists(progress_path):
        with open(progress_path, "r", encoding="utf-8") as f:
            processed = json.load(f).get("processed", [])
    processed.append(key)
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump({"processed": processed}, f, indent=2, ensure_ascii=False)

    logger.info(f"Progress saved: '{key}' → {jsonl_path}")