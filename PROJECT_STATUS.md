# TFS Agent — Project Status & Roadmap

**Date:** September 14, 2026  
**Repository:** `vvanurag/tfs_agent`  
**Architecture Theme:** Zero-Egress, Air-Gapped Enterprise AI Agent for TFS / Azure DevOps  

---

## 1. Executive Summary

Based on `project_implementation_writeup.md` and a comprehensive audit of all repository files, this project is a **zero-egress AI agent pipeline** designed to:
1. Query and prune work items from an Azure DevOps / TFS instance (or local emulator).
2. Retrieve corporate policies, SLAs, and architecture docs from a local ChromaDB vector store with Role-Based Access Control (RBAC) filtering.
3. Orchestrate multi-agent synthesis, validation, and self-healing error correction using LangGraph and a local LLM (Llama 3 via Ollama).
4. Provide network resilience with Tenacity retry decorators and exponential backoff.

The project is currently **~50% complete**. The core concepts and skeleton architectures are implemented, but several supporting files are missing, tools are stubbed with dummy data, RAG is not yet plugged into the orchestrator, and the resilience gateway has not been written.

---

## 2. Stage-by-Stage Implementation Status

### Stage 1: Ingestion & Payload Engineering
* **Status:** 🟡 **80% Complete**
* **Done:**
  * `local_tfs_emulator.py`: Complete FastAPI + SQLite server simulating TFS `/_apis/wit/wiql` (POST) and `/_apis/wit/workitems` (GET) endpoints.
  * `real_local_tfs_client.py`: Working two-stage client querying the emulator and pruning bloated responses into strict `WorkItemSummary` Pydantic models.
  * `mock_tfs_client.py`: Implements mock version of the two-stage retrieval logic.
* **To Be Done / Gaps:**
  * Missing file: `mock_tfs_response.json` (required for `mock_tfs_client.py` to run offline).
  * HTML Tag Stripping: The description fields contain HTML (e.g., `<div><b>...</b></div>`) which is not yet cleaned before passing to the LLM.
  * Enterprise NTLM Auth: Authentication headers for real corporate TFS environments are not yet integrated into `real_local_tfs_client.py`.

---

### Stage 2: Advanced Retrieval (RAG) & Access Control (RBAC)
* **Status:** 🟡 **50% Complete**
* **Done:**
  * `build_vector_store.py`: Script using `RecursiveCharacterTextSplitter` and ChromaDB with metadata-based RBAC tags (`clearance`, `department`).
  * `query_vector_store.py`: Implementation of `execute_rbac_hybrid_search` enforcing `$lte` clearance filtering at the database layer.
* **To Be Done / Gaps:**
  * Missing files: Directory `mock_documents/` and files `adjudication_architecture.md` and `security_policy.md` do not exist. Running `build_vector_store.py` currently fails with `FileNotFoundError`.
  * The local Chroma vector store (`./local_chroma_db`) is unpopulated until the sample documents are created and ingested.
  * Hybrid Search: The query function currently performs dense vector similarity search with metadata filtering, but is not yet a hybrid dense+sparse (BM25) retriever.

---

### Stage 3: Agentic Orchestration & State Management
* **Status:** 🟡 **40% Complete**
* **Done:**
  * `agent_orchestrator.py` & `agent_orchestration_test.py`: Defined LangGraph `StateGraph` with `AgentState`, state router, and conditional edges (`drafting` -> `validation` -> `correction` / `END`).
  * `agent_orchestrator_real_llm.py`: Integrated `ChatOllama(model="llama3")` and `LocalTFSClient` into the graph.
* **To Be Done / Gaps:**
  * Missing file: `mock_local_llm.py` (`MockClient`) is imported by `agent_orchestrator.py` and `agent_orchestration_test.py`, causing `ModuleNotFoundError`.
  * Incomplete Tools (`agent_tools.py`): `@tool` decorators for `query_tfs_work_items` and `search_enterprise_knowledge_base` are hardcoded mock strings and not connected to the real clients.
  * Missing RAG in Orchestrator: `agent_orchestrator_real_llm.py` only pulls TFS work items; it does not retrieve knowledge base chunks from ChromaDB.
  * Stubbed Correction Node: The correction agent in `agent_orchestrator_real_llm.py` uses hardcoded mock JSON rather than feeding validation errors back to Llama 3 for self-healing.
  * Structured Pydantic Output Validation: `validation_agent` only does a dictionary key check (`"blockers" in draft_dict`) rather than validating against a formal Pydantic schema (e.g., `SprintReportModel`).

