SYSTEM_PROMPT = """You are a knowledge graph relation canonicalizer.
Given a target relation with its definition and example triple, and candidate relations with their definitions and example triples, identify which candidates have essentially the same semantic meaning as the target relation (i.e., they are interchangeable in the knowledge graph).
Output JSON only. No explanation outside JSON.

Rules:
- canonical_name MUST be exactly one of: the target relation OR one of the candidate relation names.
- Never invent, modify, or combine relation names.
- Only match relations that are truly interchangeable in meaning.
- If unsure, output empty matches."""


def _format_example(triple: dict) -> str:
    return f"[{triple['subject']}, {triple['relation']}, {triple['object']}]"


def build_user_prompt(
    article_title: str,
    target_relation: str,
    target_definition: str,
    target_example: dict,
    candidates: list[dict],  # [{"relation": str, "definition": str, "example": dict}]
) -> str:
    labels = "ABCDEFGHIJ"

    candidate_lines = "\n".join(
        f'{labels[i]}. "{c["relation"]}"\n'
        f'   Definition: "{c["definition"]}"\n'
        f'   Example triple: {_format_example(c["example"])}'
        for i, c in enumerate(candidates)
    )

    return f"""Article: {article_title}

Target relation: "{target_relation}"
Definition: "{target_definition}"
Example triple: {_format_example(target_example)}

Candidates:
{candidate_lines}

Which candidates match the "{target_relation}" (i.e., have essentially the same semantic meaning)?
Output format:
If there are matches:
{{
  "matches": ["<matched_relation>", "<matched_relation>"],
  "canonical_name": "<the most concise, representative relation name among target and all matches>",
  "reasoning": "<one line>"
}}
If no candidates match:
{{
  "matches": [],
  "canonical_name": "<normalized/concise form of target relation>",
  "reasoning": "<one line>"
}}"""