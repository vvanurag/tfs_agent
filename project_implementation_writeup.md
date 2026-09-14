---

## Detailed Project Implementation Writeup

### 1. Architectural Foundation & Zero-Egress Philosophy
The primary objective of this project was to construct a highly capable AI agent pipeline that strictly adheres to corporate data privacy and compliance laws. Because uploading sensitive corporate architecture, proprietary code, or Personal Health Information (PHI) to external cloud providers (like OpenAI or Azure) often violates enterprise security policies, this entire system was engineered to be "zero-egress"[cite: 7]. Every component—from the REST API endpoints to the vector database and the Large Language Model itself—executes locally on the host machine without requiring external internet access.

### 2. Stage 1: Ingestion & Payload Engineering
Enterprise systems like Azure DevOps (TFS) or Jira return massive, deeply nested JSON payloads that waste LLM context window tokens and increase latency[cite: 7]. To solve this, a Two-Stage Retrieval Architecture was implemented[cite: 4, 7]:
* **The API Emulator:** A local FastAPI server backed by SQLite was built (`local_tfs_emulator.py`) to simulate an enterprise TFS server.
* **Stage 1 (Metadata Search):** The pipeline executes a lightweight Work Item Query Language (WIQL) POST request to retrieve only the IDs of active work items[cite: 4, 5]. 
* **Stage 2 (Batch Lookup & Pruning):** The pipeline executes a batch GET request to fetch the full records[cite: 4]. Crucially, the resulting bloated JSON payload is immediately passed through a strict Pydantic v2 schema (`WorkItemSummary`), which normalizes the data and discards unnecessary system metadata, HTML tags, and GUIDs before it ever reaches the LLM[cite: 4, 5, 7].

### 3. Stage 2: Advanced Retrieval (RAG) & Access Control
To provide the AI with context regarding corporate SLAs, architecture specs, and policies, a Retrieval-Augmented Generation (RAG) system was built using ChromaDB (`build_vector_store.py`)[cite: 2, 3].
* **Semantic Chunking:** Documents were split using a sliding window approach (`RecursiveCharacterTextSplitter`) to preserve contextual overlap[cite: 3].
* **Retrieval-Layer RBAC:** An advanced security layer was implemented at the database level[cite: 6]. Every chunk of text ingested into the vector store was assigned explicit Role-Based Access Control (RBAC) metadata (e.g., department, clearance level)[cite: 3, 7]. When the vector store is queried, a mathematical filter (`{"$lte": user_clearance}`) ensures that the similarity search engine completely ignores documents that exceed the querying user's security clearance[cite: 6].

### 4. Stage 3: Agentic Orchestration & State Management
Standard LLM scripts are fragile; if a model outputs malformed JSON, the script crashes. To build a robust, fault-tolerant system, a stateful multi-agent network was constructed using LangGraph (`agent_orchestrator.py`)[cite: 1, 7].
* **State Machine Design:** The workflow utilizes a `TypedDict` to persistently track messages, retrieved data, draft outputs, and validation errors across node transitions[cite: 1].
* **Specialized Nodes:** The process is divided among specialized functions: a Data Retrieval node, a Drafting Agent (powered by Llama 3), a Validation Agent, and a Correction Agent[cite: 1].
* **Self-Healing Loop:** The Validation Agent enforces the Pydantic data contract[cite: 1]. If the LLM generates conversational filler or omits a required field, the Router node detects the failure and conditionally routes the state to the Correction Agent[cite: 1]. This creates a self-healing loop that forces the system to correct its own formatting errors before terminating, drastically increasing the reliability of the automation.

### 5. Stage 4: Execution & Network Resilience
To replace the initial mocked data and mocked AI responses, the project was successfully upgraded to use real, local infrastructure:
* **Local AI Engine:** LangChain's `ChatOllama` module was integrated to route prompts to a locally hosted Llama 3 model (8-billion parameters), completely severing reliance on cloud APIs.
* **Network Fault Tolerance:** A gateway layer (`resilience_gateway.py`) was engineered using the Tenacity library[cite: 7]. By wrapping external network calls in `@retry` decorators with jittered exponential backoff, the pipeline was hardened to automatically recover from simulated 500 Server Errors, connection drops, and 429 Rate Limits without crashing[cite: 7].