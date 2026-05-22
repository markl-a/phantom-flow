"""
Prefect 工作流集成
Prefect Workflow Integration

提供與 Prefect 現代數據工作流平台的集成。
"""

import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

try:
    from prefect import flow, task, get_run_logger
    from prefect.client import get_client
    from prefect.deployments import Deployment
    from prefect.server.schemas.filters import FlowFilter, FlowRunFilter
    from prefect.server.schemas.sorting import FlowRunSort
    HAS_PREFECT = True
except ImportError:
    HAS_PREFECT = False
    flow = None
    task = None


class PrefectIntegration:
    """Prefect 集成"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        初始化 Prefect 集成

        Args:
            api_url: Prefect API URL
            api_key: API 密鑰（Prefect Cloud）
        """
        if not HAS_PREFECT:
            raise ImportError(
                "需要安裝 Prefect: pip install prefect"
            )

        self.api_url = api_url or os.getenv("PREFECT_API_URL")
        self.api_key = api_key or os.getenv("PREFECT_API_KEY")

        if self.api_url:
            os.environ["PREFECT_API_URL"] = self.api_url
        if self.api_key:
            os.environ["PREFECT_API_KEY"] = self.api_key

    async def create_flow_run(
        self,
        flow_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        創建流程運行

        Args:
            flow_name: 流程名稱
            parameters: 參數
            tags: 標籤

        Returns:
            運行信息
        """
        try:
            async with get_client() as client:
                # 查找流程
                flows = await client.read_flows(
                    flow_filter=FlowFilter(name={"any_": [flow_name]})
                )

                if not flows:
                    return {
                        'success': False,
                        'error': f'Flow {flow_name} not found'
                    }

                flow_obj = flows[0]

                # 創建流程運行
                flow_run = await client.create_flow_run(
                    flow=flow_obj,
                    parameters=parameters or {},
                    tags=tags or []
                )

                return {
                    'success': True,
                    'flow_run_id': str(flow_run.id),
                    'flow_run_name': flow_run.name,
                    'state': flow_run.state.type.value if flow_run.state else None
                }
        except ConnectionError as e:
            return {
                'success': False,
                'error': f'Failed to connect to Prefect server: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def get_flow_run(self, flow_run_id: str) -> Dict[str, Any]:
        """
        獲取流程運行詳情

        Args:
            flow_run_id: 流程運行 ID

        Returns:
            運行詳情
        """
        try:
            async with get_client() as client:
                flow_run = await client.read_flow_run(flow_run_id)

                return {
                    'success': True,
                    'flow_run': {
                        'id': str(flow_run.id),
                        'name': flow_run.name,
                        'state': flow_run.state.type.value if flow_run.state else None,
                        'start_time': flow_run.start_time.isoformat() if flow_run.start_time else None,
                        'end_time': flow_run.end_time.isoformat() if flow_run.end_time else None,
                        'total_run_time': flow_run.total_run_time
                    }
                }
        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid flow run ID: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def list_flow_runs(
        self,
        flow_name: Optional[str] = None,
        limit: int = 10,
        state_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        列出流程運行

        Args:
            flow_name: 流程名稱過濾
            limit: 限制數量
            state_type: 狀態類型過濾

        Returns:
            流程運行列表
        """
        try:
            async with get_client() as client:
                flow_runs = await client.read_flow_runs(
                    limit=limit,
                    sort=FlowRunSort.START_TIME_DESC
                )

                runs = []
                for run in flow_runs:
                    runs.append({
                        'id': str(run.id),
                        'name': run.name,
                        'flow_name': run.flow_name,
                        'state': run.state.type.value if run.state else None,
                        'start_time': run.start_time.isoformat() if run.start_time else None
                    })

                return {
                    'success': True,
                    'flow_runs': runs,
                    'count': len(runs)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def cancel_flow_run(self, flow_run_id: str) -> Dict[str, Any]:
        """
        取消流程運行

        Args:
            flow_run_id: 流程運行 ID

        Returns:
            執行結果
        """
        try:
            async with get_client() as client:
                # Use the proper cancel_flow_run method instead of deprecated set_flow_run_state
                from prefect.client.schemas.states import Cancelled

                flow_run = await client.read_flow_run(flow_run_id)
                await client.set_flow_run_state(
                    flow_run_id,
                    state=Cancelled(message="Cancelled by user")
                )

                return {
                    'success': True,
                    'message': f'Flow run {flow_run_id} cancelled'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'flow_run_id': flow_run_id
            }

    async def get_flow_run_logs(
        self,
        flow_run_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        獲取流程運行日誌

        Args:
            flow_run_id: 流程運行 ID
            limit: 日誌數量限制

        Returns:
            日誌列表
        """
        try:
            async with get_client() as client:
                logs = await client.read_logs(
                    flow_run_id=flow_run_id,
                    limit=limit
                )

                log_entries = []
                for log in logs:
                    log_entries.append({
                        'timestamp': log.timestamp.isoformat(),
                        'level': log.level,
                        'message': log.message
                    })

                return {
                    'success': True,
                    'logs': log_entries,
                    'count': len(log_entries)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_flow(self, **kwargs):
        """
        創建流程裝飾器（實例方法）

        Args:
            **kwargs: 傳遞給 Prefect flow 的參數

        Returns:
            Prefect flow 裝飾器
        """
        return self.create_flow_decorator(**kwargs)

    def create_task(self, **kwargs):
        """
        創建任務裝飾器（實例方法）

        Args:
            **kwargs: 傳遞給 Prefect task 的參數

        Returns:
            Prefect task 裝飾器
        """
        return self.create_task_decorator(**kwargs)

    @staticmethod
    def create_flow_decorator(**kwargs):
        """創建流程裝飾器"""
        if not HAS_PREFECT:
            raise ImportError("需要安裝 Prefect")
        return flow(**kwargs)

    @staticmethod
    def create_task_decorator(**kwargs):
        """創建任務裝飾器"""
        if not HAS_PREFECT:
            raise ImportError("需要安裝 Prefect")
        return task(**kwargs)


# 示例流程和任務
if HAS_PREFECT:
    @task
    def sample_task(name: str) -> str:
        """示例任務"""
        logger = get_run_logger()
        logger.info(f"Processing {name}")
        return f"Processed: {name}"

    @flow(name="sample-flow")
    def sample_flow(name: str) -> str:
        """示例流程"""
        logger = get_run_logger()
        logger.info(f"Starting flow with {name}")

        result = sample_task(name)

        logger.info(f"Flow completed with result: {result}")
        return result


class PrefectFlowBuilder:
    """Prefect 流程構建器"""

    def __init__(self, name: str = ""):
        """
        初始化構建器

        Args:
            name: 流程名稱（可選）
        """
        if not HAS_PREFECT:
            raise ImportError("需要安裝 Prefect")

        self.name = name
        self.tasks = []
        self.flows = []
        self.description = ""
        self.tags = []

    def register_task(self, **kwargs):
        """
        註冊任務裝飾器

        Args:
            **kwargs: 任務參數（例如 name, retries, retry_delay_seconds）

        Returns:
            裝飾器函數
        """
        def decorator(func):
            if not HAS_PREFECT:
                raise ImportError("需要安裝 Prefect")

            # 使用 Prefect 的 task 裝飾器
            task_func = task(**kwargs)(func)
            self.tasks.append((task_func, kwargs))
            return task_func
        return decorator

    def register_flow(self, **kwargs):
        """
        註冊流程裝飾器

        Args:
            **kwargs: 流程參數（例如 name）

        Returns:
            裝飾器函數
        """
        def decorator(func):
            if not HAS_PREFECT:
                raise ImportError("需要安裝 Prefect")

            # 使用 Prefect 的 flow 裝飾器
            flow_func = flow(**kwargs)(func)
            self.flows.append(flow_func)
            return flow_func
        return decorator

    def add_task(self, task_func: Callable, **kwargs):
        """
        添加任務

        Args:
            task_func: 任務函數
            **kwargs: 任務參數
        """
        self.tasks.append((task_func, kwargs))
        return self

    def set_description(self, description: str):
        """設置描述"""
        self.description = description
        return self

    def add_tags(self, *tags: str):
        """添加標籤"""
        self.tags.extend(tags)
        return self

    def build(self) -> Callable:
        """
        構建流程

        Returns:
            流程函數
        """
        @flow(
            name=self.name,
            description=self.description,
            tags=self.tags
        )
        def built_flow(**params):
            """構建的流程"""
            logger = get_run_logger()
            logger.info(f"Starting {self.name}")

            results = []
            for task_func, task_kwargs in self.tasks:
                # 合併流程參數和任務參數
                merged_kwargs = {**task_kwargs, **params}
                result = task_func(**merged_kwargs)
                results.append(result)

            return results

        return built_flow


class PrefectScheduler:
    """Prefect 調度器"""

    def __init__(self):
        """初始化調度器"""
        if not HAS_PREFECT:
            raise ImportError("需要安裝 Prefect")

    async def create_deployment(
        self,
        flow_func: Callable,
        name: str,
        schedule: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        創建部署

        Args:
            flow_func: 流程函數
            name: 部署名稱
            schedule: 調度配置
            parameters: 默認參數
            tags: 標籤

        Returns:
            部署信息
        """
        try:
            deployment = Deployment.build_from_flow(
                flow=flow_func,
                name=name,
                schedule=schedule,
                parameters=parameters or {},
                tags=tags or []
            )

            deployment_id = await deployment.apply()

            return {
                'success': True,
                'deployment_id': str(deployment_id),
                'name': name
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def trigger_deployment(
        self,
        deployment_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        觸發部署

        Args:
            deployment_name: 部署名稱
            parameters: 參數

        Returns:
            運行信息
        """
        try:
            async with get_client() as client:
                # 查找部署
                deployments = await client.read_deployments(
                    name=deployment_name
                )

                if not deployments:
                    return {
                        'success': False,
                        'error': f'Deployment {deployment_name} not found'
                    }

                deployment = deployments[0]

                # 創建流程運行
                flow_run = await client.create_flow_run_from_deployment(
                    deployment.id,
                    parameters=parameters or {}
                )

                return {
                    'success': True,
                    'flow_run_id': str(flow_run.id)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


__all__ = [
    'PrefectIntegration',
    'PrefectFlowBuilder',
    'PrefectScheduler',
    'sample_flow',
    'sample_task'
]
