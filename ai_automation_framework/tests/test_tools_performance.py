"""Tests for the performance monitoring tools."""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class."""

    def test_initialization(self):
        """Test metrics initialization."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics(window_size=100)

        assert metrics.window_size == 100
        assert len(metrics.metrics['response_times']) == 0
        assert len(metrics.metrics['request_counts']) == 0
        assert metrics.start_time is not None

    def test_record_response_time(self):
        """Test recording response time."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_response_time(0.5, endpoint="/api/test")

        assert len(metrics.metrics['response_times']) == 1
        record = metrics.metrics['response_times'][0]
        assert record['duration'] == 0.5
        assert record['endpoint'] == "/api/test"
        assert 'timestamp' in record

    def test_record_request(self):
        """Test recording request."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_request(endpoint="/api/users")

        assert len(metrics.metrics['request_counts']) == 1
        record = metrics.metrics['request_counts'][0]
        assert record['endpoint'] == "/api/users"

    def test_record_error(self):
        """Test recording error."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics()
        metrics.record_error(error_type="ValueError", endpoint="/api/process")

        assert len(metrics.metrics['error_counts']) == 1
        record = metrics.metrics['error_counts'][0]
        assert record['error_type'] == "ValueError"
        assert record['endpoint'] == "/api/process"

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_record_system_metrics(self, mock_memory, mock_cpu):
        """Test recording system metrics."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=60.0)

        metrics = PerformanceMetrics()
        metrics.record_system_metrics()

        assert len(metrics.metrics['cpu_usage']) == 1
        assert len(metrics.metrics['memory_usage']) == 1
        assert metrics.metrics['cpu_usage'][0]['value'] == 45.5
        assert metrics.metrics['memory_usage'][0]['value'] == 60.0

    def test_get_summary_empty(self):
        """Test getting summary with no data."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics()
        summary = metrics.get_summary()

        assert 'uptime_seconds' in summary
        assert summary['total_requests'] == 0
        assert summary['total_errors'] == 0
        assert summary['error_rate'] == 0

    def test_get_summary_with_data(self):
        """Test getting summary with data."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics()

        # Add some data
        for i in range(10):
            metrics.record_request("/api/test")
            metrics.record_response_time(0.1 * (i + 1), "/api/test")

        metrics.record_error("TestError", "/api/test")

        summary = metrics.get_summary()

        assert summary['total_requests'] == 10
        assert summary['total_errors'] == 1
        assert summary['error_rate'] == 0.1
        assert 'avg_response_time' in summary
        assert 'p95_response_time' in summary

    def test_window_size_limit(self):
        """Test that window size limits data."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        metrics = PerformanceMetrics(window_size=5)

        # Add more than window size
        for i in range(10):
            metrics.record_request("/api/test")

        # Should only keep last 5
        assert len(metrics.metrics['request_counts']) == 5

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMetrics

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        p50 = PerformanceMetrics._percentile(data, 0.5)
        p90 = PerformanceMetrics._percentile(data, 0.9)

        # For 10 items:
        # p50: index = int(10 * 0.5) = 5, so data[5] = 6
        # p90: index = int(10 * 0.9) = 9, so data[9] = 10
        assert p50 == 6
        assert p90 == 10


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_initialization_without_prometheus(self):
        """Test initialization without Prometheus."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)

            assert monitor.metrics is not None
            assert monitor.enable_prometheus is False

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_get_metrics(self):
        """Test getting metrics."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)
            metrics = monitor.get_metrics()

            assert isinstance(metrics, dict)
            assert 'uptime_seconds' in metrics

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_export_metrics_json(self):
        """Test exporting metrics as JSON."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor
        import json

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)
            exported = monitor.export_metrics(format="json")

            # Should be valid JSON
            data = json.loads(exported)
            assert 'uptime_seconds' in data

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_export_metrics_invalid_format(self):
        """Test exporting metrics with invalid format."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)

            with pytest.raises(ValueError) as exc_info:
                monitor.export_metrics(format="xml")

            assert "Unsupported format" in str(exc_info.value)

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_track_request_decorator(self):
        """Test track_request decorator."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)

            @monitor.track_request(endpoint="/test", method="GET")
            def test_function():
                return "result"

            result = test_function()

            assert result == "result"
            assert monitor.metrics.get_summary()['total_requests'] == 1

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_track_request_decorator_with_error(self):
        """Test track_request decorator when function raises error."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceMonitor

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = PerformanceMonitor(enable_prometheus=False)

            @monitor.track_request(endpoint="/test", method="GET")
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                failing_function()

            summary = monitor.metrics.get_summary()
            assert summary['total_errors'] == 1


class TestResourceOptimizer:
    """Tests for ResourceOptimizer class."""

    def test_initialization_memory_backend(self):
        """Test initialization with memory backend."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        optimizer = ResourceOptimizer(cache_backend="memory")

        assert optimizer.cache_backend == "memory"
        assert optimizer.cache == {}
        assert optimizer.redis_client is None

    def test_memoize_decorator(self):
        """Test memoize decorator caches results."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        optimizer = ResourceOptimizer(cache_backend="memory")
        call_count = 0

        @optimizer.memoize(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

        # Different argument
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_memoize_cache_expiry(self):
        """Test memoize decorator with cache expiry."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        optimizer = ResourceOptimizer(cache_backend="memory")

        @optimizer.memoize(ttl=1)  # 1 second TTL
        def short_lived_cache(x):
            return x * 2

        result1 = short_lived_cache(5)
        assert result1 == 10

        # Wait for cache to expire
        time.sleep(1.1)

        # Should recompute
        result2 = short_lived_cache(5)
        assert result2 == 10

    def test_clear_cache(self):
        """Test clearing cache."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        optimizer = ResourceOptimizer(cache_backend="memory")

        @optimizer.memoize(ttl=60)
        def cached_function(x):
            return x * 2

        cached_function(5)
        assert len(optimizer.cache) == 1

        optimizer.clear_cache()
        assert len(optimizer.cache) == 0

    def test_batch_process_without_function(self):
        """Test batch processing without function."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        items = list(range(250))
        results = ResourceOptimizer.batch_process(items, batch_size=100)

        assert len(results) == 250
        assert results == items

    def test_batch_process_with_function(self):
        """Test batch processing with function."""
        from ai_automation_framework.tools.performance_monitoring import ResourceOptimizer

        items = list(range(10))

        def process_batch(batch):
            return [x * 2 for x in batch]

        results = ResourceOptimizer.batch_process(
            items,
            batch_size=3,
            process_func=process_batch
        )

        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]


