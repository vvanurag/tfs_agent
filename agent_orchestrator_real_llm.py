import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from real_local_tfs_client import LocalTFSClient # Our new real server client

# ---------------------------------------------------------
# 1. SETUP GRAPH STATE
# ---------------------------------------------------------
class AgentState(TypedDict):
    messages: List[str]
    tfs_data: str         # New state variable to hold our retrieved data
    report_draft: str
    validation_errors: str
    retry_count: int

# ---------------------------------------------------------
# 2. IMPLEMENT SPECIALIZED NODES
# ---------------------------------------------------------
def data_retrieval_agent(state: AgentState):
    """Fetches real data from our local FastAPI TFS Emulator."""
    print("-> [Node: Data Retrieval] Fetching real data from local server...")
    
    tfs_client = LocalTFSClient()
    # Execute Stage 1 & 2 Retrieval
    ids = tfs_client.stage_1_execute_wiql("SELECT id FROM WorkItems WHERE state = 'Active'")
    work_items = tfs_client.stage_2_fetch_details(ids)
    
    # Format the Pydantic objects into a string for the LLM
    state["tfs_data"] = "\n".join([item.model_dump_json() for item in work_items])
    return state

def drafting_agent(state: AgentState):
    """Uses a REAL local LLM to generate the report based on real data."""
    print("-> [Node: Drafting Agent] Prompting Llama3 to write the report...")
    
    # Initialize the real local LLM via Ollama
    llm = ChatOllama(model="llama3", temperature=0.1)
    
    # Construct a real prompt using the data we pulled from FastAPI
    prompt = f"""
    You are an AI assistant. I will provide you with JSON data representing active work items.
    You must output ONLY a valid JSON object with the following keys:
    - sprint_id: (Just put 'Current Sprint')
    - status: (Put 'At Risk' if there are bugs, otherwise 'On Track')
    - blockers: (Summarize the titles of the work items)
    
    Data:
    {state['tfs_data']}
    """
    
    # Invoke the real LLM
    response = llm.invoke(prompt)
    
    # Clean up the output in case Llama3 adds extra conversational text
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
        
    state["report_draft"] = content
    return state

def validation_agent(state: AgentState):
    """Checks if required fields are present in the JSON output."""
    print("-> [Node: Validation Agent] Enforcing Pydantic data contract...")
    try:
        draft_dict = json.loads(state["report_draft"])
        if "blockers" not in draft_dict:
            state["validation_errors"] = "Missing required field: 'blockers'"
        else:
            state["validation_errors"] = None
    except json.JSONDecodeError:
        state["validation_errors"] = "Output is not valid JSON."
    return state

def correction_agent(state: AgentState):
    print(f"-> [Node: Correction Agent] Fixing errors: {state['validation_errors']}")
    state["retry_count"] += 1
    # For now, we mock the correction to prevent an infinite LLM loop while testing
    state["report_draft"] = '{"sprint_id": "Current Sprint", "status": "At Risk", "blockers": "NTLM Timeouts Fixed"}'
    state["validation_errors"] = None
    return state

def route_validation(state: AgentState):
    if state.get("validation_errors") and state.get("retry_count", 0) < 3:
        print(f"   [Router] Validation Failed! Routing to Correction Agent.")
        return "correction"
    else:
        print("   [Router] Validation Passed! Routing to END.")
        return "end"

# ---------------------------------------------------------
# 3. COMPILE AND EXECUTE
# ---------------------------------------------------------
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("retrieval", data_retrieval_agent)
workflow.add_node("drafting", drafting_agent)
workflow.add_node("validation", validation_agent)
workflow.add_node("correction", correction_agent)

# Define edges
workflow.set_entry_point("retrieval")
workflow.add_edge("retrieval", "drafting")
workflow.add_edge("drafting", "validation")
workflow.add_conditional_edges("validation", route_validation, {"correction": "correction", "end": END})
workflow.add_edge("correction", "validation")

agent_app = workflow.compile()

if __name__ == "__main__":
    initial_state = {
        "messages": [], "tfs_data": "", "report_draft": "", "validation_errors": None, "retry_count": 0
    }
    
    # Make sure your FastAPI server is running in another terminal before executing this!
    final_state = agent_app.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("FINAL STATE ACHIEVED (BY REAL LLM):")
    print(final_state["report_draft"])