"""Set of serialize object."""

from typing import List
from typing_extensions import TypedDict

class AgentTool(TypedDict):
    """
        A typed dictionary representing a tool configuration for an agent.

        This class defines the structure for a tool used by an agent, including its name
        and description. It uses `TypedDict` to enforce type hints for the dictionary keys.        
    """
    name: str
    description: str

class AgentBuilder(TypedDict):
    """
        For building an agent with specified properties and capabilities
    """
    agent_name: str
    agent_description: str
    thought: str
    llm_type: str
    selected_tools: List[AgentTool]
    prompt: str
