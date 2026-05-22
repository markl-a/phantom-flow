"""
增強版 n8n 工作流集成
Enhanced n8n Workflow Integration

提供完整的 n8n API 集成，包括工作流管理、執行監控、節點模板等。
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """執行狀態"""
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"
    CANCELED = "canceled"


class N8NEnhanced:
    """增強版 n8n 集成"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化 n8n 集成

        Args:
            base_url: n8n 實例 URL (例如: https://n8n.example.com)
            api_key: n8n API 密鑰
            timeout: 請求超時時間（秒）
        """
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.timeout = timeout

        # Use session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        if self.api_key:
            self.session.headers['X-N8N-API-KEY'] = self.api_key

        # Keep headers for backward compatibility
        self.headers = dict(self.session.headers)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        發送 HTTP 請求

        Args:
            method: HTTP 方法
            endpoint: API 端點
            data: 請求數據
            params: 查詢參數

        Returns:
            響應數據
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            return {
                'success': True,
                'status_code': response.status_code,
                'data': response.json() if response.text else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', None)
            }

    # ========== Webhook 相關 ==========

    def trigger_webhook(
        self,
        webhook_id: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        觸發 Webhook

        Args:
            webhook_id: Webhook ID 或路徑
            data: 要發送的數據
            method: HTTP 方法

        Returns:
            執行結果
        """
        webhook_url = f"{self.base_url}/webhook/{webhook_id}"

        try:
            response = self.session.request(
                method=method.upper(),
                url=webhook_url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()

            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.text else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def trigger_test_webhook(
        self,
        webhook_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """觸發測試 Webhook"""
        webhook_url = f"{self.base_url}/webhook-test/{webhook_id}"

        try:
            response = self.session.post(
                webhook_url,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()

            return {
                'success': True,
                'response': response.json() if response.text else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ========== 工作流管理 ==========

    def get_workflows(
        self,
        active: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        獲取工作流列表

        Args:
            active: 過濾活動狀態
            tags: 標籤過濾

        Returns:
            工作流列表
        """
        params = {}
        if active is not None:
            params['active'] = str(active).lower()
        if tags:
            params['tags'] = ','.join(tags)

        return self._request('GET', '/api/v1/workflows', params=params)

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        獲取單個工作流

        Args:
            workflow_id: 工作流 ID

        Returns:
            工作流詳情
        """
        return self._request('GET', f'/api/v1/workflows/{workflow_id}')

    def create_workflow(
        self,
        name: str,
        nodes: List[Dict],
        connections: Dict,
        active: bool = False,
        settings: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        創建工作流

        Args:
            name: 工作流名稱
            nodes: 節點列表
            connections: 節點連接
            active: 是否激活
            settings: 工作流設置
            tags: 標籤

        Returns:
            創建結果
        """
        workflow_data = {
            'name': name,
            'nodes': nodes,
            'connections': connections,
            'active': active,
            'settings': settings or {},
            'tags': tags or []
        }

        return self._request('POST', '/api/v1/workflows', data=workflow_data)

    def update_workflow(
        self,
        workflow_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        更新工作流

        Args:
            workflow_id: 工作流 ID
            **updates: 要更新的字段

        Returns:
            更新結果
        """
        return self._request('PATCH', f'/api/v1/workflows/{workflow_id}', data=updates)

    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        刪除工作流

        Args:
            workflow_id: 工作流 ID

        Returns:
            刪除結果
        """
        return self._request('DELETE', f'/api/v1/workflows/{workflow_id}')

    def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """激活工作流"""
        return self.update_workflow(workflow_id, active=True)

    def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """停用工作流"""
        return self.update_workflow(workflow_id, active=False)

    # ========== 執行管理 ==========

    def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        執行工作流

        Args:
            workflow_id: 工作流 ID
            data: 輸入數據

        Returns:
            執行結果
        """
        payload = {'data': data} if data else {}
        return self._request('POST', f'/api/v1/workflows/{workflow_id}/execute', data=payload)

    def get_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        獲取執行記錄

        Args:
            workflow_id: 工作流 ID（可選）
            status: 狀態過濾
            limit: 限制數量

        Returns:
            執行記錄列表
        """
        params = {'limit': limit}
        if workflow_id:
            params['workflowId'] = workflow_id
        if status:
            params['status'] = status

        return self._request('GET', '/api/v1/executions', params=params)

    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        獲取單個執行記錄

        Args:
            execution_id: 執行 ID

        Returns:
            執行詳情
        """
        return self._request('GET', f'/api/v1/executions/{execution_id}')

    def delete_execution(self, execution_id: str) -> Dict[str, Any]:
        """刪除執行記錄"""
        return self._request('DELETE', f'/api/v1/executions/{execution_id}')

    def retry_execution(self, execution_id: str) -> Dict[str, Any]:
        """重試失敗的執行"""
        return self._request('POST', f'/api/v1/executions/{execution_id}/retry')

    # ========== 憑證管理 ==========

    def get_credentials(self) -> Dict[str, Any]:
        """獲取憑證列表"""
        return self._request('GET', '/api/v1/credentials')

    def get_credential(self, credential_id: str) -> Dict[str, Any]:
        """獲取單個憑證"""
        return self._request('GET', f'/api/v1/credentials/{credential_id}')

    def create_credential(
        self,
        name: str,
        credential_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        創建憑證

        Args:
            name: 憑證名稱
            credential_type: 憑證類型
            data: 憑證數據

        Returns:
            創建結果
        """
        credential_data = {
            'name': name,
            'type': credential_type,
            'data': data
        }

        return self._request('POST', '/api/v1/credentials', data=credential_data)

    # ========== 工作流模板 ==========

    def create_ai_workflow_template(
        self,
        name: str,
        webhook_path: str,
        ai_prompt: str
    ) -> Dict[str, Any]:
        """
        創建 AI 處理工作流模板

        Args:
            name: 工作流名稱
            webhook_path: Webhook 路徑
            ai_prompt: AI 提示詞

        Returns:
            工作流模板
        """
        nodes = [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": webhook_path,
                    "responseMode": "responseNode",
                    "options": {}
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": ""
            },
            {
                "parameters": {
                    "model": "gpt-4",
                    "messages": {
                        "messageValues": [
                            {
                                "role": "system",
                                "message": ai_prompt
                            },
                            {
                                "role": "user",
                                "message": "={{$json.input}}"
                            }
                        ]
                    }
                },
                "name": "OpenAI",
                "type": "n8n-nodes-base.openAi",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{$json}}"
                },
                "name": "Respond to Webhook",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1,
                "position": [650, 300]
            }
        ]

        connections = {
            "Webhook": {
                "main": [[{"node": "OpenAI", "type": "main", "index": 0}]]
            },
            "OpenAI": {
                "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
            }
        }

        return {
            'name': name,
            'nodes': nodes,
            'connections': connections,
            'active': False,
            'settings': {},
            'tags': ['ai', 'automation']
        }

    def create_data_processing_template(
        self,
        name: str,
        webhook_path: str
    ) -> Dict[str, Any]:
        """創建數據處理工作流模板"""
        nodes = [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": webhook_path
                },
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "functionCode": "// 數據處理邏輯\nconst items = $input.all();\nconst processed = items.map(item => ({\n  ...item.json,\n  processed_at: new Date().toISOString()\n}));\nreturn processed.map(data => ({json: data}));"
                },
                "name": "Process Data",
                "type": "n8n-nodes-base.code",
                "typeVersion": 1,
                "position": [450, 300]
            },
            {
                "parameters": {},
                "name": "Respond",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1,
                "position": [650, 300]
            }
        ]

        connections = {
            "Webhook": {
                "main": [[{"node": "Process Data", "type": "main", "index": 0}]]
            },
            "Process Data": {
                "main": [[{"node": "Respond", "type": "main", "index": 0}]]
            }
        }

        return {
            'name': name,
            'nodes': nodes,
            'connections': connections,
            'active': False
        }

    # ========== 高級功能 ==========

    def bulk_execute(
        self,
        workflow_id: str,
        data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量執行工作流

        Args:
            workflow_id: 工作流 ID
            data_list: 數據列表

        Returns:
            執行結果列表
        """
        results = []
        for data in data_list:
            result = self.execute_workflow(workflow_id, data)
            results.append(result)

        return results

    def wait_for_execution(
        self,
        execution_id: str,
        max_wait: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        等待執行完成

        Args:
            execution_id: 執行 ID
            max_wait: 最大等待時間（秒）
            poll_interval: 輪詢間隔（秒）

        Returns:
            執行結果
        """
        import time

        waited = 0
        while waited < max_wait:
            result = self.get_execution(execution_id)

            if not result.get('success'):
                return result

            status = result['data'].get('status', '')

            if status in ['success', 'error', 'canceled']:
                return result

            time.sleep(poll_interval)
            waited += poll_interval

        return {
            'success': False,
            'error': f'Execution timeout after {max_wait} seconds'
        }

    def export_workflow(self, workflow_id: str, file_path: str) -> bool:
        """
        導出工作流到文件

        Args:
            workflow_id: 工作流 ID
            file_path: 文件路徑

        Returns:
            是否成功
        """
        result = self.get_workflow(workflow_id)

        if not result.get('success'):
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result['data'], f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False

    def import_workflow(self, file_path: str) -> Dict[str, Any]:
        """
        從文件導入工作流

        Args:
            file_path: 文件路徑

        Returns:
            導入結果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            # 移除 ID 字段（由服務器生成）
            workflow_data.pop('id', None)
            workflow_data.pop('createdAt', None)
            workflow_data.pop('updatedAt', None)

            return self.create_workflow(
                name=workflow_data['name'],
                nodes=workflow_data['nodes'],
                connections=workflow_data['connections'],
                active=workflow_data.get('active', False),
                settings=workflow_data.get('settings', {}),
                tags=workflow_data.get('tags', [])
            )
        except Exception as e:
            return {
                'success': False,
                'error': f'Import error: {e}'
            }

    def get_workflow_statistics(self, workflow_id: str) -> Dict[str, Any]:
        """
        獲取工作流統計信息

        Args:
            workflow_id: 工作流 ID

        Returns:
            統計信息
        """
        executions = self.get_executions(workflow_id=workflow_id, limit=100)

        if not executions.get('success'):
            return executions

        exec_data = executions['data'].get('data', [])

        total = len(exec_data)
        success_count = sum(1 for e in exec_data if e.get('finished') and not e.get('stoppedAt'))
        error_count = sum(1 for e in exec_data if e.get('stoppedAt'))

        return {
            'success': True,
            'statistics': {
                'total_executions': total,
                'successful_executions': success_count,
                'failed_executions': error_count,
                'success_rate': (success_count / total * 100) if total > 0 else 0
            }
        }


__all__ = ['N8NEnhanced', 'ExecutionStatus']
