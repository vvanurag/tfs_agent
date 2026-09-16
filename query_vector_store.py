import chromadb

CHROMA_PATH = "./local_chroma_db"
COLLECTION_NAME = "enterprise_architecture"

# 1. Connect to the local persistent ChromaDB instance
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_collection(name=COLLECTION_NAME)

def execute_rbac_search(
    query_text: str, 
    user_clearance: int = 1, 
    user_department: str = None, 
    top_k: int = 3
) -> list[dict]:
    """
    Executes vector search while enforcing Retrieval-Layer RBAC metadata filtering.
    Only returns chunks where the clearance level <= user's clearance.
    
    The vector engine completely filters out documents that exceed the user's clearance.
    """
    print(f"\n" + "=" * 65)
    print(f"🔍 QUERY           : '{query_text}'")
    print(f"👤 USER CLEARANCE  : Level {user_clearance} ({'Public/General' if user_clearance == 1 else 'Internal Engineering' if user_clearance == 2 else 'Confidential/Audit'})")
    if user_department:
        print(f"🏢 USER DEPARTMENT : {user_department}")
    print("=" * 65)

    # Construct RBAC Metadata Filter (Where Clause)
    # The mathematical engine completely ignores vectors that fail this condition
    where_filter = {
        "clearance": {"$lte": user_clearance}  # $lte = Less Than or Equal To
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
        print("❌ [ACCESS DENIED / NO MATCH] No documents found matching your security clearance.")
        return []

    retrieved_chunks = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        print(f"\n📄 [MATCH {i+1}] (Relevance Distance: {dist:.4f})")
        print(f"  • Source File : {meta.get('source')}")
        print(f"  • Title       : {meta.get('title')}")
        print(f"  • Dept        : {meta.get('department')}")
        print(f"  • Clearance   : Level {meta.get('clearance')}")
        print(f"  • Snippet     : {doc[:180]}...")
        
        retrieved_chunks.append({
            "content": doc,
            "metadata": meta,
            "distance": dist
        })

    return retrieved_chunks


# ---------------------------------------------------------
# EXECUTE VERIFICATION SCENARIOS
# ---------------------------------------------------------
if __name__ == "__main__":
    search_term = "What is the SLA retry policy for NTLM handshake timeouts?"

    # Scenario A: Junior Engineer (Clearance Level 1)
    # Tries to search for NTLM SLAs (Requires Clearance Level 2)
    print("\n" + "#" * 65)
    print("### SCENARIO A: Junior Engineer (Level 1 Clearance) Access Test ###")
    print("#" * 65)
    execute_rbac_search(
        query_text=search_term,
        user_clearance=1,
        user_department="Engineering"
    )

    # Scenario B: Senior Engineer (Clearance Level 2)
    # Searches for NTLM SLAs (Has required Level 2 clearance)
    print("\n" + "#" * 65)
    print("### SCENARIO B: Senior Engineer (Level 2 Clearance) Access Test ###")
    print("#" * 65)
    execute_rbac_search(
        query_text=search_term,
        user_clearance=2,
        user_department="Engineering"
    )

    # Scenario C: Compliance Officer (Clearance Level 3)
    # Searches for Zero-Egress Cloud API policy (Requires Level 3 clearance)
    print("\n" + "#" * 65)
    print("### SCENARIO C: Compliance Officer (Level 3 Clearance) Access Test ###")
    print("#" * 65)
    execute_rbac_search(
        query_text="Are we allowed to use OpenAI API or Azure Cloud for LLMs?",
        user_clearance=3,
        user_department="Audit and Compliance"
    )