---

### Stage 4: Execution & Network Resilience
* **Status:** 🔴 **20% Complete**
* **Done:**
  * Local Conda environment (`ai_agent`) is verified with `pydantic`, `tenacity`, `requests`, `requests_ntlm`, `langchain`, `langgraph`, and `chromadb`.
  * Ollama is installed on the machine (`/usr/local/bin/ollama`).
* **To Be Done / Gaps:**
  * Missing file: `resilience_gateway.py` (referenced in writeup section 5) is completely missing. No Tenacity `@retry` decorators or exponential backoff wrappers exist around TFS API calls or Ollama invocations.
  * Ollama Service: The Ollama daemon needs to be running with `llama3` downloaded (`ollama pull llama3`).
  * Unified CLI / End-to-End Pipeline: No single entrypoint or test runner to start the emulator, ingest documents, and execute the complete agent pipeline.

---

## 3. File Inventory & Status Matrix

| File | Status | Description / Issues |
| :--- | :---: | :--- |
| `project_implementation_writeup.md` | ✅ Complete | Architectural spec and design document. |
| `verify_env.py` | ✅ Complete | Environment & dependency check (passes on `ai_agent` conda env). |
| `local_tfs_emulator.py` | ✅ Complete | FastAPI + SQLite server simulating TFS REST API endpoints. |
| `real_local_tfs_client.py` | ✅ Complete | Real HTTP client for the emulator with Pydantic v2 pruning. |
| `mock_tfs_client.py` | ⚠️ Missing Data | Functional logic, but missing `mock_tfs_response.json`. |
| `build_vector_store.py` | ⚠️ Missing Data | Vector indexing logic exists, but missing `mock_documents/*.md`. |
| `query_vector_store.py` | ⚠️ Needs DB | RBAC query logic exists, requires Chroma DB to be built. |
| `agent_tools.py` | ⚠️ Stubbed | Contains mock placeholder returns; needs connection to real clients. |
| `test_agent_tools.py` | ✅ Complete | Basic unit test for `agent_tools.py`. |
| `agent_orchestrator.py` | ❌ Missing Import | Fails on `import from mock_local_llm`. |
| `agent_orchestration_test.py` | ❌ Missing Import | Fails on `import from mock_local_llm`. |
| `agent_orchestrator_real_llm.py` | 🟡 Partial | Working skeleton, but lacks RAG node, real correction node, and Pydantic validation. |
| `mock_local_llm.py` | ❌ **Missing File** | Needed for offline mock testing. |
| `mock_documents/` | ❌ **Missing Files** | `adjudication_architecture.md` & `security_policy.md` needed for RAG. |
| `mock_tfs_response.json` | ❌ **Missing File** | Needed for offline `MockTFSClient`. |
| `resilience_gateway.py` | ❌ **Missing File** | Tenacity retry/backoff layer described in writeup is unbuilt. |

---

## 4. Prioritized Action Plan / Next Steps

1. **Create Missing Mock Files & Data**:
   - Create `mock_documents/adjudication_architecture.md` and `mock_documents/security_policy.md` with realistic SLA, NTLM timeout rules, and RBAC metadata.
   - Create `mock_tfs_response.json` for standalone offline execution of `mock_tfs_client.py`.
   - Create `mock_local_llm.py` to fix imports in `agent_orchestrator.py` and `agent_orchestration_test.py`.

2. **Implement Network Resilience (`resilience_gateway.py`)**:
   - Build Tenacity `@retry` wrappers with jittered exponential backoff for HTTP GET/POST calls to recover from simulated network errors (429, 500, timeouts).
   - Wrap `LocalTFSClient` methods with the resilience gateway.

3. **Wire Real Tools in `agent_tools.py`**:
   - Connect `query_tfs_work_items` to `LocalTFSClient`.
   - Connect `search_enterprise_knowledge_base` to `execute_rbac_hybrid_search`.

4. **Enhance LangGraph Orchestrator (`agent_orchestrator_real_llm.py`)**:
   - Add a dedicated **RAG Retrieval Node** that queries the vector database based on work item blockers.
   - Upgrade `validation_agent` to validate against a formal `SprintReportSchema` Pydantic model.
   - Upgrade `correction_agent` to dynamically reprompt the LLM with the specific Pydantic validation error message for true self-healing.

5. **End-to-End Integration & Validation**:
   - Build vector store with `build_vector_store.py`.
   - Start local TFS emulator.
   - Run end-to-end agent pipeline and verify zero-egress report generation.
