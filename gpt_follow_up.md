# 🤖 AI Handover & Project Context Specification (`gpt_follow_up.md`)

> **Instructions for the Incoming AI Agent:**  
> Read this document first. This file contains a complete, self-contained technical blueprint of the project, including architectural philosophy, code inventory, what has already been built and verified, and the exact next steps to complete the pipeline.

---

## 1. Executive Summary & Core Philosophy

* **Project Name:** TFS Agent (Zero-Egress Multi-Agent DevOps Pipeline)
* **Repository:** `vvanurag/tfs_agent`
* **Python Environment:** Conda environment `ai_agent` (Python 3.12, located at `/opt/homebrew/Caskroom/miniforge/base/envs/ai_agent/bin/python`)
* **Local LLM Engine:** Ollama running `llama3:latest` (8.0B parameters, local server on `http://127.0.0.1:11434`)
* **Core Philosophy (Zero-Egress / Air-Gapped):**
  In heavily regulated enterprise settings (e.g., healthcare, finance, defense), proprietary code, internal architecture blueprints, and ticket descriptions containing Personal Health Information (PHI) must never leave the corporate firewall.
  - **No Cloud LLM Calls:** Zero dependency on OpenAI, Anthropic, or Azure OpenAI cloud endpoints.
  - **100% Real Local LLM Execution:** Prompts are processed on-premises using **local Llama 3 via Ollama** (`ChatOllama`); vector search runs locally via **ChromaDB**; TFS API emulation runs via local **FastAPI + SQLite**.

---

## 2. Four-Stage Architectural Pipeline

```text
[Stage 1: TFS Ingestion] ────► [Stage 2: RAG & RBAC] ────► [Stage 3: LangGraph Multi-Agent] ────► [Stage 4: Network Resilience]
FastAPI Emulator + SQLite       ChromaDB + Sliding Chunks    Drafting (Llama 3) -> Validation     Tenacity @retry with Jitter
Pydantic v2 Payload Pruning     $lte Mathematical Clearance   -> Self-Healing Correction Loop      & Exponential Backoff
                                                             (100% Real Local Llama 3)
```

---

## 3. Implementation Status By Stage

### ✅ Stage 1: Ingestion & Payload Engineering (STATUS: 100% COMPLETE & VERIFIED)
1. **`tfs_dataset.json`**: Comprehensive enterprise dataset with 12 rich work items (Bugs, Tasks, Stories, Features) including priorities, severities, tags, iteration paths, and HTML descriptions.
2. **`seed_database.py`**: Initializes SQLite database `local_tfs.db` and exports `mock_tfs_response.json` for offline testing.
3. **`local_tfs_emulator.py`**: FastAPI server running on `http://127.0.0.1:8000`:
   - `POST /_apis/wit/wiql` (Stage 1): Translates Azure DevOps WIQL syntax (e.g., `WHERE [System.State] = 'Active' AND [System.WorkItemType] = 'Bug'`) into SQL and returns matching IDs.
   - `GET /_apis/wit/workitems?ids=...` (Stage 2): Returns authentic enterprise Azure DevOps JSON payloads with nested GUIDs and system fields.
   - `GET /`: Health check endpoint.
4. **`real_local_tfs_client.py`**: Two-stage HTTP client that queries the emulator, cleans HTML formatting from descriptions, and prunes bloated payloads into strict Pydantic v2 `WorkItemSummary` objects.
5. **`mock_tfs_client.py`**: Offline mock client reading `mock_tfs_response.json`.

---

### ✅ Stage 2: Advanced Retrieval (RAG) & Access Control (STATUS: 100% COMPLETE & VERIFIED)
1. **`mock_documents/`**:
   - `engineering_handbook.md` (*Clearance Level 1 - General*): Sprint cadences (Sprint 12), severity classifications, git standards.
   - `adjudication_architecture.md` (*Clearance Level 2 - Internal Engineering*): NTLM SLA retry policies (3 retries, 500ms initial delay, 30s timeout ceiling), SQLite connection lease guidelines, 15-minute batch claim processing SLA.
   - `security_policy.md` (*Clearance Level 3 - Confidential / Audit*): Zero-Egress SEC-099 compliance, strict cloud API prohibition, mandatory on-premises LLM (Ollama).
2. **`build_vector_store.py`**:
   - Splits documents using `RecursiveCharacterTextSplitter` (`chunk_size=300`, `chunk_overlap=50`).
   - Tags each chunk with explicit RBAC metadata (`clearance`: 1, 2, or 3, `department`, `source`).
   - Indexes and persists 20 chunks into local ChromaDB at `./local_chroma_db` in collection `enterprise_architecture`.
3. **`query_vector_store.py`**:
   - Implements `execute_rbac_search` enforcing mathematical database-layer filtering using `{"clearance": {"$lte": user_clearance}}`.
   - Verified across Level 1 (Junior Engineer), Level 2 (Senior Engineer), and Level 3 (Compliance Officer) scenarios.

---

### ✅ Stage 3: Multi-Agent Orchestration & Real LLM (STATUS: 100% COMPLETE & VERIFIED)
1. **100% Real Local LLM Execution**:
   - Replaced all mock LLM classes with **`ChatOllama(model="llama3")`** running locally on Ollama.
   - Created [real_llm_guide.py](real_llm_guide.py) as an educational tutorial on raw LLM invocation, Pydantic type-safe structured output (`with_structured_output`), and cloud provider switching.
2. **Live Agent Tools ([agent_tools.py](agent_tools.py))**:
   - `query_tfs_work_items` wired to live `LocalTFSClient`.
   - `search_enterprise_knowledge_base` wired to live `execute_rbac_search`.
