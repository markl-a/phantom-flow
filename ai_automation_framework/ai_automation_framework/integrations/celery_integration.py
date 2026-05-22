"""
Celery 分布式任務隊列集成
Celery Distributed Task Queue Integration

提供與 Celery 分布式任務隊列的集成。
"""

import os
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta

try:
    from celery import Celery, Task, group, chain, chord
    from celery.result import AsyncResult, GroupResult
    from celery.schedules import crontab, schedule
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    Celery = None
    crontab = None
    schedule = None


class CeleryIntegration:
    """Celery 集成"""

    def __init__(
        self,
        broker_url: Optional[str] = None,
        backend_url: Optional[str] = None,
        app_name: str = "ai_automation"
    ):
        """
        初始化 Celery 集成

        Args:
            broker_url: 消息代理 URL (如 redis://localhost:6379/0)
            backend_url: 結果後端 URL
            app_name: 應用名稱
        """
        if not HAS_CELERY:
            raise ImportError(
                "需要安裝 Celery: pip install celery[redis]"
            )

        self.broker_url = broker_url or os.getenv(
            "CELERY_BROKER_URL",
            "redis://localhost:6379/0"
        )
        self.backend_url = backend_url or os.getenv(
            "CELERY_RESULT_BACKEND",
            "redis://localhost:6379/0"
        )

        self.app = Celery(
            app_name,
            broker=self.broker_url,
            backend=self.backend_url
        )

        # 配置 Celery
        self.app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Asia/Taipei',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,  # 1 小時
            task_soft_time_limit=3000,  # 50 分鐘
        )

    def create_task(
        self,
        name: Optional[str] = None,
        bind: bool = False,
        **options
    ):
        """
        創建任務裝飾器

        Args:
            name: 任務名稱
            bind: 是否綁定實例
            **options: 其他選項

        Returns:
            任務裝飾器
        """
        return self.app.task(name=name, bind=bind, **options)

    def send_task(
        self,
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        countdown: Optional[int] = None,
        eta: Optional[datetime] = None,
        expires: Optional[int] = None,
        **options
    ) -> Dict[str, Any]:
        """
        發送任務到隊列

        Args:
            task_name: 任務名稱
            args: 位置參數
            kwargs: 關鍵字參數
            countdown: 延遲執行（秒）
            eta: 預定執行時間
            expires: 過期時間（秒）
            **options: 其他選項

        Returns:
            任務信息
        """
        try:
            result = self.app.send_task(
                task_name,
                args=args or [],
                kwargs=kwargs or {},
                countdown=countdown,
                eta=eta,
                expires=expires,
                **options
            )

            return {
                'success': True,
                'task_id': result.id,
                'task_name': task_name,
                'state': result.state
            }
        except ConnectionError as e:
            return {
                'success': False,
                'error': f'Failed to connect to broker: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_task_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        獲取任務結果

        Args:
            task_id: 任務 ID
            timeout: 超時時間（秒）

        Returns:
            任務結果
        """
        try:
            result = AsyncResult(task_id, app=self.app)

            if timeout:
                task_result = result.get(timeout=timeout)
            else:
                task_result = result.result if result.ready() else None

            return {
                'success': True,
                'task_id': task_id,
                'state': result.state,
                'result': task_result,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None
            }
        except TimeoutError as e:
            return {
                'success': False,
                'error': f'Task timed out after {timeout} seconds: {str(e)}',
                'task_id': task_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def revoke_task(
        self,
        task_id: str,
        terminate: bool = False,
        signal: str = 'SIGTERM'
    ) -> Dict[str, Any]:
        """
        撤銷任務

        Args:
            task_id: 任務 ID
            terminate: 是否終止正在運行的任務
            signal: 終止信號

        Returns:
            執行結果
        """
        try:
            self.app.control.revoke(
                task_id,
                terminate=terminate,
                signal=signal
            )

            return {
                'success': True,
                'message': f'Task {task_id} revoked'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_tasks(self) -> Dict[str, Any]:
        """
        獲取活動任務列表

        Returns:
            活動任務信息
        """
        try:
            inspect = self.app.control.inspect()
            active = inspect.active()

            return {
                'success': True,
                'active_tasks': active or {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """
        獲取計劃任務列表

        Returns:
            計劃任務信息
        """
        try:
            inspect = self.app.control.inspect()
            scheduled = inspect.scheduled()

            return {
                'success': True,
                'scheduled_tasks': scheduled or {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_task_chain(self, *tasks) -> Dict[str, Any]:
        """
        創建任務鏈（順序執行）

        Args:
            *tasks: 任務簽名列表

        Returns:
            執行結果
        """
        try:
            task_chain = chain(*tasks)
            result = task_chain.apply_async()

            return {
                'success': True,
                'chain_id': result.id,
                'state': result.state
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_task_group(self, *tasks) -> Dict[str, Any]:
        """
        創建任務組（並行執行）

        Args:
            *tasks: 任務簽名列表

        Returns:
            執行結果
        """
        try:
            task_group = group(*tasks)
            result = task_group.apply_async()

            return {
                'success': True,
                'group_id': result.id,
                'task_count': len(tasks)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def add_periodic_task(
        self,
        schedule: Union[timedelta, 'crontab', float],
        task_name: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加週期性任務

        Args:
            schedule: 調度（crontab、timedelta 或秒數）
            task_name: 任務名稱
            args: 參數
            kwargs: 關鍵字參數
            name: 任務別名

        Returns:
            添加結果
        """
        try:
            self.app.conf.beat_schedule[name or task_name] = {
                'task': task_name,
                'schedule': schedule,
                'args': args or [],
                'kwargs': kwargs or {}
            }

            return {
                'success': True,
                'message': f'Periodic task {name or task_name} added'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class CeleryTaskBuilder:
    """Celery 任務構建器"""

    def __init__(self, celery_app: Celery):
        """
        初始化構建器

        Args:
            celery_app: Celery 應用實例
        """
        if not HAS_CELERY:
            raise ImportError("需要安裝 Celery")

        self.app = celery_app
        self.tasks = {}

    def register_task(
        self,
        func: Callable,
        name: Optional[str] = None,
        **options
    ):
        """
        註冊任務

        Args:
            func: 任務函數
            name: 任務名稱
            **options: 任務選項

        Returns:
            任務對象
        """
        task_name = name or func.__name__
        task = self.app.task(name=task_name, **options)(func)
        self.tasks[task_name] = task
        return task

    def get_task(self, name: str):
        """獲取已註冊的任務"""
        return self.tasks.get(name)

    def create_workflow(
        self,
        workflow_type: str,
        tasks: List[Any]
    ) -> Any:
        """
        創建工作流

        Args:
            workflow_type: 工作流類型 (chain, group, chord)
            tasks: 任務列表

        Returns:
            工作流對象
        """
        if workflow_type == 'chain':
            return chain(*tasks)
        elif workflow_type == 'group':
            return group(*tasks)
        elif workflow_type == 'chord':
            if len(tasks) < 2:
                raise ValueError("Chord requires at least 2 tasks")
            return chord(tasks[:-1])(tasks[-1])
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")


# 示例任務定義
def create_sample_tasks(celery_app: Celery):
    """創建示例任務"""

    @celery_app.task(name='sample.add')
    def add(x: int, y: int) -> int:
        """加法任務"""
        return x + y

    @celery_app.task(name='sample.multiply')
    def multiply(x: int, y: int) -> int:
        """乘法任務"""
        return x * y

    @celery_app.task(name='sample.process_data')
    def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """數據處理任務"""
        return {
            'processed': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

    return {
        'add': add,
        'multiply': multiply,
        'process_data': process_data
    }


class CeleryMonitor:
    """Celery 監控器"""

    def __init__(self, celery_app: Celery):
        """
        初始化監控器

        Args:
            celery_app: Celery 應用實例
        """
        self.app = celery_app

    def get_stats(self) -> Dict[str, Any]:
        """
        獲取統計信息

        Returns:
            統計數據
        """
        try:
            inspect = self.app.control.inspect()

            return {
                'success': True,
                'stats': {
                    'active': inspect.active(),
                    'scheduled': inspect.scheduled(),
                    'reserved': inspect.reserved(),
                    'registered': inspect.registered()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_worker_stats(self) -> Dict[str, Any]:
        """
        獲取 Worker 統計

        Returns:
            Worker 統計信息
        """
        try:
            inspect = self.app.control.inspect()
            stats = inspect.stats()

            return {
                'success': True,
                'workers': stats or {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def ping_workers(self) -> Dict[str, Any]:
        """
        Ping Workers

        Returns:
            響應信息
        """
        try:
            inspect = self.app.control.inspect()
            pong = inspect.ping()

            return {
                'success': True,
                'workers': pong or {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


__all__ = [
    'CeleryIntegration',
    'CeleryTaskBuilder',
    'CeleryMonitor',
    'create_sample_tasks'
]
