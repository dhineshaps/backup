from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

# Your OpenAI LLM setup
llm = ChatOpenAI(model_name=model, temperature=temperature)

# RAG-specific system and human prompts
system_rag = SystemMessagePromptTemplate.from_template(
    "You are an assistant for question-answering tasks. Use only the provided context to answer."
)

human_rag = HumanMessagePromptTemplate.from_template(
    """
Answer the question below using only the retrieved context.

Question: {question}
Context: {context}

Answer in bullet points. If you don't know the answer, say you don't know.
"""
)

# Assemble RAG prompt
rag_prompt = ChatPromptTemplate.from_messages([
    system_rag,
    MessagesPlaceholder(variable_name='history'),
    human_rag
])

# Wrap with LLM + output parser
rag_chain = rag_prompt | llm | StrOutputParser()

# Chat history loader
def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, "sqlite:///chat_history.db")

# Wrap with history
rag_with_history = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",   # Must match placeholder in HumanMessagePromptTemplate
    history_messages_key="history"
)


def run_rag_with_history(user_input, session_id):
    docs = retriever.get_relevant_documents(user_input)
    context = "\n\n".join([doc.page_content for doc in docs])

    for chunk in rag_with_history.stream(
        {"question": user_input, "context": context},
        config={"configurable": {"session_id": session_id}}
    ):
        yield chunk
