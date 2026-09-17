"""
=============================================================================
DEMO 2: SEMANTIC CHUNKING & LOCAL CHROMADB VECTOR STORE INGESTION
=============================================================================
Core Capability:
  - Splitting long documents using RecursiveCharacterTextSplitter with sliding overlap.
  - Tagging chunks with RBAC metadata (Clearance Level 1, 2, 3).
  - Indexing and embedding into local persistent ChromaDB.
=============================================================================
"""

import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

def demonstrate_chunking_and_ingestion():
    print("=" * 65)
    print("DEMO 2: SEMANTIC CHUNKING & CHROMADB VECTOR INGESTION")
    print("=" * 65)

    # 1. Sample Enterprise Markdown Document
    sample_doc = """# Adjudication Service Architecture Specification

## 1. NTLM Handshake Timeout Remediation & SLA Policy
SLA Rule 4.2.1: All NTLM authentication handshakes against legacy Active Directory services must incorporate jittered exponential backoff.
- Maximum retries: 3 attempts.
- Initial delay: 500ms with a multiplier of 2.0.
- Random jitter: ±150ms to prevent thundering herd spikes against domain controllers.
- Hard timeout ceiling: 30,000ms.

## 2. Database Connection Pooling & SQLite Concurrency
When running local SQLite instances under concurrent FastAPI workers, the database handle must be instantiated with check_same_thread=False.
- Lease Timeout: Database connection lease timeout must not exceed 5000ms.
- Cursor Cleanup: All cursor executions must be wrapped in try...finally blocks.
"""

    print("Raw Document Length:", len(sample_doc), "characters.\n")

    # 2. Configure Recursive Text Splitter
    print("--> [Step 1] Configuring RecursiveCharacterTextSplitter (chunk_size=200, overlap=40)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=40,
        separators=["\n## ", "\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_text(sample_doc)
    print(f"    Document split into {len(chunks)} overlapping chunks.\n")

    for i, chunk in enumerate(chunks):
        print(f"    • Chunk {i+1} ({len(chunk)} chars): {chunk.strip()[:60]}...")

    # 3. Ingest into ChromaDB with RBAC Metadata
    print("\n--> [Step 2] Storing chunks into local ChromaDB with RBAC metadata...")
    client = chromadb.PersistentClient(path="./local_chroma_db")
    
    # Use demo collection
    collection = client.get_or_create_collection(name="demo_architecture")
    
    doc_ids = [f"demo_chunk_{i+1}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": "adjudication_architecture.md",
            "department": "Engineering",
            "clearance": 2,
            "chunk_index": i
        }
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=doc_ids
    )

    print(f"    ✅ Ingested {len(chunks)} chunks into ChromaDB.")
    print("    Every chunk now has metadata: {'clearance': 2, 'department': 'Engineering'}")
    print("\n" + "=" * 65)

if __name__ == "__main__":
    demonstrate_chunking_and_ingestion()
