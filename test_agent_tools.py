from agent_tools import query_tfs_work_items, search_enterprise_knowledge_base

print("--- TESTING TOOL 1: TFS DATA CONNECTOR ---")
# Invoking the tool with a mock WIQL query
tfs_response = query_tfs_work_items.invoke({
    "wiql_query": "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
})
print(f"Tool Output:\n{tfs_response}\n")

print("--- TESTING TOOL 2: KNOWLEDGE BASE SEARCH ---")
# Invoking the tool with a mock search term and clearance level
rag_response = search_enterprise_knowledge_base.invoke({
    "search_term": "NTLM handshake timeouts",
    "user_clearance_level": 2
})
print(f"Tool Output:\n{rag_response}\n")