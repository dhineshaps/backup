from langchain_community.vectorstores import FAISS

db = FAISS.load_local("TMON", embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever()
results = retriever.get_relevant_documents("What does TMVS00101E mean?")

for doc in results:
    print(f"\n🔎 Result from {doc.metadata}:\n{doc.page_content}")
