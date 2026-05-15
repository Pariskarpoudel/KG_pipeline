import os
import json
import logging
from pathlib import Path
from pipeline.chunker import chunk_article, chunk_wiki_record, chunk_essay
from pipeline.extractor import extract_all_triples
from pipeline.deduplicator import deduplicate_triples
from pipeline.entity_resolver import resolve_entities
from pipeline.relation_definer import define_relations
from pipeline.relation_canonicalizer import canonicalize_relations
from pipeline.schema_inducer import induce_schema
from pipeline.graph_assembler import assemble_graph, save_graph
from pipeline.progress_tracker import load_progress, save_progress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

DATASET = "wikigraphs"  # or "wikigraphs"

def run_pipeline(article_path: str, output_dir: str = "data/output/raw") -> dict:
    """
    Run full KG pipeline on a single WikiGraphs .txt file.
    Title is parsed from the level-1 heading inside the file.

    Usage:
        python main.py data/raw/article_1.txt
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: {article_path}")
    logger.info(f"{'='*60}")

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking article...")
    chunks = chunk_article(article_path)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from {article_path}")

    article_title = chunks[0]["article_title"]
    logger.info(f"  → Article: '{article_title}'")

    # ── Step 2: Triple Extraction ─────────────────────────────
    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    # ── Step 3: Deduplication ─────────────────────────────────
    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    # ── Step 4: Entity Resolution ─────────────────────────────
    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, article_title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    # ── Step 5: Relation Definition ───────────────────────────
    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, article_title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    # ── Step 6: Relation Canonicalization ─────────────────────
    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    # ── Step 7: Schema Induction ──────────────────────────────
    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")

    # ── Step 8: Graph Assembly ────────────────────────────────
    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = article_title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{article_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")

    return kg


def run_pipeline_essay_txt(filepath: str, output_dir: str = "data/output/raw") -> dict:
    """
    Run full KG pipeline on a single MINE-1 .txt file.
    Title is taken from the filename (without extension).

    Usage:
        python main.py --mine-txt data/raw/mine_essay.txt
    """
    title = Path(filepath).stem

    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: {filepath} (title: '{title}')")
    logger.info(f"{'='*60}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    record = {
        "essay_title":   title,
        "essay_content": content,
    }

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking essay...")
    chunks = chunk_essay(record)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from {filepath}")

    # ── Step 2: Triple Extraction ─────────────────────────────
    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    # ── Step 3: Deduplication ─────────────────────────────────
    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    # ── Step 4: Entity Resolution ─────────────────────────────
    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    # ── Step 5: Relation Definition ───────────────────────────
    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    # ── Step 6: Relation Canonicalization ─────────────────────
    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    # ── Step 7: Schema Induction ──────────────────────────────
    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")

    # ── Step 8: Graph Assembly ────────────────────────────────
    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")
    
    return kg


def run_pipeline_wiki(record: dict, output_dir: str = "data/output/wiki") -> dict:
    """
    Run full KG pipeline on a single WikiGraphs JSONL record.
    Record keys: id, title, text.
    """
    article_title = record["title"]

    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: '{article_title}'")
    logger.info(f"{'='*60}")

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking article...")
    chunks = chunk_wiki_record(record)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from '{article_title}'")

    # ── Step 2: Triple Extraction ─────────────────────────────
    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    # ── Step 3: Deduplication ─────────────────────────────────
    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    # ── Step 4: Entity Resolution ─────────────────────────────
    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, article_title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    # ── Step 5: Relation Definition ───────────────────────────
    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, article_title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    # ── Step 6: Relation Canonicalization ─────────────────────
    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    # ── Step 7: Schema Induction ──────────────────────────────
    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")
    
    # ── Step 8: Graph Assembly ────────────────────────────────
    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = article_title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{article_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")

    return kg


def run_pipeline_essay(record: dict, output_dir: str = "data/output/mine1") -> dict:
    """
    Run full KG pipeline on a single MINE-1 JSONL record.
    Record keys: essay_title, essay_content.
    """
    essay_title = record["essay_title"]

    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: '{essay_title}'")
    logger.info(f"{'='*60}")

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking essay...")
    chunks = chunk_essay(record)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from '{essay_title}'")

    # ── Step 2: Triple Extraction ─────────────────────────────
    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    # ── Step 3: Deduplication ─────────────────────────────────
    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    # ── Step 4: Entity Resolution ─────────────────────────────
    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, essay_title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    # ── Step 5: Relation Definition ───────────────────────────
    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, essay_title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    # ── Step 6: Relation Canonicalization ─────────────────────
    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, essay_title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    # ── Step 7: Schema Induction ──────────────────────────────
    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, essay_title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")

    # ── Step 8: Graph Assembly ────────────────────────────────
    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = essay_title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{essay_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")

    return kg


def run_all(
    jsonl_path: str = "data/wiki/articles_train.jsonl",
    output_dir: str = "data/output/wiki"
):
    """
    Run pipeline on all WikiGraphs articles in jsonl_path.
    Resumable — tracked by article id via progress.json.

    Usage:
        python main.py --wiki
        python main.py --wiki data/wiki/articles_train.jsonl
    """
    if not os.path.exists(jsonl_path):
        logger.warning(f"File not found: {jsonl_path}")
        return

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        logger.warning(f"No records found in {jsonl_path}")
        return

    # Progress tracked by id
    processed = load_progress(output_dir)
    remaining = [r for r in records if str(r.get("id", "")) not in processed]

    logger.info(f"Found {len(records)} articles | "
                f"{len(processed)} already done | "
                f"{len(remaining)} remaining")

    if not remaining:
        logger.info("All articles already processed.")
        return

    results = []
    for i, record in enumerate(remaining, 1):
        article_id    = str(record.get("id", f"article_{i}"))
        article_title = record.get("title", article_id)
        logger.info(f"\nProcessing article {i}/{len(remaining)}: '{article_title}' (id: {article_id})")
        try:
            kg = run_pipeline_wiki(record, output_dir)
            save_progress(output_dir, article_id, kg, "wiki_output.jsonl")
            results.append({
                "article":   kg["article_title"],
                "nodes":     len(kg["nodes"]),
                "relations": len(kg["relations"]),
                "triples":   len(kg["triples"]),
                "status":    "success"
            })
        except Exception as e:
            logger.error(f"Failed on '{article_title}' (id: {article_id}): {e}")
            results.append({"article": article_title, "status": "failed", "error": str(e)})

    _print_summary(results)


def run_all_mine(
    jsonl_path: str = "data/mine1/mine_train.jsonl",
    output_dir: str = "data/output/mine1"
):
    """
    Run pipeline on all MINE-1 essays in jsonl_path.
    Resumable — tracked by essay_title via progress.json.

    Usage:
        python main.py --mine
        python main.py --mine data/mine1/mine_train.jsonl
    """
    if not os.path.exists(jsonl_path):
        logger.warning(f"File not found: {jsonl_path}")
        return

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        logger.warning(f"No records found in {jsonl_path}")
        return

    # Progress tracked by essay_title
    processed = load_progress(output_dir)
    remaining = [r for r in records if r.get("essay_title", "") not in processed]

    logger.info(f"Found {len(records)} essays | "
                f"{len(processed)} already done | "
                f"{len(remaining)} remaining")

    if not remaining:
        logger.info("All essays already processed.")
        return

    results = []
    for i, record in enumerate(remaining, 1):
        title = record.get("essay_title", f"essay_{i}")
        logger.info(f"\nProcessing essay {i}/{len(remaining)}: '{title}'")
        try:
            kg = run_pipeline_essay(record, output_dir)
            save_progress(output_dir, title, kg, "mine_output.jsonl")
            results.append({
                "article":   kg["article_title"],
                "nodes":     len(kg["nodes"]),
                "relations": len(kg["relations"]),
                "triples":   len(kg["triples"]),
                "status":    "success"
            })
        except Exception as e:
            logger.error(f"Failed on '{title}': {e}")
            results.append({"article": title, "status": "failed", "error": str(e)})

    _print_summary(results)


def _print_summary(results: list):
    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE SUMMARY")
    logger.info(f"{'='*60}")
    for r in results:
        if r["status"] == "success":
            logger.info(
                f"  ✅ {r['article']:30s} | "
                f"nodes: {r['nodes']:4d} | "
                f"relations: {r['relations']:3d} | "
                f"triples: {r['triples']:4d}"
            )
        else:
            logger.info(f"  ❌ {r['article']:30s} | FAILED: {r['error']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "--mine-txt":
        # Single MINE-1 .txt file, title from filename
        # python main.py --mine-txt data/raw/mine_essay.txt
        run_pipeline_essay_txt(sys.argv[2])

    elif len(sys.argv) >= 2 and sys.argv[1] == "--mine":
        # Run all MINE-1 essays from JSONL
        # python main.py --mine
        # python main.py --mine data/mine1/mine_train.jsonl
        path = sys.argv[2] if len(sys.argv) == 3 else "data/mine1/mine_train.jsonl"
        run_all_mine(jsonl_path=path)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--wiki":
        # Run all WikiGraphs articles from JSONL
        # python main.py --wiki
        # python main.py --wiki data/wiki/articles_train.jsonl
        path = sys.argv[2] if len(sys.argv) == 3 else "data/wiki/articles_train.jsonl"
        run_all(jsonl_path=path)

    elif len(sys.argv) == 2:
        # Single WikiGraphs .txt file
        # python main.py data/raw/article_1.txt
        run_pipeline(sys.argv[1])

    else:
        print("Usage:")
        print("  python main.py data/raw/article_1.txt                # single WikiGraphs .txt")
        print("  python main.py --mine-txt data/raw/mine_essay.txt    # single MINE-1 .txt")
        print("  python main.py --wiki                                 # run all WikiGraphs")
        print("  python main.py --wiki data/wiki/articles_train.jsonl")
        print("  python main.py --mine                                 # run all MINE-1")
        print("  python main.py --mine data/mine1/mine_train.jsonl")