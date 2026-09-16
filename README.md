# 🛡️ TFS Agent: Zero-Egress Multi-Agent DevOps Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Local_LLM-Llama_3-black.svg?logo=ollama&logoColor=white)](https://ollama.ai/)
[![Pydantic v2](https://img.shields.io/badge/Data_Contract-Pydantic_v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, **air-gapped, zero-egress AI agent pipeline** designed to ingest, prune, validate, and synthesize work items from **Azure DevOps (TFS)**. By combining **local LLM execution (Llama 3 via Ollama)**, **ChromaDB RAG with Role-Based Access Control (RBAC)**, and **LangGraph self-healing stateful workflows**, this system completely eliminates corporate data leakage and compliance violations.

> 🤖 **AI Assistant Handover:** If you are an AI model taking over this repository, refer to **[`gpt_follow_up.md`](gpt_follow_up.md)** for a complete, self-contained architecture and implementation handover guide.

---

## 📑 Table of Contents
- [Architecture & Philosophy](#-architecture--philosophy)
- [Key Features](#-key-features)
- [System Architecture Diagram](#-system-architecture-diagram)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Quickstart Guide](#-quickstart-guide)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Seed Enterprise Database](#2-seed-enterprise-database)
  - [3. Start Local TFS Emulator](#3-start-local-tfs-emulator)
  - [4. Test Two-Stage Data Ingestion](#4-test-two-stage-data-ingestion)
  - [5. Build Vector Store with RBAC](#5-build-vector-store-with-rbac)
  - [6. Execute Multi-Agent Orchestrator](#6-execute-multi-agent-orchestrator)
- [Data Contract & Payload Engineering](#-data-contract--payload-engineering)
- [Project Roadmap & Status](#-project-roadmap--status)
- [License](#-license)

---

## 🔒 Architecture & Philosophy

In regulated enterprise environments (e.g., healthcare, finance, defense), uploading proprietary source code, internal system architectures, and Personal Health Information (PHI) to cloud LLMs (OpenAI, Azure OpenAI, Anthropic) violates data protection mandates.

**TFS Agent** enforces a strict **Zero-Egress** model:
* **100% Local Inference**: Prompts and context are processed on-premises using local Llama 3 via Ollama.
* **Two-Stage Ingestion**: Eliminates context window bloat by converting raw Azure DevOps JSON into lightweight, strongly-typed Pydantic summaries.
* **Retrieval-Layer RBAC**: ChromaDB vector queries enforce security clearance constraints (`clearance <= user_level`) at the mathematical index layer before context reaches the agent.
* **Self-Healing State Graph**: LangGraph multi-agent loop automatically catches malformed JSON or incomplete fields and reprompts the model for self-correction.

---

## ✨ Key Features

| Stage | Technology | Capability | Status |
| :--- | :--- | :--- | :---: |
| **1. Payload Engineering** | FastAPI + SQLite + Pydantic v2 | Simulates Azure DevOps WIQL endpoints; strips system metadata, GUIDs, and raw HTML formatting. | ✅ Complete |
| **2. Secure RAG & RBAC** | ChromaDB + LangChain Splitters | Semantic chunking with mathematical `$lte` metadata security clearance filtering (Level 1–3). | ✅ Complete |
| **3. Multi-Agent Orchestrator** | LangGraph + StateGraph | Stateful multi-agent graph: Data Retrieval Node $\rightarrow$ Drafting Node $\rightarrow$ Validation Node $\rightarrow$ Correction Loop. | 🟡 In Progress |
| **4. Network Resilience** | Tenacity + Exponential Backoff | Gateway layer with retry jitter to gracefully handle transient network drops, 429s, and 500 errors. | 🟡 Up Next |

---

## 📐 System Architecture Diagram

```mermaid
flowchart TD
    subgraph Local_Enterprise_Environment ["🔒 Air-Gapped / Zero-Egress Host Machine"]
        subgraph Stage1 ["Stage 1: TFS Ingestion (Complete)"]
            TFS_DB[("SQLite TFS Database\n(local_tfs.db)")]
            Emulator["FastAPI TFS Emulator\n(local_tfs_emulator.py)"]
            TFS_Client["Two-Stage Client & Pruner\n(real_local_tfs_client.py)"]
            
            TFS_DB <--> Emulator
            Emulator -->|WIQL POST + Batch GET| TFS_Client
            TFS_Client -->|Pruned WorkItemSummary| StateGraph
        end

        subgraph Stage2 ["Stage 2: Secure RAG & RBAC (Complete)"]
            Docs["Internal Architecture & SLA Specs\n(mock_documents/*.md)"]
            Splitter["RecursiveCharacterTextSplitter\n(Overlap: 50, Size: 300)"]
            Chroma[("Local ChromaDB\n(RBAC Metadata: Clearance <= N)")]
            
            Docs --> Splitter --> Chroma
            Chroma -->|Clearance Filtered Chunks| StateGraph
        end

        subgraph Stage3 ["Stage 3: LangGraph Multi-Agent Orchestrator"]
            StateGraph{"LangGraph State Router"}
            DraftNode["Drafting Agent\n(Llama 3 via Ollama)"]
            ValNode["Validation Agent\n(Pydantic Schema Check)"]
            CorrNode["Correction Agent\n(Self-Healing Reprompt)"]
            
            StateGraph --> DraftNode
            DraftNode --> ValNode
            ValNode -->|Validation Failed & Retries < 3| CorrNode
            CorrNode --> ValNode
            ValNode -->|Validation Passed| FinalOutput["Final Validated Sprint Report (JSON)"]
        end
    end
```

---

## 📂 Repository Structure

```text
tfs_agent/
├── README.md                          # Repository documentation & architecture guide
├── gpt_follow_up.md                   # Complete AI handover & project context guide
├── PROJECT_STATUS.md                  # Comprehensive implementation status & audit
├── project_implementation_writeup.md  # Original architectural specification
│
├── local_tfs_emulator.py              # FastAPI server simulating Azure DevOps / TFS REST API
├── seed_database.py                   # Populates SQLite with enterprise work items
├── tfs_dataset.json                   # 12+ realistic work items (Bugs, Tasks, Stories, Epics)
├── local_tfs.db                       # Local SQLite database backing the TFS emulator
│
├── real_local_tfs_client.py           # Two-stage HTTP client with HTML stripping & Pydantic pruning
├── mock_tfs_client.py                 # Offline mock TFS client
├── mock_tfs_response.json             # Raw Azure DevOps response payload for offline tests
│
├── mock_documents/                    # Enterprise internal documentation
│   ├── engineering_handbook.md        # Clearance Level 1 (General)
│   ├── adjudication_architecture.md   # Clearance Level 2 (Internal Engineering SLAs)
│   └── security_policy.md             # Clearance Level 3 (Zero-Egress & Confidential)
│
├── build_vector_store.py              # Chunker & ChromaDB ingest script with RBAC tags
├── query_vector_store.py              # Vector similarity search with clearance filtering
│
├── agent_tools.py                     # LangChain @tool wrappers for TFS & RAG connectors
├── test_agent_tools.py                # Unit test for agent tools
│
├── agent_orchestrator.py              # LangGraph state machine skeleton
├── agent_orchestrator_real_llm.py     # Live LangGraph workflow with Llama 3 & TFS Client
├── agent_orchestration_test.py        # Offline test suite for multi-agent loops
└── verify_env.py                      # Environment verification & dependency checker
```

---

## 🛠️ Prerequisites

* **OS**: macOS / Linux / Windows WSL2
* **Python**: `3.10` or higher (Conda recommended: `ai_agent`)
* **Ollama**: Local LLM runner ([Download Ollama](https://ollama.ai))
  ```bash
  ollama pull llama3
  ```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

Create and activate a virtual environment or Conda environment:

```bash
# Using Conda
conda create -n ai_agent python=3.12 -y
conda activate ai_agent

# Install dependencies
pip install fastapi uvicorn requests requests-ntlm pydantic tenacity chromadb langchain langgraph langchain-ollama langchain-text-splitters
```

Verify your installation:
```bash
python verify_env.py
```

---

### 2. Seed Enterprise Database

Populate the local SQLite database with realistic work items and generate mock response files:

```bash
python seed_database.py
```

---

### 3. Start Local TFS Emulator

Launch the local FastAPI server simulating Azure DevOps REST API:

```bash
python local_tfs_emulator.py
```
* The server runs at: `http://127.0.0.1:8000`
* Interactive Swagger Docs available at: `http://127.0.0.1:8000/docs`

---

### 4. Test Two-Stage Data Ingestion

In a separate terminal, execute the client to query active bugs and verify Pydantic normalization:

```bash
python real_local_tfs_client.py
```

**Example Output:**
```json
{
  "id": 10241,
  "title": "NTLM Handshake Timeout Exception in Adjudication Service",
  "work_item_type": "Bug",
  "state": "Active",
  "assigned_to": "Jane Doe",
  "priority": 1,
  "severity": "1 - Critical",
  "iteration_path": "Sprint 12",
  "tags": ["NTLM", "Timeout", "HighPriority"],
  "description": "Error: Connection timed out after 30000ms during NTLM handshake with legacy directory services. Need to implement jittered exponential backoff and retry policy."
}
```

---

### 5. Build & Query Vector Store with RBAC

Ingest engineering specs and policies into ChromaDB with Role-Based Access Control tags, then run multi-clearance verification:

```bash
python build_vector_store.py
python query_vector_store.py
```

**RBAC Enforcement Summary:**
* **Level 1 (Junior Engineer):** Searching for NTLM SLA returns public general docs only; confidential specs are mathematically hidden.
* **Level 2 (Senior Engineer):** Unlocks exact NTLM SLA retry rules (3 attempts, 500ms jittered backoff, 30s timeout ceiling).
* **Level 3 (Compliance Officer):** Unlocks confidential SEC-099 Zero-Egress mandates and cloud API prohibitions.

---

### 6. Execute Multi-Agent Orchestrator

Start the Ollama daemon and run the LangGraph self-healing pipeline:

```bash
# Terminal 1: Start Ollama service
ollama serve

# Terminal 2: Run LangGraph orchestrator
python agent_orchestrator_real_llm.py
```

---

## 📊 Data Contract & Payload Engineering

Raw Azure DevOps JSON payloads contain massive amounts of system metadata, GUIDs, and HTML formatting that degrade LLM prompt efficiency. 

`WorkItemSummary` enforces a strict Pydantic v2 contract:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class WorkItemSummary(BaseModel):
    id: int
    title: str
    work_item_type: str = Field(alias="type")
    state: str
    assigned_to: str
    priority: int = 2
    severity: Optional[str] = None
    iteration_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    description: str

    model_config = {"populate_by_name": True}
```

---

## 🗺️ Project Roadmap & Status

For a line-by-line audit and upcoming milestones, see **[PROJECT_STATUS.md](PROJECT_STATUS.md)** and **[gpt_follow_up.md](gpt_follow_up.md)**.

- [x] **Stage 1**: Local TFS API Emulator & Two-Stage Pydantic Ingestion
- [x] **Stage 1**: Enterprise SQLite Dataset Seeding & Mock JSON generation
- [x] **Stage 2**: Ingest complete corporate architecture docs & RBAC clearance tests (`mock_documents/`, ChromaDB)
- [x] **Stage 2**: Retrieval-layer `$lte` mathematical clearance filtering
- [ ] **Stage 3**: Wire `agent_tools.py` directly to live TFS & ChromaDB clients
- [ ] **Stage 3**: Full RAG retrieval integration inside LangGraph StateGraph
- [ ] **Stage 3**: Dynamic LLM-driven self-healing correction loop
- [ ] **Stage 4**: Network Resilience Gateway with Tenacity retry & exponential backoff

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.
