from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os

# Load env
load_dotenv()
llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash",google_api_key=os.environ.get("GEMINI_API_KEY"))

class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]


def chat_node(state:ChatState):
    messages=state['messages']
    response=llm.invoke(messages)
    return {"messages":[response]}


workflow=StateGraph(ChatState)

workflow.add_node("chat",chat_node)
workflow.add_edge(START,"chat")
workflow.add_edge("chat",END)

connection=sqlite3.connect("langgraph.db",check_same_thread=False)
checkpointer=SqliteSaver(conn=connection)

chatbot=workflow.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)