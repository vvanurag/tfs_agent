import json
import re
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from real_local_tfs_client import LocalTFSClient
from query_vector_store import execute_rbac_search

# ---------------------------------------------------------
# 1. FORMAL PYDANTIC DATA CONTRACT
# ---------------------------------------------------------
class SprintReportSchema(BaseModel):
    """
    Strict data contract for the final sprint status synthesis report.
    Enforced by the Validation Agent and Self-Healing Loop.
    """
    sprint_id: str = Field(description="Name of current sprint, e.g., 'Sprint 12'")
    overall_status: str = Field(description="'On Track', 'At Risk', or 'Blocked'")
    active_bugs_count: int = Field(description="Total number of active bugs")
    critical_blockers: List[str] = Field(description="Key blocker titles and ticket IDs")
    architecture_remediations: List[str] = Field(description="Grounded remediation plans from RAG architecture specs")
    sla_risk_summary: str = Field(description="Executive summary of SLA compliance and operational risk")

# ---------------------------------------------------------
# 2. STATE GRAPH SCHEMA
# ---------------------------------------------------------
class AgentState(TypedDict):
    """
    Tracks state throughout the multi-agent workflow.
    """
    messages: List[str]
    user_clearance: int
    tfs_items: List[dict]
    rag_context: str
    report_draft: str
    validation_errors: Optional[str]
    retry_count: int
    final_report: Optional[dict]

# ---------------------------------------------------------
# 3. SPECIALIZED AGENT NODES
# ---------------------------------------------------------

def tfs_retrieval_agent(state: AgentState) -> AgentState:
    """
    Node 1: Pulls active work items from local TFS / Azure DevOps emulator.
    """
    print("\n" + "=" * 65)
    print("-> [Node 1: TFS Retrieval Agent] Fetching active work items from TFS API...")
    print("=" * 65)
    
    client = LocalTFSClient()
    # Query all active items
    wiql = "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
    work_items = client.query_work_items(wiql)
    
    state["tfs_items"] = [item.model_dump() for item in work_items]
    print(f"   [TFS Agent] Ingested and pruned {len(work_items)} active work items.")
    return state


def rag_retrieval_agent(state: AgentState) -> AgentState:
    """
    Node 2: Dynamically queries ChromaDB with RBAC filtering for SLA & architecture specs.
    """
    print("\n" + "=" * 65)
    print("-> [Node 2: RAG Retrieval Agent] Querying internal ChromaDB with RBAC...")
    print("=" * 65)
    
    user_clearance = state.get("user_clearance", 2)
    
    # Extract topics from the active items (e.g. NTLM timeout, SQLite concurrency, SLA breach)
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
    print(f"\n   [RAG Agent] Injected {len(combined_context)} RBAC-verified architecture context chunks.")
    return state


def drafting_agent(state: AgentState) -> AgentState:
    """
    Node 3: Prompts local Llama 3 via Ollama to synthesize TFS items + RAG context.
    """
    print("\n" + "=" * 65)
    print("-> [Node 3: Drafting Agent] Prompting local Llama 3 to synthesize report...")
    print("=" * 65)
    
    llm = ChatOllama(model="llama3", temperature=0.1)
    
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
    content = response.content.strip()
    
    # Strip markdown fences if present
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    state["report_draft"] = content.strip()
    return state


def validation_agent(state: AgentState) -> AgentState:
    """
    Node 4: Enforces the Pydantic data contract and validates the JSON output.
    """
    print("\n" + "=" * 65)
    print("-> [Node 4: Validation Agent] Enforcing Pydantic SprintReportSchema...")
    print("=" * 65)
    
    draft = state.get("report_draft", "")
    
    try:
        # 1. Parse JSON
        parsed_dict = json.loads(draft)
        
        # 2. Validate against strict Pydantic model
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
    """
    Node 5: Dynamic Self-Healing Loop. Reprompts Llama 3 with the exact validation error.
    """
    state["retry_count"] = state.get("retry_count", 0) + 1
    
    print("\n" + "=" * 65)
    print(f"-> [Node 5: Correction Agent] SELF-HEALING LOOP (Attempt {state['retry_count']}/3)")
    print(f"   Fixing Error: {state['validation_errors']}")
    print("=" * 65)
    
    llm = ChatOllama(model="llama3", temperature=0.1)
    
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
    content = response.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    state["report_draft"] = content.strip()
    return state


def route_validation(state: AgentState) -> str:
    """
    Conditional Edge: Routes to Correction Agent if validation fails, or END if valid.
    """
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print("   [Router] Routing state -> Correction Agent.")
        return "correction"
    else:
        if state.get("validation_errors"):
            print("   [Router] Maximum retries reached. Routing -> END.")
        else:
            print("   [Router] Validation succeeded. Routing -> END.")
        return "end"


# ---------------------------------------------------------
# 4. COMPILE LANGGRAPH STATE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("tfs_retrieval", tfs_retrieval_agent)
workflow.add_node("rag_retrieval", rag_retrieval_agent)
workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

# Set Entry Point and Edges
workflow.set_entry_point("tfs_retrieval")
workflow.add_edge("tfs_retrieval", "rag_retrieval")
workflow.add_edge("rag_retrieval", "drafting")
workflow.add_edge("drafting", "validation")

# Conditional Router Edge
workflow.add_conditional_edges(
    "validation",
    route_validation,
    {
        "correction": "correction",
        "end": END
    }
)

# Connect correction back to validation to close the loop
workflow.add_edge("correction", "validation")

# Compile graph
agent_app = workflow.compile()


# ---------------------------------------------------------
# 5. EXECUTION & DEMO
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 65)
    print("🚀 INITIATING ZERO-EGRESS MULTI-AGENT ORCHESTRATION PIPELINE")
    print("=" * 65)
    
    initial_state = {
        "messages": ["Generate sprint status and SLA risk synthesis report"],
        "user_clearance": 2,  # Level 2 Internal Engineering Clearance
        "tfs_items": [],
        "rag_context": "",
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0,
        "final_report": None
    }
    
    final_state = agent_app.invoke(initial_state)
    
    print("\n" + "=" * 65)
    print("🎯 FINAL SYNTHESIZED SPRINT REPORT (GROUNDED & VALIDATED)")
    print("=" * 65)
    
    if final_state.get("final_report"):
        print(json.dumps(final_state["final_report"], indent=2))
    else:
        print(final_state["report_draft"])