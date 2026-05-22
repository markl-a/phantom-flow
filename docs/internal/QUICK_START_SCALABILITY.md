# 可扩展性改进 - 快速入门指南

## 概览

本项目新增了三个核心可扩展性功能：

1. **LLM 客户端工厂** - 工厂模式管理 LLM 提供商
2. **工作流适配器基类** - 统一的工作流集成接口
3. **事件系统验证** - 确认已有完整的事件处理功能

---

## 1. LLM 客户端工厂

### 基本使用

```python
from ai_automation_framework.llm import LLMClientFactory, create_llm_client

# 方式 1: 使用工厂
client = LLMClientFactory.create("openai", model="gpt-4", temperature=0.7)

# 方式 2: 使用便捷函数
client = create_llm_client("anthropic", model="claude-3-5-sonnet-20241022")

# 方式 3: 从配置字典
config = {"provider": "ollama", "model": "llama2"}
client = LLMClientFactory.from_config(config)
```

### 查看可用提供商

```python
providers = LLMClientFactory.list_providers()
print(providers)  # ['anthropic', 'ollama', 'openai']
```

### 注册自定义提供商

```python
from ai_automation_framework.llm import BaseLLMClient

class MyCustomLLM(BaseLLMClient):
    # 实现必需的方法
    def chat(self, messages, **kwargs):
        # 你的实现
        pass

    def achat(self, messages, **kwargs):
        # 你的实现
        pass

    def stream_chat(self, messages, **kwargs):
        # 你的实现
        pass

# 注册
LLMClientFactory.register_provider("mycustom", MyCustomLLM)

# 使用
client = create_llm_client("mycustom", model="my-model")
```

---

## 2. 工作流适配器基类

### 创建自定义适配器

```python
from ai_automation_framework.integrations import (
    BaseWorkflowAdapter,
    WorkflowExecution,
    WorkflowInfo,
    ExecutionStatus,
    AdapterRegistry
)

class MyWorkflowAdapter(BaseWorkflowAdapter):
    def connect(self) -> bool:
        # 连接到工作流平台
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def trigger_workflow(self, workflow_id, input_data=None, **kwargs):
        # 触发工作流
        return WorkflowExecution(
            execution_id="exec-123",
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING
        )

    def get_execution_status(self, execution_id):
        # 获取执行状态
        return WorkflowExecution(
            execution_id=execution_id,
            workflow_id="workflow-123",
            status=ExecutionStatus.SUCCESS
        )

    def list_workflows(self, active_only=False, tags=None):
        # 列出工作流
        return [
            WorkflowInfo(
                workflow_id="wf-1",
                name="My Workflow",
                is_active=True
            )
        ]

    def get_workflow_info(self, workflow_id):
        # 获取工作流信息
        return WorkflowInfo(
            workflow_id=workflow_id,
            name="My Workflow"
        )
```

### 使用适配器

```python
# 创建实例
adapter = MyWorkflowAdapter(
    name="my-workflow",
    base_url="https://workflow.example.com"
)

# 方式 1: 手动管理连接
adapter.connect()
execution = adapter.trigger_workflow("workflow-123", {"key": "value"})
print(f"Execution ID: {execution.execution_id}")
adapter.disconnect()

# 方式 2: 使用上下文管理器（推荐）
with adapter.connection():
    execution = adapter.trigger_workflow("workflow-123")

    if execution.is_successful:
        print("Success!")
```

### 使用适配器注册表

```python
# 注册适配器
AdapterRegistry.register("myworkflow", MyWorkflowAdapter)

# 创建实例
adapter = AdapterRegistry.create(
    "myworkflow",
    base_url="https://example.com"
)

# 列出所有已注册的适配器
adapters = AdapterRegistry.list_adapters()
```

### ExecutionStatus 枚举

```python
ExecutionStatus.PENDING    # 等待中
ExecutionStatus.RUNNING    # 运行中
ExecutionStatus.SUCCESS    # 成功
ExecutionStatus.FAILED     # 失败
ExecutionStatus.CANCELLED  # 已取消
ExecutionStatus.TIMEOUT    # 超时
ExecutionStatus.UNKNOWN    # 未知
```

---

## 3. 事件系统（已验证）

### 事件优先级

