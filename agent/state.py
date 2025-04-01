# state.py
from dataclasses import dataclass, field
from typing import List
from langchain_core.agents import AgentAction
from langchain_core.messages import BaseMessage

@dataclass
class State:
    input: str
    chat_history: List[BaseMessage] = field(default_factory=list)
    intermediate_steps: List[AgentAction] = field(default_factory=list)
    is_quizzable: bool = False
