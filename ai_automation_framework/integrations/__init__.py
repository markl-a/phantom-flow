"""External automation framework integrations."""

from .base_adapter import (
    BaseWorkflowAdapter,
    BaseWebhookAdapter,
    BaseAPIAdapter,
    AdapterRegistry,
    WorkflowExecution,
    WorkflowInfo,
    ExecutionStatus,
)
from .zapier_integration import ZapierIntegration
from .n8n_integration import N8NIntegration
from .airflow_integration import AirflowIntegration

__all__ = [
    # Base classes
    'BaseWorkflowAdapter',
    'BaseWebhookAdapter',
    'BaseAPIAdapter',
    'AdapterRegistry',
    # Data classes
    'WorkflowExecution',
    'WorkflowInfo',
    'ExecutionStatus',
    # Implementations
    'ZapierIntegration',
    'N8NIntegration',
    'AirflowIntegration',
]
