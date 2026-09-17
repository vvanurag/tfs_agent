/**
 * ============================================================================
 * ENTERPRISE DEVOPS AI AGENT - INTERACTIVE SHOWCASE ENGINE
 * Zero-Egress • LangGraph Multi-Agent • ChromaDB RBAC • Llama 3
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  initPipelineSimulator();
  initRbacExplorer();
  initTokenDiffToggle();
  initSelfHealingDemo();
  initResilienceSimulator();
  initCopyButtons();
});

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
