"""
Temporal.io 工作流集成
Temporal.io Workflow Integration

提供與 Temporal.io 分布式工作流引擎的集成。
"""

import os
from typing import Dict, Any, List, Optional, Callable
from datetime import timedelta
from enum import Enum

try:
    from temporalio import workflow, activity
    from temporalio.client import Client, WorkflowHandle
    from temporalio.worker import Worker
    HAS_TEMPORAL = True
except ImportError:
    HAS_TEMPORAL = False
    workflow = None
    activity = None
    Client = None


class TemporalIntegration:
    """Temporal.io 集成"""

    def __init__(
        self,
        server_url: str = "localhost:7233",
        namespace: str = "default"
    ):
        """
        初始化 Temporal 集成

        Args:
            server_url: Temporal 服務器地址
            namespace: 命名空間
        """
        if not HAS_TEMPORAL:
            raise ImportError(
                "需要安裝 Temporal SDK: pip install temporalio"
            )

        self.server_url = server_url
        self.namespace = namespace
        self.client = None

    async def connect(self):
        """連接到 Temporal 服務器"""
        try:
            self.client = await Client.connect(
                self.server_url,
                namespace=self.namespace
            )
            return self.client
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Temporal server: {str(e)}")

    async def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        args: Optional[List[Any]] = None,
        task_queue: str = "default-task-queue",
        execution_timeout: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        啟動工作流

        Args:
            workflow_id: 工作流 ID
            workflow_type: 工作流類型
            args: 工作流參數
            task_queue: 任務隊列
            execution_timeout: 執行超時時間

        Returns:
            工作流句柄信息
        """
        if not self.client:
            await self.connect()

        try:
            handle = await self.client.start_workflow(
                workflow_type,
                *args if args else [],
                id=workflow_id,
                task_queue=task_queue,
                execution_timeout=execution_timeout
            )

            return {
                'success': True,
                'workflow_id': handle.id,
                'run_id': handle.result_run_id,
                'handle': handle
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_workflow_result(
        self,
        workflow_id: str,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        獲取工作流結果

        Args:
            workflow_id: 工作流 ID
            run_id: 運行 ID

        Returns:
            工作流結果
        """
        if not self.client:
            await self.connect()

        try:
            handle = self.client.get_workflow_handle(
                workflow_id,
                run_id=run_id
            )

            result = await handle.result()

            return {
                'success': True,
                'result': result,
                'workflow_id': workflow_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def query_workflow(
        self,
        workflow_id: str,
        query_name: str,
        args: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        查詢工作流狀態

        Args:
            workflow_id: 工作流 ID
            query_name: 查詢名稱
            args: 查詢參數

        Returns:
            查詢結果
        """
        if not self.client:
            await self.connect()

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            result = await handle.query(query_name, *args if args else [])

            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        args: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        向工作流發送信號

        Args:
            workflow_id: 工作流 ID
            signal_name: 信號名稱
            args: 信號參數

        Returns:
            執行結果
        """
        if not self.client:
            await self.connect()

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.signal(signal_name, *args if args else [])

            return {
                'success': True,
                'message': f'Signal {signal_name} sent to workflow {workflow_id}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        取消工作流

        Args:
            workflow_id: 工作流 ID

        Returns:
            執行結果
        """
        if not self.client:
            await self.connect()

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.cancel()

            return {
                'success': True,
                'message': f'Workflow {workflow_id} cancelled'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: str = "Terminated by user"
    ) -> Dict[str, Any]:
        """
        終止工作流

        Args:
            workflow_id: 工作流 ID
            reason: 終止原因

        Returns:
            執行結果
        """
        if not self.client:
            await self.connect()

        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.terminate(reason)

            return {
                'success': True,
                'message': f'Workflow {workflow_id} terminated: {reason}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_workflow(self, **kwargs):
        """
        創建工作流裝飾器（實例方法）

        Args:
            **kwargs: 傳遞給 Temporal workflow 的參數

        Returns:
            Temporal workflow 裝飾器
        """
        return self.create_workflow_decorator()

    def create_activity(self, **kwargs):
        """
        創建活動裝飾器（實例方法）

        Args:
            **kwargs: 傳遞給 Temporal activity 的參數

        Returns:
            Temporal activity 裝飾器
        """
        return self.create_activity_decorator()

    @staticmethod
    def create_workflow_decorator():
        """創建工作流裝飾器"""
        if not HAS_TEMPORAL:
            raise ImportError("需要安裝 Temporal SDK")

        return workflow.defn

    @staticmethod
    def create_activity_decorator():
        """創建活動裝飾器"""
        if not HAS_TEMPORAL:
            raise ImportError("需要安裝 Temporal SDK")

        return activity.defn


# 示例工作流定義
if HAS_TEMPORAL:
    @workflow.defn
    class SampleWorkflow:
        """示例工作流"""

        @workflow.run
        async def run(self, name: str) -> str:
            """
            運行工作流

            Args:
                name: 名稱參數

            Returns:
                處理結果
            """
            return f"Hello, {name}!"

    @activity.defn
    async def sample_activity(name: str) -> str:
        """示例活動"""
        return f"Processed: {name}"


class TemporalWorkflowBuilder:
    """Temporal 工作流構建器"""

    def __init__(self):
        """初始化構建器"""
        self.workflows = []
        self.activities = []

    def register_workflow(self, **kwargs):
        """
        註冊工作流裝飾器

        Args:
            **kwargs: 工作流參數（例如 name）

        Returns:
            裝飾器函數
        """
        def decorator(func):
            if not HAS_TEMPORAL:
                raise ImportError("需要安裝 Temporal SDK")

            # 使用 Temporal 的 workflow.defn 裝飾器
            workflow_func = workflow.defn(func)
            self.workflows.append(workflow_func)
            return workflow_func
        return decorator

    def register_activity(self, **kwargs):
        """
        註冊活動裝飾器

        Args:
            **kwargs: 活動參數（例如 name）

        Returns:
            裝飾器函數
        """
        def decorator(func):
            if not HAS_TEMPORAL:
                raise ImportError("需要安裝 Temporal SDK")

            # 使用 Temporal 的 activity.defn 裝飾器
            activity_func = activity.defn(func)
            self.activities.append(activity_func)
            return activity_func
        return decorator

    def add_workflow(self, workflow_class):
        """添加工作流"""
        self.workflows.append(workflow_class)
        return self

    def add_activity(self, activity_func):
        """添加活動"""
        self.activities.append(activity_func)
        return self

    async def create_worker(
        self,
        client: Client,
        task_queue: str = "default-task-queue"
    ):
        """
        創建 Worker

        Args:
            client: Temporal 客戶端
            task_queue: 任務隊列

        Returns:
            Worker 實例
        """
        if not HAS_TEMPORAL:
            raise ImportError("需要安裝 Temporal SDK")

        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=self.workflows,
            activities=self.activities
        )

        return worker


__all__ = [
    'TemporalIntegration',
    'TemporalWorkflowBuilder',
    'SampleWorkflow',
    'sample_activity'
]
