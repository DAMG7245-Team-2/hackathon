"""Define a LangGraph research agent for extracting job-related skills and building detailed reports."""

from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from agent.configuration import Configuration
from agent.state import State
from agent.utils import extract_skills_node, build_report
from agent.graph_components import create_researcher_graph

async def analyze_job(state: State, config: RunnableConfig) -> Dict[str, Any]:
    configuration = Configuration.from_runnable_config(config)
    job_description = state.input
    skills = extract_skills_node(job_description)
    researcher = create_researcher_graph()
    print('create re',researcher)
    reports = []

    for skill in skills:
        result = researcher.invoke({
            "input": skill,
            "chat_history": [],
            "intermediate_steps": []
        })
        final_step = result["intermediate_steps"][-1]
        final_input = final_step.tool_input
        report = build_report(output=final_input)
        reports.append((skill, report))

    final_markdown = ""
    for i, (skill, report) in enumerate(reports):
        final_markdown += f"\n# Skill {i+1}: {skill}\n{report}\n"

    return {"input": final_markdown}

workflow = StateGraph(State, config_schema=Configuration)
workflow.add_node("analyze_job", analyze_job)
workflow.set_entry_point("analyze_job")
graph = workflow.compile()
graph.name = "Job Skill Research Graph"
