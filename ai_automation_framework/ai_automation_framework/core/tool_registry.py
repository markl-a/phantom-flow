"""工具注册系统 - 提供统一的工具管理和执行接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Type, TypeVar, Union, Literal
try:
    from typing_extensions import TypedDict  # Prefer typing_extensions for Pydantic compatibility
except ImportError:
    from typing import TypedDict  # Fallback for environments without typing_extensions
import inspect
from threading import Lock

# TypeVar for generic tool types
T = TypeVar('T', bound='BaseTool')


class ToolExecutionSuccess(TypedDict, total=False):
    """Type definition for successful tool execution result."""
    success: Literal[True]
    result: Any


class ToolExecutionError(TypedDict, total=False):
    """Type definition for failed tool execution result."""
    success: Literal[False]
    error: str
    tool: str


# Union type for tool execution results
ToolExecutionResult = Union[ToolExecutionSuccess, ToolExecutionError]


@dataclass
class ToolMetadata:
    """工具元数据。

    定义工具的基本信息和分类。
    """
    name: str
    version: str
    author: str
    description: str
    category: str  # "automation", "ai_dev", "devops", "data", "utility" 等
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "dependencies": self.dependencies,
            "tags": self.tags,
        }


class BaseTool(ABC):
    """所有工具的基类。

    定义了工具的标准接口和生命周期方法。
    所有自定义工具都应该继承这个类。
    """

    metadata: ToolMetadata

    def __init__(self) -> None:
        """初始化工具。"""
        if not hasattr(self, 'metadata'):
            raise AttributeError(
                f"{self.__class__.__name__} must define 'metadata' attribute"
            )

    @abstractmethod
    def validate_inputs(self, **kwargs: Any) -> bool:
        """验证输入参数。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 当参数无效时
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行工具功能。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            Dict[str, Any]: 执行结果，通常包含 'success' 和 'result' 或 'error' 字段
        """
        pass

    def pre_execute(self, **kwargs: Any) -> None:
        """执行前的钩子方法。

        子类可以覆盖此方法以实现执行前的准备工作。

        Args:
            **kwargs: 工具执行所需的参数
        """
        pass

    def post_execute(self, result: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """执行后的钩子方法。

        子类可以覆盖此方法以实现执行后的清理或结果处理工作。

        Args:
            result: 执行结果
            **kwargs: 工具执行时的参数

        Returns:
            Dict[str, Any]: 处理后的结果
        """
        return result

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """运行工具的完整生命周期。

        这个方法封装了 pre_execute、validate_inputs、execute 和 post_execute 的调用。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 执行前钩子
            self.pre_execute(**kwargs)

            # 验证输入
            if not self.validate_inputs(**kwargs):
                return {
                    "success": False,
                    "error": "Input validation failed"
                }

            # 执行工具
            result = self.execute(**kwargs)

            # 执行后钩子
            result = self.post_execute(result, **kwargs)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
                "tool": self.metadata.name
            }

    def get_schema(self) -> Dict[str, Any]:
        """获取工具的函数调用 schema。

        用于 OpenAI function calling 或类似的 AI 函数调用机制。
        子类可以覆盖此方法以提供更详细的 schema。

        Returns:
            Dict[str, Any]: 工具的 schema
        """
        # 获取 execute 方法的签名
        sig = inspect.signature(self.execute)
        parameters = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            param_info = {
                "type": "string",  # 默认类型
                "description": f"Parameter {param_name}"
            }

            # 如果有类型注解，使用它
            if param.annotation != inspect.Parameter.empty:
                param_type = param.annotation
                if param_type == str:
                    param_info["type"] = "string"
                elif param_type == int:
                    param_info["type"] = "integer"
                elif param_type == float:
                    param_info["type"] = "number"
                elif param_type == bool:
                    param_info["type"] = "boolean"
                elif param_type in (list, List):
                    param_info["type"] = "array"
                elif param_type in (dict, Dict):
                    param_info["type"] = "object"

            parameters[param_name] = param_info

            # 如果没有默认值，则为必需参数
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }


