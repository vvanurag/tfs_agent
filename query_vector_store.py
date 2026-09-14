import chromadb

# 1. Connect to the local persistent ChromaDB instance
chroma_client = chromadb.PersistentClient(path="./local_chroma_db")
collection = chroma_client.get_collection(name="enterprise_architecture")

def execute_rbac_hybrid_search(query_text: str, user_clearance: int, user_department: str = None, top_k: int = 2):
    """
    Executes vector search while enforcing Retrieval-Layer RBAC metadata filtering.
    Only returns chunks where the clearance level is <= user's clearance.
    """
    print(f"\n" + "=" * 60)
    print(f"QUERY: '{query_text}'")
    print(f"USER CLEARANCE: Level {user_clearance} | DEPT: {user_department}")
    print("=" * 60)

    # Construct RBAC Metadata Filter (Where Clause)
    # The mathematical engine will completely ignore vectors that fail this condition.
    where_filter = {
        "clearance": {"$lte": user_clearance} # $lte = Less Than or Equal To
    }

    # Execute Similarity Search with Metadata Filter
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        print("[ACCESS DENIED / NO MATCH] No documents found matching your security clearance.")
        return []

    retrieved_chunks = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        print(f"\n[MATCH {i+1}] (Distance: {dist:.4f})")
        print(f"  Source Dept : {meta.get('department')}")
        print(f"  Clearance   : Level {meta.get('clearance')}")
        print(f"  Content     : {doc[:150]}...")
        
        retrieved_chunks.append({
            "content": doc,
            "metadata": meta
        })

    return retrieved_chunks


# ---------------------------------------------------------
# EXECUTE VERIFICATION SCENARIOS
# ---------------------------------------------------------
if __name__ == "__main__":
    search_term = "What is the SLA and retry rule for NTLM handshake timeouts?"

    # Scenario A: Junior Engineer (Clearance Level 1)
    # Tries to search for NTLM SLAs (Requires Clearance Level 2)
    print("\n--- SCENARIO A: Low Clearance Access Test ---")
    execute_rbac_hybrid_search(
        query_text=search_term,
        user_clearance=1,
        user_department="Engineering"
    )

    # Scenario B: Senior Lead (Clearance Level 3)
    # Searches with higher clearance—should successfully unlock Level 2 and Level 3 context
    print("\n--- SCENARIO B: Authorized Access Test ---")
    execute_rbac_hybrid_search(
        query_text=search_term,
        user_clearance=3,
        user_department="Engineering"
    )