3. **Full LangGraph Multi-Agent State Machine ([agent_orchestrator_real_llm.py](agent_orchestrator_real_llm.py))**:
   - **Node 1 (TFS Ingestion)**: Ingests and prunes active work items from the FastAPI emulator.
   - **Node 2 (RAG Ingestion)**: Extracts keywords and fetches Level 2 SLA / architecture chunks from ChromaDB.
   - **Node 3 (Drafting Agent)**: Prompts local Llama 3 to synthesize work items and SLA rules.
   - **Node 4 (Validation Agent)**: Enforces strict Pydantic `SprintReportSchema` contract.
   - **Node 5 (Correction Agent)**: Dynamic self-healing loop that reprompts Llama 3 with exact validation error traces.
   - **Router Edge**: Conditionally routes to Correction Agent (up to 3 retries) or `END`.
4. **All Orchestrator Scripts Upgraded**:
   - [agent_orchestrator.py](agent_orchestrator.py) and [agent_orchestration_test.py](agent_orchestration_test.py) now execute with real Llama 3.

---

### 🟡 Stage 4: Execution & Network Resilience (STATUS: UP NEXT / ~20% SKELETON)
* **Current State:**
  - Ollama is running at `http://127.0.0.1:11434` with `llama3:latest`.
  - Tenacity is installed in the conda environment.
* **What Remains To Be Done:**
  1. **Build `resilience_gateway.py`:**
     - Create Tenacity `@retry` decorators with jittered exponential backoff for HTTP requests (handling transient connection drops, HTTP 500/503, and 429 rate limits).
     - Wrap `LocalTFSClient` methods and LLM invocation calls with the resilience gateway.
  2. **End-to-End Test Runner (`run_pipeline.py`):**
     - Build a single unified runner script that validates environment, starts emulator if needed, builds vector store, executes the full LangGraph multi-agent pipeline, and outputs a formatted sprint status report.

---

## 4. Complete File Inventory

| File Path | Status | Purpose / Description |
| :--- | :---: | :--- |
| `tfs_dataset.json` | ✅ Complete | Enterprise dataset with 12 detailed work items. |
| `seed_database.py` | ✅ Complete | SQLite database seeder & mock JSON generator. |
| `local_tfs.db` | ✅ Complete | Local SQLite database holding work item records. |
| `local_tfs_emulator.py` | ✅ Complete | FastAPI REST API server simulating Azure DevOps endpoints. |
| `real_local_tfs_client.py` | ✅ Complete | Two-stage HTTP client with HTML stripping & Pydantic pruning. |
| `mock_tfs_client.py` | ✅ Complete | Offline mock TFS client. |
| `mock_tfs_response.json` | ✅ Complete | Raw Azure DevOps JSON response for offline tests. |
| `mock_documents/*.md` | ✅ Complete | Enterprise docs (Engineering Handbook, SLA Specs, Security Policy). |
| `build_vector_store.py` | ✅ Complete | ChromaDB chunker and vector indexer with RBAC clearance tags. |
| `query_vector_store.py` | ✅ Complete | RBAC similarity search with `$lte` metadata filtering. |
| `agent_tools.py` | ✅ Complete | LangChain `@tool` wrappers connected to live TFS & ChromaDB. |
| `test_agent_tools.py` | ✅ Complete | Unit tests for agent tools. |
| `real_llm_guide.py` | ✅ Complete | Hands-on tutorial on real LLMs, Pydantic schemas, and cloud switching. |
| `agent_orchestrator.py` | ✅ Complete | LangGraph state graph powered by real Llama 3. |
| `agent_orchestration_test.py` | ✅ Complete | Multi-agent test suite powered by real Llama 3. |
| `agent_orchestrator_real_llm.py` | ✅ Complete | Production LangGraph pipeline (TFS + RAG + Llama 3 + Self-Healing). |
| `resilience_gateway.py` | ❌ To Be Created | Tenacity retry layer with exponential backoff & jitter (Stage 4). |
| `verify_env.py` | ✅ Complete | Environment & dependency validation script. |
| `PROJECT_STATUS.md` | ✅ Complete | Detailed project audit and milestone tracker. |
| `README.md` | ✅ Complete | GitHub repository documentation. |

---

## 5. How to Run the System (Quick Commands)

Use Python from the `ai_agent` conda environment:
```bash
PYTHON_BIN="/opt/homebrew/Caskroom/miniforge/base/envs/ai_agent/bin/python"

# 1. Verify Environment
$PYTHON_BIN verify_env.py

# 2. Seed Database & Generate Mock JSON
$PYTHON_BIN seed_database.py

# 3. Start Local TFS Emulator (runs on port 8000)
$PYTHON_BIN local_tfs_emulator.py &

# 4. Test TFS Client Ingestion & Pruning
$PYTHON_BIN real_local_tfs_client.py

# 5. Build & Query ChromaDB Vector Store with RBAC
$PYTHON_BIN build_vector_store.py
$PYTHON_BIN query_vector_store.py

# 6. Run Real LLM Guide & Tutorial
$PYTHON_BIN real_llm_guide.py

# 7. Run Complete LangGraph Multi-Agent Pipeline (Llama 3 + Self-Healing)
$PYTHON_BIN agent_orchestrator_real_llm.py
```

---

## 6. Exact Next Steps for the Next AI Agent

If you are continuing work on this project, here is the remaining milestone:

1. **Step 1: Build `resilience_gateway.py` (Stage 4)**  
   - Implement Tenacity `@retry` decorators with jittered exponential backoff for HTTP requests (`requests.get`, `requests.post`) to handle simulated transient 500/503 errors and network timeouts.
   - Wrap `LocalTFSClient` methods with this gateway layer.
2. **Step 2: Build Unified Runner (`run_pipeline.py`)**  
   - Provide a single entrypoint script that executes all stages end-to-end and outputs formatted sprint reports.
