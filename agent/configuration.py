# configuration.py
from __future__ import annotations
import os
from dataclasses import dataclass, fields
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.tools import search_pinecone, web_search, final_answer, generate_quiz

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""
    my_configurable_param: str = "input"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        configurable = (config.get("configurable") or {}) if config else {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3
)

system_prompt = """You are the oracle, the great AI decision maker.
Use web search and vector search tools to collect data and generate a high-quality research report.
Avoid repeating tools more than twice per query. Finish with a final answer once enough info is collected."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}"),
])

tools = {
    "search_pinecone": search_pinecone,
    "web_search": web_search,
    "final_answer": final_answer,
    "generate_quiz": generate_quiz,
    "prompt": prompt,
    "llm": llm,
}

tool_str_to_func = {
    "search_pinecone": search_pinecone,
    "web_search": web_search,
    "final_answer": final_answer,
    "generate_quiz": generate_quiz,
}
