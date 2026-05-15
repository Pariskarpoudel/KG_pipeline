import logging
from typing import List, Dict, Tuple
import config
from utils.embedder import embed, cosine_similarity
from utils.llm import llm_call
from utils.parser import parse_llm_json
from prompts.entity_resolution import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = config.ENTITY_SIMILARITY_THRESHOLD
TOP_K_CANDIDATES     = config.ENTITY_TOP_K_CANDIDATES
MAX_CONTEXT_TRIPLES  = config.ENTITY_MAX_CONTEXT_TRIPLES


def _get_context_triples(entity: str, triples: List[Dict]) -> List[Dict]:
    return [
        t for t in triples
        if t["subject"] == entity or t["object"] == entity
    ][:MAX_CONTEXT_TRIPLES]


def _build_embed_string(entity: str, triples: List[Dict]) -> str:
    context = " | ".join(
        f"({t['subject']}, {t['relation']}, {t['object']})"
        for t in triples
    )
    return f"{entity} {context}" if context else entity


def resolve_entities(
    triples: List[Dict],
    article_title: str,
) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Resolve entity variants to canonical names.

    Returns:
        resolved_triples — triples with canonical entity names
        entity_map       — {"M. Curie": "Marie Curie", ...}
    """
    # Only resolve entities that appear as subjects
    # Objects are values — dates, descriptions, places — not resolvable entities
    subject_entities = {t["subject"].strip() for t in triples}

    entities = sorted(
        subject_entities,   # ← only subjects, not all entities
        key=len, reverse=True
    )
    # entities = sorted(
    #     {t["subject"] for t in triples} | {t["object"] for t in triples},
    #     key=len, reverse=True
    # )
    n = len(entities)

    if n < 2:
        logger.info("Too few entities — skipping resolution")
        return triples, {}

    logger.info(f"Resolving {n} unique entities...")

    # Embed all entities with context
    embed_strings = [
        _build_embed_string(e, _get_context_triples(e, triples))
        for e in entities
    ]
    embeddings = embed(embed_strings)

    entity_to_canonical = {}   # variant   → canonical name
    canonical_to_group  = {}   # canonical → set of all variants
    skip_as_target      = set()

    for i, target in enumerate(entities):
        if target in skip_as_target:
            continue

        # Find top-K candidates above threshold — skip only self
        scores = []
        for j, candidate in enumerate(entities):
            if j == i:
                continue
            score = cosine_similarity(embeddings[i], embeddings[j])
            if score >= SIMILARITY_THRESHOLD:
                scores.append((j, score))

        if not scores:
            # No candidates — entity maps to itself
            if target not in entity_to_canonical:
                entity_to_canonical[target] = target
            continue

        scores.sort(key=lambda x: x[1], reverse=True)
        top_k_candidates = [
            {
                "name": entities[j],
                "triples": _get_context_triples(entities[j], triples)
            }
            for j, _ in scores[:TOP_K_CANDIDATES]
        ]

        # LLM verification
        user_prompt = build_user_prompt(
            article_title=article_title,
            target_entity=target,
            target_triples=_get_context_triples(target, triples),
            candidates=top_k_candidates
        )

        raw = llm_call(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None or "matches" not in result or "canonical_name" not in result:
            logger.warning(f"Parse failed for '{target}' — skipping")
            if target not in entity_to_canonical:
                entity_to_canonical[target] = target
            continue

        llm_canonical = result["canonical_name"].strip()
        matches       = result.get("matches", [])
        all_entities  = [target] + [m for m in matches if m in entities]

        # Check if any entity in this group already has a canonical
        # First write wins — longest name processed first so always best name
        existing = None
        for e in all_entities:
            if e in entity_to_canonical:
                existing = entity_to_canonical[e]
                break

        final_canonical = existing if existing else llm_canonical

        # Map all entities in this group to final canonical
        for e in all_entities:
            entity_to_canonical[e] = final_canonical

        # Update group
        if final_canonical not in canonical_to_group:
            canonical_to_group[final_canonical] = set()
        canonical_to_group[final_canonical].update(all_entities)

        # Skip matched entities as targets
        for m in matches:
            skip_as_target.add(m)

        logger.info(
            f"'{target}' + {matches} → '{final_canonical}' | "
            f"{result.get('reasoning', '')}"
        )

    # Any entity not yet mapped → maps to itself
    for entity in entities:
        if entity not in entity_to_canonical:
            entity_to_canonical[entity] = entity

    # Apply to triples
    # Apply to triples — only replace subjects
    # Objects only replaced if they were also subjects
    resolved_triples = [
        {
            "subject":  entity_to_canonical.get(t["subject"], t["subject"]),
            "relation": t["relation"],
            "object":   entity_to_canonical.get(t["object"], t["object"])
            if t["object"] in subject_entities
            else t["object"]   # ← keep object as-is if not a subject entity
        }
        for t in triples
    ]

    merged = sum(1 for k, v in entity_to_canonical.items() if k != v)
    logger.info(f"Entity resolution done: {merged} surface forms merged")
    return resolved_triples, entity_to_canonical