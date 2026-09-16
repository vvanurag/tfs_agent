import json
import re
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

# ---------------------------------------------------------
# 1. SETUP GRAPH STATE
# ---------------------------------------------------------
class AgentState(TypedDict):
    """
    Tracks the state of our multi-agent workflow.
    """
    messages: List[str]
    report_draft: str
    validation_errors: str
    retry_count: int

# ---------------------------------------------------------
# 2. IMPLEMENT SPECIALIZED NODES (USING REAL LOCAL LLM)
# ---------------------------------------------------------
def drafting_agent(state: AgentState):
    """Generates the structured project update report using real local Llama 3."""
    print("-> [Node: Drafting Agent] Prompting local Llama 3 to write report draft...")
    
    # Initialize real local LLM via Ollama
    llm = ChatOllama(model="llama3", temperature=0.1)
    
    prompt = f"""You are an enterprise AI assistant.
Generate a structured project update report based on the following user request:
{state['messages'][0]}

Output ONLY a valid JSON object with the following keys:
- sprint_id: (e.g. 'Sprint 12')
- status: ('On Track', 'At Risk', or 'Blocked')
- blockers: (summary of critical blockers)
"""
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Clean markdown fences if model returned them
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
        elif "sprint_id" not in draft_dict:
            state["validation_errors"] = "Missing required field: 'sprint_id'"
        else:
            state["validation_errors"] = None
    except json.JSONDecodeError:
        state["validation_errors"] = "Output is not valid JSON."
    return state

def correction_agent(state: AgentState):
    """Triggered if validation fails; passes the error message back to Llama 3."""
    print(f"-> [Node: Correction Agent] Reprompting Llama 3 to fix: {state['validation_errors']}")
    state["retry_count"] += 1
    
    llm = ChatOllama(model="llama3", temperature=0.1)
    correction_prompt = f"""Your previous response had a validation error:
{state['validation_errors']}

Previous Output:
{state['report_draft']}

Please fix the error and output ONLY the corrected, valid JSON object with 'sprint_id', 'status', and 'blockers'.
"""
    response = llm.invoke(correction_prompt)
    content = response.content.strip()
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    
    state["report_draft"] = content.strip()
    return state

# ---------------------------------------------------------
# 3. DEFINE CONDITIONAL EDGES (The Router)
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
# 4. COMPILE THE STATE GRAPH
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

# Add our specialized nodes
workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

# Set the entry point
workflow.set_entry_point("drafting")

# Connect Drafting to Validation
workflow.add_edge("drafting", "validation")

# Add conditional routing from Validation
workflow.add_conditional_edges(
    "validation",
    route_validation,
    {
        "correction": "correction",
        "end": END
    }
)

# Connect Correction back to Validation for the loop
workflow.add_edge("correction", "validation")

# Compile the graph
agent_app = workflow.compile()

# ---------------------------------------------------------
# 5. EXECUTE THE WORKFLOW WITH REAL LLM
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("INITIATING LANGGRAPH WORKFLOW (POWERED BY REAL LLAMA 3)")
    print("=" * 60)
    
    initial_state = {
        "messages": ["Generate sprint status report for active NTLM authentication issues."],
        "report_draft": "",
        "validation_errors": None,
        "retry_count": 0
    }
    
    final_state = agent_app.invoke(initial_state)
    print("\n" + "=" * 60)
    print("FINAL STATE ACHIEVED (FROM REAL LLM):")
    print("=" * 60)
    print(final_state["report_draft"])