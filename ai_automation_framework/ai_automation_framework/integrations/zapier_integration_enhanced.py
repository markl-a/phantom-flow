"""
增強版 Zapier 集成
Enhanced Zapier Integration

提供完整的 Zapier 平台集成，包括 Webhook 觸發、CLI 工具、Zap 管理等。
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime


class ZapierEnhanced:
    """增強版 Zapier 集成"""

    def __init__(
        self,
        default_webhook_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        初始化 Zapier 集成

        Args:
            default_webhook_url: 默認 Webhook URL
            api_key: Zapier API 密鑰（用於 Platform API）
        """
        self.default_webhook_url = default_webhook_url or os.getenv("ZAPIER_WEBHOOK_URL")
        self.api_key = api_key or os.getenv("ZAPIER_API_KEY")

        self.platform_base_url = "https://api.zapier.com/v1"

        # Use session for connection pooling
        self.session = requests.Session()
        if self.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.api_key}'

        # Keep headers for backward compatibility
        self.headers = dict(self.session.headers)

    # ========== Webhook 相關 ==========

    def trigger_webhook(
        self,
        data: Dict[str, Any],
        webhook_url: Optional[str] = None,
        async_mode: bool = False
    ) -> Dict[str, Any]:
        """
        觸發 Zapier Webhook

        Args:
            data: 要發送的數據
            webhook_url: Webhook URL（覆蓋默認值）
            async_mode: 是否異步模式

        Returns:
            執行結果
        """
        url = webhook_url or self.default_webhook_url

        if not url:
            return {
                'success': False,
                'error': 'No webhook URL provided'
            }

        try:
            response = self.session.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30 if not async_mode else 5
            )
            response.raise_for_status()

            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.text,
                'zap_request_id': response.headers.get('X-Zapier-Request-Id'),
                'data_sent': data
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def batch_trigger(
        self,
        data_list: List[Dict[str, Any]],
        webhook_url: Optional[str] = None,
        delay_between: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        批量觸發 Webhook

        Args:
            data_list: 數據列表
            webhook_url: Webhook URL
            delay_between: 請求之間的延遲（秒）

        Returns:
            結果列表
        """
        import time

        results = []
        for data in data_list:
            result = self.trigger_webhook(data, webhook_url)
            results.append(result)

            if delay_between > 0:
                time.sleep(delay_between)

        return results

    # ========== 預定義動作 ==========

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通過 Zapier 發送郵件

        Args:
            to: 收件人
            subject: 主題
            body: 正文
            from_email: 發件人
            cc: 抄送
            bcc: 密送
            attachments: 附件 URL 列表
            webhook_url: Webhook URL

        Returns:
            發送結果
        """
        data = {
            'action': 'send_email',
            'to': to,
            'subject': subject,
            'body': body
        }

        if from_email:
            data['from'] = from_email
        if cc:
            data['cc'] = cc
        if bcc:
            data['bcc'] = bcc
        if attachments:
            data['attachments'] = attachments

        return self.trigger_webhook(data, webhook_url)

    def send_slack_message(
        self,
        channel: str,
        message: str,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        發送 Slack 消息

        Args:
            channel: 頻道名稱
            message: 消息內容
            username: 用戶名
            icon_emoji: 表情圖標
            webhook_url: Webhook URL

        Returns:
            發送結果
        """
        data = {
            'action': 'send_slack_message',
            'channel': channel,
            'message': message
        }

        if username:
            data['username'] = username
        if icon_emoji:
            data['icon_emoji'] = icon_emoji

        return self.trigger_webhook(data, webhook_url)

    def create_google_sheet_row(
        self,
        spreadsheet_id: str,
        row_data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        在 Google Sheets 中創建行

        Args:
            spreadsheet_id: 電子表格 ID
            row_data: 行數據
            webhook_url: Webhook URL

        Returns:
            創建結果
        """
        data = {
            'action': 'create_google_sheet_row',
            'spreadsheet_id': spreadsheet_id,
            'row_data': row_data,
            'timestamp': datetime.now().isoformat()
        }

        return self.trigger_webhook(data, webhook_url)

    def create_task(
        self,
        task_name: str,
        description: str,
        due_date: Optional[str] = None,
        priority: str = "medium",
        assignee: Optional[str] = None,
        project: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        創建任務（Trello/Asana/Todoist等）

        Args:
            task_name: 任務名稱
            description: 描述
            due_date: 截止日期
            priority: 優先級
            assignee: 負責人
            project: 項目
            webhook_url: Webhook URL

        Returns:
            創建結果
        """
        data = {
            'action': 'create_task',
            'task_name': task_name,
            'description': description,
            'priority': priority
        }

        if due_date:
            data['due_date'] = due_date
        if assignee:
            data['assignee'] = assignee
        if project:
            data['project'] = project

        return self.trigger_webhook(data, webhook_url)

    def log_to_database(
        self,
        table: str,
        record: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        記錄到數據庫（Airtable/Google Sheets/等）

        Args:
            table: 表名
            record: 記錄數據
            webhook_url: Webhook URL

        Returns:
            記錄結果
        """
        data = {
            'action': 'log_to_database',
            'table': table,
            'record': record,
            'logged_at': datetime.now().isoformat()
        }

        return self.trigger_webhook(data, webhook_url)

    def send_sms(
        self,
        to: str,
        message: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        發送短信（通過 Twilio 等）

        Args:
            to: 接收號碼
            message: 消息內容
            webhook_url: Webhook URL

        Returns:
            發送結果
        """
        data = {
            'action': 'send_sms',
            'to': to,
            'message': message
        }

        return self.trigger_webhook(data, webhook_url)

    # ========== Zapier Platform API（需要 API 密鑰）==========

    def get_zaps(self) -> Dict[str, Any]:
        """
        獲取 Zaps 列表（需要 API 密鑰）

        Returns:
            Zaps 列表
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API key required for Platform API'
            }

        try:
            response = requests.get(
                f"{self.platform_base_url}/zaps",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            return {
                'success': True,
                'zaps': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_zap_history(
        self,
        zap_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        獲取 Zap 執行歷史

        Args:
            zap_id: Zap ID
            limit: 限制數量

        Returns:
            執行歷史
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API key required for Platform API'
            }

        try:
            params = {'limit': limit}
            response = requests.get(
                f"{self.platform_base_url}/zaps/{zap_id}/history",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            return {
                'success': True,
                'history': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ========== 工具方法 ==========

    def create_webhook_template(
        self,
        trigger_type: str = "catch_hook",
        actions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        創建 Webhook Zap 模板說明

        Args:
            trigger_type: 觸發類型
            actions: 動作列表

        Returns:
            模板說明
        """
        template = {
            'trigger': {
                'type': trigger_type,
                'app': 'Webhooks by Zapier',
                'description': 'Catch webhook requests'
            },
            'actions': actions or [
                {
                    'app': 'Email by Zapier',
                    'action': 'Send Outbound Email',
                    'description': 'Send email when webhook is triggered'
                }
            ],
            'setup_instructions': [
                '1. Create a new Zap in Zapier',
                '2. Choose "Webhooks by Zapier" as trigger',
                '3. Select "Catch Hook" or "Catch Raw Hook"',
                '4. Copy the webhook URL provided by Zapier',
                '5. Add your desired actions',
                '6. Test and activate the Zap'
            ]
        }

        return template

    def validate_webhook_response(
        self,
        response: Dict[str, Any]
    ) -> bool:
        """
        驗證 Webhook 響應

        Args:
            response: 響應數據

        Returns:
            是否成功
        """
        return (
            response.get('success', False) and
            response.get('status_code') in [200, 201, 202]
        )


class ZapierWebhookServer:
    """Zapier Webhook 接收服務器"""

    def __init__(self):
        """初始化 Webhook 服務器"""
        self.handlers = {}

    def register_handler(
        self,
        action_type: str,
        handler: Callable
    ):
        """
        註冊動作處理器

        Args:
            action_type: 動作類型
            handler: 處理函數
        """
        self.handlers[action_type] = handler

    def handle_webhook(
        self,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        處理來自 Zapier 的 Webhook

        Args:
            request_data: 請求數據

        Returns:
            處理結果
        """
        action_type = request_data.get('action', 'default')

        if action_type in self.handlers:
            try:
                result = self.handlers[action_type](request_data)
                return {
                    'success': True,
                    'result': result
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            return {
                'success': False,
                'error': f'No handler for action: {action_type}'
            }


__all__ = ['ZapierEnhanced', 'ZapierWebhookServer']
