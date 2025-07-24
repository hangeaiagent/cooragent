import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Reasoning LLM configuration (for complex reasoning tasks)
REASONING_MODEL = os.getenv("REASONING_MODEL", "o1-mini")
REASONING_BASE_URL = os.getenv("REASONING_BASE_URL")
REASONING_API_KEY = os.getenv("REASONING_API_KEY")

# Non-reasoning LLM configuration (for straightforward tasks)
BASIC_MODEL = os.getenv("BASIC_MODEL", "gpt-4o")
BASIC_BASE_URL = os.getenv("BASIC_BASE_URL")
BASIC_API_KEY = os.getenv("BASIC_API_KEY")

# Vision-language LLM configuration (for tasks requiring visual understanding)
VL_MODEL = os.getenv("VL_MODEL", "gpt-4o")
VL_BASE_URL = os.getenv("VL_BASE_URL")
VL_API_KEY = os.getenv("VL_API_KEY")

# Chrome Instance configuration
CHROME_INSTANCE_PATH = os.getenv("CHROME_INSTANCE_PATH")

CODE_API_KEY = os.getenv("CODE_API_KEY")
CODE_BASE_URL = os.getenv("CODE_BASE_URL")
CODE_MODEL = os.getenv("CODE_MODEL")

USR_AGENT = eval(os.getenv("USR_AGENT", "True"))
MCP_AGENT = eval(os.getenv("MCP_AGENT", "False"))
USE_MCP_TOOLS = eval(os.getenv("USE_MCP_TOOLS", "True"))
USE_BROWSER = eval(os.getenv("USE_BROWSER", "False"))
DEBUG = eval(os.getenv("DEBUG", "False"))
BROWSER_BACKEND = os.getenv("BROWSER_BACKEND")
MAX_STEPS = eval(os.getenv("MAX_STEPS", "25"))

if DEBUG != "True":
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
else:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
