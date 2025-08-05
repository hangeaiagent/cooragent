"""
API扩展模块

扩展Cooragent现有的API功能，添加代码生成器接口
"""

from .generator_api import GeneratorServer, app

__all__ = ["GeneratorServer", "app"] 