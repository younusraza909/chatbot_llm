from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
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

checkpointer=InMemorySaver()

chatbot=workflow.compile(checkpointer=checkpointer)