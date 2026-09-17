import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialize Local ChromaDB (Persistent local storage on disk)
CHROMA_PATH = "./local_chroma_db"
COLLECTION_NAME = "enterprise_architecture"
MOCK_DOCS_DIR = "mock_documents"

print("=" * 60)
print("STAGE 2: BUILDING LOCAL CHROMADB VECTOR STORE WITH RBAC")
print("=" * 60)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Create or reset the collection
try:
    chroma_client.delete_collection(name=COLLECTION_NAME)
    print(f"[*] Resetting existing '{COLLECTION_NAME}' collection.")
except Exception:
    pass

collection = chroma_client.create_collection(name=COLLECTION_NAME)

# 2. Configure the Semantic Text Splitter (Sliding Window)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n## ", "\n\n", "\n", " ", ""]
)

# 3. Document Configurations & Clearance Levels
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

print("\n--- INGESTING & CHUNKING DOCUMENTS ---")

for filename, config in doc_configs.items():
    filepath = os.path.join(MOCK_DOCS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[!] Warning: File {filepath} not found, skipping.")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into overlapping semantic chunks
    chunks = text_splitter.split_text(content)

    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        # Apply RBAC metadata to every single chunk
        metadatas.append({
            "source": filename,
            "title": config["title"],
            "department": config["department"],
            "clearance": config["clearance"],
            "chunk_index": i
        })
        ids.append(f"chunk_{chunk_id_counter}")

        print(f" • [Chunk {chunk_id_counter:02d}] Source: {filename:<30} | Clearance: Level {config['clearance']} ({config['department']})")
        chunk_id_counter += 1

# 4. Embed and Store in ChromaDB
print(f"\nEmbedding {len(documents)} chunks and indexing into ChromaDB at '{CHROMA_PATH}'...")
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"✅ Success! ChromaDB populated with {collection.count()} chunks.")
print("=" * 60)

if __name__ == "__main__":
    pass