"""
統一工作流自動化接口
Unified Workflow Automation Interface

提供統一的接口來集成各種工作流自動化工具（n8n、Make、Zapier、Temporal、Prefect、Airflow）
"""

import os
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod


class WorkflowPlatform(Enum):
    """工作流平台類型"""
    N8N = "n8n"
    MAKE = "make"
    ZAPIER = "zapier"
    TEMPORAL = "temporal"
    PREFECT = "prefect"
    AIRFLOW = "airflow"
    CELERY = "celery"


class WorkflowStatus(Enum):
    """工作流狀態"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseWorkflowAdapter(ABC):
    """工作流適配器基類"""

    @abstractmethod
    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """觸發工作流"""
        pass

    @abstractmethod
    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """獲取工作流狀態"""
        pass

    @abstractmethod
    def list_workflows(self) -> Dict[str, Any]:
        """列出所有工作流"""
        pass


class N8NAdapter(BaseWorkflowAdapter):
    """n8n 適配器"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        from .n8n_integration_enhanced import N8NEnhanced
        self.client = N8NEnhanced(base_url, api_key)

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.client.execute_workflow(workflow_id, data)

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        return self.client.get_execution(execution_id)

    def list_workflows(self) -> Dict[str, Any]:
        return self.client.get_workflows()


class MakeAdapter(BaseWorkflowAdapter):
    """Make 適配器"""

    def __init__(self, api_token: str):
        from .make_integration import MakeIntegration
        self.client = MakeIntegration(api_token=api_token)

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.client.run_scenario(workflow_id, data)

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        # Make API 沒有直接的執行狀態查詢
        return {
            'success': True,
            'message': 'Status query not fully supported by Make API'
        }

    def list_workflows(self) -> Dict[str, Any]:
        return self.client.get_scenarios()


class ZapierAdapter(BaseWorkflowAdapter):
    """Zapier 適配器"""

    def __init__(self, webhook_url: Optional[str] = None, api_key: Optional[str] = None):
        from .zapier_integration_enhanced import ZapierEnhanced
        self.client = ZapierEnhanced(webhook_url, api_key)

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Zapier 主要通過 Webhook 觸發
        return self.client.trigger_webhook(data, workflow_id)

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        # Zapier Webhook 是即時的，沒有持久化的執行狀態
        return {
            'success': True,
            'message': 'Zapier webhooks are fire-and-forget'
        }

    def list_workflows(self) -> Dict[str, Any]:
        if hasattr(self.client, 'api_key') and self.client.api_key:
            return self.client.get_zaps()
        return {
            'success': False,
            'error': 'API key required to list Zaps'
        }


class AirflowAdapter(BaseWorkflowAdapter):
    """Apache Airflow 適配器"""

    def __init__(self, base_url: str, username: str, password: str):
        from .airflow_integration import AirflowIntegration
        self.client = AirflowIntegration(base_url, username, password)

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.client.trigger_dag(workflow_id, data)

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        # Validate execution_id before split
        if not execution_id or not isinstance(execution_id, str):
            return {
                'success': False,
                'error': 'Invalid execution_id: must be a non-empty string'
            }

        parts = execution_id.split('___')
        if len(parts) == 2:
            dag_id, dag_run_id = parts
            return self.client.get_dag_run(dag_id, dag_run_id)
        return {
            'success': False,
            'error': 'Invalid execution_id format: expected format "dag_id___dag_run_id"'
        }

    def list_workflows(self) -> Dict[str, Any]:
        return self.client.list_dags()


class TemporalAdapter(BaseWorkflowAdapter):
    """Temporal.io 適配器"""

    def __init__(self, host: str = "localhost:7233", namespace: str = "default", task_queue: str = "default"):
        from .temporal_integration import TemporalIntegration
        self.client = TemporalIntegration(host=host, namespace=namespace, task_queue=task_queue)
        self._connected = False

    async def _ensure_connected(self):
        """確保已連接到 Temporal"""
        if not self._connected:
            await self.client.connect()
            self._connected = True

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """觸發 Temporal 工作流（同步包裝器）"""
        import asyncio

        async def _trigger():
            await self._ensure_connected()
            # Safely extract workflow_type and args without mutating original data
            if data:
                workflow_type = data.pop('workflow_type', workflow_id)
                args = data.pop('args', [])
            else:
                workflow_type = workflow_id
                args = []
            return await self.client.start_workflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                args=args
            )

        try:
            return asyncio.run(_trigger())
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_trigger())
            raise

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """獲取工作流狀態"""
        import asyncio

        async def _get_status():
            await self._ensure_connected()
            return await self.client.get_workflow_result(execution_id)

        try:
            return asyncio.run(_get_status())
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_get_status())
            raise

    def list_workflows(self) -> Dict[str, Any]:
        """列出工作流（Temporal 不直接支持，返回提示）"""
        return {
            'success': True,
            'message': 'Temporal does not provide direct workflow listing. Use Temporal UI or tctl.'
        }


