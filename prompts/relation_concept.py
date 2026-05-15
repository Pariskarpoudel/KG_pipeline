SYSTEM_PROMPT = """You are a knowledge graph relation conceptualizer. For each relation, generate at least 3 abstract concept phrases that represent its semantic category at varying levels of abstraction.

Rules:
- Generate at least 3 phrases per relation at different abstraction levels — from specific to general.
  e.g. "marriedTo" → "Spouse" → "Marital Relation"
- Phrases must be 1-4 words only.
- Do not include the relation name itself as a concept.
- Do not repeat the same phrase for the same relation.
- Concepts must represent the CATEGORY or TYPE of the relationship — not the entities involved.

Output JSON only. No explanation outside JSON."""


def build_user_prompt(
    article_title: str,
    relations_with_context: list[dict],  # [{"relation": str, "definition": str, "example": dict}]
) -> str:
    relations_block = "\n".join(
        f'- Relation: "{r["relation"]}"\n'
        f'  Definition: "{r["definition"]}"\n'
        f'  Example triple: ["{r["example"]["subject"]}", "{r["example"]["relation"]}", "{r["example"]["object"]}"]'
        for r in relations_with_context
    )

    return f"""Article: {article_title}

Example:
Relation: "discovered"
Definition: "The subject entity found or identified the thing specified by the object entity."
Example triple: ["Marie Curie", "discovered", "Polonium"]
Output: ["Discovery", "Scientific Achievement", "Factual Relation"]

Now conceptualize the following relations:
{relations_block}

Output format:
{{
  "<relation_1>": ["<specific>", "<broader>", "<general>"],
  "<relation_2>": ["<specific>", "<broader>", "<general>"],
  ...
}}"""