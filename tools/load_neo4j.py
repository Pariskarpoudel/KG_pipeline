# tools/load_neo4j.py
import json
import os
import sys
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_kg_to_neo4j(kg_path: str):
    """
    Load KG JSON into Neo4j AuraDB.
    Loads nodes, concepts, triples, relation definitions and concepts.
    """
    with open(kg_path, encoding="utf-8") as f:
        kg = json.load(f)

    uri      = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, username, password]):
        raise ValueError("NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD must be set in .env")

    driver = GraphDatabase.driver(uri, auth=(username, password))

    with driver.session() as session:

        # ── Clear existing data ────────────────────────────
        logger.info("Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")

        # ── Create nodes ───────────────────────────────────
        logger.info(f"Creating {len(kg['nodes'])} nodes...")
        for node_name, data in kg["nodes"].items():
            concepts = data.get("concepts", [])
            label    = "Entity" if concepts else "Literal"
            session.run(
                f"MERGE (n:{label} {{name: $name}}) "
                f"SET n.concepts = $concepts",
                name     = node_name,
                concepts = concepts
            )

        # ── Create relationships from triples ──────────────
        logger.info(f"Creating {len(kg['triples'])} relationships...")
        relation_data = kg.get("relations", {})

        for t in kg["triples"]:
            subj     = t["subject"]
            obj      = t["object"]
            rel_name = t["relation"]

            rel_info     = relation_data.get(rel_name, {})
            definition   = rel_info.get("definition", "")
            rel_concepts = rel_info.get("concepts", [])

            # Sanitize relation name for Cypher
            rel_type = (
                rel_name
                .replace(" ", "_")
                .replace("-", "_")
                .replace("'", "")
                .replace("/", "_")
                .upper()
            )

            session.run(
                f"""
                MATCH (a {{name: $subj}})
                MATCH (b {{name: $obj}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r.relation_name = $rel_name,
                    r.definition    = $definition,
                    r.concepts      = $rel_concepts
                """,
                subj         = subj,
                obj          = obj,
                rel_name     = rel_name,
                definition   = definition,
                rel_concepts = rel_concepts
            )

    driver.close()

    logger.info(f"✅ Done — loaded '{kg['article_title']}' into Neo4j")
    logger.info(f"   Nodes:         {len(kg['nodes'])}")
    logger.info(f"   Relationships: {len(kg['triples'])}")
    logger.info(f"   Relations:     {len(kg['relations'])}")


if __name__ == "__main__":

    if len(sys.argv) == 2:
        # Single file mode
        # python tools/load_neo4j.py data/output/article.json
        load_kg_to_neo4j(sys.argv[1])

    else:
        # Load all KGs in data/output/
        # python tools/load_neo4j.py
        output_dir = "data/output"
        files = [
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.endswith(".json")
        ]

        if not files:
            logger.warning(f"No JSON files found in {output_dir}")
        else:
            logger.info(f"Found {len(files)} KG files to load...")
            for path in files:
                logger.info(f"\nLoading: {path}")
                try:
                    load_kg_to_neo4j(path)
                except Exception as e:
                    logger.error(f"Failed: {path} — {e}")



# if we are doing across multiple articles ,then creating a article node , and for all entities  in that article , we can create a relationship between article and entity node [HAS ENTITY]. 
# # tools/load_neo4j.py
# import json
# import os
# import logging
# from neo4j import GraphDatabase
# from dotenv import load_dotenv

# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# def load_kg_to_neo4j(kg_path: str):
#     """
#     Load KG JSON into Neo4j AuraDB.
#     Full utilization — nodes, concepts, triples, relation definitions.
#     """
#     # Load KG
#     with open(kg_path, encoding="utf-8") as f:
#         kg = json.load(f)

#     uri      = os.getenv("NEO4J_URI")
#     username = os.getenv("NEO4J_USERNAME")
#     password = os.getenv("NEO4J_PASSWORD")

#     if not all([uri, username, password]):
#         raise ValueError("NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD must be set in .env")

#     driver = GraphDatabase.driver(uri, auth=(username, password))

#     with driver.session() as session:

#         # ── Clear existing data ────────────────────────────
#         logger.info("Clearing existing data...")
#         session.run("MATCH (n) DETACH DELETE n")

#         # ── Create Article node ────────────────────────────
#         logger.info(f"Creating article node: {kg['article_title']}")
#         session.run(
#             "MERGE (a:Article {title: $title})",
#             title=kg["article_title"]
#         )

#         # ── Create entity nodes ────────────────────────────
#         logger.info(f"Creating {len(kg['nodes'])} nodes...")
#         for node_name, data in kg["nodes"].items():
#             concepts = data.get("concepts", [])
#             # Determine label — entity or literal
#             label = "Entity" if concepts else "Literal"
#             session.run(
#                 f"MERGE (n:{label} {{name: $name}}) "
#                 f"SET n.concepts = $concepts",
#                 name=node_name,
#                 concepts=concepts
#             )

#         # ── Create relationships from triples ──────────────
#         logger.info(f"Creating {len(kg['triples'])} relationships...")
#         relation_data = kg.get("relations", {})

#         for t in kg["triples"]:
#             subj     = t["subject"]
#             obj      = t["object"]
#             rel_name = t["relation"]

#             # Get relation definition and concepts if available
#             rel_info    = relation_data.get(rel_name, {})
#             definition  = rel_info.get("definition", "")
#             rel_concepts = rel_info.get("concepts", [])

#             # Sanitize relation name for Cypher
#             rel_type = (
#                 rel_name
#                 .replace(" ", "_")
#                 .replace("-", "_")
#                 .replace("'", "")
#                 .replace("/", "_")
#                 .upper()
#             )

#             session.run(
#                 f"""
#                 MATCH (a {{name: $subj}})
#                 MATCH (b {{name: $obj}})
#                 MERGE (a)-[r:{rel_type}]->(b)
#                 SET r.relation_name = $rel_name,
#                     r.definition    = $definition,
#                     r.concepts      = $rel_concepts
#                 """,
#                 subj        = subj,
#                 obj         = obj,
#                 rel_name    = rel_name,
#                 definition  = definition,
#                 rel_concepts = rel_concepts
#             )

#         # ── Connect nodes to Article ───────────────────────
#         logger.info("Connecting entities to article...")
#         session.run(
#             """
#             MATCH (a:Article {title: $title})
#             MATCH (n:Entity)
#             MERGE (a)-[:HAS_ENTITY]->(n)
#             """,
#             title=kg["article_title"]
#         )

#     driver.close()

#     logger.info(f"✅ Done — loaded '{kg['article_title']}' into Neo4j")
#     logger.info(f"   Nodes:         {len(kg['nodes'])}")
#     logger.info(f"   Relationships: {len(kg['triples'])}")
#     logger.info(f"   Relations:     {len(kg['relations'])}")


# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) == 2:
#         load_kg_to_neo4j(sys.argv[1])
#     else:
#         # Load all KGs in data/output/
#         output_dir = "data/output"
#         files = [
#             os.path.join(output_dir, f)
#             for f in os.listdir(output_dir)
#             if f.endswith(".json")
#         ]
#         if not files:
#             print("No JSON files found in data/output/")
#         else:
#             for path in files:
#                 logger.info(f"\nLoading: {path}")
#                 try:
#                     load_kg_to_neo4j(path)
#                 except Exception as e:
#                     logger.error(f"Failed: {path} — {e}")