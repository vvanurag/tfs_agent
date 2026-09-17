"""
=============================================================================
DEMO 3: RETRIEVAL-LAYER RBAC VECTOR SEARCH (ChromaDB Filtering)
=============================================================================
Core Capability:
  - Enforcing Role-Based Access Control directly at the database mathematical layer.
  - Using `$lte` metadata filters so unauthorized vectors are completely ignored.
=============================================================================
"""

import chromadb

def demonstrate_rbac_vector_search():
    print("=" * 65)
    print("DEMO 3: RETRIEVAL-LAYER RBAC VECTOR SEARCH")
    print("=" * 65)

    client = chromadb.PersistentClient(path="./local_chroma_db")
    
    try:
        collection = client.get_collection(name="enterprise_architecture")
    except Exception:
        print("[!] Main collection not found. Please run 'build_vector_store.py' first.")
        return

    query_text = "What is the SLA retry policy for NTLM handshake timeouts?"
    
    # ---------------------------------------------------------
    # Scenario 1: Junior Engineer (Clearance Level 1)
    # ---------------------------------------------------------
    print("\n--- TEST 1: Low Clearance Search (User Clearance = Level 1) ---")
    print(f"Query: '{query_text}'")
    
    results_level_1 = collection.query(
        query_texts=[query_text],
        n_results=2,
        where={"clearance": {"$lte": 1}}  # Filter: Clearance <= 1
    )
    
    docs_1 = results_level_1.get("documents", [[]])[0]
    meta_1 = results_level_1.get("metadatas", [[]])[0]
    
    print(f"Found {len(docs_1)} document matches.")
    for i, (d, m) in enumerate(zip(docs_1, meta_1)):
        print(f"  • Match {i+1} [Level {m.get('clearance')} - {m.get('source')}]: {d[:80]}...")
    print("  🔒 Notice: Level 2 & Level 3 SLA specs are MATHEMATICALLY HIDDEN.")

    # ---------------------------------------------------------
    # Scenario 2: Senior Engineer (Clearance Level 2)
    # ---------------------------------------------------------
    print("\n--- TEST 2: Authorized Search (User Clearance = Level 2) ---")
    print(f"Query: '{query_text}'")
    
    results_level_2 = collection.query(
        query_texts=[query_text],
        n_results=2,
        where={"clearance": {"$lte": 2}}  # Filter: Clearance <= 2
    )
    
    docs_2 = results_level_2.get("documents", [[]])[0]
    meta_2 = results_level_2.get("metadatas", [[]])[0]
    
    print(f"Found {len(docs_2)} document matches.")
    for i, (d, m) in enumerate(zip(docs_2, meta_2)):
        print(f"  • Match {i+1} [Level {m.get('clearance')} - {m.get('source')}]:")
        print(f"    \"{d[:140]}...\"")
    print("  🔓 Notice: Exact NTLM SLA retry guidelines are successfully retrieved!")

    print("\n" + "=" * 65)


if __name__ == "__main__":
    demonstrate_rbac_vector_search()
