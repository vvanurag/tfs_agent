import os
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialize Local ChromaDB (Runs entirely in memory/locally)
chroma_client = chromadb.PersistentClient(path="./local_chroma_db")

# Create or reset the collection
collection_name = "enterprise_architecture"
try:
    chroma_client.delete_collection(name=collection_name)
except Exception:
    pass
collection = chroma_client.create_collection(name=collection_name)

# 2. Configure the Semantic Text Splitter
# We use a sliding window approach with a slight overlap to keep context intact
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n## ", "\n\n", "\n", " ", ""]
)

# 3. Load and Chunk the Documents Manually
documents = []
metadata = []
ids = []

mock_docs_dir = "mock_documents"

# Hardcoding our metadata mapping based on the files we created
doc_configs = {
    "adjudication_architecture.md": {"department": "Engineering", "clearance": 2},
    "security_policy.md": {"department": "Audit and Compliance", "clearance": 3}
}

chunk_id_counter = 1

print("=" * 50)
print("INGESTING & CHUNKING DOCUMENTS")
print("=" * 50)

for filename, meta in doc_configs.items():
    filepath = os.path.join(mock_docs_dir, filename)
    
    with open(filepath, "r") as f:
        content = f.read()
        
    # Break the document into chunks
    chunks = text_splitter.split_text(content)
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadata.append(meta)  # Apply the RBAC metadata to every chunk
        ids.append(f"chunk_{chunk_id_counter}")
        
        print(f"Created Chunk {chunk_id_counter} | Source: {filename} | Clearance: Level {meta['clearance']}")
        chunk_id_counter += 1

# 4. Embed and Store in ChromaDB
print("\nEmbedding and storing vectors into ChromaDB...")
collection.add(
    documents=documents,
    metadatas=metadata,
    ids=ids
)
print("Success! Vector Database populated locally.")