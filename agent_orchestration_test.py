import json
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# ---------------------------------------------------------
# 1. SETUP GRAPH STATE
# ---------------------------------------------------------
class AgentState(TypedDict):
    messages: List[str]
    report_draft: str
    validation_errors: str
    retry_count: int

# ---------------------------------------------------------
# 2. IMPLEMENT SPECIALIZED NODES WITH REAL LLAMA 3
# ---------------------------------------------------------
def drafting_agent(state: AgentState):
    """Generates the structured project update report using real local Llama 3."""
    print("-> [Node: Drafting Agent] Synthesizing data with local Llama 3...")
    
    llm = ChatOllama(model="llama3", temperature=0.1)
    prompt = f"""You are an AI assistant. Output ONLY a valid JSON object with the following keys:
- sprint_id: (e.g. 'Sprint 12')
- status: ('At Risk' or 'On Track')
- blockers: (summary of blockers)

User Task: {state['messages'][0]}
"""
    response = llm.invoke(prompt)
    content = response.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    state["report_draft"] = content.strip()
    return state

def validation_agent(state: AgentState):
    """Checks if required fields are present in the JSON output."""
    print("-> [Node: Validation Agent] Enforcing data contract...")
    
    try:
        draft_dict = json.loads(state["report_draft"])
        if "blockers" not in draft_dict:
            state["validation_errors"] = "Missing required field: 'blockers'"
        elif "status" not in draft_dict:
            state["validation_errors"] = "Missing required field: 'status'"
        else:
            state["validation_errors"] = None
    except json.JSONDecodeError:
        state["validation_errors"] = "Output is not valid JSON."
        
    return state

def correction_agent(state: AgentState):
    """Triggered if validation fails; reprompts Llama 3 with the exact error."""
    print(f"-> [Node: Correction Agent] Fixing errors with Llama 3: {state['validation_errors']}")
    state["retry_count"] += 1
    
    llm = ChatOllama(model="llama3", temperature=0.1)
    prompt = f"""Your previous response had an error: {state['validation_errors']}.
Previous text: {state['report_draft']}
Please fix it and output ONLY a valid JSON object with 'sprint_id', 'status', and 'blockers'."""
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    state["report_draft"] = content.strip()
    return state

# ---------------------------------------------------------
# 3. DEFINE CONDITIONAL EDGES
# ---------------------------------------------------------
def route_validation(state: AgentState):
    """Routes to END if validation succeeds, or Correction if it fails."""
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print("   [Router] Validation Failed! Routing to Correction Agent.")
        return "correction"
    else:
        print("   [Router] Validation Passed! Routing to END.")
        return "end"

# ---------------------------------------------------------
# 4. COMPILE STATE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

workflow.set_entry_point("drafting")
workflow.add_edge("drafting", "validation")

workflow.add_conditional_edges(
    "validation",
    route_validation,
    {
        "correction": "correction",
        "end": END
    }
)

workflow.add_edge("correction", "validation")
agent_app = workflow.compile()

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING REAL LLM MULTI-AGENT ORCHESTRATION TEST")
    print("=" * 60)
    
    initial_state = {
        "messages": ["Generate sprint status report for Sprint 12 with active NTLM and Database bugs."],
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0
    }
    
    final_state = agent_app.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("FINAL VALIDATED OUTPUT (FROM REAL LLAMA 3):")
    print("=" * 60)
    print(final_state["report_draft"])