import logging
from typing import List, Dict, Tuple
import config
from utils.embedder import embed, cosine_similarity
from utils.llm import llm_call
from utils.parser import parse_llm_json
from prompts.relation_canon import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = config.RELATION_SIMILARITY_THRESHOLD
TOP_K_CANDIDATES     = config.RELATION_TOP_K_CANDIDATES
SINGLETON_BATCH_SIZE = config.RELATION_SINGLETON_BATCH_SIZE


def _get_example_triple(relation: str, triples: List[Dict]) -> Dict:
    for t in triples:
        if t["relation"] == relation:
            return t
    return {"subject": "?", "relation": relation, "object": "?"}


def _build_embed_string(relation: str, definition: str) -> str:
    return f"{relation} {definition}"


def _normalize_singletons(
    singletons: List[str],
    relation_definitions: Dict[str, str],
    triples: List[Dict],
    article_title: str,
) -> Dict[str, str]:
    """
    Send singleton relations to LLM in batches.
    LLM keeps concise relations as-is, normalizes only verbose ones.
    Returns {original: normalized_or_same}
    """
    normalized = {}
    batches = [
        singletons[i:i + SINGLETON_BATCH_SIZE]
        for i in range(0, len(singletons), SINGLETON_BATCH_SIZE)
    ]

    for batch in batches:
        relations_block = "\n".join(
            f'- "{r}" | Example: ({_get_example_triple(r, triples)["subject"]}, '
            f'{r}, {_get_example_triple(r, triples)["object"]})'
            for r in batch
        )

        user_prompt = f"""Article: {article_title}

Review each relation name below:
- If it is lengthy, verbose, or imprecise — normalize it to a shorter cleaner form.
- Never change the meaning, only shorten the phrasing if needed.
- Output every relation in the list — do not skip any.

Relations to review:
{relations_block}

Output format:
{{
  "original_relation": "normalized_or_same_relation",
  ...
}}"""

        raw = llm_call(
            system_prompt="You are a knowledge graph relation normalizer. Output JSON only. No explanation outside JSON.",
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None:
            logger.warning("Singleton normalization parse failed — keeping originals")
            for r in batch:
                normalized[r] = r
            continue

        for r in batch:
            if r in result and isinstance(result[r], str) and result[r].strip():
                normalized_name = result[r].strip()
                normalized[r]   = normalized_name
                if normalized_name != r:
                    logger.info(f"Singleton normalized: '{r}' → '{normalized_name}'")
                else:
                    logger.info(f"Singleton kept as-is: '{r}'")
            else:
                logger.warning(f"No result for '{r}' — keeping original")
                normalized[r] = r

    return normalized


def canonicalize_relations(
    triples: List[Dict],
    relation_definitions: Dict[str, str],
    article_title: str,
) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Canonicalize relation variants to single canonical relation names.
    Singleton relations are normalized via LLM even without candidates.

    Returns:
        resolved_triples  — triples with canonical relation names
        relation_map      — {"was born in": "born in", ...}
    """
    relations = sorted(
        relation_definitions.keys(),
        key=lambda r: sum(1 for t in triples if t["relation"] == r),
        reverse=True
    )
    n = len(relations)

    if n < 2:
        logger.info("Too few relations — skipping canonicalization")
        return triples, {}

    logger.info(f"Canonicalizing {n} unique relations...")

    embed_strings = [
        _build_embed_string(r, relation_definitions[r])
        for r in relations
    ]
    embeddings = embed(embed_strings)

    relation_to_canonical = {}
    canonical_to_group    = {}
    skip_as_target        = set()
    singletons            = []   # relations with no candidates above threshold

    for i, target_rel in enumerate(relations):
        if target_rel in skip_as_target:
            continue

        scores = []
        for j, candidate_rel in enumerate(relations):
            if j == i:
                continue
            score = cosine_similarity(embeddings[i], embeddings[j])
            if score >= SIMILARITY_THRESHOLD:
                scores.append((j, score))

        if not scores:
            singletons.append(target_rel)   # ← collect for LLM normalization
            continue

        scores.sort(key=lambda x: x[1], reverse=True)
        top_k_candidates = [
            {
                "relation":   relations[j],
                "definition": relation_definitions[relations[j]],
                "example":    _get_example_triple(relations[j], triples)
            }
            for j, _ in scores[:TOP_K_CANDIDATES]
        ]

        user_prompt = build_user_prompt(
            article_title=article_title,
            target_relation=target_rel,
            target_definition=relation_definitions[target_rel],
            target_example=_get_example_triple(target_rel, triples),
            candidates=top_k_candidates
        )

        raw = llm_call(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None or "matches" not in result or "canonical_name" not in result:
            logger.warning(f"Parse failed for '{target_rel}' — adding to singletons")
            singletons.append(target_rel)
            skip_as_target.add(target_rel)
            continue

        llm_canonical = result["canonical_name"].strip()
        matches       = result.get("matches", [])
        all_relations = [target_rel] + [m for m in matches if m in relations]

        existing = None
        for r in all_relations:
            if r in relation_to_canonical:
                existing = relation_to_canonical[r]
                break

        final_canonical = existing if existing else llm_canonical

        for r in all_relations:
            relation_to_canonical[r] = final_canonical

        if final_canonical not in canonical_to_group:
            canonical_to_group[final_canonical] = set()
        canonical_to_group[final_canonical].update(all_relations)

        for m in matches:
            skip_as_target.add(m)

        skip_as_target.add(target_rel)
        logger.info(
            f"'{target_rel}' + {matches} → '{final_canonical}' | "
            f"{result.get('reasoning', '')}"
        )

    # Normalize singletons via LLM
    if singletons:
        logger.info(f"Normalizing {len(singletons)} singleton relations...")
        normalized = _normalize_singletons(
            singletons, relation_definitions, triples, article_title
        )
        relation_to_canonical.update(normalized)

    # Any relation still not mapped → maps to itself
    for rel in relations:
        if rel not in relation_to_canonical:
            relation_to_canonical[rel] = rel

    # Apply to triples
    resolved_triples = [
        {
            "subject":  t["subject"],
            "relation": relation_to_canonical.get(t["relation"], t["relation"]),
            "object":   t["object"]
        }
        for t in triples
    ]

    merged = sum(1 for k, v in relation_to_canonical.items() if k != v)
    logger.info(f"Relation canonicalization done: {merged} relations merged/normalized")
    return resolved_triples, relation_to_canonical