# 工具系统文档 (Tool System Documentation)

## 概述

AI Automation Framework 的工具系统提供了一个标准化、可扩展的架构来创建和管理工具。通过使用 `BaseTool` 基类和 `ToolRegistry` 注册表，您可以轻松地创建新工具并将它们集成到您的 AI 应用程序中。

## 核心组件

### 1. ToolMetadata - 工具元数据

工具元数据定义了工具的基本信息和分类：

```python
from ai_automation_framework.core import ToolMetadata

metadata = ToolMetadata(
    name="my_tool",              # 工具的唯一名称
    version="1.0.0",             # 版本号
    author="Your Name",          # 作者
    description="工具描述",      # 工具功能描述
    category="utility",          # 分类: automation, ai_dev, devops, data, utility 等
    dependencies=["numpy"],      # 依赖的 Python 包（可选）
    tags=["math", "data"]        # 标签（可选）
)
```

### 2. BaseTool - 工具基类

所有工具都应该继承 `BaseTool` 基类。这个基类定义了标准的工具接口：

```python
from ai_automation_framework.core import BaseTool, ToolMetadata
from typing import Dict, Any

class MyTool(BaseTool):
    """我的自定义工具。"""

    metadata = ToolMetadata(
        name="my_tool",
        version="1.0.0",
        author="Your Name",
        description="我的自定义工具",
        category="utility",
        tags=["example"]
    )

    def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 当参数无效时
        """
        # 实现您的验证逻辑
        if 'required_param' not in kwargs:
            raise ValueError("Missing required parameter: required_param")
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具功能。

        Args:
            **kwargs: 工具执行所需的参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 实现您的工具逻辑
        result = {"success": True, "data": "some result"}
        return result
```

### 3. ToolRegistry - 工具注册表

`ToolRegistry` 是一个单例类，用于管理所有已注册的工具：

```python
from ai_automation_framework.core import get_tool_registry

# 获取全局注册表实例
registry = get_tool_registry()

# 列出所有工具
tools = registry.list_tools()

# 获取特定工具
my_tool = registry.get_tool("my_tool")

# 执行工具
result = registry.execute_tool("my_tool", required_param="value")
```

## 创建新工具

### 步骤 1: 创建工具类

创建一个继承自 `BaseTool` 的新类：

```python
# my_tools.py
from ai_automation_framework.core import BaseTool, ToolMetadata, register_tool
from typing import Dict, Any

@register_tool  # 使用装饰器自动注册工具
class TextProcessorTool(BaseTool):
    """文本处理工具示例。"""

    metadata = ToolMetadata(
        name="text_processor",
        version="1.0.0",
        author="AI Team",
        description="处理文本的工具，支持转换大小写、计数等操作",
        category="utility",
        tags=["text", "processing"]
    )

    def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数。"""
        operation = kwargs.get('operation', 'uppercase')

        if 'text' not in kwargs:
            raise ValueError("Missing required parameter: text")

        if not isinstance(kwargs['text'], str):
            raise ValueError("text must be a string")

        valid_operations = ['uppercase', 'lowercase', 'count_words']
        if operation not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")

        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行文本处理。"""
        text = kwargs['text']
        operation = kwargs.get('operation', 'uppercase')

        try:
            if operation == 'uppercase':
                result = text.upper()
            elif operation == 'lowercase':
                result = text.lower()
            elif operation == 'count_words':
                result = len(text.split())

            return {
                "success": True,
                "operation": operation,
                "result": result,
                "original_text": text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        """返回 OpenAI function calling schema。"""
        return {
            "type": "function",
            "function": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要处理的文本"
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["uppercase", "lowercase", "count_words"],
                            "description": "要执行的操作",
                            "default": "uppercase"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
```

### 步骤 2: 导入工具（触发自动注册）

使用 `@register_tool` 装饰器后，只需导入模块即可自动注册：

```python
# 在您的应用程序中
import my_tools  # 导入会触发 @register_tool 装饰器，自动注册工具
```

### 步骤 3: 使用工具

```python
from ai_automation_framework.core import get_tool_registry

# 获取注册表
registry = get_tool_registry()

# 方式 1: 通过注册表执行
result = registry.execute_tool(
    "text_processor",
    text="Hello World",
    operation="uppercase"
)
print(result)  # {'success': True, 'operation': 'uppercase', 'result': 'HELLO WORLD', ...}

# 方式 2: 获取工具实例后执行
tool = registry.get_tool("text_processor")
result = tool.run(text="Hello World", operation="count_words")
print(result)  # {'success': True, 'operation': 'count_words', 'result': 2, ...}
```

## 工具生命周期钩子