class PrefectAdapter(BaseWorkflowAdapter):
    """Prefect 適配器"""

    def __init__(self):
        from .prefect_integration import PrefectIntegration
        self.client = PrefectIntegration()

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """觸發 Prefect Flow（同步包裝器）"""
        import asyncio

        async def _trigger():
            return await self.client.create_flow_run(
                flow_name=workflow_id,
                parameters=data or {}
            )

        try:
            return asyncio.run(_trigger())
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_trigger())
            raise

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """獲取 Flow Run 狀態"""
        import asyncio

        async def _get_status():
            return await self.client.get_flow_run_status(execution_id)

        try:
            return asyncio.run(_get_status())
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_get_status())
            raise

    def list_workflows(self) -> Dict[str, Any]:
        """列出所有 Flows"""
        import asyncio

        async def _list():
            return await self.client.list_flows()

        try:
            return asyncio.run(_list())
        except RuntimeError as e:
            # Handle case where event loop is already running
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_list())
            raise


class CeleryAdapter(BaseWorkflowAdapter):
    """Celery 適配器"""

    def __init__(self, broker_url: Optional[str] = None, backend_url: Optional[str] = None):
        from .celery_integration import CeleryIntegration
        self.client = CeleryIntegration(broker_url=broker_url, backend_url=backend_url)

    def trigger_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """發送 Celery 任務"""
        # Safely extract args without mutating original data
        if data:
            args = data.pop('args', [])
            kwargs = data
        else:
            args = []
            kwargs = {}

        return self.client.send_task(
            task_name=workflow_id,
            args=args,
            kwargs=kwargs
        )

    def get_workflow_status(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """獲取任務狀態"""
        return self.client.get_task_result(execution_id)

    def list_workflows(self) -> Dict[str, Any]:
        """獲取活動任務"""
        return self.client.get_active_tasks()


class UnifiedWorkflowManager:
    """統一工作流管理器"""

    def __init__(self):
        """初始化工作流管理器"""
        self.adapters: Dict[WorkflowPlatform, BaseWorkflowAdapter] = {}

    def register_platform(
        self,
        platform: WorkflowPlatform,
        adapter: BaseWorkflowAdapter
    ):
        """
        註冊工作流平台

        Args:
            platform: 平台類型
            adapter: 平台適配器
        """
        self.adapters[platform] = adapter

    def register_n8n(
        self,
        base_url: str,
        api_key: Optional[str] = None
    ):
        """註冊 n8n"""
        adapter = N8NAdapter(base_url, api_key)
        self.register_platform(WorkflowPlatform.N8N, adapter)

    def register_make(
        self,
        api_token: str
    ):
        """註冊 Make"""
        adapter = MakeAdapter(api_token)
        self.register_platform(WorkflowPlatform.MAKE, adapter)

    def register_zapier(
        self,
        webhook_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """註冊 Zapier"""
        adapter = ZapierAdapter(webhook_url, api_key)
        self.register_platform(WorkflowPlatform.ZAPIER, adapter)

    def register_airflow(
        self,
        base_url: str,
        username: str,
        password: str
    ):
        """註冊 Airflow"""
        adapter = AirflowAdapter(base_url, username, password)
        self.register_platform(WorkflowPlatform.AIRFLOW, adapter)

    def register_temporal(
        self,
        host: str = "localhost:7233",
        namespace: str = "default",
        task_queue: str = "default"
    ):
        """註冊 Temporal"""
        adapter = TemporalAdapter(host, namespace, task_queue)
        self.register_platform(WorkflowPlatform.TEMPORAL, adapter)

    def register_prefect(self):
        """註冊 Prefect"""
        adapter = PrefectAdapter()
        self.register_platform(WorkflowPlatform.PREFECT, adapter)

    def register_celery(
        self,
        broker_url: Optional[str] = None,
        backend_url: Optional[str] = None
    ):
        """註冊 Celery"""
        adapter = CeleryAdapter(broker_url, backend_url)
        self.register_platform(WorkflowPlatform.CELERY, adapter)

    def trigger_workflow(
        self,
        platform: Union[WorkflowPlatform, str],
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        觸發工作流

        Args:
            platform: 平台類型
            workflow_id: 工作流 ID
            data: 輸入數據

        Returns:
            執行結果
        """
        if isinstance(platform, str):
            platform = WorkflowPlatform(platform)

        if platform not in self.adapters:
            return {
                'success': False,
                'error': f'Platform {platform.value} not registered'
            }

        try:
            result = self.adapters[platform].trigger_workflow(workflow_id, data)
            result['platform'] = platform.value
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': platform.value
            }

    def get_workflow_status(
        self,
        platform: Union[WorkflowPlatform, str],
        execution_id: str
    ) -> Dict[str, Any]:
        """獲取工作流狀態"""
        if isinstance(platform, str):
            platform = WorkflowPlatform(platform)

        if platform not in self.adapters:
            return {
                'success': False,
                'error': f'Platform {platform.value} not registered'
            }

        try:
            result = self.adapters[platform].get_workflow_status(execution_id)
            result['platform'] = platform.value
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': platform.value
            }

    def list_workflows(
        self,
        platform: Union[WorkflowPlatform, str]
    ) -> Dict[str, Any]:
        """列出工作流"""
        if isinstance(platform, str):
            platform = WorkflowPlatform(platform)

        if platform not in self.adapters:
            return {
                'success': False,
                'error': f'Platform {platform.value} not registered'
            }

        try:
            result = self.adapters[platform].list_workflows()
            result['platform'] = platform.value
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': platform.value
            }

    def broadcast_trigger(
        self,
        platforms: List[Union[WorkflowPlatform, str]],
        workflow_configs: Dict[str, str],
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        廣播觸發多個平台的工作流

        Args:
            platforms: 平台列表
            workflow_configs: 平台到工作流 ID 的映射
            data: 共享的輸入數據

        Returns:
            各平台的執行結果
        """
        results = {}

        for platform in platforms:
            if isinstance(platform, str):
                platform = WorkflowPlatform(platform)

            platform_key = platform.value

            if platform_key in workflow_configs:
                workflow_id = workflow_configs[platform_key]
                results[platform_key] = self.trigger_workflow(
                    platform,
                    workflow_id,
                    data
                )
            else:
                results[platform_key] = {
                    'success': False,
                    'error': 'No workflow_id configured for this platform'
                }

        return results


class WorkflowOrchestrator:
    """工作流編排器 - 協調多個工作流"""

    def __init__(self, manager: UnifiedWorkflowManager):
        """
        初始化編排器

        Args:
            manager: 統一工作流管理器
        """
        self.manager = manager

    def execute_sequential(
        self,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        順序執行多個工作流

        Args:
            steps: 步驟列表，每個步驟包含 platform 和 workflow_id

        Returns:
            執行結果
        """
        results = []
        previous_output = None

        for i, step in enumerate(steps):
            platform = step['platform']
            workflow_id = step['workflow_id']
            data = step.get('data', {})

            # 如果有前一步的輸出，合併到數據中
            if previous_output and step.get('use_previous_output', True):
                data = {**data, 'previous_output': previous_output}

            result = self.manager.trigger_workflow(platform, workflow_id, data)
            results.append({
                'step': i + 1,
                'platform': platform,
                'workflow_id': workflow_id,
                'result': result
            })

            if not result.get('success'):
                return {
                    'success': False,
                    'failed_at_step': i + 1,
                    'results': results
                }

            previous_output = result.get('data')

        return {
            'success': True,
            'results': results
        }

    def execute_parallel(
        self,
        workflows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        並行執行多個工作流

        Args:
            workflows: 工作流配置列表

        Returns:
            執行結果
        """
        import concurrent.futures

        def execute_single(workflow_config):
            platform = workflow_config['platform']
            workflow_id = workflow_config['workflow_id']
            data = workflow_config.get('data', {})

            return self.manager.trigger_workflow(platform, workflow_id, data)

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(workflows)) as executor:
            future_to_workflow = {
                executor.submit(execute_single, wf): wf
                for wf in workflows
            }

            for future in concurrent.futures.as_completed(future_to_workflow):
                workflow = future_to_workflow[future]
                try:
                    result = future.result()
                    results.append({
                        'platform': workflow['platform'],
                        'workflow_id': workflow['workflow_id'],
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'platform': workflow['platform'],
                        'workflow_id': workflow['workflow_id'],
                        'result': {
                            'success': False,
                            'error': str(e)
                        }
                    })

        return {
            'success': all(r['result'].get('success', False) for r in results),
            'results': results
        }


__all__ = [
    'WorkflowPlatform',
    'WorkflowStatus',
    'UnifiedWorkflowManager',
    'WorkflowOrchestrator',
    'BaseWorkflowAdapter',
    'N8NAdapter',
    'MakeAdapter',
    'ZapierAdapter',
    'AirflowAdapter',
    'TemporalAdapter',
    'PrefectAdapter',
    'CeleryAdapter',
]
