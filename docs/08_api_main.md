# api/main.py

This file is the application bootstrap and runtime assembly point of the GraphRAG system.

It is responsible for:

- building runtime settings
- selecting concrete backends
- constructing the dependency injection container
- creating the FastAPI application
- registering middleware
- registering exception handlers
- including route modules

---

## 1. Purpose of `api/main.py`

This file acts as the composition root of the API layer.

Instead of letting route files manually instantiate services or infrastructure objects, everything is constructed centrally here.

This design gives the project:

- better modularity
- better testability
- cleaner backend switching
- clearer runtime wiring

---

## 2. `build_settings`

```python
def build_settings(settings_override: dict | None = None) -> Settings:
    return Settings(**(settings_override or {}))
```

Creates a `Settings` object from optional override values.

### Responsibility

This function provides a unified configuration entry point for application startup.

It allows the system to:

- use default settings
- override settings in tests
- centralize configuration parsing into the `Settings` model

### Why it matters

By building the settings object first, the rest of the system can rely on one consistent source of runtime configuration.

---

## 3. `build_graph_store`

```python
def build_graph_store(settings: Settings):
```

Builds the graph store implementation according to runtime configuration.

### Supported Backends

- `memory` → `InMemoryGraphStore`
- `neo4j` → `Neo4jGraphStore`

### Responsibility

This function isolates graph backend selection from the rest of the application.

That means:

- the API layer does not need to know which graph backend is active
- the Application layer always depends on the same abstract graph behavior
- runtime backend switching is handled centrally

### Behavior

If `graph_store_backend == "memory"`:

- create an `InMemoryGraphStore`
- inject graph retrieval configuration such as:
  - `expand_per_term_limit`
  - `direct_hit_weight`
  - `expanded_hit_weight`
  - `max_expanded_terms`

If `graph_store_backend == "neo4j"`:

- create a Neo4j driver
- create a `Neo4jGraphStore`
- inject:
  - driver
  - database
  - schema initialization option
  - graph retrieval parameters

If the backend is unsupported, the function raises:

```python
ValueError(f"Unsupported graph_store_backend: {settings.graph_store_backend}")
```

---

## 4. `build_container`

```python
def build_container(settings: Settings) -> Dict[str, Any]:
```

Builds the application's dependency injection container.

This is the central composition root of the system.

It is responsible for constructing all major runtime components and wiring them together.

---

## 5. Container Construction Order

### 5.1 Initialize logging

```python
setup_logging(settings.log_level)
```

Logging is initialized early so later components can emit logs consistently.

---

### 5.2 Create foundational components

These components support cross-cutting concerns and shared runtime behavior.

#### Clock

```python
clock = SystemClock()
```

Used for time-related behavior.

#### Trace

```python
trace = SimpleTrace(clock=clock)
```

Used for request tracing, event recording, and observability.

#### Post Processor

```python
post_processor = DefaultRetrievalPostProcessor()
```

Used to finalize retrieved candidates before answer generation.

---

### 5.3 Create LLM backend

The LLM backend is selected by `settings.llm_backend`.

#### Supported options

- `fake`
- `local`
- `openai`

#### Fake backend

```python
llm = FakeLLM()
```

Useful for tests or lightweight runs.

#### Local backend

```python
llm = LocalLLM(
    base_url=settings.local_llm_base_url,
    model=settings.local_llm_model,
)
```

Used for locally hosted model inference.

#### OpenAI backend

```python
from graph_rag.infra.adapters import OpenAILLM

llm = OpenAILLM(
    api_key=settings.openai_api_key,
    model=settings.openai_model,
    instructions=settings.openai_instructions,
)
```

Used for remote LLM generation through the OpenAI backend.

If the backend is unknown, the function raises:

```python
ValueError(f"unknown llm_backend: {llm_backend}")
```

---

### 5.4 Create vector store backend

The vector store backend is selected by `settings.vector_store_backend`.

#### Supported options in current code

- `sqlite`
- memory fallback

#### SQLite backend

```python
sqlite_path = settings.sqlite_path
if not sqlite_path:
    raise ValueError("sqlite backend requires sqlite_path")
vector_store = SQLiteVectorStore(sqlite_path)
```

This backend supports persistent storage.

#### Memory backend

```python
vector_store = InMemoryVectorStore()
```

This backend is suitable for fast local testing and simple runtime experiments.

---

### 5.5 Create graph store backend

Graph store construction is delegated to:

```python
graph_store = build_graph_store(settings)
```

This keeps graph backend selection encapsulated in one place.

---

### 5.6 Create embedding backend

The embedding backend is selected by `settings.embedding_backend`.

#### Supported options

- `sentence_transformer`
- `hash`
- `fake`

#### SentenceTransformer backend

```python
embedder = SentenceTransformerEmbeddingProvider(
    model_name_or_path=settings.embedding_model_name_or_path,
)
```

This is the real embedding backend.

#### Hash backend

```python
embedder = HashEmbeddingProvider(dim=32)
```

Useful for deterministic lightweight tests.

#### Fake backend

```python
embedder = FakeEmbeddingV2()
```

Useful for mock-based or placeholder execution.

---

### 5.7 Create kernel

