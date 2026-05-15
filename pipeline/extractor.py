import logging
from typing import List, Dict
from utils.llm import llm_call
from utils.parser import parse_llm_json
from prompts.oie import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _validate_triples(data: list) -> List[Dict]:
    """Keep only valid triples — all three keys present and non-empty."""
    valid = []
    for item in data:
        if (
            isinstance(item, dict)
            and all(k in item for k in ["subject", "relation", "object"])
            and all(isinstance(item[k], str) and item[k].strip() for k in ["subject", "relation", "object"])
        ):
            valid.append({
                "subject":  item["subject"].strip(),
                "relation": item["relation"].strip(),
                "object":   item["object"].strip(),
            })
    return valid


def extract_triples_from_chunk(chunk: Dict) -> List[Dict]:
    """
    Extract triples from a single chunk.
    Returns list of validated triple dicts.
    """
    user_prompt = build_user_prompt(
        article_title=chunk["article_title"],
        section_heading=chunk["section_path"],
        chunk_text=chunk["chunk_text"]
    )

    raw = llm_call(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    data = parse_llm_json(raw, expected_type="list")

    if data is None:
        logger.warning(f"Chunk {chunk['chunk_index']} — parse failed, returning []")
        return []

    triples = _validate_triples(data)
    logger.info(f"Chunk {chunk['chunk_index']} ({chunk['section_path']}) → {len(triples)} triples")
    return triples


def extract_all_triples(chunks: List[Dict]) -> List[Dict]:
    """
    Run triple extraction over all chunks.
    Returns merged flat list of all triples.
    """
    all_triples = []

    for chunk in chunks:
        triples = extract_triples_from_chunk(chunk)
        all_triples.extend(triples)

    logger.info(f"Total triples extracted: {len(all_triples)}")
    return all_triples