"""Tests for the integrations module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from ai_automation_framework.integrations.base_adapter import (
    ExecutionStatus,
    WorkflowExecution,
    WorkflowInfo,
    BaseWorkflowAdapter
)


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_all_statuses_exist(self):
        """Test that all expected statuses exist."""
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.CANCELLED.value == "cancelled"
        assert ExecutionStatus.TIMEOUT.value == "timeout"
        assert ExecutionStatus.UNKNOWN.value == "unknown"

    def test_status_comparison(self):
        """Test status comparison."""
        assert ExecutionStatus.SUCCESS != ExecutionStatus.FAILED
        assert ExecutionStatus.PENDING == ExecutionStatus.PENDING


class TestWorkflowExecution:
    """Tests for WorkflowExecution dataclass."""

    def test_create_execution(self):
        """Test creating a workflow execution."""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.RUNNING
        )

        assert execution.execution_id == "exec-123"
        assert execution.workflow_id == "workflow-456"
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.start_time is None
        assert execution.end_time is None

    def test_execution_with_times(self):
        """Test execution with start and end times."""
        start = datetime.now()
        end = start + timedelta(seconds=10)

        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.SUCCESS,
            start_time=start,
            end_time=end
        )

        assert execution.duration == 10.0

    def test_duration_without_times(self):
        """Test duration when times are not set."""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.PENDING
        )

        assert execution.duration is None

    def test_is_complete_for_completed_statuses(self):
        """Test is_complete for completed statuses."""
        for status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED,
                       ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
            execution = WorkflowExecution(
                execution_id="exec-123",
                workflow_id="workflow-456",
                status=status
            )
            assert execution.is_complete is True

    def test_is_complete_for_incomplete_statuses(self):
        """Test is_complete for incomplete statuses."""
        for status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING,
                       ExecutionStatus.UNKNOWN]:
            execution = WorkflowExecution(
                execution_id="exec-123",
                workflow_id="workflow-456",
                status=status
            )
            assert execution.is_complete is False

    def test_is_successful(self):
        """Test is_successful property."""
        success_exec = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.SUCCESS
        )
        assert success_exec.is_successful is True

        failed_exec = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.FAILED
        )
        assert failed_exec.is_successful is False

    def test_execution_with_data(self):
        """Test execution with input/output data."""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.SUCCESS,
            input_data={"key": "input_value"},
            output_data={"result": "output_value"}
        )

        assert execution.input_data == {"key": "input_value"}
        assert execution.output_data == {"result": "output_value"}

    def test_execution_with_error(self):
        """Test execution with error message."""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.FAILED,
            error="Connection timeout"
        )

        assert execution.error == "Connection timeout"

    def test_execution_with_metadata(self):
        """Test execution with metadata."""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_id="workflow-456",
            status=ExecutionStatus.RUNNING,
            metadata={"retry_count": 3, "priority": "high"}
        )

        assert execution.metadata["retry_count"] == 3
        assert execution.metadata["priority"] == "high"


class TestWorkflowInfo:
    """Tests for WorkflowInfo dataclass."""

    def test_create_workflow_info(self):
        """Test creating workflow info."""
        info = WorkflowInfo(
            workflow_id="workflow-123",
            name="Test Workflow"
        )

        assert info.workflow_id == "workflow-123"
        assert info.name == "Test Workflow"
        assert info.description is None
        assert info.is_active is True
        assert info.tags == []

    def test_workflow_info_full(self):
        """Test workflow info with all fields."""
        info = WorkflowInfo(
            workflow_id="workflow-123",
            name="Test Workflow",
            description="A test workflow for processing data",
            is_active=True,
            tags=["production", "data-processing"],
            metadata={"version": "1.0", "author": "test"}
        )

        assert info.description == "A test workflow for processing data"
        assert "production" in info.tags
        assert info.metadata["version"] == "1.0"

    def test_inactive_workflow(self):
        """Test inactive workflow."""
        info = WorkflowInfo(
            workflow_id="workflow-123",
            name="Disabled Workflow",
            is_active=False
        )

        assert info.is_active is False


class ConcreteWorkflowAdapter(BaseWorkflowAdapter):
    """Concrete implementation for testing."""

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def trigger_workflow(self, workflow_id: str, input_data=None) -> WorkflowExecution:
        return WorkflowExecution(
            execution_id="test-exec-123",
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            input_data=input_data
        )

    def get_execution_status(self, execution_id: str) -> WorkflowExecution:
        return WorkflowExecution(
            execution_id=execution_id,
            workflow_id="test-workflow",
            status=ExecutionStatus.SUCCESS
        )

    def list_workflows(self) -> list:
        return [
            WorkflowInfo(workflow_id="wf-1", name="Workflow 1"),
            WorkflowInfo(workflow_id="wf-2", name="Workflow 2")
        ]

    def get_workflow_info(self, workflow_id: str) -> WorkflowInfo:
        return WorkflowInfo(workflow_id=workflow_id, name=f"Workflow {workflow_id}")


class TestBaseWorkflowAdapter:
    """Tests for BaseWorkflowAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080",
            auto_connect=False
        )

        assert adapter.name == "TestAdapter"
        assert adapter.base_url == "http://localhost:8080"
        assert adapter._connected is False

    def test_auto_connect(self):
        """Test auto-connect on initialization."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080",
            auto_connect=True
        )

        assert adapter._connected is True

    def test_connect(self):
        """Test connect method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            auto_connect=False
        )

        result = adapter.connect()

        assert result is True
        assert adapter._connected is True

    def test_disconnect(self):
        """Test disconnect method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080"
        )

        result = adapter.disconnect()

        assert result is True
        assert adapter._connected is False

    def test_trigger_workflow(self):
        """Test trigger_workflow method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080"
        )

        execution = adapter.trigger_workflow(
            "test-workflow",
            input_data={"key": "value"}
        )

        assert isinstance(execution, WorkflowExecution)
        assert execution.workflow_id == "test-workflow"
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.input_data == {"key": "value"}

    def test_get_execution_status(self):
        """Test get_execution_status method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080"
        )

        execution = adapter.get_execution_status("exec-123")

        assert isinstance(execution, WorkflowExecution)
        assert execution.execution_id == "exec-123"
        assert execution.status == ExecutionStatus.SUCCESS

    def test_list_workflows(self):
        """Test list_workflows method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080"
        )

        workflows = adapter.list_workflows()

        assert len(workflows) == 2
        assert all(isinstance(wf, WorkflowInfo) for wf in workflows)

    def test_get_workflow_info(self):
        """Test get_workflow_info method."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            base_url="http://localhost:8080"
        )

        info = adapter.get_workflow_info("wf-123")

        assert isinstance(info, WorkflowInfo)
        assert info.workflow_id == "wf-123"

    def test_config_storage(self):
        """Test that extra config is stored."""
        adapter = ConcreteWorkflowAdapter(
            name="TestAdapter",
            auto_connect=False,
            api_key="secret-key",
            timeout=30
        )

        assert adapter._config["api_key"] == "secret-key"
        assert adapter._config["timeout"] == 30


class TestN8NIntegration:
    """Tests for n8n integration."""

    @pytest.fixture
    def mock_requests(self):
        """Mock requests for n8n tests."""
        with patch('requests.Session') as mock_session:
            session_instance = MagicMock()
            session_instance.request.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": "test"}
            )
            mock_session.return_value = session_instance
            yield session_instance

    @pytest.mark.integration
    def test_n8n_integration_import(self):
        """Test that n8n integration can be imported."""
        try:
            from ai_automation_framework.integrations.n8n_integration import N8NIntegration
            assert N8NIntegration is not None
        except ImportError as e:
            pytest.skip(f"N8N integration not available: {e}")

    @pytest.mark.integration
    def test_n8n_enhanced_integration_import(self):
        """Test that enhanced n8n integration can be imported."""
        try:
            from ai_automation_framework.integrations.n8n_integration_enhanced import N8NEnhancedIntegration
            assert N8NEnhancedIntegration is not None
        except ImportError as e:
            pytest.skip(f"N8N enhanced integration not available: {e}")


class TestZapierIntegration:
    """Tests for Zapier integration."""

    @pytest.mark.integration
    def test_zapier_integration_import(self):
        """Test that Zapier integration can be imported."""
        try:
            from ai_automation_framework.integrations.zapier_integration import ZapierIntegration
            assert ZapierIntegration is not None
        except ImportError as e:
            pytest.skip(f"Zapier integration not available: {e}")


class TestAirflowIntegration:
    """Tests for Airflow integration."""

    @pytest.mark.integration
    def test_airflow_integration_import(self):
        """Test that Airflow integration can be imported."""
        try:
            from ai_automation_framework.integrations.airflow_integration import AirflowIntegration
            assert AirflowIntegration is not None
        except ImportError as e:
            pytest.skip(f"Airflow integration not available: {e}")


class TestCloudServicesIntegration:
    """Tests for cloud services integration."""

    @pytest.mark.integration
    def test_cloud_services_exceptions_import(self):
        """Test that cloud services exceptions can be imported."""
        from ai_automation_framework.integrations.cloud_services import (
            CloudServiceError,
            AzureStorageError,
            AliyunOSSError
        )

        assert CloudServiceError is not None
        assert AzureStorageError is not None
        assert AliyunOSSError is not None

    def test_cloud_service_error_hierarchy(self):
        """Test exception hierarchy."""
        from ai_automation_framework.integrations.cloud_services import (
            CloudServiceError,
            AzureStorageError,
            AliyunOSSError
        )

        assert issubclass(AzureStorageError, CloudServiceError)
        assert issubclass(AliyunOSSError, CloudServiceError)
        assert issubclass(CloudServiceError, Exception)

    def test_raise_azure_storage_error(self):
        """Test raising AzureStorageError."""
        from ai_automation_framework.integrations.cloud_services import AzureStorageError

        with pytest.raises(AzureStorageError) as exc_info:
            raise AzureStorageError("Upload failed")

        assert "Upload failed" in str(exc_info.value)

    def test_raise_aliyun_oss_error(self):
        """Test raising AliyunOSSError."""
        from ai_automation_framework.integrations.cloud_services import AliyunOSSError

        with pytest.raises(AliyunOSSError) as exc_info:
            raise AliyunOSSError("Download failed")

        assert "Download failed" in str(exc_info.value)
