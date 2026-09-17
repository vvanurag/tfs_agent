import json
from langchain_core.tools import tool
from src.emulator.client import LocalTFSClient
from src.rag.search import execute_rbac_search

@tool
def query_tfs_work_items(wiql_query: str) -> str:
    """
    Executes a WIQL (Work Item Query Language) query against Azure DevOps / TFS.
    Use this tool to fetch active bugs, tasks, or sprint work items.
    """
    try:
        client = LocalTFSClient()
        work_items = client.query_work_items(wiql_query)
        if not work_items:
            return "TFS Query Result: No matching work items found."
        pruned_json = [item.model_dump() for item in work_items]
        return json.dumps(pruned_json, indent=2)
    except Exception as e:
        return f"TFS Error: Failed to execute query - {str(e)}"

@tool
def search_enterprise_knowledge_base(search_term: str, user_clearance_level: int = 2) -> str:
    """
    Queries the internal engineering vector database (ChromaDB) using RBAC filtering.
    Use this tool to retrieve architecture specifications, SLAs, and security policies.
    """
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
