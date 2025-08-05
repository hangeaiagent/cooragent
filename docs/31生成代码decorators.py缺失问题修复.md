# 生成代码decorators.py缺失问题修复

## 问题描述

在生成的代码项目中，发现缺少 `src/tools/decorators.py` 文件，导致工具导入失败：

```
ModuleNotFoundError: No module named 'src.tools.decorators'
```

## 问题原因

1. **生成器配置不完整**：`DynamicComponentAnalyzer.tool_dependencies` 中没有为所有工具明确包含 `decorators.py` 依赖
2. **工具依赖关系**：所有工具文件都需要 `decorators.py` 中的 `create_logged_tool` 装饰器
3. **复制逻辑缺陷**：生成器在复制工具文件时没有确保 `decorators.py` 被包含

## 解决方案

### 1. 修改工具依赖配置

在 `src/generator/cooragent_generator.py` 的 `DynamicComponentAnalyzer` 类中：

```python
self.tool_dependencies = {
    "tavily_tool": ["search.py", "decorators.py"],
    "python_repl_tool": ["python_repl.py", "decorators.py"],
    "bash_tool": ["bash_tool.py", "decorators.py"],
    "crawl_tool": ["crawl.py", "crawler/", "decorators.py"],
    "browser_tool": ["browser.py", "browser_decorators.py", "decorators.py"],
    "excel_tool": ["excel/", "decorators.py"],
    "gmail_tool": ["gmail.py", "decorators.py"],
    "slack_tool": ["slack.py", "decorators.py"],
    "video_tool": ["video.py", "decorators.py"],
    "file_management_tool": ["file_management.py", "decorators.py"],
    "avatar_tool": ["avatar_tool.py", "decorators.py"],
    "office365_tool": ["office365.py", "decorators.py"],
    "web_preview_tool": ["web_preview_tool.py", "web_preview/", "decorators.py"],
    "websocket_tool": ["websocket_manager.py", "decorators.py"],
    "decorators": ["decorators.py"]
}
```

### 2. 确保decorators.py总是被包含

在 `analyze_requirements` 方法中添加：

```python
# 确保decorators.py总是被包含，所有工具都需要它
if requirements["tool_components"]:
    requirements["tool_components"]["decorators"] = ["decorators.py"]
```

## decorators.py 文件内容

```python
import logging
import functools
from typing import Any, Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def log_io(func: Callable) -> Callable:
    """
    A decorator that logs the input parameters and output of a tool function.

    Args:
        func: The tool function to be decorated

    Returns:
        The wrapped function with input/output logging
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Log input parameters
        func_name = func.__name__
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        logger.debug(f"Tool {func_name} called with parameters: {params}")

        # Execute the function
        result = func(*args, **kwargs)

        # Log the output
        logger.debug(f"Tool {func_name} returned: {result}")

        return result

    return wrapper


class LoggedToolMixin:
    """A mixin class that adds logging functionality to any tool."""

    def _log_operation(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """Helper method to log tool operations."""
        tool_name = self.__class__.__name__.replace("Logged", "")
        params = ", ".join(
            [*(str(arg) for arg in args), *(f"{k}={v}" for k, v in kwargs.items())]
        )
        logger.debug(f"Tool {tool_name}.{method_name} called with parameters: {params}")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Override _run method to add logging."""
        self._log_operation("_run", *args, **kwargs)
        result = super()._run(*args, **kwargs)
        logger.debug(
            f"Tool {self.__class__.__name__.replace('Logged', '')} returned: {result}"
        )
        return result


def create_logged_tool(base_tool_class: Type[T]) -> Type[T]:
    """
    Factory function to create a logged version of any tool class.

    Args:
        base_tool_class: The original tool class to be enhanced with logging

    Returns:
        A new class that inherits from both LoggedToolMixin and the base tool class
    """

    class LoggedTool(LoggedToolMixin, base_tool_class):
        pass

    # Set a more descriptive name for the class
    LoggedTool.__name__ = f"Logged{base_tool_class.__name__}"
    return LoggedTool
```

## 验证修复

### 1. 手动修复现有项目

```bash
# 复制decorators.py到生成的项目中
cp src/tools/decorators.py generated_projects/cooragent_app_1753873913/src/tools/
```

### 2. 测试导入

```bash
# 测试decorators.py导入
python -c "from src.tools.decorators import create_logged_tool; print('decorators.py 导入成功')"

# 测试工具导入
python -c "from src.tools.bash_tool import bash_tool; print('bash_tool 导入成功')"
python -c "from src.tools.python_repl import python_repl_tool; print('python_repl_tool 导入成功')"
```

## 影响范围

- **所有工具文件**：都需要 `decorators.py` 中的装饰器
- **生成的项目**：确保包含完整的工具依赖
- **未来生成**：新生成的项目将自动包含 `decorators.py`

## 预防措施

1. **依赖检查**：在生成器中添加工具依赖完整性检查
2. **测试验证**：生成后自动验证关键文件的导入
3. **文档更新**：确保工具依赖关系文档完整

## 提交记录

- **提交ID**: `9e2bfcc`
- **提交信息**: "修复生成代码中缺少decorators.py的问题，确保所有工具都包含decorators.py依赖"
- **修改文件**: `src/generator/cooragent_generator.py`

## 总结

通过修改生成器的工具依赖配置，确保所有工具都明确包含 `decorators.py` 依赖，解决了生成代码中缺少核心装饰器文件的问题。这个修复确保了生成的项目具有完整的工具功能。 