class TestPerformanceProfiler:
    """Tests for PerformanceProfiler class."""

    def test_initialization(self):
        """Test profiler initialization."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()

        assert profiler.profiles == {}

    def test_profile_decorator(self):
        """Test profile decorator."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()

        @profiler.profile(name="test_func")
        def test_function():
            total = sum(range(1000))
            return total

        result = test_function()

        assert result == 499500
        assert "test_func" in profiler.profiles

    def test_profile_decorator_default_name(self):
        """Test profile decorator with default name."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()

        @profiler.profile()
        def my_function():
            return 42

        result = my_function()

        assert result == 42
        assert "my_function" in profiler.profiles

    def test_get_profile(self):
        """Test getting profile results."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()

        @profiler.profile(name="test")
        def test_function():
            return "result"

        test_function()

        profile = profiler.get_profile("test")
        assert profile != "No profile found"

    def test_get_profile_not_found(self):
        """Test getting non-existent profile."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()
        profile = profiler.get_profile("nonexistent")

        assert profile == "No profile found"

    def test_get_all_profiles(self):
        """Test getting all profiles."""
        from ai_automation_framework.tools.performance_monitoring import PerformanceProfiler

        profiler = PerformanceProfiler()

        @profiler.profile(name="func1")
        def func1():
            return 1

        @profiler.profile(name="func2")
        def func2():
            return 2

        func1()
        func2()

        all_profiles = profiler.get_all_profiles()

        assert "func1" in all_profiles
        assert "func2" in all_profiles


class TestHealthChecker:
    """Tests for HealthChecker class."""

    def test_initialization(self):
        """Test health checker initialization."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        checker = HealthChecker()

        assert checker.checks == {}

    def test_register_check(self):
        """Test registering a health check."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        checker = HealthChecker()
        checker.register_check("test", lambda: True)

        assert "test" in checker.checks

    def test_run_checks_all_pass(self):
        """Test running checks when all pass."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        checker = HealthChecker()
        checker.register_check("check1", lambda: True)
        checker.register_check("check2", lambda: True)

        results = checker.run_checks()

        assert results['status'] == 'healthy'
        assert results['checks']['check1']['healthy'] is True
        assert results['checks']['check2']['healthy'] is True

    def test_run_checks_one_fails(self):
        """Test running checks when one fails."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        checker = HealthChecker()
        checker.register_check("healthy_check", lambda: True)
        checker.register_check("failing_check", lambda: False)

        results = checker.run_checks()

        assert results['status'] == 'unhealthy'
        assert results['checks']['healthy_check']['healthy'] is True
        assert results['checks']['failing_check']['healthy'] is False

    def test_run_checks_exception_handling(self):
        """Test that exceptions in checks are handled."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        checker = HealthChecker()

        def failing_check():
            raise Exception("Check error")

        checker.register_check("error_check", failing_check)

        results = checker.run_checks()

        assert results['status'] == 'unhealthy'
        assert results['checks']['error_check']['status'] == 'error'
        assert 'error' in results['checks']['error_check']

    @patch('psutil.disk_usage')
    def test_check_disk_space_healthy(self, mock_disk):
        """Test disk space check when healthy."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        mock_disk.return_value = MagicMock(percent=50.0)

        result = HealthChecker.check_disk_space(threshold=90.0)

        assert result is True

    @patch('psutil.disk_usage')
    def test_check_disk_space_unhealthy(self, mock_disk):
        """Test disk space check when unhealthy."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        mock_disk.return_value = MagicMock(percent=95.0)

        result = HealthChecker.check_disk_space(threshold=90.0)

        assert result is False

    @patch('psutil.virtual_memory')
    def test_check_memory_healthy(self, mock_memory):
        """Test memory check when healthy."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        mock_memory.return_value = MagicMock(percent=60.0)

        result = HealthChecker.check_memory(threshold=90.0)

        assert result is True

    @patch('psutil.virtual_memory')
    def test_check_memory_unhealthy(self, mock_memory):
        """Test memory check when unhealthy."""
        from ai_automation_framework.tools.performance_monitoring import HealthChecker

        mock_memory.return_value = MagicMock(percent=95.0)

        result = HealthChecker.check_memory(threshold=90.0)

        assert result is False


class TestFactoryFunctions:
    """Tests for factory functions."""

    @patch('ai_automation_framework.tools.performance_monitoring.HAS_PROMETHEUS', False)
    def test_create_performance_monitor(self):
        """Test create_performance_monitor factory."""
        from ai_automation_framework.tools.performance_monitoring import (
            create_performance_monitor,
            PerformanceMonitor
        )

        with patch.object(PerformanceMonitor, '_start_system_metrics_collector'):
            monitor = create_performance_monitor(enable_prometheus=False)

            assert isinstance(monitor, PerformanceMonitor)

    def test_create_resource_optimizer(self):
        """Test create_resource_optimizer factory."""
        from ai_automation_framework.tools.performance_monitoring import (
            create_resource_optimizer,
            ResourceOptimizer
        )

        optimizer = create_resource_optimizer(use_redis=False)

        assert isinstance(optimizer, ResourceOptimizer)
        assert optimizer.cache_backend == "memory"

    def test_create_health_checker(self):
        """Test create_health_checker factory."""
        from ai_automation_framework.tools.performance_monitoring import (
            create_health_checker,
            HealthChecker
        )

        checker = create_health_checker()

        assert isinstance(checker, HealthChecker)
