import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage

def convert_to_langchain_message(messages):
    langchain_messages = []
    for message in messages:
        if message["role"] == "user":
            langchain_messages.append(HumanMessage(content=message["content"]))
        else:
            langchain_messages.append(AIMessage(content=message["content"]))

    return langchain_messages


config={'configurable':{'thread_id':"1"}}

if "messages_history" not in st.session_state:
    st.session_state.messages_history = []


for message in st.session_state.messages_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])


user_input = st.chat_input("Enter a message")

if user_input:
    st.session_state.messages_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # calling langgraph backend
    langchain_messages=convert_to_langchain_message(st.session_state.messages_history)
    
    with st.chat_message("assistant"):
       ai_message= st.write_stream(
           message_chunk.content for message_chunk, metadata in chatbot.stream({
                "messages":langchain_messages
            },
            config=config,
            stream_mode="messages"
            )
        )
    st.session_state.messages_history.append({"role": "assistant", "content": ai_message})