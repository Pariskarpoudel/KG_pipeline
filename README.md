# WikiPipeline
An automated Knowledge Graph construction pipeline from Wikipedia articles using LLMs and semantic embeddings.

## Project Structure
```
wikigraph-pipeline/
│
├── .env                        ← API keys (create from .env.example)
├── .env.example                ← API keys template
├── requirements.txt            ← dependencies
├── main.py                     ← runs full pipeline
│
├── prompts/
│   ├── oie.py                  ← Step 2: triple extraction prompt
│   ├── entity_resolution.py   ← Step 4: entity resolution prompt
│   ├── relation_definition.py ← Step 5: relation definition prompt
│   ├── relation_canon.py      ← Step 6: relation canonicalization prompt
│   ├── entity_concept.py      ← Step 7a: entity conceptualization prompt
│   └── relation_concept.py    ← Step 7b: relation conceptualization prompt
│
├── pipeline/
│   ├── chunker.py              ← Step 1: chunk article into paragraphs
│   ├── extractor.py            ← Step 2: extract triples from chunks
│   ├── deduplicator.py         ← Step 3: remove duplicate triples
│   ├── entity_resolver.py      ← Step 4: resolve entity variants
│   ├── relation_definer.py     ← Step 5: define relations
│   ├── relation_canonicalizer.py ← Step 6: canonicalize relations
│   ├── schema_inducer.py       ← Step 7: induce schema concepts
│   └── graph_assembler.py      ← Step 8: assemble final KG
│
├── utils/
│   ├── llm.py                  ← LLM API wrapper (Groq)
│   ├── embedder.py             ← sentence embedding wrapper
│   └── parser.py               ← JSON output parser
│
├── data/
│   ├── raw/                    ← input Wikipedia articles (.txt)
│   │   ├── article_1.txt
│   │   ├── article_2.txt
│   │   ├── article_3.txt
│   │   ├── article_4.txt
│   │   └── article_5.txt
│   └── output/                 ← generated KG JSON files
│
└── tools/
    └── load_neo4j.py           ← load KG into Neo4j AuraDB
```

## Setup

**1. Clone the repo:**
```bash
git clone https://github.com/Pariskarpoudel/wikigraph-pipeline
cd wikigraph-pipeline
```

**2. Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set up API keys:**

Create a `.env` file in the root of the project:
```
GROQ_API_KEY=your_groq_api_key_here
NEO4J_URI=your_neo4j_uri_here
NEO4J_USERNAME=your_neo4j_username_here
NEO4J_PASSWORD=your_neo4j_password_here
```

Get your free Groq API key at: `https://console.groq.com`
Get your free Neo4j AuraDB credentials at: `https://neo4j.com/cloud/aura`

## Running the Pipeline

**1. Wiki: run a single article (.txt)**
```bash
python main.py data/raw/article_5.txt
```

**2. Wiki: run JSONL bulk mode**
```bash
# uses config.WIKI_JSONL_INPUT_FILE by default
python main.py --jsonl

# or provide a custom JSONL path
python main.py --jsonl path/to/articles.jsonl
```

**3. Essay: run JSONL bulk mode**
```bash
# uses config.ESSAY_JSONL_INPUT_FILE by default
python main.py --essay

# or provide a custom JSONL path
python main.py --essay path/to/essays.jsonl
```

**4. Essay: run a single essay (.txt)**
```bash
python main.py --essay-txt data/mine_raw/essay1.txt
```

**Outputs**
- All output files are saved to `data/output/`.

## Global Config (config.py)

All major settings are centralized in `config.py`:

```python
LLM_DEFAULT_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
RELATION_DEFINITION_BATCH_SIZE = 10
...
```

To change models or batch settings, edit only `config.py`.

## Neo4j Visualization (Optional)

Visualize the generated KG in Neo4j AuraDB.

**1. Create a free Neo4j AuraDB instance:**
- Go to `https://neo4j.com/cloud/aura`
- Sign up and click **"Create a free instance"**
- Copy the credentials shown — URI, username, password 

**2. Add Neo4j credentials to `.env`**

**3. Load a KG into Neo4j:**
```bash
python tools/load_neo4j.py data/output/article_5.json

```

**4. Visualize:**
- Go to your AuraDB instance
- Click **"Open"** → Neo4j Browser opens
- Run this query to peek the graph:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```
