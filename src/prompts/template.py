import os
import re
import logging
from datetime import datetime
import copy
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt.chat_agent_executor import AgentState
from src.utils.path_utils import get_project_root
from langchain_core.messages import HumanMessage
from src.interface.agent import Agent
from src.interface.agent import State

# === 配置提示词模板专用日志记录器 ===
def setup_template_logger():
    """设置专门的提示词模板日志记录器，输出到 logs/generator.log"""
    # 创建logs目录
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 创建模板专用logger
    template_logger = logging.getLogger("template_debug")
    template_logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if not template_logger.handlers:
        # 文件handler - 详细调试日志
        file_handler = logging.FileHandler("logs/generator.log", encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # 格式化器 - 包含更多调试信息和行号
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | TEMPLATE | %(funcName)-20s | %(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(detailed_formatter)
        template_logger.addHandler(file_handler)
    
    return template_logger

# 创建模板日志记录器
tmpl_logger = setup_template_logger()

# 为日志添加行号追踪的辅助函数
def log_template_with_line(logger_func, message, line_offset=0):
    """为模板日志消息添加行号信息"""
    import inspect
    frame = inspect.currentframe().f_back
    line_no = frame.f_lineno + line_offset
    return logger_func(f"{message} | src_line:{line_no}")

def get_prompt_template(prompt_name: str) -> str:
    """加载并处理提示词模板文件"""
    # === 详细的模板加载日志记录 ===
    tmpl_logger.info("=" * 80)
    log_template_with_line(tmpl_logger.info, f"📄 LOADING PROMPT TEMPLATE: {prompt_name}")
    tmpl_logger.info("=" * 80)
    
    prompts_dir = get_project_root() / "src" / "prompts"                            # line:54
    template_path = os.path.join(prompts_dir, f"{prompt_name}.md")                  # line:55
    
    log_template_with_line(tmpl_logger.debug, f"TEMPLATE_LOADING_PARAMS:")          # line:57
    log_template_with_line(tmpl_logger.debug, f"  ├─ prompt_name: {prompt_name}")  # line:58
    log_template_with_line(tmpl_logger.debug, f"  ├─ prompts_dir: {prompts_dir}")  # line:59
    log_template_with_line(tmpl_logger.debug, f"  ├─ template_path: {template_path}")  # line:60
    log_template_with_line(tmpl_logger.debug, f"  └─ file_exists: {os.path.exists(template_path)}")  # line:61
    
    try:
        template = open(template_path).read()                                       # line:64
        template_length = len(template)                                             # line:65
        template_lines = template.count('\n') + 1                                  # line:66
        
        log_template_with_line(tmpl_logger.debug, f"TEMPLATE_FILE_LOADED:")         # line:68
        log_template_with_line(tmpl_logger.debug, f"  ├─ file_size: {template_length} characters")  # line:69
        log_template_with_line(tmpl_logger.debug, f"  ├─ line_count: {template_lines} lines")  # line:70
        log_template_with_line(tmpl_logger.debug, f"  ├─ preview: {repr(template[:200])}")  # line:71
        log_template_with_line(tmpl_logger.debug, f"  └─ loading_success: True")    # line:72
        
    except Exception as e:
        log_template_with_line(tmpl_logger.error, f"❌ TEMPLATE_LOADING_FAILED:")   # line:74
        log_template_with_line(tmpl_logger.error, f"  ├─ error_type: {type(e).__name__}")  # line:75
        log_template_with_line(tmpl_logger.error, f"  ├─ error_message: {str(e)}")  # line:76
        log_template_with_line(tmpl_logger.error, f"  └─ file_path: {template_path}")  # line:77
        raise e
    
    # 提取模板中的变量名（格式为 <<VAR>>）
    log_template_with_line(tmpl_logger.debug, f"TEMPLATE_VARIABLE_EXTRACTION:")     # line:81
    variables = re.findall(r"<<([^>>]+)>>", template)                               # line:82
    log_template_with_line(tmpl_logger.debug, f"  ├─ variable_pattern: <<VAR>>")    # line:83
    log_template_with_line(tmpl_logger.debug, f"  ├─ variables_found: {len(variables)}")  # line:84
    log_template_with_line(tmpl_logger.debug, f"  └─ variable_list: {variables}")   # line:85
    
    # Escape curly braces using backslash
    original_template = template                                                    # line:88
    template = template.replace("{", "{{").replace("}", "}}")                      # line:89
    log_template_with_line(tmpl_logger.debug, f"TEMPLATE_BRACE_ESCAPING:")          # line:90
    log_template_with_line(tmpl_logger.debug, f"  ├─ curly_braces_escaped: True")  # line:91
    log_template_with_line(tmpl_logger.debug, f"  └─ escaped_preview: {repr(template[:200])}")  # line:92
    
    # Replace `<<VAR>>` with `{VAR}`
    template = re.sub(r"<<([^>>]+)>>", r"{\1}", template)                           # line:95
    log_template_with_line(tmpl_logger.debug, f"TEMPLATE_VARIABLE_SUBSTITUTION:")   # line:96
    log_template_with_line(tmpl_logger.debug, f"  ├─ variable_substitution: <<VAR>> -> {{VAR}}")  # line:97
    log_template_with_line(tmpl_logger.debug, f"  └─ final_template_preview: {repr(template[:200])}")  # line:98
    
    log_template_with_line(tmpl_logger.info, f"✅ TEMPLATE_PROCESSED_SUCCESSFULLY:")  # line:100
    log_template_with_line(tmpl_logger.debug, f"  ├─ variables_extracted: {len(variables)}")  # line:101
    log_template_with_line(tmpl_logger.debug, f"  ├─ template_ready: True")         # line:102
    log_template_with_line(tmpl_logger.debug, f"  └─ return_type: (template, variables)")  # line:103
    tmpl_logger.info("=" * 80)
    
    return template, variables


def apply_prompt_template(prompt_name: str, state: State, template: str = None) -> list:
    """应用提示词模板并注入状态变量"""
    # === 详细的模板应用日志记录 ===
    tmpl_logger.info("=" * 80)
    log_template_with_line(tmpl_logger.info, f"🔧 APPLYING PROMPT TEMPLATE: {prompt_name}")
    tmpl_logger.info("=" * 80)
    
    log_template_with_line(tmpl_logger.debug, f"TEMPLATE_APPLICATION_PARAMS:")      # line:117
    log_template_with_line(tmpl_logger.debug, f"  ├─ prompt_name: {prompt_name}")   # line:118
    log_template_with_line(tmpl_logger.debug, f"  ├─ template_provided: {template is not None}")  # line:119
    log_template_with_line(tmpl_logger.debug, f"  ├─ state_keys: {list(state.keys())}")  # line:120
    log_template_with_line(tmpl_logger.debug, f"  └─ state_message_count: {len(state.get('messages', []))}")  # line:121
    
    # 深拷贝状态以避免修改原始状态
    state = copy.deepcopy(state)                                                    # line:124
    log_template_with_line(tmpl_logger.debug, f"STATE_DEEP_COPY_CREATED: True")     # line:125
    
    # 处理消息格式
    messages = []                                                                   # line:128
    log_template_with_line(tmpl_logger.debug, f"MESSAGE_FORMAT_CONVERSION:")        # line:129
    
    for i, msg in enumerate(state["messages"]):                                     # line:131
        if isinstance(msg, HumanMessage):                                           # line:132
            converted_msg = {"role": "user", "content": msg.content}               # line:133
            messages.append(converted_msg)                                         # line:134
            log_template_with_line(tmpl_logger.debug, f"  ├─ msg_{i}: HumanMessage -> user")  # line:135
        elif isinstance(msg, dict) and 'role' in msg:                              # line:136
            if msg["role"] == "user":                                               # line:137
                converted_msg = {"role": "user", "content": msg["content"]}        # line:138
                messages.append(converted_msg)                                     # line:139
                log_template_with_line(tmpl_logger.debug, f"  ├─ msg_{i}: dict[user] -> user")  # line:140
            else:
                converted_msg = {"role": "assistant", "content": msg["content"]}   # line:142
                messages.append(converted_msg)                                     # line:143
                log_template_with_line(tmpl_logger.debug, f"  ├─ msg_{i}: dict[{msg['role']}] -> assistant")  # line:144
        else:
            log_template_with_line(tmpl_logger.warning, f"  ⚠️  msg_{i}: unknown_format -> skipped")  # line:146
    
    state["messages"] = messages                                                    # line:148
    log_template_with_line(tmpl_logger.debug, f"  └─ total_converted_messages: {len(messages)}")  # line:149
    
    # 获取或使用提供的模板
    if template:
        _template = template                                                        # line:153
        log_template_with_line(tmpl_logger.debug, f"USING_PROVIDED_TEMPLATE:")      # line:154
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_source: provided_parameter")  # line:155
        log_template_with_line(tmpl_logger.debug, f"  └─ template_length: {len(template)}")  # line:156
    else:
        _template, variables = get_prompt_template(prompt_name)                     # line:158
        log_template_with_line(tmpl_logger.debug, f"LOADED_TEMPLATE_FROM_FILE:")    # line:159
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_source: {prompt_name}.md")  # line:160
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_variables: {variables}")  # line:161
        log_template_with_line(tmpl_logger.debug, f"  └─ template_length: {len(_template)}")  # line:162
    
    # 创建PromptTemplate并格式化
    current_time = datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")              # line:165
    log_template_with_line(tmpl_logger.debug, f"PROMPT_FORMATTING:")                # line:166
    log_template_with_line(tmpl_logger.debug, f"  ├─ current_time: {current_time}")  # line:167
    log_template_with_line(tmpl_logger.debug, f"  ├─ injecting_state_variables...")  # line:168
    
    # 记录即将注入的变量
    state_vars_preview = {}
    for key, value in state.items():
        if key == "messages":
            state_vars_preview[key] = f"[{len(value)} messages]"
        elif isinstance(value, str):
            state_vars_preview[key] = value[:100] + "..." if len(value) > 100 else value
        else:
            state_vars_preview[key] = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
    
    log_template_with_line(tmpl_logger.debug, f"STATE_VARIABLES_TO_INJECT:")        # line:177
    for key, preview in state_vars_preview.items():
        log_template_with_line(tmpl_logger.debug, f"  ├─ {key}: {repr(preview)}")   # line:179
    
    try:
        system_prompt = PromptTemplate(                                             # line:182
            input_variables=["CURRENT_TIME"],
            template=_template,
        ).format(CURRENT_TIME=current_time, **state)
        
        log_template_with_line(tmpl_logger.info, f"✅ PROMPT_FORMATTING_SUCCESS:")   # line:187
        log_template_with_line(tmpl_logger.debug, f"  ├─ system_prompt_length: {len(system_prompt)}")  # line:188
        log_template_with_line(tmpl_logger.debug, f"  ├─ system_prompt_preview: {repr(system_prompt[:300])}")  # line:189
        log_template_with_line(tmpl_logger.debug, f"  └─ formatting_success: True")  # line:190
        
        # 记录完整的系统提示词（用于调试）
        log_template_with_line(tmpl_logger.debug, f"📝 LLM_PROMPT | 模板: {prompt_name}.md | 作用: 系统指令提示词 | 内容: {system_prompt.replace(chr(10), ' ').replace(chr(13), ' ')}")  # line:193
            
    except Exception as e:
        log_template_with_line(tmpl_logger.error, f"❌ PROMPT_FORMATTING_FAILED:")  # line:201
        log_template_with_line(tmpl_logger.error, f"  ├─ error_type: {type(e).__name__}")  # line:202
        log_template_with_line(tmpl_logger.error, f"  ├─ error_message: {str(e)}")  # line:203
        log_template_with_line(tmpl_logger.error, f"  └─ template_name: {prompt_name}")  # line:204
        raise e
    
    # 构建最终的消息列表
    final_messages = [{"role": "system", "content": system_prompt}] + messages     # line:208
    
    log_template_with_line(tmpl_logger.info, f"🎯 FINAL_MESSAGE_STRUCTURE:")        # line:210
    log_template_with_line(tmpl_logger.debug, f"  ├─ system_message: 1")           # line:211
    log_template_with_line(tmpl_logger.debug, f"  ├─ user_messages: {len([m for m in messages if m['role'] == 'user'])}")  # line:212
    log_template_with_line(tmpl_logger.debug, f"  ├─ assistant_messages: {len([m for m in messages if m['role'] == 'assistant'])}")  # line:213
    log_template_with_line(tmpl_logger.debug, f"  └─ total_messages: {len(final_messages)}")  # line:214
    
    # 记录发送给LLM的完整对话结构
    log_template_with_line(tmpl_logger.debug, f"🤖 LLM_INPUT | 模板: {prompt_name}.md | 作用: 完整对话消息列表 | 消息数: {len(final_messages)} | 内容: {[{'role': msg['role'], 'content': msg['content'].replace(chr(10), ' ').replace(chr(13), ' ')} for msg in final_messages]}")  # line:217
    
    tmpl_logger.info("=" * 80)
    return final_messages


def decorate_prompt(template: str) -> list:
    """装饰提示词模板，添加时间戳和处理变量"""
    log_template_with_line(tmpl_logger.debug, f"DECORATING_PROMPT:")                # line:229
    log_template_with_line(tmpl_logger.debug, f"  ├─ input_template_length: {len(template)}")  # line:230
    
    variables = re.findall(r"<<([^>>]+)>>", template)                               # line:232
    log_template_with_line(tmpl_logger.debug, f"  ├─ variables_found: {variables}") # line:233
    
    template = template.replace("{", "{{").replace("}", "}}")                      # line:235
    # Replace `<<VAR>>` with `{VAR}`
    template = re.sub(r"<<([^>>]+)>>", r"{\1}", template)                           # line:237
    
    if "CURRENT_TIME" not in template:                                              # line:239
        template = "Current time: {CURRENT_TIME}\n\n" + template                   # line:240
        log_template_with_line(tmpl_logger.debug, f"  ├─ current_time_added: True") # line:241
    else:
        log_template_with_line(tmpl_logger.debug, f"  ├─ current_time_exists: True") # line:243
    
    log_template_with_line(tmpl_logger.debug, f"  └─ decorated_template_length: {len(template)}")  # line:245
    return template


def apply_prompt(state: AgentState, template: str = None) -> list:
    """应用提示词到AgentState"""
    log_template_with_line(tmpl_logger.debug, f"APPLYING_PROMPT_TO_AGENT_STATE:")   # line:251
    log_template_with_line(tmpl_logger.debug, f"  ├─ state_type: {type(state).__name__}")  # line:252
    log_template_with_line(tmpl_logger.debug, f"  ├─ template_provided: {template is not None}")  # line:253
    
    template = decorate_prompt(template)                                            # line:255
    current_time = datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")              # line:256
    
    log_template_with_line(tmpl_logger.debug, f"  ├─ current_time: {current_time}") # line:258
    log_template_with_line(tmpl_logger.debug, f"  └─ formatting_with_state...")     # line:259
    
    _prompt = PromptTemplate(                                                       # line:261
        input_variables=["CURRENT_TIME"],
        template=template,
    ).format(CURRENT_TIME=current_time, **state)
    
    log_template_with_line(tmpl_logger.debug, f"FORMATTED_PROMPT_RESULT:")          # line:266
    log_template_with_line(tmpl_logger.debug, f"  ├─ prompt_length: {len(_prompt)}")  # line:267
    log_template_with_line(tmpl_logger.debug, f"  └─ prompt_preview: {repr(_prompt[:200])}")  # line:268
    
    return _prompt


def apply_polish_template(_agent: Agent, instruction: str):
    """应用智能体优化模板"""
    log_template_with_line(tmpl_logger.info, f"🔨 APPLYING POLISH TEMPLATE:")       # line:275
    log_template_with_line(tmpl_logger.debug, f"  ├─ agent_name: {_agent.agent_name if hasattr(_agent, 'agent_name') else 'unknown'}")  # line:276
    log_template_with_line(tmpl_logger.debug, f"  ├─ instruction_length: {len(instruction)}")  # line:277
    log_template_with_line(tmpl_logger.debug, f"  └─ instruction_preview: {repr(instruction[:100])}")  # line:278
    
    try:
        template_dir = get_project_root() / "src" / "prompts"                       # line:281
        polish_template_path = os.path.join(template_dir, "agent_polish.md")       # line:282
        
        log_template_with_line(tmpl_logger.debug, f"LOADING_POLISH_TEMPLATE:")      # line:284
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_path: {polish_template_path}")  # line:285
        log_template_with_line(tmpl_logger.debug, f"  └─ file_exists: {os.path.exists(polish_template_path)}")  # line:286
        
        polish_template = open(polish_template_path).read()                         # line:288
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_loaded: True")    # line:289
        log_template_with_line(tmpl_logger.debug, f"  ├─ template_length: {len(polish_template)}")  # line:290
        log_template_with_line(tmpl_logger.debug, f"  └─ template_preview: {repr(polish_template[:200])}")  # line:291
        
        # First, escape all literal curly braces in the template
        polish_template = polish_template.replace("{", "{{").replace("}", "}}")    # line:294
        # Then, unescape the <<VAR>> style placeholders by converting them to single brace {VAR}
        polish_template = re.sub(r"<<([^>>]+)>>", r"{\1}", polish_template)         # line:296
        
        log_template_with_line(tmpl_logger.debug, f"TEMPLATE_PROCESSING:")          # line:298
        log_template_with_line(tmpl_logger.debug, f"  ├─ braces_escaped: True")     # line:299
        log_template_with_line(tmpl_logger.debug, f"  └─ variables_converted: True") # line:300

        # 准备变量
        agent_json = _agent.model_dump_json()                                       # line:303
        current_time = datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")          # line:304
        
        log_template_with_line(tmpl_logger.debug, f"TEMPLATE_VARIABLES:")           # line:306
        log_template_with_line(tmpl_logger.debug, f"  ├─ CURRENT_TIME: {current_time}")  # line:307
        log_template_with_line(tmpl_logger.debug, f"  ├─ agent_json_length: {len(agent_json)}")  # line:308
        log_template_with_line(tmpl_logger.debug, f"  ├─ agent_json_preview: {repr(agent_json[:200])}")  # line:309
        log_template_with_line(tmpl_logger.debug, f"  └─ user_instruction: {repr(instruction[:100])}")  # line:310

        # Create the PromptTemplate instance
        prompt_instance = PromptTemplate(                                           # line:313
            input_variables=["CURRENT_TIME", "agent_to_modify", "available_tools", "user_instruction"],
            template=polish_template,
        )
        
        # Format the prompt
        formatted_prompt = prompt_instance.format(                                  # line:319
            CURRENT_TIME=current_time,
            agent_to_modify=agent_json,
            user_instruction=instruction
        )
        
        log_template_with_line(tmpl_logger.info, f"✅ POLISH_TEMPLATE_SUCCESS:")     # line:325
        log_template_with_line(tmpl_logger.debug, f"  ├─ formatted_prompt_length: {len(formatted_prompt)}")  # line:326
        log_template_with_line(tmpl_logger.debug, f"  ├─ prompt_preview: {repr(formatted_prompt[:300])}")  # line:327
        log_template_with_line(tmpl_logger.debug, f"  └─ template_application: successful")  # line:328
        
        # 记录完整的优化提示词（用于调试）
        log_template_with_line(tmpl_logger.debug, f"🔨 LLM_PROMPT | 模板: agent_polish.md | 作用: 智能体优化指令提示词 | 内容: {formatted_prompt.replace(chr(10), ' ').replace(chr(13), ' ')}")  # line:331
            
    except Exception as e:
        log_template_with_line(tmpl_logger.error, f"❌ POLISH_TEMPLATE_FAILED:")    # line:339
        log_template_with_line(tmpl_logger.error, f"  ├─ error_type: {type(e).__name__}")  # line:340
        log_template_with_line(tmpl_logger.error, f"  ├─ error_message: {str(e)}")  # line:341
        log_template_with_line(tmpl_logger.error, f"  └─ agent_name: {getattr(_agent, 'agent_name', 'unknown')}")  # line:342
        
        # 记录异常堆栈信息
        import traceback
        log_template_with_line(tmpl_logger.error, f"EXCEPTION_TRACEBACK:")          # line:346
        stack_trace = traceback.format_exc()
        for i, line in enumerate(stack_trace.split('\n')):
            if line.strip():
                log_template_with_line(tmpl_logger.error, f"  {i:02d}: {line}")     # line:350
        return None
    
    return formatted_prompt
