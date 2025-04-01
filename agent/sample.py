import os
import re
import operator
from typing import List, Tuple, Optional, TypedDict, Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from tavily import TavilyClient
from pinecone import Pinecone
from langgraph.graph import StateGraph, END

load_dotenv()

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["PINECONE_API_KEY"]=os.getenv("PINECONE_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# ========== LLM + Embeddings + Clients ==========
llm = ChatOpenAI(model="gpt-4o", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
client = TavilyClient(os.getenv("TAVILY_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("resourcebooks")

# def extract_year_quarter(query: str) -> Tuple[Optional[str], Optional[str]]:
#     """Extracts year and quarter (e.g. Q1, Q2) from a query."""
#     query = query.lower()
#     quarter_match = re.search(r"\b(q[1-4])\b", query)
#     year_match = re.search(r"\b(20[2-9][0-9])\b", query)
#     quarter = quarter_match.group(1).upper() if quarter_match else None
#     year = year_match.group(1) if year_match else None
#     return year, quarter

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

# ========== Tools ==========
@tool("search_pinecone")
def search_pinecone(query: str, top_k: int = 5) -> str:
    """
    Search Pinecone for relevant documents based on the skill query.

    Args:
        query (str): The topic or skill to search for.
        top_k (int): Number of top documents to retrieve.

    Returns:
        str: Formatted string of retrieved document metadata and content.
    """
    query_emb = embeddings.embed_query(query)

    response = index.query(
        vector=query_emb,
        top_k=top_k,
        include_metadata=True
    )
    matches = response.get("matches", [])
    if not matches:
        return "No relevant documents found in Pinecone."
    return format_rag_contexts(matches)

@tool("web_search")
def web_search(query: str) -> str:
    """
    Search the web using Tavily API for current content on a skill.

    Args:
        query (str): The topic or skill to search.

    Returns:
        str: Top 3 search results with titles, URLs, and summaries.
    """
    response = client.search(
        query=query,
        max_results=3,
        time_range="week",
        include_answer="basic"
    )
    results = response['results']
    return "\n---\n".join(
        ["\n".join([x["title"], x["url"], x["content"]]) for x in results]
    )

@tool("final_answer")
def final_answer(final_report: str) -> str:
    """
    Combine all skill reports into one final formatted report.

    Args:
        final_report (str): Combined text of all researched skill reports.

    Returns:
        str: Final plain text report.
    """
    return final_report

# ========== State Type ==========
class AgentState(TypedDict):
    input: str
    skills: List[str]
    current_skill_index: int
    skill_reports: List[str]
    chat_history: list[BaseMessage]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

# ========== Graph Nodes ==========
def plan_skills(state: AgentState):
    print("\n Planning skills...")
    skill_extraction_prompt = f"""
You are an expert career assistant. Extract the top 5 most important technical skills from the following job description.

Job Description:
{state['input']}

Return only a Python list of 5 skills like: ["Python", "AWS", "SQL", "Tableau", "Data Analysis"]
"""
    llm_response = llm.invoke(skill_extraction_prompt)
    raw = llm_response.content.strip()
    print("LLM skill extraction response:", raw)

    # Fix markdown-wrapped output
    if raw.startswith("```"):
        raw = re.sub(r"```(?:python)?", "", raw)
        raw = raw.replace("```", "").strip()

    try:
        skills = eval(raw)
    except Exception as e:
        print("Skill parsing error:", e)
        skills = []

    return {
        "skills": skills,
        "current_skill_index": 0
    }


def run_skill_research(state: AgentState):
    skill = state["skills"][state["current_skill_index"]]
    print(f"\n Researching skill: {skill}")


    pinecone_args = {"query": skill}


    pinecone_context = search_pinecone.invoke(pinecone_args)
    web_context = web_search.invoke(skill)

    combined_context = f"PINECONE CONTEXT:\n{pinecone_context}\n\nWEB CONTEXT:\n{web_context}"

    report_prompt = f"""
You are an expert technical trainer. Based on the following skill and research context, write a detailed explanation of the skill, what someone should learn, include examples, and a mini quiz (3 questions with answers). End with 2-3 recommended resources (links if present).

Skill: {skill}

Context:
{combined_context}

Return the result in this structure:
SKILL: <skill name>

DESCRIPTION:
<detailed explanation>

EXAMPLES:
<short examples or use cases>

QUIZ:
- Q1
  A1
- Q2
  A2
- Q3
  A3

RESOURCES:
- <link or description>
- <link or description>
"""
    report_response = llm.invoke(report_prompt)
    updated_reports = state.get("skill_reports", []) + [report_response.content]

    return {
        "skill_reports": updated_reports,
        "current_skill_index": state["current_skill_index"] + 1
    }

def generate_final_report(state: AgentState):
    print("\n📝 Generating final report...")
    full_report = "\n\n".join(state["skill_reports"])
    return {
        "intermediate_steps": [
            AgentAction(
                tool="final_answer",
                tool_input={"final_report": full_report},
                log="Done"
            )
        ]
    }



# ========== Graph ==========
def compile_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan_skills", plan_skills)
    graph.add_node("research_skill", run_skill_research)
    graph.add_node("final_answer", generate_final_report)
    graph.set_entry_point("plan_skills")

    def next_step_router(state: AgentState):
        if state["current_skill_index"] < len(state["skills"]):
            return "research_skill"
        return "final_answer"

    graph.add_conditional_edges("plan_skills", next_step_router)
    graph.add_conditional_edges("research_skill", next_step_router)
    graph.add_edge("final_answer", END)
    return graph.compile()

# ========== Runner ==========
def run_oracle_query(job_description: str):
    print("\n Starting agent for job description...")
    runnable = compile_graph()
    result = runnable.invoke({
        "input": job_description,
        "skills": [],
        "current_skill_index": 0,
        "skill_reports": [],
        "chat_history": [],
        "intermediate_steps": [],
    })

    print(" Graph finished running.")
    final_step = result["intermediate_steps"][-1]
    return final_step.tool_input["final_report"]

# ========== CLI Main ==========
if __name__ == "__main__":
    job_description = """
We are hiring a Data Scientist proficient in Python, machine learning, cloud computing (AWS/GCP), and large-scale data analysis using SQL and Spark. Familiarity with MLOps tools and good understanding of data visualization using Tableau or Power BI is a plus.
"""
    report = run_oracle_query(job_description)
    print("\n🎉 Final Report:\n")
    print(report)