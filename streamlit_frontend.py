import streamlit as st
from langgraph_backend import chatbot,retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

# --- Helper Functions ---
def convert_to_langchain_message(messages):
    langchain_messages = []
    for message in messages:
        if message["role"] == "user":
            langchain_messages.append(HumanMessage(content=message["content"]))
        else:
            langchain_messages.append(AIMessage(content=message["content"]))

    return langchain_messages

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def update_thread_history(thread_id):
    if thread_id not in st.session_state.thread_history:
        st.session_state.thread_history.append(thread_id)
    st.session_state.thread_id=thread_id

def clear_message_state():
    st.session_state.messages_history=[]

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

# --- Streamlit Session State ---
if "messages_history" not in st.session_state:
    st.session_state.messages_history = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id=generate_thread_id()

if 'thread_history' not in st.session_state:
    st.session_state.thread_history=retrieve_all_threads()

# To push new thread id immediately on first run
update_thread_history(st.session_state.thread_id)

# --- Streamlit Sidebar---
st.sidebar.title("Langgraph Chat")

if st.sidebar.button("Create Chat"):
    new_thread_id=generate_thread_id()
    update_thread_history(new_thread_id)
    clear_message_state()

st.sidebar.title("Conversation History")

for thread_history_id in st.session_state.thread_history:
    if st.sidebar.button(str(thread_history_id)):
        messages=load_conversation(thread_history_id)
        temp_messages=[]
        for msg in messages:
            if isinstance(msg,HumanMessage):
                role='user'
            else:
                role="assistant"
            temp_messages.append({"content":msg.content,"role":role})
        st.session_state.messages_history=temp_messages



# --- Streamlit UI Chat Interface ---

for message in st.session_state.messages_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

conversation_thread_id=st.session_state.thread_id

user_input = st.chat_input("Enter a message")

if user_input:
    st.session_state.messages_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # calling langgraph backend
    langchain_messages=convert_to_langchain_message(st.session_state.messages_history)
    config={'configurable':{'thread_id':conversation_thread_id}}

    
    with st.chat_message("assistant"):
        status_holder = {"box": None}
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages",
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                # Stream ONLY assistant tokens
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content
        ai_message=st.write_stream(ai_only_stream)

        if status_holder['box'] is not None:
              status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
    st.session_state.messages_history.append({"role": "assistant", "content": ai_message})