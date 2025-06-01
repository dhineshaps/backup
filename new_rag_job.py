import os
import re
import requests
import streamlit as st
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.output_parsers import StrOutputParser

# Load env vars
load_dotenv()

# UI Setup
st.title("JCL Job Analyzer + RAG Assistant")
st.write("Chat with me! Catch me at https://youtube.com/kgptalkie")

user_id = st.text_input("Enter your user id", "laxmikant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("Start New Conversation"):
    st.session_state.chat_history = []
    history = SQLChatMessageHistory(user_id, "sqlite:///chat_history.db")
    history.clear()

for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# History-aware prompt
system = SystemMessagePromptTemplate.from_template("You are a helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")
messages = [system, MessagesPlaceholder(variable_name='history'), human]
prompt = ChatPromptTemplate(messages=messages)
chain = prompt | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: SQLChatMessageHistory(session_id, "sqlite:///chat_history.db"),
    input_messages_key='input',
    history_messages_key='history'
)

# RAG Setup
retriever = FAISS.load_local("your_index", OpenAIEmbeddings())

rag_prompt = PromptTemplate.from_template("""
You are an assistant for question-answering tasks. Use the following retrieved context to answer the question.
If you don't know the answer, just say so.
Answer in bullet points and stay relevant to the context.

Question: {question}
Context: {context}

Answer:
""")

rag_chain = LLMChain(llm=llm, prompt=rag_prompt)

# Pattern for job ID
job_pattern = re.compile(r"job\s*:?\s*([A-Z0-9]+)", re.IGNORECASE)

# Job log analyzer
def analyze_job(job_id):
    url = f"http://localhost:8000/job/{job_id}"
    response = requests.get(url)

    if b"file written" not in response.content:
        yield "❌ Job not found or failed to retrieve log."
        return

    log_path = f"./logs/{job_id}.log"
    if not os.path.exists(log_path):
        yield "⚠️ Job log file not found."
        return

    with open(log_path, 'r') as f:
        job_log = f.read()

    user_input = f"""
You are an expert in analyzing JCL job logs. A user is asking for help with job `{job_id}`.

Here is the log content:
{job_log[:4000]}

Please explain what went wrong in this job.
"""
    result = ""
    for output in runnable_with_history.stream({'input': user_input}, config={'configurable': {'session_id': user_id}}):
        result += output
        yield output

# RAG fallback
def answer_with_rag(user_input):
    docs = retriever.get_relevant_documents(user_input)
    context = "\n\n".join([doc.page_content for doc in docs])
    rag_input = {"question": user_input, "context": context}
    result = rag_chain.invoke(rag_input)
    yield result["text"]

# Main routing logic
def chat_with_llm(session_id, user_input):
    job_match = job_pattern.search(user_input)
    if job_match:
        job_id = job_match.group(1)
        yield from analyze_job(job_id)
    else:
        yield from answer_with_rag(user_input)

# Streamlit chat input
prompt_input = st.chat_input("What is up?")

if prompt_input:
    st.session_state.chat_history.append({'role': 'user', 'content': prompt_input})

    with st.chat_message("user"):
        st.markdown(prompt_input)

    with st.chat_message("assistant"):
        response = st.write_stream(chat_with_llm(user_id, prompt_input))

    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
