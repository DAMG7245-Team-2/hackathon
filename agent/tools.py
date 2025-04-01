# tools.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.agents import AgentAction
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import os
import re
import operator
from typing import List, Tuple, Optional
from dotenv import load_dotenv
load_dotenv()

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["PINECONE_API_KEY"]=os.getenv("PINECONE_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
pinecone = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone.Index("resourcebooks")


def format_rag_contexts(matches: list) -> str:
    """Formats Pinecone results into a readable string."""
    contexts = []
    for x in matches:
        text = (
            f"Text: {x['metadata']['text']}\n"
            f"Title: {x['metadata'].get('title', 'N/A')}\n"
            f"Author: {x['metadata'].get('author', 'N/A')}\n"
        )
        contexts.append(text)
    return "\n---\n".join(contexts)



def create_scratchpad(intermediate_steps: List[AgentAction]) -> str:
    research_steps = []
    for action in intermediate_steps:
        if action.log != "TBD":
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\nOutput: {action.log}"
            )
    return "\n---\n".join(research_steps)



@tool("search_pinecone")
def search_pinecone(query: str, year: str = None, quarter: str = None, top_k: int = 5) -> str:
    """Search Pinecone for documents."""
    query_emb = embeddings.embed_query(query)
    filter_dict = {}
    if year:
        filter_dict["year"] = year
    if quarter:
        filter_dict["quarter"] = quarter
    response = index.query(
        vector=query_emb,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict if filter_dict else None
    )
    matches = response.get("matches", [])
    if not matches:
        return "No results."
    return "\n---\n".join([
        f"Text: {x['metadata']['text']}\nYear: {x['metadata'].get('year')}\nQuarter: {x['metadata'].get('quarter')}"
        for x in matches
    ])

@tool("web_search")
def web_search(query: str) -> str:
    """Search the web via Tavily."""
    response = client.search(query=query, max_results=3, time_range="week", include_answer="basic")
    return "\n---\n".join(
        ["\n".join([r["title"], r["url"], r["content"]]) for r in response.get("results", [])]
    )

@tool("final_answer")
def final_answer(introduction: str, research_steps: str, main_body: str, conclusion: str, sources: str) -> str:
    """Final structured report."""
    if isinstance(research_steps, list):
        research_steps = "\n".join([f"- {r}" for r in research_steps])
    if isinstance(sources, list):
        sources = "\n".join([f"- {s}" for s in sources])
    return f"""
INTRODUCTION
------------
{introduction}

RESEARCH STEPS
--------------
{research_steps}

REPORT
------
{main_body}

CONCLUSION
----------
{conclusion}

SOURCES
-------
{sources}
"""

@tool("generate_quiz")
def generate_quiz(summary: str) -> str:
    """Generate 5-question MCQ quiz from the given summary text."""
    return f"[Quiz Placeholder based on summary]\n{summary}"

system_prompt = """
You are a research agent.

You have access to tools like web search and document retrievers.

Rules:
- NEVER repeat a tool with the same input twice.
- NEVER call a tool more than twice in the same session.
- STOP and call `final_answer` once enough information is gathered.
- The `scratchpad` shows what you've already done. Read it carefully.

Your goal is to produce a detailed answer with sources and references.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}"),
])

llm = ChatOpenAI(model="gpt-4o", temperature=0)

all_tools = [search_pinecone, web_search, final_answer, generate_quiz]

oracle = (
    {
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "scratchpad": lambda x: create_scratchpad(x["intermediate_steps"]),
    }
    | prompt
    | llm.bind_tools(tools=all_tools, tool_choice="any")
)

tools = {
    "llm": llm,
    "prompt": prompt,
    "oracle": oracle,
}

tool_str_to_func = {
    "search_pinecone": search_pinecone,
    "web_search": web_search,
    "final_answer": final_answer,
    "generate_quiz": generate_quiz,
}