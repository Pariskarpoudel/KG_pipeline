import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def deduplicate_triples(triples: List[Dict]) -> List[Dict]:
    """
    Remove exact duplicate triples (case-sensitive).
    Only strips whitespace — preserves original casing for Steps 4-6.
    """
    seen   = set()
    unique = []

    for triple in triples:
        key = (
            triple["subject"].strip(),
            triple["relation"].strip(),
            triple["object"].strip()
        )
        if key not in seen:
            seen.add(key)
            unique.append(triple)

    removed = len(triples) - len(unique)
    logger.info(f"Deduplication: {len(triples)} → {len(unique)} triples ({removed} removed)")
    return unique