`BaseTool` 提供了生命周期钩子方法，您可以覆盖这些方法来添加自定义逻辑：

```python
class MyAdvancedTool(BaseTool):
    metadata = ToolMetadata(
        name="advanced_tool",
        version="1.0.0",
        author="AI Team",
        description="高级工具示例",
        category="utility"
    )

    def pre_execute(self, **kwargs) -> None:
        """执行前的钩子 - 可以用于准备工作。"""
        print(f"准备执行工具，参数: {kwargs}")
        # 例如：初始化连接、加载资源等

    def validate_inputs(self, **kwargs) -> bool:
        """验证输入。"""
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行主要逻辑。"""
        return {"success": True, "data": "result"}

    def post_execute(self, result: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行后的钩子 - 可以用于清理或结果处理。"""
        print(f"执行完成，结果: {result}")
        # 例如：关闭连接、清理资源、记录日志等
        result['timestamp'] = datetime.now().isoformat()
        return result
```

## 与 AI 模型集成

### 获取 OpenAI Function Calling Schema

工具系统可以自动生成 OpenAI function calling 格式的 schema：

```python
from ai_automation_framework.core import get_tool_registry

registry = get_tool_registry()

# 获取所有工具的 schemas
schemas = registry.get_tool_schemas()

# 获取特定分类的工具 schemas
utility_schemas = registry.get_tool_schemas(category="utility")

# 在 OpenAI API 调用中使用
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "将 'hello' 转换为大写"}],
    functions=schemas  # 传入工具 schemas
)
```

### 处理 AI 模型的函数调用

```python
import openai
from ai_automation_framework.core import get_tool_registry

registry = get_tool_registry()

# 获取 AI 响应
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "计算 2 + 2"}],
    functions=registry.get_tool_schemas()
)

# 如果 AI 选择调用函数
if response.choices[0].message.get("function_call"):
    function_call = response.choices[0].message.function_call
    function_name = function_call.name
    function_args = json.loads(function_call.arguments)

    # 执行工具
    result = registry.execute_tool(function_name, **function_args)
    print(result)
```

## 工具管理

### 列出所有工具

```python
from ai_automation_framework.core import get_tool_registry

registry = get_tool_registry()

# 列出所有工具
all_tools = registry.list_tools()
for name, metadata in all_tools.items():
    print(f"{name}: {metadata.description}")

# 按分类列出
utility_tools = registry.list_tools(category="utility")
```

### 获取工具分类

```python
# 获取所有可用的分类
categories = registry.get_categories()
print(categories)  # ['utility', 'automation', 'data', ...]
```

### 手动注册工具

除了使用 `@register_tool` 装饰器，您也可以手动注册：

```python
from ai_automation_framework.core import get_tool_registry

registry = get_tool_registry()

# 手动注册工具类
registry.register(MyToolClass, singleton=True)

# 注销工具
registry.unregister("my_tool")
```

## 最佳实践

### 1. 命名规范

- 工具名称应该使用小写字母和下划线（snake_case）
- 工具名称应该清晰描述功能，例如：`text_processor`, `calculator_v2`
- 版本号遵循语义化版本规范（SemVer）

### 2. 错误处理

始终在工具中进行适当的错误处理：

```python
def execute(self, **kwargs) -> Dict[str, Any]:
    try:
        # 执行逻辑
        result = self._do_something(kwargs)
        return {
            "success": True,
            "result": result
        }
    except SpecificError as e:
        return {
            "success": False,
            "error": f"Specific error: {str(e)}",
            "error_type": "SpecificError"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        }
```

### 3. 参数验证

在 `validate_inputs` 中进行完整的参数验证：

```python
def validate_inputs(self, **kwargs) -> bool:
    # 检查必需参数
    required = ['param1', 'param2']
    for param in required:
        if param not in kwargs:
            raise ValueError(f"Missing required parameter: {param}")

    # 检查参数类型
    if not isinstance(kwargs['param1'], str):
        raise ValueError("param1 must be a string")

    # 检查参数值范围
    if kwargs['param2'] < 0:
        raise ValueError("param2 must be non-negative")

    return True
```

### 4. 文档字符串

为工具类和方法提供清晰的文档字符串：

```python
class MyTool(BaseTool):
    """工具的简短描述。

    这里可以提供更详细的说明，包括：
    - 工具的主要功能
    - 使用场景
    - 限制和注意事项

    示例：
        >>> tool = MyTool()
        >>> result = tool.run(param="value")
        >>> print(result)
    """

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具功能。

        Args:
            param1: 参数 1 的描述
            param2: 参数 2 的描述

        Returns:
            Dict[str, Any]: 包含以下键的字典：
                - success (bool): 是否成功
                - result: 执行结果（如果成功）
                - error: 错误信息（如果失败）
        """
        pass
```

