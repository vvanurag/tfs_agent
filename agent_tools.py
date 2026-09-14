from langchain_core.tools import tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# TOOL 1: The Azure DevOps / TFS Data Connector
# ---------------------------------------------------------
@tool
def query_tfs_work_items(wiql_query: str) -> str:
    """
    Executes a WIQL (Work Item Query Language) query against Azure DevOps / TFS.
    Use this tool to fetch active bugs, data requests, or sprint metrics.
    """
    print(f"\n[Agent Action] Invoking TFS Tool with Query: {wiql_query}")
    
    # In a real implementation, you would instantiate your TFS client here:
    # client = MockTFSClient("mock_tfs_response.json")
    # mock_ids = client.stage_1_execute_wiql(wiql_query)
    # pruned_items = client.stage_2_fetch_details(mock_ids)
    
    return "TFS Data Retrieved: 2 Active Production Bugs identified."

# ---------------------------------------------------------
# TOOL 2: The Enterprise RAG / Vector Store Search
# ---------------------------------------------------------
@tool
def search_enterprise_knowledge_base(search_term: str, user_clearance_level: int = 2) -> str:
    """
    Queries the internal engineering vector database using Hybrid Search.
    Use this tool to retrieve architecture specs, SLAs, and security policies.
    """
    print(f"\n[Agent Action] Searching Knowledge Base for: '{search_term}'")
    
    # In a real implementation, you would invoke your RAG hybrid search here:
    # results = execute_rbac_hybrid_search(search_term, user_clearance=user_clearance_level)
    
    return "Knowledge Match: NTLM handshake timeouts must implement jittered exponential backoff and retry up to 3 times."

# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    print(f"Tool 1 Name: {query_tfs_work_items.name}")
    print(f"Tool 1 Description: {query_tfs_work_items.description}\n")
    print(f"Tool 2 Name: {search_enterprise_knowledge_base.name}")
    print(f"Tool 2 Description: {search_enterprise_knowledge_base.description}")