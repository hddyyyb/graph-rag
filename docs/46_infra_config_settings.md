# Settings

## Overview

`Settings` is the **single source of truth configuration object** for the entire GraphRAG system.

It is implemented using Pydantic `BaseModel` and is responsible for:

- defining all runtime configuration
- validating configuration correctness
- normalizing user input
- enforcing cross-field constraints
- enabling deterministic backend switching

This class is the foundation of the system’s **Clean Architecture configuration layer**. :contentReference[oaicite:0]{index=0}

---

## Design Goals

The `Settings` class is designed to achieve:

- ✅ Strong typing (via `Literal`, `Field`)
- ✅ Safe defaults (system runs out-of-the-box)
- ✅ Input normalization (case-insensitive configs)
- ✅ Cross-field validation (prevent invalid runtime states)
- ✅ Centralized configuration (no scattered config usage)
- ✅ Compatibility with DI container

---

## Core Fields

### 1. Application

'''python
app_name: str = "graph-rag"
log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
'''

- `app_name`: logical application identifier
- `log_level`: controls logging verbosity

---

### 2. Retrieval Defaults

'''python
vector_top_k: int = Field(default=5, ge=1)
graph_top_k: int = Field(default=5, ge=1)
'''

- defines default retrieval limits
- enforced to be ≥ 1

---

### 3. Chunking Configuration

'''python
chunk_size: int = Field(default=400, ge=1)
chunk_overlap: int = Field(default=50, ge=0)
'''

- controls text splitting during ingestion
- overlap must be smaller than chunk size (validated later)

---

### 4. Backend Selection (Core Feature)

'''python
embedding_backend: Literal["sentence_transformer", "fake", "hash"]
vector_store_backend: Literal["memory", "sqlite"]
graph_store_backend: Literal["memory", "neo4j"]
llm_backend: Literal["fake", "local", "openai"]
'''

These fields define **which implementation is used at runtime**.

This enables:

- switching infrastructure without changing code
- test vs production separation
- consistent DI container wiring

---

### 5. Embedding Configuration

'''python
embedding_model_name_or_path: str
normalize_embeddings: bool
'''

- supports local model path or HF model
- optional normalization for cosine similarity

---

### 6. SQLite Configuration

'''python
sqlite_path: str = ":memory:"
'''

- `:memory:` for ephemeral testing
- file path for persistence

---

### 7. Graph Retrieval Configuration

'''python
graph_expand_hops: int = 1
graph_expand_per_term_limit: int = Field(default=2, ge=1)
graph_max_expanded_terms: int = Field(default=10, ge=1)

graph_direct_hit_weight: float = Field(default=1.0, gt=0)
graph_expanded_hit_weight: float = Field(default=0.5, ge=0)
'''

Controls GraphRAG behavior:

- expansion depth (currently 1-hop)
- expansion limits
- scoring weights

Key idea:

- direct match > expanded match

---

### 8. Hybrid Retrieval Fusion

'''python
fusion_alpha: float = Field(default=0.5, ge=0, le=1)
fusion_beta: float = Field(default=0.5, ge=0, le=1)
'''

Defines final scoring:

'''python
final_score = alpha * vector_score + beta * graph_score
'''

---

### 9. Neo4j Configuration

'''python
neo4j_uri: str
neo4j_username: str
neo4j_password: str
neo4j_database: str | None
'''

Used when:

'''python
graph_store_backend == "neo4j"
'''

---

### 10. LLM Configuration

#### Local LLM

'''python
local_llm_base_url: str
local_llm_model: str
'''

#### OpenAI

'''python
openai_api_key: str | None
openai_model: str
openai_instructions: str
'''

---

## Input Normalization (field_validator)

'''python
@field_validator(..., mode="before")
def normalize_lower(cls, v: str):
    if isinstance(v, str):
        return v.strip().lower()
    return v
'''

### Purpose

- removes whitespace
- converts to lowercase
- ensures consistent config values

### Example

'''python
Settings(graph_store_backend=" Neo4J ")
→ "neo4j"
'''

This prevents subtle bugs caused by user input variations. :contentReference[oaicite:1]{index=1}

---

## Cross-field Validation (model_validator)

'''python
@model_validator(mode="after")
def validate_cross_fields(self):
    ...
'''

This runs **after all fields are parsed and normalized**.

### Rules enforced

#### 1. Chunk constraint

'''python
chunk_overlap < chunk_size
'''

#### 2. SQLite requirement

'''python
if vector_store_backend == "sqlite":
    sqlite_path must exist
'''

#### 3. Neo4j requirement

'''python
if graph_store_backend == "neo4j":
    uri + username + password required
'''

#### 4. OpenAI requirement

'''python
if llm_backend == "openai":
    openai_api_key required
'''

#### 5. Graph scoring constraint

'''python
expanded_weight <= direct_weight
'''

This ensures:

- graph expansion never outweighs direct matches

:contentReference[oaicite:2]{index=2}

---

## Configuration Flow (Critical)

'''text
settings_override (API)
        ↓
build_settings()
        ↓
Settings (validated object)
        ↓
build_container(settings)
        ↓
All components use Settings
'''

This guarantees:

- no raw dict usage
- no inconsistent config states
- full runtime determinism

:contentReference[oaicite:3]{index=3}

---

## Role in Clean Architecture

'''text
Infra Layer
    ↓
Settings
    ↓
Container (Composition Root)
    ↓
Application Services
'''

Key idea:

- Services do NOT read environment variables
- Services do NOT parse config
- Services only consume already-validated config

:contentReference[oaicite:4]{index=4}

---

## Reliability Pipeline

'''text
User Input (untrusted)
        ↓
field_validator (normalize)
        ↓
model_validator (validate)
        ↓
Safe Settings Object
'''

This ensures:

- all runtime config is **correct before execution**
- no runtime surprises
- fail-fast behavior

:contentReference[oaicite:5]{index=5}

---

## Example Usage

### Basic

'''python
settings = Settings()
'''

### Override config

'''python
settings = Settings(
    vector_store_backend="sqlite",
    sqlite_path="data.db",
    graph_store_backend="neo4j",
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password",
)
'''

### Invalid config (raises error)

'''python
Settings(
    chunk_size=100,
    chunk_overlap=200
)
# ❌ ValueError
'''

---

## Strengths

- strong validation guarantees
- backend switching without code change
- test-friendly (override config easily)
- consistent with Clean Architecture
- production-ready configuration pattern

---

## Limitations

- no environment variable auto-loading (yet)
- no config file support (YAML/JSON)
- no dynamic reload
- fusion_alpha + fusion_beta not enforced to sum to 1

---

## Suggested Improvements

- support `.env` loading
- add config file support
- enforce alpha + beta normalization
- introduce config profiles (dev / prod / test)
- add schema export for documentation

---

## Summary

`Settings` is the **configuration backbone** of the GraphRAG system.

It transforms:

- messy user input

into:

- validated, normalized, reliable runtime configuration

and enables:

- clean dependency injection
- safe backend switching
- deterministic system behavior

This is a key component that elevates the project from a prototype to an **engineering-grade system**. :contentReference[oaicite:6]{index=6}