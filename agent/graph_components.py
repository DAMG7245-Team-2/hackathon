from langgraph.graph import StateGraph, END
from langchain_core.agents import AgentAction
from agent.state import State
from agent.configuration import tools, tool_str_to_func, Configuration
from agent.utils import create_scratchpad, extract_year_quarter

def create_researcher_graph():
    def run_oracle(state: State):
        user_query = state.input
        year, quarter = extract_year_quarter(user_query)
        scratchpad = create_scratchpad(state.intermediate_steps)

        prompt = tools["prompt"].format_messages(
            input=user_query,
            chat_history=state.chat_history,
            scratchpad=scratchpad,
        )

        out = tools["llm"].bind_tools(list(tool_str_to_func.values())).invoke(prompt)

        if not out.tool_calls:
            print("[ORACLE] No tool suggested. Forcing final_answer.")
            return {
                "intermediate_steps": state.intermediate_steps + [
                    AgentAction(
                        tool="final_answer",
                        tool_input={
                            "introduction": "LLM did not suggest any action.",
                            "research_steps": "- No tool was called by the model.",
                            "main_body": "The model could not decide on a next action.",
                            "conclusion": "Please try rewording the job description.",
                            "sources": "- N/A"
                        },
                        log="TBD"
                    )
                ],
                "is_quizzable": False
            }

        tool_name = out.tool_calls[0]["name"]
        tool_args = out.tool_calls[0]["args"]

        print(f"[ORACLE] Selected tool: {tool_name} | Args: {tool_args}")

        if tool_name == "search_pinecone":
            if "year" not in tool_args and year:
                tool_args["year"] = year
            if "quarter" not in tool_args and quarter:
                tool_args["quarter"] = quarter

        for step in state.intermediate_steps:
            if step.tool == tool_name and step.tool_input == tool_args:
                print("[ORACLE] Tool/input already used. Forcing final_answer.")
                return {
                    "intermediate_steps": state.intermediate_steps + [
                        AgentAction(
                            tool="final_answer",
                            tool_input={
                                "introduction": "Research was inconclusive.",
                                "research_steps": "- Tool was used",
                                "main_body": "No new information could be retrieved.",
                                "conclusion": "Try a different query.",
                                "sources": "- N/A"
                            },
                            log="TBD"
                        )
                    ],
                    "is_quizzable": False
                }

        recent_tools = [s.tool for s in state.intermediate_steps[-5:]]
        if recent_tools.count("web_search") >= 3:
            print("[ORACLE] Too many web_search calls. Forcing final_answer.")
            return {
                "intermediate_steps": state.intermediate_steps + [
                    AgentAction(
                        tool="final_answer",
                        tool_input={
                            "introduction": "Too many web searches.",
                            "research_steps": "- Limited to 3 searches.",
                            "main_body": "We hit the web search limit.",
                            "conclusion": "Try again or use more specific queries.",
                            "sources": "- N/A"
                        },
                        log="TBD"
                    )
                ],
                "is_quizzable": False
            }

        return {
            "intermediate_steps": state.intermediate_steps + [
                AgentAction(tool=tool_name, tool_input=tool_args, log="TBD")
            ],
            "is_quizzable": state.is_quizzable
        }

    def run_tool(state: State):
        tool_action = state.intermediate_steps[-1]
        tool_name = tool_action.tool
        tool_args = tool_action.tool_input
        out = tool_str_to_func[tool_name].invoke(input=tool_args)

        print(f"[TOOL] Ran: {tool_name} | Output: {str(out)[:100]}")

        return {
            "intermediate_steps": state.intermediate_steps + [
                AgentAction(tool=tool_name, tool_input=tool_args, log=str(out))
            ],
            "is_quizzable": state.is_quizzable or (tool_name == "final_answer" and "N/A" not in str(out))
        }

    def router(state: State):
        tool_name = state.intermediate_steps[-1].tool
        print(f"[ROUTER] Last tool: {tool_name} | Step count: {len(state.intermediate_steps)}")

        if len(state.intermediate_steps) > 20:
            print("[ROUTER] Too many steps! Forcing end.")
            return END

        if tool_name == "final_answer":
            if state.is_quizzable:
                return "generate_quiz"
            else:
                print("[ROUTER] Final answer is not quizzable. Ending.")
                return END
        elif tool_name == "generate_quiz":
            return END
        else:
            return "oracle"

    graph = StateGraph(State, config_schema=Configuration)

    graph.add_node("oracle", run_oracle)

    for tool_name in tool_str_to_func:
        graph.add_node(tool_name, run_tool)

    graph.set_entry_point("oracle")
    graph.add_conditional_edges("oracle", router)

    for tool_name in tool_str_to_func:
        if tool_name != "final_answer":
            graph.add_edge(tool_name, "oracle")

    graph.add_edge("final_answer", "generate_quiz")
    graph.add_edge("generate_quiz", END)

    return graph.compile()
