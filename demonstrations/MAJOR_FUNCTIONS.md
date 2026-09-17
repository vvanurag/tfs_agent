# 📚 Comprehensive Inventory of Major Functions & Classes

This document catalogs all the major functions, classes, decorators, endpoints, and library methods used across the **TFS Agent** project.

---

## 📑 Quick Navigation
1. [Stage 1: FastAPI API Emulator & Database Seeder](#1-stage-1-fastapi-api-emulator--database-seeder)
2. [Stage 1: Pydantic Payload Pruning & HTTP Client](#2-stage-1-pydantic-payload-pruning--http-client)
3. [Stage 2: Chunking, ChromaDB Vector Store & RBAC Search](#3-stage-2-chunking-chromadb-vector-store--rbac-search)
4. [Stage 3: LangChain Tools & Connectors](#4-stage-3-langchain-tools--connectors)
5. [Stage 3: Local Llama 3 (Ollama) & Structured Output](#5-stage-3-local-llama-3-ollama--structured-output)
6. [Stage 3: LangGraph Multi-Agent Graph & Self-Healing](#6-stage-3-langgraph-multi-agent-graph--self-healing)
7. [Stage 4: Network Resilience & Exponential Backoff (Tenacity)](#7-stage-4-network-resilience--exponential-backoff-tenacity)

---

## 1. Stage 1: FastAPI API Emulator & Database Seeder

**Source Files:** `local_tfs_emulator.py`, `seed_database.py`

| Function / Component | Signature / Route | Description |
| :--- | :--- | :--- |
| `seed_database()` | `seed_database() -> None` | Reads `tfs_dataset.json`, populates `local_tfs.db` SQLite database, and generates `mock_tfs_response.json`. |
| `get_db_connection()` | `get_db_connection() -> sqlite3.Connection` | Returns a thread-safe SQLite connection configured with `sqlite3.Row` for key-value dictionary row access. |
| `parse_wiql_to_sql()` | `parse_wiql_to_sql(wiql: str) -> (str, list)` | Translates Azure DevOps WIQL syntax (e.g., `[System.State] = 'Active'`) into SQL. |
| `@app.get("/")` | `root() -> dict` | Health-check endpoint reporting server status and total work items count. |
| `@app.post("/_apis/wit/wiql")` | `execute_wiql(payload: WIQLRequest) -> dict` | Stage 1 endpoint: Accepts a WIQL query string and returns an array of matching work item IDs. |
| `@app.get("/_apis/wit/workitems")` | `get_workitems(ids: str) -> dict` | Stage 2 endpoint: Batch lookup returning authentic Azure DevOps bloated JSON payloads with system metadata. |
| `uvicorn.run()` | `uvicorn.run(app, host, port)` | Starts the local ASGI web server listening on port 8000. |

---

## 2. Stage 1: Pydantic Payload Pruning & HTTP Client

**Source Files:** `real_local_tfs_client.py`, `mock_tfs_client.py`

| Function / Method | Signature | Description |
| :--- | :--- | :--- |
| `WorkItemSummary.clean_html()` | `clean_html(raw_html: str) -> str` | Strips all HTML tags (`<div>`, `<p>`, `<b>`, `<code>`) and unescapes HTML entities (`&lt;`, `&gt;`). |
| `LocalTFSClient.__init__()` | `__init__(base_url: str)` | Initializes the HTTP client pointing to `http://127.0.0.1:8000`. |
| `LocalTFSClient.stage_1_execute_wiql()` | `stage_1_execute_wiql(query: str) -> List[int]` | Sends `POST /_apis/wit/wiql` to retrieve matching ticket IDs. |
| `LocalTFSClient.stage_2_fetch_details()` | `stage_2_fetch_details(ids: List[int]) -> List[WorkItemSummary]` | Sends `GET /_apis/wit/workitems?ids=...`, strips system GUIDs and URLs, and returns normalized Pydantic objects. |
| `LocalTFSClient.query_work_items()` | `query_work_items(wiql: str) -> List[WorkItemSummary]` | Convenience pipeline executing Stage 1 and Stage 2 in one seamless call. |
| `LocalTFSClient.query_active_bugs()` | `query_active_bugs() -> List[WorkItemSummary]` | Helper fetching all items where `[System.WorkItemType] = 'Bug'` and `[System.State] = 'Active'`. |
| `LocalTFSClient.query_by_assignee()` | `query_by_assignee(name: str) -> List[WorkItemSummary]` | Helper fetching work items assigned to a specific engineer name. |

---

## 3. Stage 2: Chunking, ChromaDB Vector Store & RBAC Search

**Source Files:** `build_vector_store.py`, `query_vector_store.py`

| Function / Method | Signature | Description |
| :--- | :--- | :--- |
| `RecursiveCharacterTextSplitter.split_text()` | `split_text(text: str) -> List[str]` | Splits documents using a sliding window (`chunk_size=300`, `chunk_overlap=50`) preserving header boundaries. |
| `chromadb.PersistentClient()` | `PersistentClient(path: str)` | Initializes local on-disk ChromaDB persistent storage at `./local_chroma_db`. |
| `collection.add()` | `collection.add(documents, metadatas, ids)` | Automatically converts raw text chunks into 384-dimensional vectors via local ONNX model and indexes them with RBAC tags. |
| `execute_rbac_search()` | `execute_rbac_search(query_text, user_clearance, top_k) -> List[dict]` | Executes similarity search while enforcing database-layer filtering: `where={"clearance": {"$lte": user_clearance}}`. |

---

## 4. Stage 3: LangChain Tools & Connectors

**Source Files:** `agent_tools.py`

| Function / Decorator | Signature | Description |
| :--- | :--- | :--- |
| `@tool query_tfs_work_items` | `query_tfs_work_items(wiql_query: str) -> str` | LangChain tool allowing AI agents to query active work items from the live TFS API. |
| `@tool search_enterprise_knowledge_base` | `search_enterprise_knowledge_base(search_term, user_clearance_level) -> str` | LangChain tool allowing AI agents to perform RBAC vector searches on ChromaDB for architecture & SLA context. |

---

## 5. Stage 3: Local Llama 3 (Ollama) & Structured Output

**Source Files:** `real_llm_guide.py`, `llama3_ollama_demo.py`

| Function / Method | Signature | Description |
| :--- | :--- | :--- |
| `ChatOllama()` | `ChatOllama(model="llama3", temperature=0.1)` | Initializes local Llama 3 (8B) model connection through the local Ollama server (`http://127.0.0.1:11434`). |
| `llm.invoke()` | `llm.invoke(messages: List[BaseMessage]) -> AIMessage` | Synchronous invocation passing System and Human messages to the local model. |
| `llm.stream()` | `llm.stream(prompt: str) -> Iterator[AIMessageChunk]` | Streams response tokens word-by-word in real time as Llama 3 generates them. |
| `llm.with_structured_output()` | `llm.with_structured_output(PydanticModel)` | Binds a Pydantic schema to Llama 3, forcing the output into a strongly-typed, validated Python object. |
| `ollama.chat()` | `ollama.chat(model="llama3", messages=[...], stream=True)` | Direct API call using the official Ollama Python SDK. |

---

## 6. Stage 3: LangGraph Multi-Agent Graph & Self-Healing

**Source Files:** `agent_orchestrator_real_llm.py`, `agent_orchestrator.py`

| Function / Node | Signature | Description |
| :--- | :--- | :--- |
| `StateGraph(AgentState)` | `StateGraph(schema: Type[TypedDict])` | Initializes the LangGraph state machine tracking messages, TFS data, RAG context, and validation errors. |
| `tfs_retrieval_agent()` | `node(state: AgentState) -> AgentState` | **Node 1**: Queries the live TFS API and prunes active work items into the state. |
| `rag_retrieval_agent()` | `node(state: AgentState) -> AgentState` | **Node 2**: Performs RBAC vector search on ChromaDB for SLA and architecture specs matching active blockers. |
| `drafting_agent()` | `node(state: AgentState) -> AgentState` | **Node 3**: Prompts local Llama 3 to synthesize TFS items + RAG context into a structured JSON report. |
| `validation_agent()` | `node(state: AgentState) -> AgentState` | **Node 4**: Validates output against strict `SprintReportSchema` Pydantic model. |
| `correction_agent()` | `node(state: AgentState) -> AgentState` | **Node 5 (Self-Healing)**: Triggered when validation fails; reprompts Llama 3 with exact validation error traces. |
| `route_validation()` | `route_validation(state: AgentState) -> str` | Conditional Edge: Routes to `correction` if validation errors exist (up to 3 retries), or `end` when valid. |
| `workflow.compile()` | `compile() -> CompiledGraph` | Compiles nodes and edges into an executable agent application. |
| `app.invoke()` | `invoke(initial_state: dict) -> dict` | Executes the complete multi-agent pipeline. |

---

## 7. Stage 4: Network Resilience & Exponential Backoff (Tenacity)

**Source Files:** `demonstrations/07_network_resilience_tenacity_demo.py`

| Decorator / Parameter | Usage | Description |
| :--- | :--- | :--- |
| `@retry` | `@retry(...)` | Decorator that automatically wraps network functions with retry logic. |
| `stop_after_attempt(N)` | `stop=stop_after_attempt(4)` | Caps retry attempts to prevent infinite loops. |
| `wait_random_exponential()` | `wait=wait_random_exponential(multiplier=0.5, max=5)` | Implements jittered exponential backoff (e.g. 500ms $\rightarrow$ 1s $\rightarrow$ 2s $\pm$ jitter) to prevent thundering herd load spikes. |
| `retry_if_exception_type()` | `retry=retry_if_exception_type(TransientError)` | Selectively retries only transient errors (timeouts, HTTP 500, 503, 429) while letting fatal 400/404 errors raise immediately. |

---

## 📂 Demonstrations Directory Map

All individual standalone demonstration scripts can be run directly from the `demonstrations/` folder:

```bash
# Demo 1: Two-Stage TFS Ingestion & Pydantic Pruning
python demonstrations/01_tfs_two_stage_ingestion_demo.py

# Demo 2: Semantic Chunking & ChromaDB Ingestion
python demonstrations/02_semantic_chunking_and_chroma_demo.py

# Demo 3: Retrieval-Layer RBAC Vector Search
python demonstrations/03_rbac_vector_search_demo.py

# Demo 4: Local Llama 3 via Ollama (Chat & Streaming)
python demonstrations/04_local_llama3_ollama_demo.py

# Demo 5: Pydantic Structured Output from Llama 3
python demonstrations/05_pydantic_structured_output_demo.py

# Demo 6: LangGraph Multi-Agent State Graph with Self-Healing Loop
python demonstrations/06_langgraph_multiagent_self_healing_demo.py

# Demo 7: Network Resilience Gateway with Tenacity Retry
python demonstrations/07_network_resilience_tenacity_demo.py
```
