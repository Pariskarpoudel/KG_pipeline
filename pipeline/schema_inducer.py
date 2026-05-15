import logging
from typing import List, Dict, Tuple

from utils.llm import llm_call
from utils.parser import parse_llm_json
from prompts.entity_concept import SYSTEM_PROMPT as ENTITY_SYSTEM, build_user_prompt as build_entity_prompt
from prompts.relation_concept import SYSTEM_PROMPT as RELATION_SYSTEM, build_user_prompt as build_relation_prompt

logger = logging.getLogger(__name__)

BATCH_SIZE = 8   # as per pipeline doc


def _get_entity_context(entity: str, triples: List[Dict]) -> List[Dict]:
    """Get up to 3 context triples for an entity."""
    return [
        t for t in triples
        if t["subject"] == entity or t["object"] == entity
    ][:3]


def _get_relation_example(relation: str, triples: List[Dict]) -> Dict:
    """Get one example triple for a relation."""
    for t in triples:
        if t["relation"] == relation:
            return t
    return {"subject": "?", "relation": relation, "object": "?"}


def _batch(items: list, size: int) -> list:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _validate_concepts(concepts: any) -> List[str]:
    """Ensure concepts is a non-empty list of non-empty strings."""
    if not isinstance(concepts, list):
        return []
    return [c.strip() for c in concepts if isinstance(c, str) and c.strip()]


# ─────────────────────────────────────────────
# Entity conceptualization
# ─────────────────────────────────────────────

def conceptualize_entities(
    triples: List[Dict],
    article_title: str,
) -> Dict[str, List[str]]:
    """
    Generate concept phrases for all unique entities.

    Returns:
        entity_concepts — {"Marie Curie": ["Physicist", "Scientist", "Academic"], ...}
    """
    # Collect unique entities — subjects only
    entities = sorted(
        {t["subject"] for t in triples},
        key=len, reverse=True
    )

    logger.info(f"Conceptualizing {len(entities)} entities...")

    entity_concepts = {}

    for batch in _batch(entities, BATCH_SIZE):
        entities_with_context = [
            {
                "entity":  e,
                "triples": _get_entity_context(e, triples)
            }
            for e in batch
        ]

        user_prompt = build_entity_prompt(
            article_title=article_title,
            entities_with_context=entities_with_context
        )

        raw = llm_call(
            system_prompt=ENTITY_SYSTEM,
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None:
            logger.warning(f"Entity concept parse failed for batch — skipping")
            continue

        for e in batch:
            if e in result:
                concepts = _validate_concepts(result[e])
                if concepts:
                    entity_concepts[e] = concepts
                else:
                    logger.warning(f"Invalid concepts for entity '{e}' — skipping")
            else:
                logger.warning(f"Missing concepts for entity '{e}' — skipping")

    logger.info(f"Entity conceptualization done: {len(entity_concepts)}/{len(entities)}")
    return entity_concepts


# ─────────────────────────────────────────────
# Relation conceptualization
# ─────────────────────────────────────────────

def conceptualize_relations(
    triples: List[Dict],
    relation_definitions: Dict[str, str],
    article_title: str,
) -> Dict[str, List[str]]:
    """
    Generate concept phrases for all canonical relations.

    Returns:
        relation_concepts — {"discovered": ["Scientific Discovery", "Achievement", "Factual Relation"], ...}
    """
    relations = list(relation_definitions.keys())

    logger.info(f"Conceptualizing {len(relations)} relations...")

    relation_concepts = {}

    for batch in _batch(relations, BATCH_SIZE):
        relations_with_context = [
            {
                "relation":   r,
                "definition": relation_definitions[r],
                "example":    _get_relation_example(r, triples)
            }
            for r in batch
        ]

        user_prompt = build_relation_prompt(
            article_title=article_title,
            relations_with_context=relations_with_context
        )

        raw = llm_call(
            system_prompt=RELATION_SYSTEM,
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None:
            logger.warning(f"Relation concept parse failed for batch — skipping")
            continue

        for r in batch:
            if r in result:
                concepts = _validate_concepts(result[r])
                if concepts:
                    relation_concepts[r] = concepts
                else:
                    logger.warning(f"Invalid concepts for relation '{r}' — skipping")
            else:
                logger.warning(f"Missing concepts for relation '{r}' — skipping")

    logger.info(f"Relation conceptualization done: {len(relation_concepts)}/{len(relations)}")
    return relation_concepts


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────

def induce_schema(
    triples: List[Dict],
    relation_definitions: Dict[str, str],
    article_title: str,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Run both entity and relation conceptualization.

    Returns:
        entity_concepts   — {"Marie Curie": ["Physicist", "Scientist", "Academic"]}
        relation_concepts — {"discovered": ["Discovery", "Achievement", "Factual Relation"]}
    """
    entity_concepts   = conceptualize_entities(triples, article_title)
    relation_concepts = conceptualize_relations(triples, relation_definitions, article_title)
    return entity_concepts, relation_concepts