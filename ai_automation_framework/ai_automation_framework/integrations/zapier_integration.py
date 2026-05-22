"""Zapier webhook integration."""

import requests
from typing import Dict, Any, Optional
import json


class ZapierIntegration:
    """
    Zapier webhook integration for connecting to Zapier workflows.

    This allows you to trigger Zapier zaps from your automation framework.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Zapier integration.

        Args:
            webhook_url: Zapier webhook URL
        """
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def trigger_zap(
        self,
        data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a Zapier zap via webhook.

        Args:
            data: Data to send to Zapier
            webhook_url: Webhook URL (overrides default)

        Returns:
            Result dictionary

        Example:
            >>> zap = ZapierIntegration("https://hooks.zapier.com/hooks/catch/...")
            >>> result = zap.trigger_zap({"name": "John", "email": "john@example.com"})
        """
        url = webhook_url or self.webhook_url

        if not url:
            return {"success": False, "error": "No webhook URL provided"}

        try:
            response = self.session.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.text,
                "data_sent": data
            }
        except requests.Timeout as e:
            return {"success": False, "error": f"Request timeout: {str(e)}", "error_type": "timeout"}
        except requests.ConnectionError as e:
            return {"success": False, "error": f"Connection error: {str(e)}", "error_type": "connection_error"}
        except requests.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {str(e)}", "error_type": "http_error"}
        except requests.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}", "error_type": "request_error"}

    def send_email_via_zap(
        self,
        to: str,
        subject: str,
        body: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email through Zapier."""
        data = {
            "to": to,
            "subject": subject,
            "body": body,
            "action": "send_email"
        }
        return self.trigger_zap(data, webhook_url)

    def create_task_via_zap(
        self,
        task_name: str,
        description: str,
        priority: str = "medium",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create task in connected task manager through Zapier."""
        data = {
            "task_name": task_name,
            "description": description,
            "priority": priority,
            "action": "create_task"
        }
        return self.trigger_zap(data, webhook_url)

    def log_event_via_zap(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log event through Zapier."""
        data = {
            "event_type": event_type,
            "event_data": event_data,
            "action": "log_event"
        }
        return self.trigger_zap(data, webhook_url)

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if hasattr(self, 'session') and self.session:
            self.session.close()
            self.session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


# Example Zapier workflows you can create:
"""
Example Zapier Zap Configurations:

1. Email Notification Zap:
   - Trigger: Webhook (Catch Hook)
   - Action: Gmail (Send Email)
   - Map webhook data to email fields

2. Slack Notification Zap:
   - Trigger: Webhook (Catch Hook)
   - Action: Slack (Send Channel Message)
   - Map webhook data to Slack message

3. Google Sheets Logger Zap:
   - Trigger: Webhook (Catch Hook)
   - Action: Google Sheets (Create Spreadsheet Row)
   - Map webhook data to sheet columns

4. Task Creation Zap:
   - Trigger: Webhook (Catch Hook)
   - Action: Trello/Asana/Todoist (Create Task)
   - Map webhook data to task fields
"""
