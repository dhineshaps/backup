import os
import re
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import faiss

# Set your OpenAI key
os.environ["OPENAI_API_KEY"] = "your-openai-key-here"

# Load PDFs
pdfs = []
for root, dirs, files in os.walk("rag-dataset"):
    for file in files:
        if file.endswith(".pdf"):
            pdfs.append(os.path.join(root, file))

docs = []
for pdf in pdfs:
    loader = PyMuPDFLoader(pdf)
    docs.extend(loader.load())

# Hybrid chunking
def error_code_chunker(docs):
    error_chunks = []
    generic_docs = []
    pattern = re.compile(r'TMVS\d{5}E')

    for doc in docs:
        if pattern.search(doc.page_content):
            blocks = re.findall(r'(TMVS\d{5}E[\s\S]+?)(?=TMVS\d{5}E|\Z)', doc.page_content)
            for block in blocks:
                error_chunks.append(Document(
                    page_content=block.strip(),
                    metadata={**doc.metadata, "type": "error_code"}
                ))
        else:
            generic_docs.append(doc)

    return error_chunks, generic_docs

error_chunks, generic_docs = error_code_chunker(docs)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
generic_chunks = text_splitter.split_documents(generic_docs)

chunks = error_chunks + generic_chunks

# OpenAI embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
d = len(embeddings.embed_query("test"))  # usually 1536 or 3072
index = faiss.IndexFlatL2(d)

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)

vector_store.add_documents(documents=chunks)
vector_store.save_local("TMON")
