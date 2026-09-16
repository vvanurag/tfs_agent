# 🤖 AI Handover & Project Context Specification (`gpt_follow_up.md`)

> **Instructions for the Incoming AI Agent:**  
> Read this document first. This file contains a complete, self-contained technical blueprint of the project, including architectural philosophy, code inventory, what has already been built and verified, and the exact next steps to complete the pipeline.

---

## 1. Executive Summary & Core Philosophy

* **Project Name:** TFS Agent (Zero-Egress Multi-Agent DevOps Pipeline)
* **Repository:** `vvanurag/tfs_agent`
* **Python Environment:** Conda environment `ai_agent` (Python 3.12, located at `/opt/homebrew/Caskroom/miniforge/base/envs/ai_agent/bin/python`)
* **Core Philosophy (Zero-Egress / Air-Gapped):**
  In heavily regulated enterprise settings (e.g., healthcare, finance, defense), proprietary code, internal architecture blueprints, and ticket descriptions containing Personal Health Information (PHI) must never leave the corporate firewall.
  - **No Cloud LLM Calls:** Zero dependency on OpenAI, Anthropic, or Azure OpenAI cloud endpoints.
  - **100% Local Execution:** Inference runs locally via **Ollama (Llama 3)**; vector search runs locally via **ChromaDB**; TFS API emulation runs via local **FastAPI + SQLite**.

---

## 2. Four-Stage Architectural Pipeline

```text
[Stage 1: TFS Ingestion] ────► [Stage 2: RAG & RBAC] ────► [Stage 3: LangGraph Multi-Agent] ────► [Stage 4: Network Resilience]
FastAPI Emulator + SQLite       ChromaDB + Sliding Chunks    Drafting (Llama 3) -> Validation     Tenacity @retry with Jitter
Pydantic v2 Payload Pruning     $lte Mathematical Clearance   -> Self-Healing Correction Loop      & Exponential Backoff
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

### 🟡 Stage 3: Multi-Agent Orchestration & State Management (STATUS: NEXT UP / ~40% SKELETON)
* **Current State:**
  - `agent_orchestrator_real_llm.py` contains a basic LangGraph `StateGraph` with nodes: `retrieval` -> `drafting` -> `validation` -> `correction` / `END`.
* **What Remains To Be Done:**
  1. **Connect Real Tools in `agent_tools.py`:**
     - Replace dummy hardcoded strings in `query_tfs_work_items` with `LocalTFSClient.query_work_items()`.
     - Replace dummy strings in `search_enterprise_knowledge_base` with `execute_rbac_search()`.
  2. **Integrate RAG into Orchestrator:**
     - Add a dedicated **RAG Retrieval Node** in `agent_orchestrator_real_llm.py` that inspects the blockers identified in TFS work items (e.g., NTLM timeouts) and queries ChromaDB for relevant architecture/SLA specs.
  3. **Formal Pydantic Schema Validation:**
     - Create a formal `SprintReportSchema` Pydantic model (`sprint_id`, `status`, `blockers`, `remediation_plan`, `sla_impact`).
     - Update `validation_agent` to validate LLM output against this model and capture exact validation error traces.
  4. **True Dynamic Self-Healing Correction Loop:**
     - Update `correction_agent` to pass the exact validation error message and schema requirements back to Llama 3 for iterative self-correction (up to 3 retries).
  5. **Create `mock_local_llm.py`:**
     - Create a mock OpenAI-compatible client wrapper so unit tests in `agent_orchestrator.py` and `agent_orchestration_test.py` can run without a live Ollama daemon.

---

### 🔴 Stage 4: Execution & Network Resilience (STATUS: ~20% SKELETON)
* **Current State:**
  - Ollama is installed at `/usr/local/bin/ollama`.
  - Tenacity is installed in the conda environment.
* **What Remains To Be Done:**
  1. **Build `resilience_gateway.py`:**
     - Create Tenacity `@retry` decorators with jittered exponential backoff for HTTP requests (handling transient connection drops, HTTP 500/503, and 429 rate limits).
     - Wrap `LocalTFSClient` methods and LLM invocation calls with the resilience gateway.
  2. **End-to-End Test Runner (`run_pipeline.py`):**
     - Build a single runner script that starts the emulator (if needed), executes the RAG retrieval, runs the multi-agent graph, and outputs a formatted sprint status report.

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
| `agent_tools.py` | 🟡 Needs Wiring | LangChain `@tool` wrappers (needs live client connections). |
| `test_agent_tools.py` | ✅ Complete | Unit tests for agent tools. |
| `agent_orchestrator.py` | 🟡 Needs Mock | LangGraph state graph skeleton (needs `mock_local_llm.py`). |
| `agent_orchestration_test.py` | 🟡 Needs Mock | Test suite for multi-agent graph. |
| `agent_orchestrator_real_llm.py` | 🟡 In Progress | Live LangGraph workflow with Llama 3 (needs RAG + dynamic correction). |
| `mock_local_llm.py` | ❌ To Be Created | Offline mock LLM client to support unit tests. |
| `resilience_gateway.py` | ❌ To Be Created | Tenacity retry layer with exponential backoff & jitter. |
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

# 2. Seed Database & Mock JSON
$PYTHON_BIN seed_database.py

# 3. Start Local TFS Emulator (runs on port 8000)
$PYTHON_BIN local_tfs_emulator.py &

# 4. Test TFS Client Ingestion
$PYTHON_BIN real_local_tfs_client.py

# 5. Build & Query ChromaDB Vector Store
$PYTHON_BIN build_vector_store.py
$PYTHON_BIN query_vector_store.py

# 6. Run LangGraph Multi-Agent Orchestrator (requires Ollama running with llama3)
ollama serve &
$PYTHON_BIN agent_orchestrator_real_llm.py
```

---

## 6. Exact Next Steps for the Next AI Agent

If you are continuing work on this project, here is the recommended sequence:

1. **Step 1: Wire `agent_tools.py`**  
   Connect `query_tfs_work_items` to `LocalTFSClient` and `search_enterprise_knowledge_base` to `execute_rbac_search`.
2. **Step 2: Create `mock_local_llm.py`**  
   Implement a lightweight mock `MockClient` class mimicking OpenAI's chat completion interface so `agent_orchestration_test.py` and `agent_orchestrator.py` can run standalone unit tests.
3. **Step 3: Enhance `agent_orchestrator_real_llm.py`**  
   - Add a `rag_retrieval_node` that extracts keywords/blockers from TFS items and pulls matching SLA/Architecture specs from ChromaDB.
   - Define a formal `SprintReport` Pydantic model and enforce it in `validation_agent`.
   - Upgrade `correction_agent` to pass validation error feedback back to `ChatOllama(model="llama3")` for true self-healing.
4. **Step 4: Build `resilience_gateway.py`**  
   Add Tenacity `@retry` decorators with jittered exponential backoff around network calls.
5. **Step 5: Run end-to-end integration tests.**
