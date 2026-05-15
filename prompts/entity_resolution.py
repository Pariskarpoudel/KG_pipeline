SYSTEM_PROMPT = """You are a knowledge graph entity resolver.
Given a target entity with its context triples and candidate entities, identify which candidates refer to the same real-world entity as the target.
Output JSON only. No explanation outside JSON.

### Constraints
- Only match entities that refer to the exact same real-world entity.
- If unsure, output empty matches.
"""


def _format_triples(triples: list[dict]) -> str:
    """Format triples list as readable string for prompt."""
    if not triples:
        return "none"
    return " | ".join(
        f"({t['subject']}, {t['relation']}, {t['object']})"
        for t in triples[:3]  # max 3 context triples per entity
    )


def build_user_prompt(
    article_title: str,
    target_entity: str,
    target_triples: list[dict],
    candidates: list[dict],  # [{"name": str, "triples": list[dict]}]
) -> str:
    candidate_lines = "\n".join(
        f'- "{c["name"]}" | Context: {_format_triples(c["triples"])}'
        for c in candidates
    )

    return f"""Article: {article_title}
Target entity: "{target_entity}"
Context triples:
{_format_triples(target_triples)}
Candidates:
{candidate_lines}
Which candidates match the "{target_entity}" (i.e., refer to the same real-world entity)?
Output format:
If there are matches:
{{
  "matches": ["<matched_entity>", "<matched_entity>"],
  "canonical_name": "<the best representative entity name among all matches including target>",
  "reasoning": "<one line>"
}}
If no candidates match, output:
{{
  "matches": [],
  "canonical_name": "{target_entity}",
  "reasoning": "<one line>"
}}"""