The current implementation uses:

```python
kernel = SimpleRAGKernel(llm=llm)
```

The kernel is responsible for answer generation using the selected LLM backend.

---

### 5.8 Create application services

After infrastructure components are ready, the application services are constructed.

#### IngestService

```python
ingest_service = IngestService(
    vector_store=vector_store,
    graph_store=graph_store,
    embedder=embedder,
    trace=trace,
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)
```

Responsible for the ingest pipeline:

- validate document input
- chunk text
- generate embeddings
- write vector data
- write graph data

#### QueryService

```python
query_service = QueryService(
    vector_store=vector_store,
    graph_store=graph_store,
    embedder=embedder,
    kernel=kernel,
    trace=trace,
    post_processor=post_processor,
    vector_top_k=settings.vector_top_k,
    graph_top_k=settings.graph_top_k,
    fusion_alpha=settings.fusion_alpha,
    fusion_beta=settings.fusion_beta,
)
```

Responsible for the query pipeline:

- query embedding
- vector retrieval
- graph retrieval
- retrieval fusion
- post-processing
- answer generation

---

## 6. Container Output

The function returns a dictionary containing shared runtime instances.

### Returned Keys

- `settings`
- `clock`
- `trace`
- `vector_store`
- `graph_store`
- `embedder`
- `ingest_service`
- `query_service`
- `llm`
- `kernel`

### Purpose

This dictionary is later attached to:

```python
app.state.container
```

So route handlers and middleware can access shared dependencies.

---

## 7. Why This Design Matters

This container-based design provides several engineering benefits.

### Centralized wiring

All runtime construction happens in one place.

### Clear dependency boundaries

The API layer does not manually instantiate business services.

### Better testability

Tests can create the app with different settings and validate backend behavior.

### Backend swappability

Embedding, vector, graph, and LLM backends can be switched without changing service logic.

### Shared instances

Both `IngestService` and `QueryService` use the same store instances, ensuring consistent runtime state.

---

## 8. `create_app`

```python
def create_app(settings_override: dict | None = None) -> FastAPI:
```

Builds and returns the FastAPI application object.

This is the final assembly step of the API layer.

---

## 9. Responsibilities of `create_app`

### Build settings

```python
settings = build_settings(settings_override)
```

Creates the runtime configuration object.

### Build container

```python
container = build_container(settings)
```

Constructs all application dependencies.

### Create FastAPI app

```python
app = FastAPI(title="GraphRAG", version="0.1.0")
```

### Attach runtime state

```python
app.state.container = container
app.state.settings = settings
```

This makes shared configuration and services available during request handling.

### Register middleware

Adds request-level trace handling.

### Register exception handlers

Maps domain and runtime exceptions into HTTP responses.

### Include routers

```python
app.include_router(health_router, tags=["health"])
app.include_router(ingest_router, tags=["ingest"])
app.include_router(query_router, tags=["query"])
```

---

## 10. Trace Middleware

The application defines an HTTP middleware for trace propagation.

### Implementation Pattern

```python
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace = request.app.state.container["trace"]
    incoming = request.headers.get("x-trace-id", "").strip()
    trace_id = incoming or uuid.uuid4().hex
    trace.set_trace_id(trace_id)

    response = await call_next(request)
    response.headers["x-trace-id"] = trace.get_trace_id()
    return response
```

### Behavior

For every request:

1. read `x-trace-id` from request headers
2. if absent, generate a new UUID-based trace id
3. store the trace id in the trace context
4. continue request execution
5. write the final trace id back into the response header

### Why it matters

This supports:

- request tracing
- easier debugging
- cross-service observability
- log correlation

---

## 11. Exception Handlers

The app maps known domain exceptions into consistent JSON responses.

### ValidationError

```python
@app.exception_handler(ValidationError)
async def handle_validation(_: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "message": str(exc)},
    )
```

### NotFoundError

```python
@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc)},
    )
```

### ConflictError

```python
@app.exception_handler(ConflictError)
async def handle_conflict(_: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content={"error": "conflict", "message": str(exc)},
    )
```

### DependencyError

```python
@app.exception_handler(DependencyError)
async def handle_dependency(_: Request, exc: DependencyError):
    return JSONResponse(
        status_code=502,
        content={"error": "dependency_error", "message": str(exc)},
    )
```

### Generic Exception

```python
@app.exception_handler(Exception)
async def handle_unknown(request: Request, exc: Exception):
    trace = request.app.state.container["trace"]
    trace.event("unhandled_exception", path=str(request.url.path), err=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "internal error"},
    )
```

This fallback handler ensures unknown failures are still converted into stable API responses.

---

## 12. Final App Export

At the end of the file:

```python
app = create_app()
```

This exports the ASGI application instance used by FastAPI servers such as Uvicorn.

Example startup command:

```python
uvicorn graph_rag.api.main:app --reload
```

---

## 13. Summary

`api/main.py` is the runtime assembly point of the entire GraphRAG system.

It does not implement business logic directly.

Instead, it is responsible for:

- configuration loading
- dependency construction
- backend selection
- middleware setup
- exception mapping
- route registration
- application export

This makes it one of the most important engineering files in the whole project.