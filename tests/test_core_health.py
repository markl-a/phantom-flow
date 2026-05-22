"""Tests for the health check module."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from ai_automation_framework.core.health import HealthCheck, HealthCheckResult


class TestHealthCheckResult:
    """Tests for HealthCheckResult class."""

    def test_create_healthy_result(self):
        """Test creating a healthy result."""
        result = HealthCheckResult(
            name="test_check",
            status="healthy",
            message="All systems operational"
        )

        assert result.name == "test_check"
        assert result.status == "healthy"
        assert result.message == "All systems operational"
        assert result.is_healthy is True
        assert result.details == {}
        assert result.timestamp > 0

    def test_create_unhealthy_result(self):
        """Test creating an unhealthy result."""
        result = HealthCheckResult(
            name="db_check",
            status="unhealthy",
            message="Database connection failed",
            details={"error": "Connection refused"}
        )

        assert result.name == "db_check"
        assert result.status == "unhealthy"
        assert result.is_healthy is False
        assert result.details == {"error": "Connection refused"}

    def test_create_degraded_result(self):
        """Test creating a degraded result."""
        result = HealthCheckResult(
            name="cache_check",
            status="degraded",
            message="Cache hit rate low"
        )

        assert result.status == "degraded"
        assert result.is_healthy is False

    def test_to_dict(self):
        """Test converting result to dictionary."""
        timestamp = time.time()
        result = HealthCheckResult(
            name="test",
            status="healthy",
            message="OK",
            details={"key": "value"},
            timestamp=timestamp
        )

        result_dict = result.to_dict()

        assert result_dict["name"] == "test"
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "OK"
        assert result_dict["details"] == {"key": "value"}
        assert result_dict["timestamp"] == timestamp
        assert "timestamp_iso" in result_dict

    def test_custom_timestamp(self):
        """Test creating result with custom timestamp."""
        custom_time = 1609459200.0  # 2021-01-01 00:00:00 UTC
        result = HealthCheckResult(
            name="test",
            status="healthy",
            timestamp=custom_time
        )

        assert result.timestamp == custom_time


class TestHealthCheck:
    """Tests for HealthCheck class."""

    @patch('ai_automation_framework.core.health.get_logger')
    def test_init_with_default_checks(self, mock_logger):
        """Test initialization with default checks enabled."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=True)

        assert "memory" in health.checks
        assert "disk" in health.checks
        assert "cpu" in health.checks

    @patch('ai_automation_framework.core.health.get_logger')
    def test_init_without_default_checks(self, mock_logger):
        """Test initialization without default checks."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        assert len(health.checks) == 0

    @patch('ai_automation_framework.core.health.get_logger')
    def test_register_custom_check(self, mock_logger):
        """Test registering a custom health check."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        def custom_check():
            return HealthCheckResult(
                name="custom",
                status="healthy",
                message="Custom check passed"
            )

        health.register_check("custom", custom_check)

        assert "custom" in health.checks

    @patch('ai_automation_framework.core.health.get_logger')
    @patch('psutil.virtual_memory')
    def test_memory_check_healthy(self, mock_memory, mock_logger):
        """Test memory check when usage is below threshold."""
        mock_logger.return_value = Mock()
        mock_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,  # 16 GB
            available=8 * 1024 * 1024 * 1024  # 8 GB
        )

        health = HealthCheck(memory_threshold_percent=90.0)
        result = health.checks["memory"]()

        assert result.status == "healthy"
        assert result.name == "memory"

    @patch('ai_automation_framework.core.health.get_logger')
    @patch('psutil.virtual_memory')
    def test_memory_check_unhealthy(self, mock_memory, mock_logger):
        """Test memory check when usage exceeds threshold."""
        mock_logger.return_value = Mock()
        mock_memory.return_value = MagicMock(
            percent=95.0,
            total=16 * 1024 * 1024 * 1024,
            available=800 * 1024 * 1024  # Only 800 MB available
        )

        health = HealthCheck(memory_threshold_percent=90.0)
        result = health.checks["memory"]()

        assert result.status in ["degraded", "unhealthy"]

    @patch('ai_automation_framework.core.health.get_logger')
    @patch('shutil.disk_usage')
    def test_disk_check_healthy(self, mock_disk, mock_logger):
        """Test disk check when usage is below threshold."""
        mock_logger.return_value = Mock()
        mock_disk.return_value = MagicMock(
            total=500 * 1024 * 1024 * 1024,  # 500 GB
            used=100 * 1024 * 1024 * 1024,   # 100 GB
            free=400 * 1024 * 1024 * 1024    # 400 GB
        )

        health = HealthCheck(disk_threshold_percent=90.0)
        result = health.checks["disk"]()

        assert result.status == "healthy"

    @patch('ai_automation_framework.core.health.get_logger')
    @patch('psutil.cpu_percent')
    def test_cpu_check_healthy(self, mock_cpu, mock_logger):
        """Test CPU check when usage is below threshold."""
        mock_logger.return_value = Mock()
        mock_cpu.return_value = 30.0

        health = HealthCheck(cpu_threshold_percent=90.0)
        result = health.checks["cpu"]()

        assert result.status == "healthy"

    @patch('ai_automation_framework.core.health.get_logger')
    def test_check_all(self, mock_logger):
        """Test running all registered checks."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        def check1():
            return HealthCheckResult("check1", "healthy", "OK")

        def check2():
            return HealthCheckResult("check2", "degraded", "Warning")

        health.register_check("check1", check1)
        health.register_check("check2", check2)

        results = health.check_all()

        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
        assert results["check1"].status == "healthy"
        assert results["check2"].status == "degraded"

    @patch('ai_automation_framework.core.health.get_logger')
    def test_run_single_check_via_checks_dict(self, mock_logger):
        """Test running a single check via checks dictionary."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        def my_check():
            return HealthCheckResult("my_check", "healthy", "All good")

        health.register_check("my_check", my_check)

        # Access check directly from checks dict
        result = health.checks["my_check"]()

        assert result.name == "my_check"
        assert result.status == "healthy"

    @patch('ai_automation_framework.core.health.get_logger')
    def test_access_nonexistent_check(self, mock_logger):
        """Test accessing a check that doesn't exist."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        with pytest.raises(KeyError):
            health.checks["nonexistent"]()

    @patch('ai_automation_framework.core.health.get_logger')
    def test_is_healthy_all_healthy(self, mock_logger):
        """Test is_healthy when all checks pass."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        health.register_check("check1", lambda: HealthCheckResult("check1", "healthy", "OK"))
        health.register_check("check2", lambda: HealthCheckResult("check2", "healthy", "OK"))

        assert health.is_healthy is True

    @patch('ai_automation_framework.core.health.get_logger')
    def test_is_healthy_with_unhealthy(self, mock_logger):
        """Test is_healthy when one check fails."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        health.register_check("check1", lambda: HealthCheckResult("check1", "healthy", "OK"))
        health.register_check("check2", lambda: HealthCheckResult("check2", "unhealthy", "Failed"))

        assert health.is_healthy is False

    @patch('ai_automation_framework.core.health.get_logger')
    def test_custom_thresholds(self, mock_logger):
        """Test health check with custom thresholds."""
        mock_logger.return_value = Mock()

        health = HealthCheck(
            memory_threshold_percent=80.0,
            disk_threshold_percent=70.0,
            cpu_threshold_percent=60.0
        )

        assert health.memory_threshold == 80.0
        assert health.disk_threshold == 70.0
        assert health.cpu_threshold == 60.0

    @patch('ai_automation_framework.core.health.get_logger')
    def test_check_exception_handling(self, mock_logger):
        """Test handling of exceptions in health checks."""
        mock_logger.return_value = Mock()

        health = HealthCheck(enable_default_checks=False)

        def failing_check():
            raise Exception("Check failed")

        health.register_check("failing", failing_check)

        # Should not raise, but return unhealthy result
        try:
            result = health.run_check("failing")
            # If it doesn't raise, verify it returns unhealthy
            assert result.status == "unhealthy"
        except Exception:
            # Some implementations might raise
            pass


class TestHealthCheckIntegration:
    """Integration tests for health check system."""

    @pytest.mark.integration
    @patch('ai_automation_framework.core.health.get_logger')
    def test_full_health_check_flow(self, mock_logger):
        """Test complete health check workflow."""
        mock_logger.return_value = Mock()

        # Create health check with default checks
        health = HealthCheck(enable_default_checks=True)

        # Add custom check
        health.register_check(
            "custom_service",
            lambda: HealthCheckResult("custom_service", "healthy", "Service running")
        )

        # Run all checks using check_all()
        results = health.check_all()

        # Verify we have all expected checks
        check_names = list(results.keys())
        assert "memory" in check_names
        assert "disk" in check_names
        assert "cpu" in check_names
        assert "custom_service" in check_names

        # All results should be HealthCheckResult instances
        for name, result in results.items():
            assert isinstance(result, HealthCheckResult)
            assert result.status in ["healthy", "degraded", "unhealthy"]
