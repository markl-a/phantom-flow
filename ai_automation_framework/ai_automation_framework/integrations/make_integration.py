"""
Make (Integromat) 集成
Make (formerly Integromat) Integration

提供與 Make.com 平台的集成，支持場景觸發、數據傳遞等功能。
"""

import os
import requests
import hmac
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class MakeIntegration:
    """Make.com (Integromat) 集成"""

    def __init__(
        self,
        api_token: Optional[str] = None,
        organization_id: Optional[str] = None,
        team_id: Optional[str] = None
    ):
        """
        初始化 Make 集成

        Args:
            api_token: Make API Token
            organization_id: 組織 ID
            team_id: 團隊 ID
        """
        self.api_token = api_token or os.getenv("MAKE_API_TOKEN")
        self.organization_id = organization_id or os.getenv("MAKE_ORGANIZATION_ID")
        self.team_id = team_id or os.getenv("MAKE_TEAM_ID")

        self.base_url = "https://eu1.make.com/api/v2"  # 可根據區域調整

        self.headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """發送 API 請求"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            return {
                'success': True,
                'data': response.json() if response.text else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ========== Webhook 相關 ==========

    def trigger_webhook(
        self,
        webhook_url: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        觸發 Make Webhook

        Args:
            webhook_url: Webhook URL
            data: 要發送的數據
            method: HTTP 方法

        Returns:
            執行結果
        """
        try:
            response = requests.request(
                method=method.upper(),
                url=webhook_url,
                json=data,
                timeout=30
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

    def trigger_custom_webhook(
        self,
        webhook_key: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        觸發自定義 Webhook（使用 webhook key）

        Args:
            webhook_key: Webhook 密鑰
            data: 數據

        Returns:
            結果
        """
        webhook_url = f"https://hook.eu1.make.com/{webhook_key}"
        return self.trigger_webhook(webhook_url, data)

    # ========== 場景管理 ==========

    def get_scenarios(
        self,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        獲取場景列表

        Args:
            folder_id: 文件夾 ID（可選）

        Returns:
            場景列表
        """
        params = {}
        if self.organization_id:
            params['organizationId'] = self.organization_id
        if self.team_id:
            params['teamId'] = self.team_id
        if folder_id:
            params['folderId'] = folder_id

        return self._request('GET', '/scenarios', params=params)

    def get_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """獲取單個場景"""
        return self._request('GET', f'/scenarios/{scenario_id}')

    def update_scenario(
        self,
        scenario_id: str,
        **updates
    ) -> Dict[str, Any]:
        """更新場景"""
        return self._request('PATCH', f'/scenarios/{scenario_id}', data=updates)

    def activate_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """激活場景"""
        return self._request('PATCH', f'/scenarios/{scenario_id}', data={'scheduling': {'type': 'immediately'}})

    def deactivate_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """停用場景"""
        return self._request('PATCH', f'/scenarios/{scenario_id}', data={'scheduling': {'type': 'inactive'}})

    # ========== 執行管理 ==========

    def run_scenario(
        self,
        scenario_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        手動運行場景

        Args:
            scenario_id: 場景 ID
            data: 輸入數據

        Returns:
            執行結果
        """
        payload = {'data': data} if data else {}
        return self._request('POST', f'/scenarios/{scenario_id}/run', data=payload)

    def get_scenario_executions(
        self,
        scenario_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        獲取場景執行記錄

        Args:
            scenario_id: 場景 ID
            limit: 限制數量

        Returns:
            執行記錄
        """
        params = {'limit': limit}
        return self._request('GET', f'/scenarios/{scenario_id}/executions', params=params)

    # ========== 連接管理 ==========

    def get_connections(self) -> Dict[str, Any]:
        """獲取連接列表"""
        params = {}
        if self.organization_id:
            params['organizationId'] = self.organization_id
        if self.team_id:
            params['teamId'] = self.team_id

        return self._request('GET', '/connections', params=params)

    def get_connection(self, connection_id: str) -> Dict[str, Any]:
        """獲取單個連接"""
        return self._request('GET', f'/connections/{connection_id}')

    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """測試連接"""
        return self._request('POST', f'/connections/{connection_id}/test')

    # ========== 數據存儲 ==========

    def get_data_stores(self) -> Dict[str, Any]:
        """獲取數據存儲列表"""
        params = {}
        if self.organization_id:
            params['organizationId'] = self.organization_id
        if self.team_id:
            params['teamId'] = self.team_id

        return self._request('GET', '/datastores', params=params)

    def get_data_store_records(
        self,
        datastore_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """獲取數據存儲記錄"""
        params = {'limit': limit}
        return self._request('GET', f'/datastores/{datastore_id}/records', params=params)

    def add_data_store_record(
        self,
        datastore_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加數據存儲記錄"""
        return self._request('POST', f'/datastores/{datastore_id}/records', data=data)

    # ========== 組織和團隊 ==========

    def get_organizations(self) -> Dict[str, Any]:
        """獲取組織列表"""
        return self._request('GET', '/organizations')

    def get_teams(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """獲取團隊列表"""
        org_id = organization_id or self.organization_id
        params = {'organizationId': org_id} if org_id else {}
        return self._request('GET', '/teams', params=params)

    # ========== 工具方法 ==========

    @staticmethod
    def create_webhook_signature(
        webhook_secret: str,
        timestamp: str,
        body: str
    ) -> str:
        """
        創建 Webhook 簽名（用於驗證）

        Args:
            webhook_secret: Webhook 密鑰
            timestamp: 時間戳
            body: 請求體

        Returns:
            簽名
        """
        message = f"{timestamp}.{body}"
        signature = hmac.new(
            webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"v1={signature}"

    @staticmethod
    def verify_webhook_signature(
        webhook_secret: str,
        signature_header: str,
        timestamp: str,
        body: str,
        tolerance: int = 300
    ) -> bool:
        """
        驗證 Webhook 簽名

        Args:
            webhook_secret: Webhook 密鑰
            signature_header: 簽名頭
            timestamp: 時間戳
            body: 請求體
            tolerance: 時間容差（秒）

        Returns:
            是否有效
        """
        # 檢查時間戳
        try:
            request_time = int(timestamp)
            current_time = int(datetime.now().timestamp())

            if abs(current_time - request_time) > tolerance:
                return False
        except ValueError:
            return False

        # 驗證簽名
        expected_signature = MakeIntegration.create_webhook_signature(
            webhook_secret,
            timestamp,
            body
        )

        return hmac.compare_digest(signature_header, expected_signature)


class MakeWebhookHandler:
    """Make Webhook 處理器"""

    def __init__(self, webhook_secret: Optional[str] = None):
        """
        初始化 Webhook 處理器

        Args:
            webhook_secret: Webhook 密鑰（用於驗證）
        """
        self.webhook_secret = webhook_secret

    def handle_webhook(
        self,
        request_data: Dict[str, Any],
        signature: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        處理 Webhook 請求

        Args:
            request_data: 請求數據
            signature: 簽名（如果啟用驗證）
            timestamp: 時間戳

        Returns:
            處理結果
        """
        # 如果啟用了簽名驗證
        if self.webhook_secret and signature and timestamp:
            body = json.dumps(request_data)

            if not MakeIntegration.verify_webhook_signature(
                self.webhook_secret,
                signature,
                timestamp,
                body
            ):
                return {
                    'success': False,
                    'error': 'Invalid signature'
                }

        # 處理 Webhook 數據
        return {
            'success': True,
            'data': request_data,
            'processed_at': datetime.now().isoformat()
        }


__all__ = ['MakeIntegration', 'MakeWebhookHandler']
