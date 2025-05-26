import os
import re
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

# --------------------------
# 1. Load PDF Documents
# --------------------------
pdfs = []
for root, dirs, files in os.walk("rag-dataset"):
    for file in files:
        if file.endswith(".pdf"):
            pdfs.append(os.path.join(root, file))

docs = []
for pdf in pdfs:
    loader = PyMuPDFLoader(pdf)
    temp = loader.load()
    docs.extend(temp)

print(f"🔹 Loaded {len(docs)} documents from {len(pdfs)} PDFs.")

# --------------------------
# 2. Hybrid Chunking
# --------------------------
def error_code_chunker(docs):
    error_chunks = []
    generic_docs = []
    error_pattern = re.compile(r'TMVS\d{5}E')

    for doc in docs:
        if error_pattern.search(doc.page_content):
            blocks = re.findall(r'(TMVS\d{5}E[\s\S]+?)(?=TMVS\d{5}E|\Z)', doc.page_content, re.MULTILINE)
            for block in blocks:
                error_chunks.append(Document(
                    page_content=block.strip(),
                    metadata={**doc.metadata, "type": "error_code"}
                ))
        else:
            generic_docs.append(doc)

    return error_chunks, generic_docs

# Apply chunking
error_chunks, generic_docs = error_code_chunker(docs)

# Split generic documentation normally
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
generic_chunks = text_splitter.split_documents(generic_docs)

# Combine all chunks
chunks = error_chunks + generic_chunks
print(f"✅ Total chunks: {len(chunks)} ({len(error_chunks)} error blocks, {len(generic_chunks)} general)")

# --------------------------
# 3. Generate Embeddings
# --------------------------
embeddings = OllamaEmbeddings(
    model='nomic-embed-text',
    base_url='http://localhost:11434'
)

# Optional: test embedding
_ = embeddings.embed_query("Hello World")

# --------------------------
# 4. Save to FAISS
# --------------------------
index = None  # Let FAISS auto-build

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

ids = vector_store.add_documents(documents=chunks)
db_name = "TMON"
vector_store.save_local(db_name)

print(f"📦 FAISS index saved to: {db_name}")
