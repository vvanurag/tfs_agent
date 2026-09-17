from pathlib import Path
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(PROJECT_ROOT / "data" / "local_chroma_db")
COLLECTION_NAME = "enterprise_architecture"

def get_chroma_collection():
    """Returns the persistent ChromaDB collection, auto-indexing if missing."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception:
        from .indexer import build_vector_store
        return build_vector_store(verbose=False)

def execute_rbac_search(
    query_text: str, 
    user_clearance: int = 1, 
    user_department: str = None, 
    top_k: int = 3,
    verbose: bool = False
) -> list[dict]:
    """
    Executes vector search while enforcing Retrieval-Layer RBAC metadata filtering.
    Only returns chunks where clearance level <= user's clearance.
    """
    collection = get_chroma_collection()

    if verbose:
        print(f"\n" + "=" * 65)
        print(f"🔍 QUERY           : '{query_text}'")
        print(f"👤 USER CLEARANCE  : Level {user_clearance}")
        print("=" * 65)

    where_filter = {
        "clearance": {"$lte": user_clearance}
    }

    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        if verbose:
            print("❌ [ACCESS DENIED / NO MATCH] No documents found matching clearance.")
        return []

    retrieved_chunks = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        if verbose:
            print(f"\n📄 [MATCH {i+1}] (Relevance Distance: {dist:.4f})")
            print(f"  • Source File : {meta.get('source')}")
            print(f"  • Title       : {meta.get('title')}")
            print(f"  • Dept        : {meta.get('department')}")
            print(f"  • Clearance   : Level {meta.get('clearance')}")
            print(f"  • Snippet     : {doc[:150]}...")
            
        retrieved_chunks.append({
            "content": doc,
            "metadata": meta,
            "distance": dist
        })

    return retrieved_chunks
