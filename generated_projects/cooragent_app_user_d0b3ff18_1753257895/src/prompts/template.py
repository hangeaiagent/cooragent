import os
import re
from datetime import datetime
import copy
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import AgentState
from src.utils.path_utils import get_project_root
from langchain_core.messages import HumanMessage
from src.interface.agent import Agent
from src.interface.agent import State


def get_prompt_template(prompt_name: str) -> str:
    prompts_dir = get_project_root() / "src" / "prompts"
    template = open(os.path.join(prompts_dir, f"{prompt_name}.md")).read()
    
    # 提取模板中的变量名（格式为 <<VAR>>）
    variables = re.findall(r"<<([^>>]+)>>", template)
    
    # Escape curly braces using backslash
    
    template = template.replace("{", "{{").replace("}", "}}")
    # Replace `<<VAR>>` with `{VAR}`
    template = re.sub(r"<<([^>>]+)>>", r"{\1}", template)
    
    return template, variables


def apply_prompt_template(prompt_name: str, state: State, template:str=None) -> list:
    state = copy.deepcopy(state)
    messages = []
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, dict) and 'role' in msg:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})
    state["messages"] = messages
    
    _template, _ = get_prompt_template(prompt_name) if not template else template
    system_prompt = PromptTemplate(
        input_variables=["CURRENT_TIME"],
        template=_template,
    ).format(CURRENT_TIME=datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"), **state)

    return [{"role": "system", "content": system_prompt}] + messages

def decorate_prompt(template: str) -> list:
    variables = re.findall(r"<<([^>>]+)>>", template)
    template = template.replace("{", "{{").replace("}", "}}")
    # Replace `<<VAR>>` with `{VAR}`
    template = re.sub(r"<<([^>>]+)>>", r"{\1}", template)
    if "CURRENT_TIME" not in template:
        template = "Current time: {CURRENT_TIME}\n\n" + template
    return template

def apply_prompt(state: AgentState, template:str=None) -> list:
    template = decorate_prompt(template)
    _prompt = PromptTemplate(
        input_variables=["CURRENT_TIME"],
        template=template,
    ).format(CURRENT_TIME=datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"), **state)
    return _prompt


def apply_polish_template(_agent: Agent, instruction: str):
    try:
        template_dir = get_project_root() / "src" / "prompts"
        polish_template = open(os.path.join(template_dir, "agent_polish.md")).read()
        # First, escape all literal curly braces in the template
        polish_template = polish_template.replace("{", "{{").replace("}", "}}")
        # Then, unescape the <<VAR>> style placeholders by converting them to single brace {VAR}
        polish_template = re.sub(r"<<([^>>]+)>>", r"{\1}", polish_template)

        # Create the PromptTemplate instance
        prompt_instance = PromptTemplate(
            input_variables=["CURRENT_TIME", "agent_to_modify", "available_tools", "user_instruction"],
            template=polish_template,
        )
        # Format the prompt
        formatted_prompt = prompt_instance.format(
            CURRENT_TIME=datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
            agent_to_modify=_agent.model_dump_json(),
            user_instruction=instruction
        )
    except Exception as e:
        from traceback import print_exc
        print_exc()
        return None
    return formatted_prompt
