/**
 * ============================================================================
 * ENTERPRISE DEVOPS AI AGENT - INTERACTIVE SHOWCASE ENGINE
 * Zero-Egress • LangGraph Multi-Agent • ChromaDB RBAC • Llama 3
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  initAgentFlowchart();
  initFunctionFlowchart();
  initPipelineSimulator();
  initRbacExplorer();
  initTokenDiffToggle();
  initSelfHealingDemo();
  initResilienceSimulator();
  initCopyButtons();
});

// ----------------------------------------------------------------------------
// 0. INTERACTIVE FLOWCHART OF AGENTS (LANGGRAPH STATEGRAPH)
// ----------------------------------------------------------------------------
function initAgentFlowchart() {
  const agentNodes = document.querySelectorAll('#agent-flowchart-grid .agent-node, #flow-node-correction');
  const animateBtn = document.getElementById('animate-agent-flow-btn');

  const inspectBadge = document.getElementById('inspect-node-badge');
  const inspectFunc = document.getElementById('inspect-func-name');
  const inspectTitle = document.getElementById('inspect-agent-title');
  const inspectDesc = document.getElementById('inspect-agent-desc');
  const inspectMutation = document.getElementById('inspect-state-mutation');
  const inspectCode = document.getElementById('inspect-code-snippet');

  const agentData = {
    start: {
      badge: "ENTRY POINT",
      func: "workflow.set_entry_point('tfs_retrieval')",
      title: "Graph Initialization & Trigger",
      desc: "Initializes the shared AgentState dictionary with the initial user prompt and sets up the execution graph schema.",
      mutation: "state = {'messages': ['...'], 'retry_count': 0, 'validation_errors': None}",
      code: `workflow = StateGraph(AgentState)\nworkflow.set_entry_point("tfs_retrieval")\nworkflow.add_edge("tfs_retrieval", "rag_retrieval")`
    },
    tfs: {
      badge: "NODE 1: TFS RETRIEVAL AGENT",
      func: "tfs_retrieval_agent(state: AgentState) -> AgentState",
      title: "TFS Work Item Retrieval & Pruning Agent",
      desc: "Executes Stage 1 WIQL query against the Azure DevOps REST API, batch-fetches full ticket metadata, strips HTML tags, and extracts only the essential fields into strongly-typed Pydantic summaries.",
      mutation: "state['tfs_items'] = [item.model_dump() for item in work_items]",
      code: `def tfs_retrieval_agent(state: AgentState) -> AgentState:\n    client = LocalTFSClient()\n    wiql = "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"\n    work_items = client.query_work_items(wiql)\n    state["tfs_items"] = [item.model_dump() for item in work_items]\n    return state`
    },
    rag: {
      badge: "NODE 2: RAG CONTEXT AGENT",
      func: "rag_retrieval_agent(state: AgentState) -> AgentState",
      title: "ChromaDB RBAC Context Retrieval Agent",
      desc: "Extracts keywords from active blockers and queries local ChromaDB vector store using mathematical where={'clearance': {'$lte': clearance}} filtering.",
      mutation: "state['rag_context'] = '\\n\\n'.join(combined_context)",
      code: `def rag_retrieval_agent(state: AgentState) -> AgentState:\n    user_clearance = state.get("user_clearance", 2)\n    chunks = execute_rbac_search(\n        query_text="NTLM timeout SLA retry policy",\n        user_clearance=user_clearance,\n        top_k=2\n    )\n    state["rag_context"] = "\\n\\n".join([c["content"] for c in chunks])\n    return state`
    },
    drafting: {
      badge: "NODE 3: SYNTHESIS / DRAFTING AGENT",
      func: "drafting_agent(state: AgentState) -> AgentState",
      title: "Zero-Egress Llama 3 Synthesis Agent",
      desc: "Injects pruned TFS items and RBAC SLA guidelines into local Llama 3 (via ChatOllama with format='json') to draft a structured incident synthesis.",
      mutation: "state['report_draft'] = response.content.strip()",
      code: `def drafting_agent(state: AgentState) -> AgentState:\n    llm = ChatOllama(model="llama3", format="json", temperature=0.1)\n    prompt = f"Synthesize these work items and SLA rules into JSON:\\n{state['tfs_items']}"\n    response = llm.invoke(prompt)\n    state["report_draft"] = response.content.strip()\n    return state`
    },
    validation: {
      badge: "NODE 4: VALIDATION AGENT",
      func: "validation_agent(state: AgentState) -> AgentState",
      title: "Pydantic Contract Enforcement Agent",
      desc: "Validates the raw LLM JSON draft against SprintReportSchema. If valid, populates final_report and clears errors; if invalid, captures ValidationError messages.",
      mutation: "state['final_report'] = validated_obj.model_dump(); state['validation_errors'] = None",
      code: `def validation_agent(state: AgentState) -> AgentState:\n    try:\n        data = json.loads(_extract_json_str(state['report_draft']))\n        validated = SprintReportSchema.model_validate(data)\n        state['final_report'] = validated.model_dump()\n        state['validation_errors'] = None\n    except ValidationError as e:\n        state['validation_errors'] = str(e)\n    return state`
    },
    correction: {
      badge: "NODE 5: CORRECTION AGENT (SELF-HEALING)",
      func: "correction_agent(state: AgentState) -> AgentState",
      title: "Self-Healing Schema Correction Agent",
      desc: "Triggered whenever validation fails. Increments retry_count and reprompts Llama 3 with the exact ValidationError traceback and previous malformed draft to self-heal.",
      mutation: "state['retry_count'] += 1; state['report_draft'] = corrected_content",
      code: `def correction_agent(state: AgentState) -> AgentState:\n    state['retry_count'] += 1\n    llm = ChatOllama(model="llama3", format="json", temperature=0.0)\n    prompt = f"Fix these schema errors in JSON:\\nERROR: {state['validation_errors']}"\n    response = llm.invoke(prompt)\n    state['report_draft'] = response.content.strip()\n    return state`
    },
    end: {
      badge: "TERMINAL NODE: OUTPUT",
      func: "app.invoke(initial_state) -> final_state",
      title: "Final Validated Sprint Report Output",
      desc: "Graph reaches END node. Returns the fully validated, deterministic, strongly-typed JSON report with zero egress and guaranteed contract compliance.",
      mutation: "final_report = state['final_report']",
      code: `workflow.add_conditional_edges(\n    "validation",\n    route_validation,\n    {"correction": "correction", "end": END}\n)\napp = workflow.compile()\nfinal_state = app.invoke(initial_state)`
    }
  };

  agentNodes.forEach(node => {
    node.addEventListener('click', () => {
      agentNodes.forEach(n => n.classList.remove('selected'));
      node.classList.add('selected');

      const agentKey = node.dataset.agent;
      const data = agentData[agentKey];
      if (!data) return;

      if (inspectBadge) inspectBadge.textContent = data.badge;
      if (inspectFunc) inspectFunc.textContent = data.func;
      if (inspectTitle) inspectTitle.textContent = data.title;
      if (inspectDesc) inspectDesc.textContent = data.desc;
      if (inspectMutation) inspectMutation.textContent = data.mutation;
      if (inspectCode) inspectCode.textContent = data.code;
    });
  });

  if (animateBtn) {
    animateBtn.addEventListener('click', async () => {
      animateBtn.disabled = true;
      const flowOrder = ['start', 'tfs', 'rag', 'drafting', 'validation', 'correction', 'validation', 'end'];

      for (const key of flowOrder) {
        agentNodes.forEach(n => {
          if (n.dataset.agent === key) {
            n.click();
            n.style.transform = 'translateY(-8px) scale(1.06)';
            n.style.borderColor = 'var(--cyan)';
          } else {
            n.style.transform = '';
            n.style.borderColor = '';
          }
        });
        await new Promise(r => setTimeout(r, 700));
      }

      animateBtn.disabled = false;
    });
  }
}

// ----------------------------------------------------------------------------
// 0.5. INTERACTIVE FLOWCHART OF MAJOR FUNCTIONS
// ----------------------------------------------------------------------------
function initFunctionFlowchart() {
  const funcCards = document.querySelectorAll('.func-card');
  const detailBadge = document.getElementById('func-detail-badge');
  const detailTitle = document.getElementById('func-detail-title');
  const detailDesc = document.getElementById('func-detail-desc');
  const detailModule = document.getElementById('func-detail-module');
  const detailSignature = document.getElementById('func-detail-signature');

  const funcData = {
    seed_db: {
      badge: "DATABASE SEEDER",
      title: "seed_database(verbose: bool = True) -> None",
      desc: "Reads the raw TFS JSON seed dataset, creates the local SQLite database schema, populates 12 enterprise work items with priority, severity, and HTML descriptions, and generates an offline mock dataset.",
      module: "src/emulator/seeder.py",
      sig: `def seed_database(verbose: bool = True) -> None:\n    \"\"\"Initializes and seeds local_tfs.db with authentic Azure DevOps enterprise work items.\"\"\"`
    },
    parse_wiql: {
      badge: "QUERY TRANSLATOR",
      title: "parse_wiql_to_sql(wiql_query: str) -> tuple[str, list]",
      desc: "Translates Azure DevOps WIQL syntax (e.g. [System.State] = 'Active' and [System.WorkItemType] = 'Bug') into parameterized SQLite SQL queries.",
      module: "src/emulator/server.py",
      sig: `def parse_wiql_to_sql(wiql_query: str) -> tuple[str, list]:\n    \"\"\"Translates Azure DevOps WIQL syntax into SQLite SQL.\"\"\"`
    },
    api_wiql: {
      badge: "FASTAPI STAGE 1 ENDPOINT",
      title: "POST /_apis/wit/wiql",
      desc: "Stage 1 REST API endpoint. Accepts a WIQL JSON payload, executes SQL translation against SQLite, and returns an array of matching work item IDs.",
      module: "src/emulator/server.py",
      sig: `@app.post("/_apis/wit/wiql")\ndef execute_wiql(payload: WIQLRequest) -> dict:\n    \"\"\"Returns: {'workItems': [{'id': 10241}, ...]}\"\"\"`
    },
    clean_html: {
      badge: "DATA SANITIZER & PRUNER",
      title: "clean_html(raw_html: str) -> str",
      desc: "Strips all HTML tags (<div>, <p>, <b>, <code>) and unescapes XML/HTML entities (&lt;, &gt;) to eliminate 82% of verbose context window overhead.",
      module: "src/emulator/client.py",
      sig: `@staticmethod\ndef clean_html(raw_html: str) -> str:\n    \"\"\"Strips HTML tags & unescapes entities for clean LLM prompt context.\"\"\"`
    },
    split_text: {
      badge: "SEMANTIC CHUNKER",
      title: "RecursiveCharacterTextSplitter.split_text(text: str) -> List[str]",
      desc: "Splits enterprise markdown architecture specifications using sliding window chunks (300 characters, 50 character overlap) while preserving markdown header structure.",
      module: "src/rag/indexer.py",
      sig: `splitter = RecursiveCharacterTextSplitter(\n    chunk_size=300,\n    chunk_overlap=50,\n    separators=["\\n## ", "\\n\\n", "\\n", " ", ""]\n)`
    },
    chroma_client: {
      badge: "PERSISTENT VECTOR DB",
      title: "chromadb.PersistentClient(path: str)",
      desc: "Initializes local on-disk ChromaDB persistent vector storage at data/local_chroma_db with zero cloud dependencies.",
      module: "src/rag/indexer.py",
      sig: `client = chromadb.PersistentClient(path="./data/local_chroma_db")\ncollection = client.get_or_create_collection(name="enterprise_architecture")`
    },
    collection_add: {
      badge: "VECTOR EMBEDDING & RBAC",
      title: "collection.add(documents, metadatas, ids)",
      desc: "Embeds text chunks into 384-dimensional dense vectors using local ONNX all-MiniLM-L6-v2 embeddings and attaches RBAC clearance metadata tags (Levels 1, 2, 3).",
      module: "src/rag/indexer.py",
      sig: `collection.add(\n    documents=chunks,\n    metadatas=[{"clearance": 2, "source": "adjudication_architecture.md", ...}],\n    ids=[f"chunk_{i}"]\n)`
    },
    rbac_search: {
      badge: "MATHEMATICAL RBAC QUERY",
      title: "execute_rbac_search(query_text, user_clearance, top_k=2) -> List[dict]",
      desc: "Executes cosine similarity search against ChromaDB while enforcing where={'clearance': {'$lte': user_clearance}} at the vector database mathematical layer.",
      module: "src/rag/search.py",
      sig: `def execute_rbac_search(query_text: str, user_clearance: int = 1, top_k: int = 2) -> List[dict]:\n    \"\"\"Filters out unauthorized clearance tiers directly in vector math.\"\"\"`
    },
    stategraph: {
      badge: "LANGGRAPH STATE MACHINE",
      title: "StateGraph(AgentState) -> CompiledGraph",
      desc: "Defines the multi-agent graph nodes, directional edges, and conditional routing functions for autonomous error-recovery and state passing.",
      module: "src/agents/orchestrator.py",
      sig: `workflow = StateGraph(AgentState)\nworkflow.add_node("tfs_retrieval", tfs_retrieval_agent)\nworkflow.add_node("rag_retrieval", rag_retrieval_agent)\nworkflow.add_node("drafting", drafting_agent)\nworkflow.add_node("validation", validation_agent)\nworkflow.add_node("correction", correction_agent)`
    },
    drafting_agent: {
      badge: "LOCAL LLM INVOCATION",
      title: "drafting_agent(state: AgentState) -> AgentState",
      desc: "Invokes local zero-egress Llama 3 via ChatOllama(model='llama3', format='json', temperature=0.1) to synthesize TFS work items and internal SLA guidelines.",
      module: "src/agents/orchestrator.py",
      sig: `def drafting_agent(state: AgentState) -> AgentState:\n    llm = ChatOllama(model="llama3", format="json", temperature=0.1)\n    response = llm.invoke(system_prompt)\n    state["report_draft"] = response.content.strip()\n    return state`
    },
    validation_agent: {
      badge: "PYDANTIC CONTRACT CHECK",
      title: "validation_agent(state: AgentState) -> AgentState",
      desc: "Extracts JSON substring from LLM response and validates against SprintReportSchema.populating final_report on success or capturing ValidationError traces.",
      module: "src/agents/orchestrator.py",
      sig: `def validation_agent(state: AgentState) -> AgentState:\n    json_str = _extract_json_str(state["report_draft"])\n    validated = SprintReportSchema.model_validate(json.loads(json_str))\n    state["final_report"] = validated.model_dump()\n    return state`
    },
    correction_agent: {
      badge: "AUTONOMOUS RECOVERY",
      title: "correction_agent(state: AgentState) -> AgentState",
      desc: "Self-healing node triggered on validation failures. Injects the exact ValidationError traceback back into Llama 3 with zero human intervention.",
      module: "src/agents/orchestrator.py",
      sig: `def correction_agent(state: AgentState) -> AgentState:\n    state["retry_count"] += 1\n    llm = ChatOllama(model="llama3", format="json", temperature=0.0)\n    response = llm.invoke(correction_prompt)\n    state["report_draft"] = response.content.strip()\n    return state`
    },
    tenacity_retry: {
      badge: "FAULT-TOLERANT DECORATOR",
      title: "@retry(wait=wait_exponential_jitter, stop=stop_after_attempt(3))",
      desc: "Production retry policy using Tenacity to automatically intercept transient 503, 504, and connection reset errors with randomized ±150ms jitter.",
      module: "src/resilience/gateway.py",
      sig: `@retry(\n    stop=stop_after_attempt(3),\n    wait=wait_exponential(multiplier=1, min=0.5, max=5) + wait_random(-0.15, 0.15),\n    retry=retry_if_exception_type(TransientHTTPError)\n)`
    },
    gateway_call: {
      badge: "RESILIENCE GATEWAY",
      title: "LocalTFSGateway.call_with_retry(endpoint, params) -> dict",
      desc: "Wraps raw HTTP calls in exponential backoff policies, preventing transient domain controller downtime from crashing the agent pipeline.",
      module: "src/resilience/gateway.py",
      sig: `def call_with_retry(self, endpoint: str, params: dict = None) -> dict:\n    \"\"\"Resilient execution wrapper over TFS REST endpoints.\"\"\"`
    },
    structured_llm: {
      badge: "TYPE-SAFE INTERFACE",
      title: "llm.with_structured_output(PydanticModel)",
      desc: "Binds a Pydantic schema to any LLM (Ollama Llama 3, Google Gemini, OpenAI GPT-4o, Anthropic Claude), guaranteeing strongly typed response parsing.",
      module: "legacy_scripts/real_llm_guide.py",
      sig: `structured_llm = llm.with_structured_output(WorkItemRemediation)\nresult: WorkItemRemediation = structured_llm.invoke("Bug 10241: NTLM timeout...")`
    },
    main_pipeline: {
      badge: "UNIFIED CLI & PIPELINE",
      title: "main.py: run_pipeline() -> None",
      desc: "Master orchestration runner executing Seeder -> ChromaDB Indexer -> LangGraph Multi-Agent Orchestrator end-to-end in a single command.",
      module: "main.py",
      sig: `def run_pipeline() -> None:\n    \"\"\"Runs entire TFS DevOps AI Agent ecosystem end-to-end.\"\"\"`
    }
  };

  funcCards.forEach(card => {
    card.addEventListener('click', () => {
      funcCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');

      const funcKey = card.dataset.func;
      const data = funcData[funcKey];
      if (!data) return;

      if (detailBadge) detailBadge.textContent = data.badge;
      if (detailTitle) detailTitle.textContent = data.title;
      if (detailDesc) detailDesc.textContent = data.desc;
      if (detailModule) detailModule.textContent = data.module;
      if (detailSignature) detailSignature.textContent = data.sig;
    });
  });
}

// ----------------------------------------------------------------------------
// 1. LIVE PIPELINE SIMULATOR
// ----------------------------------------------------------------------------
function initPipelineSimulator() {
  const runBtn = document.getElementById('run-sim-btn');
  const terminal = document.getElementById('sim-terminal-logs');
  const finalJsonBlock = document.getElementById('sim-final-json');
  const statusBadge = document.getElementById('sim-status-badge');
  const stepItems = document.querySelectorAll('.sim-step-item');

  if (!runBtn) return;

  const mockSteps = [
    {
      stepIndex: 0,
      badgeText: "INGESTING TFS",
      log: `[00.12s] [TFS Client] Executing Stage 1 WIQL query:
         SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'
[00.25s] [TFS Client] Stage 1 returned 4 Work Item IDs: [10241, 10243, 10245, 10251]
[00.41s] [TFS Client] Executing Stage 2 Batch GET for IDs -> [10241, 10243, 10245, 10251]
[00.58s] [TFS Client] Sanitized HTML markup and pruned payload (82% token reduction).`,
    },
    {
      stepIndex: 1,
      badgeText: "CHROMA RAG RBAC",
      log: `[00.82s] [RAG Agent] Connecting to local ChromaDB at 'data/local_chroma_db'
[00.95s] [RAG Agent] Applying mathematical RBAC filter: { "clearance": { "$lte": 2 } }
[01.12s] [RAG Agent] Retrieved 3 relevant architecture chunks:
         • [Chunk #02 - Clearance Level 1]: engineering_handbook.md
         • [Chunk #06 - Clearance Level 2]: adjudication_architecture.md
         • [Chunk #09 - Clearance Level 2]: adjudication_architecture.md
[01.20s] [RAG Agent] 🔒 Clearance Level 3 audit policies mathematically hidden from context.`,
    },
    {
      stepIndex: 2,
      badgeText: "LLAMA 3 SYNTHESIS",
      log: `[01.45s] [Drafting Agent] Prompting local zero-egress Llama 3 on Ollama (model='llama3')
[01.60s] [Drafting Agent] Injected 4 pruned TFS items + 3 RBAC SLA guidelines.
[02.10s] [Drafting Agent] Streaming tokens from local GPU/CPU memory...
[02.85s] [Drafting Agent] Synthesis complete. Generating raw structured output.`,
    },
    {
      stepIndex: 3,
      badgeText: "PYDANTIC VALIDATION",
      log: `[03.02s] [Validation Agent] Validating draft against 'SprintReportSchema'
[03.15s] [Validation Agent] Contract Check:
         • sprint_id: str -> 'Sprint 12' [OK]
         • overall_status: str -> 'At Risk' [OK]
         • active_bugs_count: int -> 3 [OK]
         • critical_blockers: List[str] -> (3 items) [OK]
         • architecture_remediations: List[str] -> (2 items) [OK]
[03.24s] [Validation Agent] ✅ 0 Schema Violations detected. Routing -> END.`,
    }
  ];

  const finalSprintReport = {
    "sprint_id": "Sprint 12",
    "overall_status": "At Risk",
    "active_bugs_count": 3,
    "critical_blockers": [
      "NTLM Handshake Timeout Exception in Adjudication Service (#10241)",
      "Database Connection Pool Exhaustion under Peak Traffic (#10243)",
      "ChromaDB Embedding Dimension Mismatch on Document Ingest (#10245)"
    ],
    "architecture_remediations": [
      "Implement jittered exponential backoff and retry policy for NTLM authentication handshakes (SLA Rule 4.2.1).",
      "Set check_same_thread=False and implement a connection lease timeout manager for SQLite connection handles under concurrent FastAPI worker requests."
    ],
    "sla_risk_summary": "Sprint 12 is at risk due to critical blockers violating architecture SLAs. Immediate remediation required for NTLM timeouts and SQLite database pooling to prevent production claim adjudication delays."
  };

  runBtn.addEventListener('click', async () => {
    runBtn.disabled = true;
    runBtn.innerHTML = `
      <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
        <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
      </svg>
      Executing Agent Pipeline...
    `;
    terminal.innerHTML = '<span class="t-cyan">🚀 [Orchestrator] Initializing LangGraph StateGraph...</span>\n';
    finalJsonBlock.textContent = '// Synthesizing output...';
    
    // Reset steps
    stepItems.forEach(item => {
      item.classList.remove('active', 'completed');
    });

    for (let i = 0; i < mockSteps.length; i++) {
      const step = mockSteps[i];
      const el = stepItems[step.stepIndex];
      
      el.classList.add('active');
      statusBadge.textContent = step.badgeText;
      statusBadge.className = 'badge badge-cyan';

      terminal.innerHTML += `\n<span class="t-yellow">-> [Node ${i+1}] ${step.badgeText}...</span>\n` + step.log + '\n';
      terminal.scrollTop = terminal.scrollHeight;

      await new Promise(r => setTimeout(r, 900));
      
      el.classList.remove('active');
      el.classList.add('completed');
    }

    statusBadge.textContent = 'COMPLETED';
    statusBadge.className = 'badge badge-emerald';
    terminal.innerHTML += '\n<span class="t-green">🎯 [Orchestrator] Multi-Agent Pipeline Completed Successfully in 3.24s!</span>';
    terminal.scrollTop = terminal.scrollHeight;

    finalJsonBlock.textContent = JSON.stringify(finalSprintReport, null, 2);
    runBtn.disabled = false;
    runBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      Re-run Pipeline Simulation
    `;
  });
}

// ----------------------------------------------------------------------------
// 2. RBAC CLEARANCE EXPLORER
// ----------------------------------------------------------------------------
function initRbacExplorer() {
  const pills = document.querySelectorAll('.clearance-pill');
  const docCards = document.querySelectorAll('.doc-chunk-card');
  const countDisplay = document.getElementById('rbac-accessible-count');

  if (!pills.length) return;

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      const clearanceLevel = parseInt(pill.dataset.level, 10);
      let accessibleCount = 0;

      docCards.forEach(card => {
        const requiredLevel = parseInt(card.dataset.level, 10);
        const lockBadge = card.querySelector('.rbac-status-badge');

        if (clearanceLevel >= requiredLevel) {
          card.classList.remove('locked');
          card.classList.add('unlocked');
          lockBadge.innerHTML = '<span class="badge badge-emerald">🔓 ACCESSIBLE (Level ' + requiredLevel + ')</span>';
          accessibleCount++;
        } else {
          card.classList.remove('unlocked');
          card.classList.add('locked');
          lockBadge.innerHTML = '<span class="badge badge-rose">🔒 BLOCKED (Requires Level ' + requiredLevel + ')</span>';
        }
      });

      if (countDisplay) {
        countDisplay.textContent = `${accessibleCount} of ${docCards.length} chunks accessible`;
      }
    });
  });
}

// ----------------------------------------------------------------------------
// 3. TWO-STAGE INGESTION & TOKEN DIFF TOGGLE
// ----------------------------------------------------------------------------
function initTokenDiffToggle() {
  const tabs = document.querySelectorAll('.diff-tab-btn');
  const rawBox = document.getElementById('diff-raw-box');
  const prunedBox = document.getElementById('diff-pruned-box');

  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const mode = tab.dataset.mode;
      if (mode === 'side-by-side') {
        if (rawBox) rawBox.style.display = 'block';
        if (prunedBox) prunedBox.style.display = 'block';
      } else if (mode === 'pruned-only') {
        if (rawBox) rawBox.style.display = 'none';
        if (prunedBox) prunedBox.style.display = 'block';
      } else if (mode === 'raw-only') {
        if (rawBox) rawBox.style.display = 'block';
        if (prunedBox) prunedBox.style.display = 'none';
      }
    });
  });
}

// ----------------------------------------------------------------------------
// 4. SELF-HEALING STATEGRAPH DEMO
// ----------------------------------------------------------------------------
function initSelfHealingDemo() {
  const triggerBtn = document.getElementById('trigger-heal-btn');
  const healStatus = document.getElementById('heal-status-badge');
  const attempt2Box = document.getElementById('heal-attempt-2');

  if (!triggerBtn) return;

  triggerBtn.addEventListener('click', async () => {
    triggerBtn.disabled = true;
    healStatus.textContent = "HEALING...";
    healStatus.className = "badge badge-amber";

    if (attempt2Box) {
      attempt2Box.style.opacity = '0.4';
      attempt2Box.style.borderColor = 'var(--amber)';
    }

    await new Promise(r => setTimeout(r, 1200));

    if (attempt2Box) {
      attempt2Box.style.opacity = '1';
      attempt2Box.style.borderColor = 'var(--emerald)';
    }

    healStatus.textContent = "AUTONOMOUSLY HEALED";
    healStatus.className = "badge badge-emerald";
    triggerBtn.disabled = false;
  });
}

// ----------------------------------------------------------------------------
// 5. NETWORK RESILIENCE SIMULATOR
// ----------------------------------------------------------------------------
function initResilienceSimulator() {
  const retryBtn = document.getElementById('sim-retry-btn');
  const nodes = document.querySelectorAll('.retry-node');
  const summaryBox = document.getElementById('retry-summary-text');

  if (!retryBtn) return;

  retryBtn.addEventListener('click', async () => {
    retryBtn.disabled = true;
    retryBtn.innerHTML = 'Simulating Outage & Retries...';

    nodes.forEach(n => {
      n.style.borderColor = 'var(--border-color)';
      n.style.background = 'var(--bg-tertiary)';
    });
    if (summaryBox) summaryBox.textContent = 'Simulating network connection...';

    // Step 1: Attempt 1
    nodes[0].style.borderColor = 'var(--rose)';
    nodes[0].style.background = 'rgba(244, 63, 94, 0.08)';
    if (summaryBox) summaryBox.textContent = 'Attempt 1: Received HTTP 503 (Domain Controller Timeout). Applying backoff...';
    await new Promise(r => setTimeout(r, 800));

    // Step 2: Attempt 2
    nodes[1].style.borderColor = 'var(--amber)';
    nodes[1].style.background = 'rgba(245, 158, 11, 0.08)';
    if (summaryBox) summaryBox.textContent = 'Attempt 2: Received HTTP 503 (Socket Hangup). Applying jittered backoff (1240ms)...';
    await new Promise(r => setTimeout(r, 1200));

    // Step 3: Attempt 3
    nodes[2].style.borderColor = 'var(--emerald)';
    nodes[2].style.background = 'rgba(16, 185, 129, 0.08)';
    if (summaryBox) summaryBox.textContent = '✅ Attempt 3: HTTP 200 OK! Payload successfully ingested without crashing the pipeline.';
    
    retryBtn.disabled = false;
    retryBtn.innerHTML = 'Re-run Resilience Simulation';
  });
}

// ----------------------------------------------------------------------------
// 6. COPY BUTTONS
// ----------------------------------------------------------------------------
function initCopyButtons() {
  const copyBtns = document.querySelectorAll('.copy-btn');

  copyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      navigator.clipboard.writeText(targetEl.textContent).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span>Copied!</span>';
        setTimeout(() => {
          btn.innerHTML = originalHtml;
        }, 2000);
      });
    });
  });
}
