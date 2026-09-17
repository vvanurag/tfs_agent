import json
from langchain_core.tools import tool
from real_local_tfs_client import LocalTFSClient
from query_vector_store import execute_rbac_search

# ---------------------------------------------------------
# TOOL 1: The Azure DevOps / TFS Data Connector
# ---------------------------------------------------------
@tool
def query_tfs_work_items(wiql_query: str) -> str:
    """
    Executes a WIQL (Work Item Query Language) query against Azure DevOps / TFS.
    Use this tool to fetch active bugs, tasks, or sprint work items.
    
    Example input: "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
    """
    print(f"\n[Agent Tool: TFS Connector] Executing WIQL: '{wiql_query}'")
    try:
        client = LocalTFSClient()
        work_items = client.query_work_items(wiql_query)
        if not work_items:
            return "TFS Query Result: No matching work items found."
        
        pruned_json = [item.model_dump() for item in work_items]
        return json.dumps(pruned_json, indent=2)
    except Exception as e:
        return f"TFS Error: Failed to execute query - {str(e)}"

# ---------------------------------------------------------
# TOOL 2: The Enterprise RAG / Vector Store Search
# ---------------------------------------------------------
@tool
def search_enterprise_knowledge_base(search_term: str, user_clearance_level: int = 2) -> str:
    """
    Queries the internal engineering vector database (ChromaDB) using RBAC filtering.
    Use this tool to retrieve architecture specifications, SLAs, and security policies.
    
    Example input: search_term="NTLM handshake timeout SLA", user_clearance_level=2
    """
    print(f"\n[Agent Tool: RAG Search] Searching Knowledge Base for: '{search_term}' (Clearance: {user_clearance_level})")
    try:
        chunks = execute_rbac_search(
            query_text=search_term,
            user_clearance=user_clearance_level,
            top_k=2
        )
        if not chunks:
            return "Knowledge Base: No documents found matching your search term and clearance level."
        
        formatted_context = []
        for i, chunk in enumerate(chunks):
            meta = chunk["metadata"]
            formatted_context.append(
                f"[Doc {i+1}: {meta.get('title')} (Clearance Level {meta.get('clearance')})]\n{chunk['content']}"
            )
        return "\n\n".join(formatted_context)
    except Exception as e:
        return f"RAG Error: Failed to query vector store - {str(e)}"

# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING AGENT TOOLS (LIVE TFS + CHROMADB)")
    print("=" * 60)
    
    # Test TFS Tool
    tfs_res = query_tfs_work_items.invoke({
        "wiql_query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'Active'"
    })
    print(f"Tool 1 Output Preview: {tfs_res[:200]}...\n")
    
    # Test RAG Tool
    rag_res = search_enterprise_knowledge_base.invoke({
        "search_term": "NTLM handshake timeouts SLA",
        "user_clearance_level": 2
    })
    print(f"Tool 2 Output Preview: {rag_res[:200]}...")