class ToolRegistry:
    """工具注册表 - 单例模式。

    管理所有已注册的工具，提供工具的注册、获取和列举功能。
    """

    _instance: Optional['ToolRegistry'] = None
    _lock: Lock = Lock()

    def __new__(cls) -> 'ToolRegistry':
        """单例模式实现。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化注册表。"""
        if self._initialized:
            return

        self._tools: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._initialized = True

    def register(self, tool_class: Type[BaseTool], singleton: bool = True) -> None:
        """注册工具类。

        Args:
            tool_class: 工具类（必须继承自 BaseTool）
            singleton: 是否使用单例模式（默认为 True）

        Raises:
            TypeError: 当 tool_class 不是 BaseTool 的子类时
            ValueError: 当工具名称已被注册时
        """
        if not issubclass(tool_class, BaseTool):
            raise TypeError(
                f"{tool_class.__name__} must be a subclass of BaseTool"
            )

        # 创建临时实例以获取 metadata
        temp_instance = tool_class()
        tool_name = temp_instance.metadata.name

        if tool_name in self._tools:
            raise ValueError(
                f"Tool '{tool_name}' is already registered"
            )

        self._tools[tool_name] = tool_class

        # 如果是单例模式，创建并缓存实例
        if singleton:
            self._tool_instances[tool_name] = temp_instance

        # 更新分类索引
        category = temp_instance.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)

    def unregister(self, tool_name: str) -> None:
        """注销工具。

        Args:
            tool_name: 工具名称
        """
        if tool_name in self._tools:
            tool_class = self._tools[tool_name]
            temp_instance = tool_class()
            category = temp_instance.metadata.category

            # 从分类中移除
            if category in self._categories:
                self._categories[category].remove(tool_name)
                if not self._categories[category]:
                    del self._categories[category]

            # 移除工具
            del self._tools[tool_name]
            if tool_name in self._tool_instances:
                del self._tool_instances[tool_name]

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具实例。

        Args:
            name: 工具名称

        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回 None
        """
        if name not in self._tools:
            return None

        # 如果已有实例，直接返回
        if name in self._tool_instances:
            return self._tool_instances[name]

        # 否则创建新实例
        tool_class = self._tools[name]
        return tool_class()

    def list_tools(self, category: Optional[str] = None) -> Dict[str, ToolMetadata]:
        """列出所有可用工具。

        Args:
            category: 可选的分类过滤

        Returns:
            Dict[str, ToolMetadata]: 工具名称到元数据的映射
        """
        tools = {}

        if category:
            # 按分类过滤
            if category in self._categories:
                tool_names = self._categories[category]
                for name in tool_names:
                    tool = self.get_tool(name)
                    if tool:
                        tools[name] = tool.metadata
        else:
            # 返回所有工具
            for name in self._tools:
                tool = self.get_tool(name)
                if tool:
                    tools[name] = tool.metadata

        return tools

    def get_categories(self) -> List[str]:
        """获取所有工具分类。

        Returns:
            List[str]: 分类列表
        """
        return list(self._categories.keys())

    def get_tool_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取工具的函数调用 schemas。

        Args:
            category: 可选的分类过滤

        Returns:
            List[Dict[str, Any]]: schema 列表
        """
        schemas = []
        tools = self.list_tools(category)

        for name, metadata in tools.items():
            tool = self.get_tool(name)
            if tool:
                schemas.append(tool.get_schema())

        return schemas

    def execute_tool(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        """执行工具。

        这是一个便捷方法，用于直接通过工具名称执行工具。

        Args:
            name: 工具名称
            **kwargs: 工具执行参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found"
            }

        return tool.run(**kwargs)

    def clear(self) -> None:
        """清空注册表。

        主要用于测试。
        """
        self._tools.clear()
        self._tool_instances.clear()
        self._categories.clear()


# 全局注册表实例
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册表实例。

    Returns:
        ToolRegistry: 全局注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool_class: Type[T], singleton: bool = True) -> Type[T]:
    """装饰器：注册工具类。

    使用方法：
        @register_tool
        class MyTool(BaseTool):
            ...

    Args:
        tool_class: 工具类
        singleton: 是否使用单例模式

    Returns:
        Type[T]: 原始工具类（支持链式装饰）
    """
    registry = get_tool_registry()
    registry.register(tool_class, singleton=singleton)
    return tool_class
