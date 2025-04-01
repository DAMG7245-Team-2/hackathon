# utils.py
import os
import re
from langchain_core.agents import AgentAction
from langchain_openai import ChatOpenAI


def create_scratchpad(intermediate_steps):
    research_steps = []
    for action in intermediate_steps:
        if action.log != "TBD":
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\nOutput: {action.log}"
            )
    return "\n---\n".join(research_steps)

def build_report(output: dict):
    research_steps = output.get("research_steps", "")
    if isinstance(research_steps, list):
        research_steps = "\n".join([f"- {r}" for r in research_steps])
    sources = output.get("sources", "")
    if isinstance(sources, list):
        sources = "\n".join([f"- {s}" for s in sources])
    return f"""
INTRODUCTION
------------
{output.get("introduction", "")}

RESEARCH STEPS
--------------
{research_steps}

REPORT
------
{output.get("main_body", "")}

CONCLUSION
----------
{output.get("conclusion", "")}

SOURCES
-------
{sources}
"""

def extract_skills_node(job_description: str):
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3
    )
    prompt = f"""
Extract the top 7 most important technical skills required from the following job description.
Return them as a plain list:

{job_description}
"""
    response = llm.invoke(prompt)
    skills = [line.strip("-•* ") for line in response.content.strip().split("\n") if line.strip()]
    #print('skills',skills)
    return skills
