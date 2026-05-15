# Global project configuration

# Paths — WikiGraphs
WIKI_DATA_FILE  = "data/wiki/articles_train.jsonl"
WIKI_OUTPUT_DIR = "data/output/wiki"

# Paths — MINE-1
MINE_DATA_FILE  = "data/mine1/mine_train.jsonl"
MINE_OUTPUT_DIR = "data/output/mine1"

RAW_OUTPUT_DIR = "data/output/raw"
 
LLM_BACKEND = "ollama"  # "ollama" or "groq"
OLLAMA_BASE_URL   = "http://localhost:11434/v1"
OLLAMA_MODEL      = "gemma3:27b"  

LLM_DEFAULT_MODEL = OLLAMA_MODEL  # for ollama
# LLM_DEFAULT_MODEL = "llama-3.3-70b-versatile"  # for groq
  
LLM_TEMPERATURE         = 0.0
LLM_MAX_RETRIES         = 3
LLM_RETRY_DELAY_SECONDS = 5
LLM_MAX_TOKENS = 2048

# Embedding
EMBEDDING_MODEL             = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_TRUST_REMOTE_CODE = True
EMBEDDING_NORMALIZE         = True

# Chunking — same settings for both datasets
CHUNK_TARGET_TOKENS = 400
CHUNK_MAX_TOKENS    = 550
CHUNK_MIN_TOKENS    = 50

# Per-step model selection
EXTRACTOR_MODEL                        = LLM_DEFAULT_MODEL
ENTITY_RESOLUTION_MODEL                = LLM_DEFAULT_MODEL
RELATION_DEFINITION_MODEL              = LLM_DEFAULT_MODEL
RELATION_CANONICALIZATION_MODEL        = LLM_DEFAULT_MODEL
RELATION_SINGLETON_NORMALIZATION_MODEL = LLM_DEFAULT_MODEL
ENTITY_CONCEPT_MODEL                   = LLM_DEFAULT_MODEL
RELATION_CONCEPT_MODEL                 = LLM_DEFAULT_MODEL

# Pipeline parameters
ENTITY_SIMILARITY_THRESHOLD    = 0.8
ENTITY_TOP_K_CANDIDATES        = 5
ENTITY_MAX_CONTEXT_TRIPLES     = 3
RELATION_SIMILARITY_THRESHOLD  = 0.8
RELATION_TOP_K_CANDIDATES      = 5
RELATION_SINGLETON_BATCH_SIZE  = 8
RELATION_DEFINITION_BATCH_SIZE = 8
SCHEMA_BATCH_SIZE              = 8