### 5. 返回值格式

统一返回值格式，始终包含 `success` 字段：

```python
# 成功时
{
    "success": True,
    "result": actual_result,
    "metadata": {
        # 可选的额外信息
    }
}

# 失败时
{
    "success": False,
    "error": "错误描述",
    "error_type": "ErrorClassName"  # 可选
}
```

## 示例：完整的工具实现

参考 `/home/user/Automation_with_AI/ai_automation_framework/tools/calculator_v2.py` 获取完整的工具实现示例。

这个示例展示了：
- 完整的工具类实现
- 多种操作模式（calculate, percentage, compound_interest）
- 参数验证
- 错误处理
- OpenAI function calling schema
- 便捷函数

## 迁移现有工具

如果您有使用旧方式实现的工具，可以按以下步骤迁移到新系统：

### 1. 添加元数据

```python
# 旧方式
class OldTool:
    @staticmethod
    def do_something(param):
        return result

# 新方式
from ai_automation_framework.core import BaseTool, ToolMetadata

class NewTool(BaseTool):
    metadata = ToolMetadata(
        name="new_tool",
        version="1.0.0",
        author="Your Name",
        description="工具描述",
        category="utility"
    )
```

### 2. 实现必需方法

```python
def validate_inputs(self, **kwargs) -> bool:
    # 将参数验证逻辑移到这里
    return True

def execute(self, **kwargs) -> Dict[str, Any]:
    # 将原有的静态方法逻辑移到这里
    return {"success": True, "result": ...}
```

### 3. 注册工具

```python
from ai_automation_framework.core import register_tool

@register_tool
class NewTool(BaseTool):
    # ... 工具实现
```

## 工具分类指南

选择合适的分类有助于组织和发现工具：

- **automation**: 自动化相关工具（任务调度、工作流等）
- **ai_dev**: AI 开发工具（模型训练、推理等）
- **devops**: DevOps 工具（部署、监控等）
- **data**: 数据处理工具（转换、分析等）
- **utility**: 通用工具（计算、文本处理等）
- **integration**: 第三方集成工具（API 客户端等）
- **media**: 媒体处理工具（图像、音频、视频等）

## 进阶主题

### 异步工具

虽然当前基类不直接支持异步，但您可以在 `execute` 方法中使用异步操作：

```python
import asyncio
from typing import Dict, Any

class AsyncTool(BaseTool):
    metadata = ToolMetadata(...)

    def validate_inputs(self, **kwargs) -> bool:
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        # 使用 asyncio.run 执行异步操作
        result = asyncio.run(self._async_execute(**kwargs))
        return result

    async def _async_execute(self, **kwargs) -> Dict[str, Any]:
        # 实现异步逻辑
        await asyncio.sleep(1)
        return {"success": True, "result": "async result"}
```

### 工具依赖注入

结合框架的依赖注入系统使用工具：

```python
from ai_automation_framework.core import get_global_container, BaseTool

# 注册工具到 DI 容器
container = get_global_container()
container.register_singleton(ToolRegistry, lambda: get_tool_registry())

# 在其他组件中注入
class MyService:
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry

    def process(self):
        result = self.registry.execute_tool("my_tool", param="value")
        return result
```

## 故障排除

### 工具未注册

问题：调用 `registry.get_tool("my_tool")` 返回 `None`

解决方案：
1. 确保使用了 `@register_tool` 装饰器
2. 确保工具模块已被导入
3. 检查工具名称是否正确

### 参数验证失败

问题：执行工具时抛出 `ValueError`

解决方案：
1. 检查传入的参数是否完整
2. 检查参数类型是否正确
3. 查看工具的 `validate_inputs` 实现

### Schema 生成问题

问题：生成的 schema 不正确

解决方案：
1. 覆盖 `get_schema` 方法提供自定义 schema
2. 确保 `execute` 方法有正确的类型注解

## 相关资源

- [BaseTool 源码](/home/user/Automation_with_AI/ai_automation_framework/core/tool_registry.py)
- [Calculator V2 示例](/home/user/Automation_with_AI/ai_automation_framework/tools/calculator_v2.py)
- [核心组件文档](/home/user/Automation_with_AI/docs/API_REFERENCE.md)
- [依赖注入系统](/home/user/Automation_with_AI/docs/dependency_injection.md)

## 更新日志

### v2.0.0 (2024)
- 初始发布工具系统
- 添加 `BaseTool` 基类
- 添加 `ToolRegistry` 注册表
- 添加 `@register_tool` 装饰器
- 支持 OpenAI function calling schema 生成
