SYSTEM_PROMPT = """You are a knowledge graph relation definer. For each unique relation in the given triples, write a concise general definition.
Definitions must be general enough to apply to other entities beyond those listed.
Pay attention to direction — subject → relation → object.
Output JSON only. No explanation outside JSON."""


def build_user_prompt(
    article_title: str,
    relations_with_examples: list[dict]  # [{"relation": str, "example": dict}]
) -> str:
    # Format each relation with its example triple
    relations_block = "\n".join(
        f'- Relation: "{r["relation"]}" | Example: ({r["example"]["subject"]}, {r["example"]["relation"]}, {r["example"]["object"]})'
        for r in relations_with_examples
    )

    return f"""Article: {article_title}

Example:
Triple: ["Marie Curie", "discovered", "Polonium"]
Output: {{"discovered": "The subject entity found or identified the thing specified by the object entity."}}

Define a concise general definition for each of the following relations:
{relations_block}

Output format:
{{
  "relation_name": "definition...",
  "relation_name": "definition...",
  ...
}}"""