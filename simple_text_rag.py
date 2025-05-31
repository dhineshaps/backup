import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss

# Load a small text file
with open("errors.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Optional: Split by double newlines or error codes
chunks_raw = content.strip().split("\n\n")

# Wrap in LangChain Document objects
documents = [Document(page_content=chunk) for chunk in chunks_raw]

# Split further if needed
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# Set up OpenAI embeddings
os.environ["OPENAI_API_KEY"] = "your-api-key"
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
d = len(embeddings.embed_query("test"))
index = faiss.IndexFlatL2(d)

# Build vector store
vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

vector_store.add_documents(docs)
vector_store.save_local("errors_faiss")
