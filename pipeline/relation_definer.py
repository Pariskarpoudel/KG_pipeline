import logging
from typing import List, Dict
from utils.llm import llm_call
from utils.parser import parse_llm_json
from prompts.relation_definition import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

BATCH_SIZE = 10   # relations per LLM call — as per pipeline doc


def _collect_unique_relations(triples: List[Dict]) -> Dict[str, Dict]:
    """
    Collect unique relations with one example triple each.
    Returns dict: {relation: example_triple}
    """
    seen = {}
    for t in triples:
        relation = t["relation"].strip()
        if relation not in seen:
            seen[relation] = t   # first occurrence as example
    return seen


def _batch(items: list, size: int) -> list:
    """Split list into batches of given size."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def define_relations(
    triples: List[Dict],
    article_title: str
) -> Dict[str, str]:
    """
    Generate natural language definitions for all unique relations.

    Returns:
        relation_definitions — {"born in": "The subject was born in...", ...}
    """
    unique_relations = _collect_unique_relations(triples)
    logger.info(f"Defining {len(unique_relations)} unique relations...")

    # Build list of {relation, example} dicts
    relations_list = [
        {"relation": rel, "example": example_triple}
        for rel, example_triple in unique_relations.items()
    ]

    relation_definitions = {}

    # Process in batches of BATCH_SIZE
    for batch in _batch(relations_list, BATCH_SIZE):
        user_prompt = build_user_prompt(
            article_title=article_title,
            relations_with_examples=batch
        )

        raw = llm_call(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None:
            logger.warning(f"Parse failed for batch — skipping {len(batch)} relations")
            continue

        # Validate and store definitions
        for rel_dict in batch:
            rel = rel_dict["relation"]
            if rel in result and isinstance(result[rel], str) and result[rel].strip():
                relation_definitions[rel] = result[rel].strip()
            else:
                logger.warning(f"Missing definition for '{rel}' — skipping")

    logger.info(f"Defined {len(relation_definitions)}/{len(unique_relations)} relations")
    return relation_definitions