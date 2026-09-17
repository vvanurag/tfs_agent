import json
import re
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from src.emulator.client import LocalTFSClient
from src.rag.search import execute_rbac_search
from .schemas import SprintReportSchema, AgentState

def tfs_retrieval_agent(state: AgentState) -> AgentState:
    print("\n" + "=" * 65)
    print("-> [Node 1: TFS Retrieval Agent] Fetching active work items from TFS API...")
    print("=" * 65)
    
    client = LocalTFSClient()
    wiql = "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
    work_items = client.query_work_items(wiql)
    
    state["tfs_items"] = [item.model_dump() for item in work_items]
    print(f"   [TFS Agent] Ingested and pruned {len(work_items)} active work items.")
    return state

def rag_retrieval_agent(state: AgentState) -> AgentState:
    print("\n" + "=" * 65)
    print("-> [Node 2: RAG Retrieval Agent] Querying internal ChromaDB with RBAC...")
    print("=" * 65)
    
    user_clearance = state.get("user_clearance", 2)
    search_queries = [
        "NTLM handshake timeout SLA retry policy",
        "Adjudication batch claim processing SLA timeout",
        "Database connection pool SQLite concurrency"
    ]
    
    combined_context = []
    for query in search_queries:
        chunks = execute_rbac_search(
            query_text=query,
            user_clearance=user_clearance,
            top_k=1
        )
        for chunk in chunks:
            meta = chunk["metadata"]
            combined_context.append(
                f"[{meta.get('title')} - Clearance Level {meta.get('clearance')}]:\n{chunk['content']}"
            )
            
    state["rag_context"] = "\n\n".join(combined_context)
    print(f"   [RAG Agent] Injected {len(combined_context)} RBAC-verified architecture context chunks.")
    return state

def _extract_json_str(raw_text: str) -> str:
    """Robustly extracts JSON substring from markdown fences or conversational chatter."""
    if not raw_text:
        return ""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()

def drafting_agent(state: AgentState) -> AgentState:
    print("\n" + "=" * 65)
    print("-> [Node 3: Drafting Agent] Prompting local Llama 3 to synthesize report...")
    print("=" * 65)
    
    llm = ChatOllama(model="llama3", format="json", temperature=0.1)
    tfs_text = json.dumps(state["tfs_items"][:5], indent=2)
    rag_text = state["rag_context"]
    
    system_prompt = f"""You are an expert Enterprise AI DevOps Copilot.
You must synthesize active TFS work items and internal architecture SLA guidelines into a formal JSON report.

You MUST respond with ONLY a valid, raw JSON object matching this exact schema:
{{
  "sprint_id": "Sprint 12",
  "overall_status": "At Risk",
  "active_bugs_count": <integer count of active bugs>,
  "critical_blockers": ["<string summary of blocker 1>", ...],
  "architecture_remediations": ["<string remediation step citing SLA/architecture rules>", ...],
  "sla_risk_summary": "<string executive summary of SLA impact>"
}}

Do NOT include any markdown code fences (like ```json), commentary, or extra text. Output ONLY the JSON string.

=== ACTIVE TFS WORK ITEMS ===
{tfs_text}

=== INTERNAL ARCHITECTURE & SLA POLICIES ===
{rag_text}
"""

    response = llm.invoke(system_prompt)
    state["report_draft"] = response.content.strip()
    return state

def validation_agent(state: AgentState) -> AgentState:
    print("\n" + "=" * 65)
    print("-> [Node 4: Validation Agent] Enforcing Pydantic SprintReportSchema...")
    print("=" * 65)
    
    raw_draft = state.get("report_draft", "")
    try:
        json_str = _extract_json_str(raw_draft)
        parsed_dict = json.loads(json_str)
        validated_obj = SprintReportSchema.model_validate(parsed_dict)
        state["final_report"] = validated_obj.model_dump()
        state["validation_errors"] = None
        print("   ✅ [Validation Agent] Pydantic Contract PASSED with 0 errors.")
    except json.JSONDecodeError as e:
        state["validation_errors"] = f"JSON Syntax Error: {str(e)}"
        print(f"   ❌ [Validation Agent] FAILED: {state['validation_errors']}")
    except ValidationError as e:
        error_messages = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        state["validation_errors"] = f"Pydantic Validation Errors: {'; '.join(error_messages)}"
        print(f"   ❌ [Validation Agent] FAILED: {state['validation_errors']}")
        
    return state

def correction_agent(state: AgentState) -> AgentState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    print("\n" + "=" * 65)
    print(f"-> [Node 5: Correction Agent] SELF-HEALING LOOP (Attempt {state['retry_count']}/3)")
    print(f"   Fixing Error: {state['validation_errors']}")
    print("=" * 65)
    
    llm = ChatOllama(model="llama3", format="json", temperature=0.1)
    correction_prompt = f"""Your previous output failed strict enterprise Pydantic validation.

VALIDATION ERROR:
{state['validation_errors']}

PREVIOUS MALFORMED DRAFT:
{state['report_draft']}

Please fix the error and output ONLY the corrected, valid JSON object with ALL required fields:
- sprint_id (string)
- overall_status ('On Track', 'At Risk', or 'Blocked')
- active_bugs_count (integer)
- critical_blockers (list of strings)
- architecture_remediations (list of strings)
- sla_risk_summary (string)

Output ONLY raw JSON with no explanation or formatting tags.
"""
    response = llm.invoke(correction_prompt)
    state["report_draft"] = response.content.strip()
    return state

def route_validation(state: AgentState) -> str:
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print("   [Router] Routing state -> Correction Agent.")
        return "correction"
    else:
        if state.get("validation_errors"):
            print("   [Router] Maximum retries reached. Routing -> END.")
        else:
            print("   [Router] Validation succeeded. Routing -> END.")
        return "end"

# Compile Workflow Graph
workflow = StateGraph(AgentState)
workflow.add_node("tfs_retrieval", tfs_retrieval_agent)
workflow.add_node("rag_retrieval", rag_retrieval_agent)
workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

workflow.set_entry_point("tfs_retrieval")
workflow.add_edge("tfs_retrieval", "rag_retrieval")
workflow.add_edge("rag_retrieval", "drafting")
workflow.add_edge("drafting", "validation")
workflow.add_conditional_edges("validation", route_validation, {"correction": "correction", "end": END})
workflow.add_edge("correction", "validation")

agent_app = workflow.compile()

def run_orchestrator(clearance: int = 2) -> dict:
    """Executes the full multi-agent pipeline."""
    initial_state = {
        "messages": ["Generate sprint status and SLA risk synthesis report"],
        "user_clearance": clearance,
        "tfs_items": [],
        "rag_context": "",
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0,
        "final_report": None
    }
    return agent_app.invoke(initial_state)

if __name__ == "__main__":
    result = run_orchestrator()
    print("\n" + "=" * 65)
    print("FINAL SPRINT REPORT:")
    print("=" * 65)
    print(json.dumps(result.get("final_report") or result.get("report_draft"), indent=2))
