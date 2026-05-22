"""Tests for scheduler and API testing tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from ai_automation_framework.tools.scheduler_and_testing import TaskScheduler, APITestingTool


class TestTaskScheduler:
    """Test Task scheduler tool."""

    def test_initialization(self):
        """Test scheduler initialization."""
        scheduler = TaskScheduler()
        assert scheduler.jobs == []
        assert scheduler.running is False

    def test_schedule_task(self):
        """Test scheduling a task."""
        scheduler = TaskScheduler()
        task_executed = []

        def sample_task():
            task_executed.append(True)

        result = scheduler.schedule_task(
            task_func=sample_task,
            schedule_type="seconds",
            interval=1
        )

        assert result["success"] is True
        assert len(scheduler.jobs) == 1

    def test_schedule_different_types(self):
        """Test scheduling with different schedule types."""
        scheduler = TaskScheduler()

        def dummy_task():
            pass

        # Test different schedule types
        for schedule_type in ["seconds", "minutes", "hours", "days"]:
            result = scheduler.schedule_task(
                task_func=dummy_task,
                schedule_type=schedule_type,
                interval=1
            )
            assert result["success"] is True

    def test_invalid_schedule_type(self):
        """Test invalid schedule type."""
        scheduler = TaskScheduler()

        result = scheduler.schedule_task(
            task_func=lambda: None,
            schedule_type="invalid_type",
            interval=1
        )

        assert result["success"] is False
        assert "error" in result
        assert "Unknown schedule type" in result["error"]

    def test_start_stop_scheduler(self):
        """Test starting and stopping scheduler."""
        scheduler = TaskScheduler()

        start_result = scheduler.start()
        assert start_result["success"] is True
        assert scheduler.running is True

        # Can't start again when already running
        start_again = scheduler.start()
        assert start_again["success"] is False

        stop_result = scheduler.stop()
        assert stop_result["success"] is True
        assert scheduler.running is False


class TestAPITestingTool:
    """Test API testing tool."""

    def test_initialization(self):
        """Test tool initialization."""
        tool = APITestingTool(base_url="https://api.example.com")
        assert tool.base_url == "https://api.example.com"

    def test_get_request_mock(self, mock_http_response):
        """Test GET request with mock."""
        tool = APITestingTool(base_url="https://api.example.com")
        result = tool.get("/users")

        assert result["success"] is True
        assert result["status_code"] == 200

    def test_post_request_mock(self, mock_http_response):
        """Test POST request with mock."""
        tool = APITestingTool(base_url="https://api.example.com")
        result = tool.post("/users", data={"name": "Test"})

        assert result["success"] is True
        assert result["status_code"] == 200

    def test_test_endpoint_mock(self, mock_http_response):
        """Test endpoint testing with mock."""
        tool = APITestingTool(base_url="https://api.example.com")
        result = tool.test_endpoint(
            endpoint="/users",
            method="GET",
            expected_status=200
        )

        assert result["success"] is True
        assert result["passed"] is True

    def test_load_test_mock(self, mock_http_response):
        """Test load testing with mock."""
        tool = APITestingTool(base_url="https://api.example.com")

        # Run a small load test
        result = tool.load_test(
            endpoint="/users",
            method="GET",
            num_requests=5,
            concurrent=2
        )

        assert result["success"] is True
        assert "total_requests" in result
        assert "success_rate" in result