```python
from ai_automation_framework.core.events import EventBus, Event, EventPriority

bus = EventBus()

# 注册不同优先级的处理器
bus.subscribe("task", high_priority_handler, priority=EventPriority.HIGHEST)
bus.subscribe("task", normal_handler, priority=EventPriority.NORMAL)
bus.subscribe("task", low_priority_handler, priority=EventPriority.LOWEST)

# 发布事件 - 处理器按优先级顺序执行
bus.publish(Event(event_type="task", source="system"))
```

### 事件过滤

```python
# 使用通配符
bus.subscribe("user.*", handler)  # 匹配 user.login, user.logout 等

# 使用过滤器
bus.subscribe(
    "log",
    handler,
    filter_dict={"metadata.level": "ERROR"}  # 只处理错误日志
)

# 组合使用
bus.subscribe(
    "payment.*",
    handler,
    priority=EventPriority.HIGH,
    filter_dict={"metadata.amount": 1000}
)
```

### 异步事件处理

```python
import asyncio

# 定义异步处理器
async def async_handler(event: Event):
    await asyncio.sleep(1)
    print(f"Processed: {event.event_type}")

# 注册
bus.subscribe("async.task", async_handler)

# 异步发布
await bus.publish_async(Event(event_type="async.task", source="system"))
```

---

## 完整示例

### 示例 1: 配置驱动的应用

```python
import yaml
from ai_automation_framework.llm import LLMClientFactory
from ai_automation_framework.core.events import EventBus, Event

# 加载配置
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# 创建 LLM 客户端
llm = LLMClientFactory.from_config(config["llm"])

# 创建事件总线
bus = EventBus()

# 定义处理器
def process_query(event: Event):
    query = event.data.get("query")
    response = llm.simple_chat(query)
    print(f"Response: {response}")

# 订阅事件
bus.subscribe("user.query", process_query)

# 发布事件
bus.publish(Event(
    event_type="user.query",
    source="web-app",
    data={"query": "What is AI?"}
))
```

### 示例 2: 多平台工作流

```python
from ai_automation_framework.integrations import AdapterRegistry

# 注册适配器（假设已实现）
AdapterRegistry.register("n8n", N8NWorkflowAdapter)
AdapterRegistry.register("airflow", AirflowWorkflowAdapter)

# 配置
workflows = {
    "n8n": {"base_url": "https://n8n.example.com"},
    "airflow": {"base_url": "https://airflow.example.com"}
}

# 触发所有平台
for platform, config in workflows.items():
    adapter = AdapterRegistry.create(platform, **config)

    with adapter.connection():
        execution = adapter.trigger_workflow(
            "data-pipeline",
            {"data": "value"}
        )
        print(f"{platform}: {execution.status.value}")
```

---

## 文件结构

```
ai_automation_framework/
├── llm/
│   ├── __init__.py           # ✨ 已更新：导入工厂
│   ├── factory.py            # ✨ 新文件：LLM 客户端工厂
│   ├── base_client.py
│   ├── openai_client.py
│   ├── anthropic_client.py
│   └── ollama_client.py
│
├── integrations/
│   ├── __init__.py           # ✨ 已更新：导入基类
│   ├── base_adapter.py       # ✨ 新文件：工作流适配器基类
│   ├── n8n_integration.py
│   ├── airflow_integration.py
│   └── zapier_integration.py
│
└── core/
    ├── events.py             # ✅ 已验证：功能完整
    └── ...
```

---

## 关键类和方法

### LLMClientFactory
- `register_provider(name, class)` - 注册提供商
- `create(provider, **kwargs)` - 创建客户端
- `from_config(config)` - 从配置创建
- `list_providers()` - 列出提供商

### BaseWorkflowAdapter
- `connect()` - 连接
- `disconnect()` - 断开
- `trigger_workflow(id, data)` - 触发工作流
- `get_execution_status(id)` - 获取状态
- `list_workflows()` - 列出工作流
- `get_workflow_info(id)` - 获取信息

### AdapterRegistry
- `register(name, class)` - 注册适配器
- `create(name, **kwargs)` - 创建适配器
- `list_adapters()` - 列出适配器

### EventBus
- `subscribe(type, handler, priority, filter)` - 订阅事件
- `publish(event)` - 发布事件（同步）
- `publish_async(event)` - 发布事件（异步）
- `get_history()` - 获取历史
- `get_stats()` - 获取统计

---

## 下一步

1. 阅读完整文档：`SCALABILITY_IMPROVEMENTS.md`
2. 查看测试建议部分
3. 迁移现有代码到新架构
4. 实现自定义提供商/适配器

---

**快速入门指南版本**: 1.0
**创建日期**: 2025-12-21
