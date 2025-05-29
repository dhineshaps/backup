import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.output_parsers import StrOutputParser

# Load environment variables from .env (includes OPENAI_API_KEY)
load_dotenv('./../.env')

st.title("Make Your Own Chatbot")
st.write("Chat with me! Catch me at https://youtube.com/kgptalkie")

# OpenAI model setup
model = "gpt-4o"  # or "gpt-3.5-turbo", etc.
temperature = 0.7
llm = ChatOpenAI(model_name=model, temperature=temperature)

# User ID input
user_id = st.text_input("Enter your user id", "laxmikant")

# Chat history retrieval
def get_session_history(session_id):
    return SQLChatMessageHistory(session_id, "sqlite:///chat_history.db")

# Reset chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("Start New Conversation"):
    st.session_state.chat_history = []
    history = get_session_history(user_id)
    history.clear()

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Prompt setup
system = SystemMessagePromptTemplate.from_template("You are a helpful assistant.")
human = HumanMessagePromptTemplate.from_template("{input}")
messages = [system, MessagesPlaceholder(variable_name='history'), human]
prompt = ChatPromptTemplate(messages=messages)

# LangChain chain setup
chain = prompt | llm | StrOutputParser()

runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key='input',
    history_messages_key='history'
)

# Chat function
def chat_with_llm(session_id, input):
    for output in runnable_with_history.stream(
        {'input': input},
        config={'configurable': {'session_id': session_id}}
    ):
        yield output

# Chat UI
prompt = st.chat_input("What is up?")

if prompt:
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(chat_with_llm(user_id, prompt))

    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
