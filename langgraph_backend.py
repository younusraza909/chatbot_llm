from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode,tools_condition
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool
from enum import Enum
import sqlite3
import requests
import os


# Load env
load_dotenv()
llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash",google_api_key=os.environ.get("GEMINI_API_KEY"))

class OPERATION(Enum):
    ADDITION = 'addition'
    SUBTRACTION = 'subtraction'
    DIVISION = 'division'
    MULTIPLICATION= 'multiplication'

class CalculatorResult(TypedDict, total=False):
    first_num: float
    second_num: float
    operation: OPERATION
    result: float
    error: str

class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]
    

# ----------- DEFINING TOOLS------


@tool
def calculator(first_num: float, second_num: float, operation: OPERATION) -> CalculatorResult:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == OPERATION.ADDITION:
            result = first_num + second_num
        elif operation == OPERATION.SUBTRACTION:
            result = first_num - second_num
        elif operation == OPERATION.MULTIPLICATION:
            result = first_num * second_num
        elif operation == OPERATION.DIVISION:
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except:
        return {"error","Somehting went wrong while calling this tool"}


search = DuckDuckGoSearchResults()

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json()


tools=[search,calculator,get_stock_price]
llm_with_tools=llm.bind_tools(tools)
tool_node = ToolNode(tools)

def chat_node(state:ChatState):
    messages=state['messages']
    response=llm_with_tools.invoke(messages)
    return {"messages":[response]}


workflow=StateGraph(ChatState)

workflow.add_node("chat",chat_node)
workflow.add_node("tools",tool_node)

workflow.add_edge(START,"chat")
workflow.add_conditional_edges("chat",tools_condition)
workflow.add_edge("tools","chat")


connection=sqlite3.connect("langgraph.db",check_same_thread=False)
checkpointer=SqliteSaver(conn=connection)

chatbot=workflow.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)