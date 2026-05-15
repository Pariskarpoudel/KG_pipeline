SYSTEM_PROMPT = """You are a knowledge graph entity conceptualizer. For each entity, generate at least 3 abstract concept phrases that represent its type or category at varying levels of abstraction.

Rules:
- Generate at least 3 phrases per entity at different abstraction levels — from specific to general.
  e.g. "Chemist" → "Scientist" → "Academic"
- Phrases must be 1-3 words only.
- Do not include the entity name itself as a concept.
- Do not repeat the same phrase for the same entity.
- Concepts must represent the TYPE of the entity or its closest semantic categories.

Output JSON only. No explanation outside JSON."""


def _format_context(triples: list[dict]) -> str:
    return "\n".join(
        f'    ["{t["subject"]}", "{t["relation"]}", "{t["object"]}"]'
        for t in triples
    )


def build_user_prompt(
    article_title: str,
    entities_with_context: list[dict],  # [{"entity": str, "triples": list[dict]}]
) -> str:
    entities_block = "\n".join(
        f'- Entity: "{e["entity"]}"\n'
        f'  Context triples:\n'
        f'{_format_context(e["triples"]) if e["triples"] else "    (no context triples)"}'
        for e in entities_with_context
    )

    return f"""Article: {article_title}

Example:
Entity: "Polonium"
Context triples:
    ["Marie Curie", "discovered", "Polonium"],
    ["Polonium", "discovery year", "1898"]
Output: ["Chemical Element", "Radioactive Substance", "Matter"]

Now conceptualize the following entities:
{entities_block}

Output format:
{{
  "<entity_1>": ["<specific>", "<broader>", "<general>"],
  "<entity_2>": ["<specific>", "<broader>", "<general>"],
  ...
}}"""