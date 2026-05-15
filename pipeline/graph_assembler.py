# pipeline/graph_assembler.py
import json
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)


def assemble_graph(
    article_title:        str,
    resolved_triples:     List[Dict],
    entity_map:           Dict[str, str],
    relation_map:         Dict[str, str],
    relation_definitions: Dict[str, str],
    entity_concepts:      Dict[str, List[str]],
    relation_concepts:    Dict[str, List[str]],
) -> Dict:

    all_nodes = set()
    for t in resolved_triples:
        all_nodes.add(t["subject"])
        all_nodes.add(t["object"])

    nodes = {
        node: {
            "concepts": entity_concepts.get(node, [])
        }
        for node in all_nodes
    }

    relations = {
        t["relation"]: {
            "definition": relation_definitions.get(t["relation"], ""),
            "concepts":   relation_concepts.get(t["relation"], [])
        }
        for t in resolved_triples
    }

    kg = {
        "article_title":  article_title,
        "nodes":          nodes,
        "relations":      relations,
        "triples":        resolved_triples,
        "entity_map":     entity_map,
        "relation_map":   relation_map,
    }

    logger.info(
        f"Graph assembled: {len(nodes)} nodes, "
        f"{len(relations)} relations, "
        f"{len(resolved_triples)} triples"
    )
    return kg


def save_graph(kg: Dict, output_dir: str = "data/output") -> str:
    """
    Save KG as individual .json file.
    Used in single article mode (python main.py data/raw/article.txt)
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = kg["article_title"].replace(" ", "_").replace("/", "_") + ".json"
    path     = os.path.join(output_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

    logger.info(f"Graph saved to: {path}")
    return path


def save_graph_jsonl(kg: Dict, jsonl_path: str) -> None:
    """
    Append KG as one line to a shared JSONL output file.
    Used in JSONL bulk mode (python main.py --jsonl)
    Each article = one line in the file.
    """
    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)

    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(kg, ensure_ascii=False) + "\n")

    logger.info(f"Graph appended to: {jsonl_path}")


def load_graph(path: str) -> Dict:
    """Load a saved knowledge graph from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def concepts_to_triples(kg: Dict) -> List[Dict]:
    """Convert concept metadata to triples for downstream tasks."""
    concept_triples = []
    for entity, data in kg["nodes"].items():
        for concept in data.get("concepts", []):
            concept_triples.append({
                "subject":  entity,
                "relation": "type",
                "object":   concept
            })
    for relation, data in kg["relations"].items():
        for concept in data.get("concepts", []):
            concept_triples.append({
                "subject":  relation,
                "relation": "category",
                "object":   concept
            })
    return concept_triples