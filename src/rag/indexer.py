import os
from pathlib import Path
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_PATH = str(PROJECT_ROOT / "data" / "local_chroma_db")
DOCS_DIR = PROJECT_ROOT / "data" / "documents"
COLLECTION_NAME = "enterprise_architecture"

def build_vector_store(verbose: bool = True):
    """Builds and indexes the local ChromaDB vector store with RBAC clearance tags."""
    if verbose:
        print("=" * 60)
        print("STAGE 2: BUILDING LOCAL CHROMADB VECTOR STORE WITH RBAC")
        print("=" * 60)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Create or reset collection
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        if verbose:
            print(f"[*] Resetting existing '{COLLECTION_NAME}' collection.")
    except Exception:
        pass

    collection = chroma_client.create_collection(name=COLLECTION_NAME)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n## ", "\n\n", "\n", " ", ""]
    )

    doc_configs = {
        "engineering_handbook.md": {
            "department": "Engineering",
            "clearance": 1,
            "title": "Engineering Handbook & Guidelines"
        },
        "adjudication_architecture.md": {
            "department": "Engineering",
            "clearance": 2,
            "title": "Adjudication Architecture & SLA Specs"
        },
        "security_policy.md": {
            "department": "Audit and Compliance",
            "clearance": 3,
            "title": "Zero-Egress & Security Mandate"
        }
    }

    documents = []
    metadatas = []
    ids = []
    chunk_id_counter = 1

    if verbose:
        print("\n--- INGESTING & CHUNKING DOCUMENTS ---")

    for filename, config in doc_configs.items():
        filepath = DOCS_DIR / filename
        if not filepath.exists():
            # Fallback to mock_documents
            filepath = PROJECT_ROOT / "mock_documents" / filename

        if not filepath.exists():
            if verbose:
                print(f"[!] Warning: File {filepath} not found, skipping.")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = text_splitter.split_text(content)

        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "source": filename,
                "title": config["title"],
                "department": config["department"],
                "clearance": config["clearance"],
                "chunk_index": i
            })
            ids.append(f"chunk_{chunk_id_counter}")

            if verbose:
                print(f" • [Chunk {chunk_id_counter:02d}] Source: {filename:<30} | Clearance: Level {config['clearance']} ({config['department']})")
            chunk_id_counter += 1

    if verbose:
        print(f"\nEmbedding {len(documents)} chunks and indexing into ChromaDB at '{CHROMA_PATH}'...")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    if verbose:
        print(f"✅ Success! ChromaDB populated with {collection.count()} chunks.")
        print("=" * 60)
        
    return collection

if __name__ == "__main__":
    build_vector_store()
