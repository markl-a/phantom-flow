## 工作流自動化集成指南
# Workflow Automation Integration Guide

本指南詳細介紹如何使用 AI Automation Framework 集成各種工作流自動化平台。

---

## 📋 目錄

- [支持的平台](#支持的平台)
- [快速開始](#快速開始)
- [平台集成詳解](#平台集成詳解)
  - [n8n](#n8n-集成)
  - [Make (Integromat)](#make-integromat-集成)
  - [Zapier](#zapier-集成)
  - [Apache Airflow](#apache-airflow-集成)
  - [Temporal](#temporal-集成)
  - [Prefect](#prefect-集成)
  - [Celery](#celery-集成)
- [統一接口使用](#統一接口使用)
- [高級用法](#高級用法)
- [最佳實踐](#最佳實踐)
- [故障排除](#故障排除)

---

## 支持的平台

| 平台 | 類型 | 開源 | 自託管 | 支持功能 |
|------|------|------|--------|---------|
| **n8n** | 工作流自動化 | ✅ | ✅ | Webhook、API、工作流管理 |
| **Make** | 工作流自動化 | ❌ | ❌ | Webhook、場景管理 |
| **Zapier** | 工作流自動化 | ❌ | ❌ | Webhook、Zap 觸發 |
| **Apache Airflow** | 數據管道 | ✅ | ✅ | DAG 管理、執行監控 |
| **Temporal** | 分布式工作流引擎 | ✅ | ✅ | 工作流編排、長時間運行任務、狀態管理 |
| **Prefect** | 現代數據工作流 | ✅ | ✅ | Flow 編排、調度、監控 |
| **Celery** | 分布式任務隊列 | ✅ | ✅ | 異步任務、定時任務、任務鏈 |

---

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設置環境變量

創建 `.env` 文件：

```bash
# n8n
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key

# Make
MAKE_API_TOKEN=your_make_api_token
MAKE_ORGANIZATION_ID=your_org_id
MAKE_TEAM_ID=your_team_id

# Zapier
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/xxx/yyy/
ZAPIER_API_KEY=your_zapier_api_key

# Airflow
AIRFLOW_BASE_URL=http://localhost:8080
AIRFLOW_USERNAME=admin
AIRFLOW_PASSWORD=admin

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=ai-automation

# Prefect
# Prefect uses local configuration by default

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. 基本使用

```python
from ai_automation_framework.integrations.workflow_automation_unified import (
    UnifiedWorkflowManager,
    WorkflowPlatform
)

# 創建管理器
manager = UnifiedWorkflowManager()

# 註冊 n8n
manager.register_n8n(
    base_url="http://localhost:5678",
    api_key="your_api_key"
)

# 觸發工作流
result = manager.trigger_workflow(
    platform=WorkflowPlatform.N8N,
    workflow_id="workflow_123",
    data={"key": "value"}
)

print(result)
```

---

## 平台集成詳解

### n8n 集成

#### 基本功能

```python
from ai_automation_framework.integrations.n8n_integration_enhanced import N8NEnhanced

# 初始化
n8n = N8NEnhanced(
    base_url="http://localhost:5678",
    api_key="your_api_key"
)

# 1. 工作流管理
workflows = n8n.get_workflows(active=True)
workflow = n8n.get_workflow("workflow_id")

# 2. 執行工作流
result = n8n.execute_workflow(
    workflow_id="workflow_123",
    data={"input": "data"}
)

# 3. 監控執行
execution = n8n.get_execution(result['data']['id'])
print(f"狀態: {execution['data']['status']}")

# 4. Webhook 觸發
webhook_result = n8n.trigger_webhook(
    webhook_id="webhook_path",
    data={"event": "new_order"}
)
```

#### 創建 AI 工作流模板

```python
# 創建 AI 處理工作流
template = n8n.create_ai_workflow_template(
    name="AI Content Generator",
    webhook_path="ai-content",
    ai_prompt="You are a helpful content writer..."
)

# 創建工作流
result = n8n.create_workflow(
    name=template['name'],
    nodes=template['nodes'],
    connections=template['connections'],
    active=True
)
```

#### 批量執行

```python
# 批量執行工作流
data_list = [
    {"customer": "John", "order": 1},
    {"customer": "Jane", "order": 2},
    {"customer": "Bob", "order": 3}
]

results = n8n.bulk_execute("workflow_id", data_list)

for result in results:
    print(f"執行: {result.get('success')}")
```

#### 等待執行完成

```python
# 觸發工作流
execution = n8n.execute_workflow("workflow_id", {"data": "test"})
execution_id = execution['data']['id']

# 等待完成（最多 5 分鐘）
final_result = n8n.wait_for_execution(
    execution_id=execution_id,
    max_wait=300,
    poll_interval=2
)

if final_result.get('success'):
    print(f"執行狀態: {final_result['data']['status']}")
```

---

### Make (Integromat) 集成

#### 基本功能

```python
from ai_automation_framework.integrations.make_integration import MakeIntegration

# 初始化
make = MakeIntegration(
    api_token="your_token",
    organization_id="org_id",
    team_id="team_id"
)

# 1. 場景管理
scenarios = make.get_scenarios()
scenario = make.get_scenario("scenario_id")

# 2. 執行場景
result = make.run_scenario(
    scenario_id="scenario_123",
    data={"input": "data"}
)

# 3. 激活/停用場景
make.activate_scenario("scenario_id")
make.deactivate_scenario("scenario_id")
```

#### Webhook 觸發

```python
# 方式 1: 直接 URL
result = make.trigger_webhook(
    webhook_url="https://hook.eu1.make.com/xxx",
    data={"event": "order_created"}
)

# 方式 2: 使用 webhook key
result = make.trigger_custom_webhook(
    webhook_key="your_webhook_key",
    data={"event": "order_created"}
)
```

#### 數據存儲

```python
# 獲取數據存儲
datastores = make.get_data_stores()

# 讀取記錄
records = make.get_data_store_records(
    datastore_id="ds_123",
    limit=100
)

# 添加記錄
result = make.add_data_store_record(
    datastore_id="ds_123",
    data={"name": "John", "email": "john@example.com"}
)
```

---

### Zapier 集成

#### 基本功能

```python
from ai_automation_framework.integrations.zapier_integration_enhanced import ZapierEnhanced

# 初始化
zapier = ZapierEnhanced(
    default_webhook_url="https://hooks.zapier.com/hooks/catch/xxx/yyy/",
    api_key="your_api_key"
)

# 1. 觸發 Webhook
result = zapier.trigger_webhook({
    "event": "new_user",
    "name": "John Doe",
    "email": "john@example.com"
})

# 2. 批量觸發
results = zapier.batch_trigger(
    data_list=[
        {"user": "John"},
        {"user": "Jane"},
        {"user": "Bob"}
    ],
    delay_between=0.5  # 500ms 延遲
)
```

#### 預定義動作

```python
# 發送郵件
zapier.send_email(
    to="recipient@example.com",
    subject="Test Email",
    body="This is a test email from AI Framework",
    cc=["cc@example.com"],
    attachments=["https://example.com/file.pdf"]
)

# 發送 Slack 消息
zapier.send_slack_message(
    channel="#general",
    message="New order received!",
    username="Order Bot",
    icon_emoji=":package:"
)

# 創建 Google Sheets 行
zapier.create_google_sheet_row(
    spreadsheet_id="sheet_123",
    row_data={
        "Name": "John Doe",
        "Email": "john@example.com",
        "Date": "2025-01-XX"
    }
)

# 創建任務
zapier.create_task(
    task_name="Follow up with customer",
    description="Contact John about the order",
    due_date="2025-02-01",
    priority="high",
    assignee="sales@example.com"
)

# 發送短信
zapier.send_sms(
    to="+1234567890",
    message="Your order has been shipped!"
)
```

---

### Apache Airflow 集成

#### 基本功能

```python
from ai_automation_framework.integrations.airflow_integration import AirflowIntegration

# 初始化
airflow = AirflowIntegration(
    base_url="http://localhost:8080",
    username="admin",
    password="admin"
)

# 1. DAG 管理
dags = airflow.list_dags()
dag = airflow.get_dag("dag_id")

# 2. 觸發 DAG
result = airflow.trigger_dag(
    dag_id="example_dag",
    conf={"param1": "value1"}
)

# 3. 查詢執行狀態
dag_run = airflow.get_dag_run("dag_id", "run_id")
print(f"狀態: {dag_run['state']}")

# 4. 暫停/恢復 DAG
airflow.pause_dag("dag_id")
airflow.unpause_dag("dag_id")
```

---

### Temporal 集成

Temporal 是一個開源的分布式工作流引擎，用於構建可靠的、可擴展的應用程序。

#### 基本功能

```python
from ai_automation_framework.integrations.temporal_integration import TemporalIntegration
import asyncio

async def main():
    # 初始化
    temporal = TemporalIntegration(
        host="localhost:7233",
        namespace="default",
        task_queue="ai-automation"
    )

    # 連接到 Temporal
    await temporal.connect()

    # 1. 定義 Activity
    @temporal.create_activity()
    async def process_order(order_id: str):
        print(f"處理訂單: {order_id}")
        return {"order_id": order_id, "status": "processed"}

    # 2. 定義 Workflow
    @temporal.create_workflow()
    async def order_workflow(order_id: str):
        result = await process_order(order_id)
        return result

    # 3. 啟動 Workflow
    result = await temporal.start_workflow(
        workflow_id="order-001",
        workflow_type="order_workflow",
        args=["ORD-12345"]
    )
    print(f"工作流已啟動: {result}")

    # 4. 查詢 Workflow 狀態
    if result.get('success'):
        status = await temporal.get_workflow_result(result['workflow_id'])
        print(f"工作流狀態: {status}")

    # 5. 發送信號到 Workflow
    await temporal.signal_workflow(
        workflow_id="order-001",
        signal_name="approve",
        args=[{"approved": True}]
    )

    # 6. 取消 Workflow
    await temporal.cancel_workflow("order-001")

asyncio.run(main())
```

#### 使用工作流構建器

```python
from ai_automation_framework.integrations.temporal_integration import TemporalWorkflowBuilder

builder = TemporalWorkflowBuilder(temporal.client)

# 註冊 Activity
@builder.register_activity(name="send_notification")
async def send_notification(user_id: str, message: str):
    print(f"發送通知給 {user_id}: {message}")
    return True

# 註冊 Workflow
@builder.register_workflow(name="notification_workflow")
async def notification_workflow(user_id: str):
    await send_notification(user_id, "您有新消息")
    return {"success": True}
```

#### 安裝和運行

```bash
# 安裝 Temporal
pip install temporalio

# 啟動 Temporal 服務器（開發環境）
temporal server start-dev

# 啟動 Worker（在另一個終端）
python your_worker.py
```

---

### Prefect 集成

Prefect 是一個現代化的數據工作流編排平台，專注於可觀察性和易用性。

#### 基本功能

```python
from ai_automation_framework.integrations.prefect_integration import PrefectIntegration
import asyncio

async def main():
    # 初始化
    prefect = PrefectIntegration()

    # 1. 定義 Task
    @prefect.create_task(name="extract_data")
    async def extract_data(source: str):
        print(f"從 {source} 提取數據")
        return {"records": 1000}

    @prefect.create_task(name="transform_data")
    async def transform_data(data: dict):
        print(f"轉換 {data['records']} 條記錄")
        return {"transformed": True}

    # 2. 定義 Flow
    @prefect.create_flow(name="etl_pipeline")
    async def etl_pipeline(source: str):
        raw_data = await extract_data(source)
        result = await transform_data(raw_data)
        return result

    # 3. 創建 Flow Run
    flow_run = await prefect.create_flow_run(
        flow_name="etl_pipeline",
        parameters={"source": "database"}
    )
    print(f"Flow Run 已創建: {flow_run}")

    # 4. 等待 Flow 完成
    if flow_run.get('success'):
        result = await prefect.wait_for_flow_run(flow_run['flow_run_id'])
        print(f"Flow 執行結果: {result}")

    # 5. 獲取 Flow Run 狀態
    status = await prefect.get_flow_run_status(flow_run['flow_run_id'])
    print(f"狀態: {status}")

    # 6. 取消 Flow Run
    await prefect.cancel_flow_run(flow_run['flow_run_id'])

asyncio.run(main())
```

#### 定時調度

```python
from ai_automation_framework.integrations.prefect_integration import PrefectScheduler
from datetime import timedelta

async def setup_schedules():
    scheduler = PrefectScheduler()

    # 1. Cron 調度（每天早上 8 點）
    await scheduler.create_cron_schedule(
        flow_name="daily_report",
        cron="0 8 * * *",
        schedule_name="morning_report"
    )

    # 2. 間隔調度（每小時）
    await scheduler.create_interval_schedule(
        flow_name="health_check",
        interval_seconds=3600,
        schedule_name="hourly_health_check"
    )

    # 3. 列出所有調度
    schedules = await scheduler.list_schedules()
    print(f"當前調度: {schedules}")

asyncio.run(setup_schedules())
```

#### 安裝和運行

```bash
# 安裝 Prefect
pip install prefect

# 啟動 Prefect 服務器
prefect server start

# 訪問 UI
open http://localhost:4200
```

---

### Celery 集成

Celery 是一個分布式任務隊列，用於處理大量異步任務。

#### 基本功能

```python
from ai_automation_framework.integrations.celery_integration import CeleryIntegration

# 初始化
celery = CeleryIntegration(
    broker_url="redis://localhost:6379/0",
    backend_url="redis://localhost:6379/0"
)

# 1. 定義任務
@celery.create_task(name="send_email")
def send_email(to: str, subject: str, body: str):
    print(f"發送郵件到 {to}")
    return {"sent": True}

@celery.create_task(name="process_image")
def process_image(image_path: str):
    print(f"處理圖片: {image_path}")
    return {"processed": True}

# 2. 發送任務
result = celery.send_task(
    task_name="send_email",
    kwargs={
        "to": "user@example.com",
        "subject": "Hello",
        "body": "Test message"
    }
)
print(f"任務已發送: {result}")

# 3. 獲取任務結果
if result.get('success'):
    task_result = celery.get_task_result(result['task_id'])
    print(f"任務結果: {task_result}")

# 4. 延遲任務（5秒後執行）
delayed_result = celery.send_task(
    task_name="send_email",
    args=["admin@example.com", "Reminder", "Don't forget!"],
    countdown=5
)

# 5. 撤銷任務
celery.revoke_task(task_id=result['task_id'], terminate=True)
```

#### 任務鏈和組

```python
from celery import chain, group

# 1. 任務鏈（順序執行）
@celery.create_task(name="step1")
def step1(data):
    return {"step": 1, "data": data}

@celery.create_task(name="step2")
def step2(result):
    return {"step": 2, "previous": result}

# 創建任務鏈
task_chain = chain(
    step1.s("initial_data"),
    step2.s()
)

# 2. 任務組（並行執行）
@celery.create_task(name="process_file")
def process_file(file_path):
    return {"file": file_path, "processed": True}

# 創建任務組
task_group = group(
    process_file.s("/data/file1.txt"),
    process_file.s("/data/file2.txt"),
    process_file.s("/data/file3.txt")
)
```

#### 週期性任務

```python
from datetime import timedelta
from celery.schedules import crontab

# 添加每小時執行的任務
celery.add_periodic_task(
    schedule=timedelta(hours=1),
    task_name="cleanup_task",
    name="hourly_cleanup"
)

# 添加每天凌晨 2 點的備份任務
celery.add_periodic_task(
    schedule=crontab(hour=2, minute=0),
    task_name="backup_task",
    name="daily_backup"
)
```

#### 任務監控

```python
from ai_automation_framework.integrations.celery_integration import CeleryMonitor

monitor = CeleryMonitor(celery.app)

# 1. 獲取活動任務
active = celery.get_active_tasks()
print(f"活動任務: {active}")

# 2. 獲取統計信息
stats = monitor.get_stats()
print(f"統計信息: {stats}")

# 3. Ping Workers
ping = monitor.ping_workers()
print(f"Worker 狀態: {ping}")
```

#### 安裝和運行

```bash
# 安裝 Celery 和 Redis
pip install celery[redis]

# 啟動 Redis
redis-server

# 啟動 Celery Worker
celery -A your_app worker --loglevel=info

# 啟動 Celery Beat（定時任務）
celery -A your_app beat

# 監控任務（使用 Flower）
pip install flower
celery -A your_app flower
```

---

## 統一接口使用

### 單平台使用

```python
from ai_automation_framework.integrations.workflow_automation_unified import (
    UnifiedWorkflowManager,
    WorkflowPlatform
)

manager = UnifiedWorkflowManager()

# 註冊平台
manager.register_n8n("http://localhost:5678", "api_key")

# 觸發工作流
result = manager.trigger_workflow(
    platform=WorkflowPlatform.N8N,
    workflow_id="workflow_123",
    data={"key": "value"}
)
```

### 多平台集成

```python
manager = UnifiedWorkflowManager()

# 註冊多個平台
manager.register_n8n("http://localhost:5678", "n8n_key")
manager.register_zapier(webhook_url="https://hooks.zapier.com/...")
manager.register_make(api_token="make_token")
manager.register_airflow("http://localhost:8080", "admin", "password")
manager.register_temporal(host="localhost:7233")
manager.register_prefect()
manager.register_celery(broker_url="redis://localhost:6379/0")

# 廣播觸發
results = manager.broadcast_trigger(
    platforms=[
        WorkflowPlatform.N8N,
        WorkflowPlatform.ZAPIER,
        WorkflowPlatform.MAKE
    ],
    workflow_configs={
        "n8n": "notification_workflow",
        "zapier": "https://hooks.zapier.com/...",
        "make": "scenario_notify"
    },
    data={"event": "order_completed", "order_id": "ORD-123"}
)

# 檢查結果
for platform, result in results.items():
    print(f"{platform}: {result.get('success')}")
```

---

## 高級用法

### 1. 順序工作流編排

```python
from ai_automation_framework.integrations.workflow_automation_unified import (
    WorkflowOrchestrator
)

orchestrator = WorkflowOrchestrator(manager)

# 定義順序步驟
steps = [
    {
        "platform": WorkflowPlatform.N8N,
        "workflow_id": "extract_data",
        "data": {"source": "database"}
    },
    {
        "platform": WorkflowPlatform.MAKE,
        "workflow_id": "transform_data",
        "use_previous_output": True  # 使用前一步的輸出
    },
    {
        "platform": WorkflowPlatform.ZAPIER,
        "workflow_id": "notify_users",
        "use_previous_output": True
    }
]

result = orchestrator.execute_sequential(steps)
```

### 2. 並行工作流執行

```python
# 定義並行任務
workflows = [
    {
        "platform": WorkflowPlatform.N8N,
        "workflow_id": "send_email",
        "data": {"to": "admin@example.com"}
    },
    {
        "platform": WorkflowPlatform.ZAPIER,
        "workflow_id": "log_event",
        "data": {"event_type": "notification_sent"}
    },
    {
        "platform": WorkflowPlatform.MAKE,
        "workflow_id": "update_crm",
        "data": {"customer_id": "CUST-123"}
    }
]

# 並行執行
result = orchestrator.execute_parallel(workflows)
```

### 3. 錯誤處理和重試

```python
import time

def trigger_with_retry(manager, platform, workflow_id, data, max_retries=3):
    """帶重試的工作流觸發"""
    for attempt in range(max_retries):
        result = manager.trigger_workflow(platform, workflow_id, data)

        if result.get('success'):
            return result

        print(f"嘗試 {attempt + 1} 失敗，重試中...")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # 指數退避

    return result

# 使用
result = trigger_with_retry(
    manager,
    WorkflowPlatform.N8N,
    "critical_workflow",
    {"data": "important"}
)
```

### 4. 條件執行

```python
def conditional_workflow(manager, condition, workflow_a_id, workflow_b_id):
    """根據條件執行不同的工作流"""

    if condition:
        workflow_id = workflow_a_id
        platform = WorkflowPlatform.N8N
    else:
        workflow_id = workflow_b_id
        platform = WorkflowPlatform.ZAPIER

    return manager.trigger_workflow(
        platform=platform,
        workflow_id=workflow_id,
        data={"condition": condition}
    )

# 使用
is_premium_customer = True
result = conditional_workflow(
    manager,
    is_premium_customer,
    "premium_workflow",
    "standard_workflow"
)
```

---

## 最佳實踐

### 1. 環境變量管理

```python
import os
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

manager = UnifiedWorkflowManager()

# 使用環境變量
manager.register_n8n(
    base_url=os.getenv("N8N_BASE_URL"),
    api_key=os.getenv("N8N_API_KEY")
)
```

### 2. 日誌記錄

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_with_logging(manager, platform, workflow_id, data):
    """帶日誌的工作流觸發"""
    logger.info(f"觸發工作流: {platform.value}/{workflow_id}")

    result = manager.trigger_workflow(platform, workflow_id, data)

    if result.get('success'):
        logger.info(f"執行成功: {result.get('data', {}).get('id')}")
    else:
        logger.error(f"執行失敗: {result.get('error')}")

    return result
```

### 3. 配置管理

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class WorkflowConfig:
    platform: WorkflowPlatform
    workflow_id: str
    default_data: Dict[str, Any]
    retry_count: int = 3
    timeout: int = 300

# 定義配置
WORKFLOWS = {
    "order_notification": WorkflowConfig(
        platform=WorkflowPlatform.N8N,
        workflow_id="notify_order",
        default_data={"channel": "email"},
        retry_count=3
    ),
    "data_sync": WorkflowConfig(
        platform=WorkflowPlatform.AIRFLOW,
        workflow_id="sync_dag",
        default_data={},
        timeout=600
    )
}

# 使用配置
config = WORKFLOWS["order_notification"]
result = manager.trigger_workflow(
    platform=config.platform,
    workflow_id=config.workflow_id,
    data={**config.default_data, "order_id": "ORD-123"}
)
```

### 4. 監控和告警

```python
def monitor_workflow_execution(manager, platform, execution_id, alert_func=None):
    """監控工作流執行並在失敗時告警"""
    result = manager.get_workflow_status(platform, execution_id)

    if not result.get('success'):
        error_msg = f"工作流執行失敗: {result.get('error')}"

        if alert_func:
            alert_func(error_msg)
        else:
            print(f"❌ {error_msg}")

        return False

    return True

# 使用
def send_alert(message):
    # 發送告警到 Slack/Email 等
    print(f"🚨 告警: {message}")

monitor_workflow_execution(
    manager,
    WorkflowPlatform.N8N,
    "exec_123",
    alert_func=send_alert
)
```

---

## 故障排除

### 常見問題

#### 1. 連接超時

```python
# 增加超時時間
from ai_automation_framework.integrations.n8n_integration_enhanced import N8NEnhanced

n8n = N8NEnhanced(
    base_url="http://localhost:5678",
    api_key="key",
    timeout=60  # 60 秒超時
)
```

#### 2. API 密鑰無效

```bash
# 驗證環境變量
echo $N8N_API_KEY
echo $ZAPIER_API_KEY
echo $MAKE_API_TOKEN

# 重新加載環境變量
source .env  # Bash
# 或
dotenv load  # Python-dotenv
```

#### 3. Webhook URL 錯誤

```python
# 驗證 Webhook URL
webhook_url = "https://hooks.zapier.com/hooks/catch/xxx/yyy/"

# 測試連接
import requests
response = requests.post(webhook_url, json={"test": "data"})
print(response.status_code)  # 應該返回 200
```

#### 4. 數據格式錯誤

```python
# 確保數據是 JSON 可序列化的
import json

data = {
    "string": "text",
    "number": 123,
    "boolean": True,
    "list": [1, 2, 3],
    "dict": {"key": "value"}
}

# 驗證
try:
    json.dumps(data)
    print("✅ 數據格式正確")
except TypeError as e:
    print(f"❌ 數據格式錯誤: {e}")
```

### 調試技巧

```python
# 啟用詳細日誌
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 打印請求和響應
result = manager.trigger_workflow(
    platform=WorkflowPlatform.N8N,
    workflow_id="workflow_id",
    data={"debug": True}
)

print(json.dumps(result, indent=2))
```

---

## 總結

通過本指南，您已經學會了：

- ✅ 集成多個工作流自動化平台
- ✅ 使用統一接口管理工作流
- ✅ 實現順序和並行工作流編排
- ✅ 處理錯誤和實現重試邏輯
- ✅ 應用最佳實踐和監控策略

## 更多資源

- [n8n 文檔](https://docs.n8n.io/)
- [Make 文檔](https://www.make.com/en/help)
- [Zapier 文檔](https://platform.zapier.com/docs/)
- [Airflow 文檔](https://airflow.apache.org/docs/)

---

**最後更新**: 2025-01-XX
**版本**: 2.0.0
