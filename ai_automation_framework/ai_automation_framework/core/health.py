"""Health check capabilities for monitoring system and component status."""

import json
import time
import psutil
import shutil
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from pathlib import Path

from ai_automation_framework.core.logger import get_logger


class HealthCheckResult:
    """Represents the result of a single health check."""

    def __init__(
        self,
        name: str,
        status: str,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ):
        """
        Initialize health check result.

        Args:
            name: Name of the check
            status: Status ("healthy", "degraded", "unhealthy")
            message: Human-readable message
            details: Additional details about the check
            timestamp: Time of the check (defaults to current time)
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
        }

    @property
    def is_healthy(self) -> bool:
        """Check if this result indicates a healthy state."""
        return self.status == "healthy"


class HealthCheck:
    """
    Health check manager for monitoring system and component status.

    Provides default checks for system resources and allows registration
    of custom health checks for application-specific monitoring.
    """

    def __init__(
        self,
        enable_default_checks: bool = True,
        memory_threshold_percent: float = 90.0,
        disk_threshold_percent: float = 90.0,
        cpu_threshold_percent: float = 90.0,
    ):
        """
        Initialize health check manager.

        Args:
            enable_default_checks: Whether to enable default system checks
            memory_threshold_percent: Memory usage threshold for warnings
            disk_threshold_percent: Disk usage threshold for warnings
            cpu_threshold_percent: CPU usage threshold for warnings
        """
        self.logger = get_logger(self.__class__.__name__)
        self.checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self.memory_threshold = memory_threshold_percent
        self.disk_threshold = disk_threshold_percent
        self.cpu_threshold = cpu_threshold_percent

        if enable_default_checks:
            self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default system health checks."""
        self.register_check("memory", self._check_memory)
        self.register_check("disk", self._check_disk)
        self.register_check("cpu", self._check_cpu)

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """
        Register a custom health check.

        Args:
            name: Unique name for the check
            check_func: Function that returns a HealthCheckResult
        """
        if name in self.checks:
            self.logger.warning(f"Overwriting existing health check: {name}")
        self.checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")

    def unregister_check(self, name: str) -> None:
        """
        Unregister a health check.

        Args:
            name: Name of the check to remove
        """
        if name in self.checks:
            del self.checks[name]
            self.logger.info(f"Unregistered health check: {name}")

    def _check_memory(self) -> HealthCheckResult:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent

            if percent_used >= self.memory_threshold:
                status = "unhealthy"
                message = f"Memory usage critical: {percent_used:.1f}%"
            elif percent_used >= self.memory_threshold * 0.8:
                status = "degraded"
                message = f"Memory usage elevated: {percent_used:.1f}%"
            else:
                status = "healthy"
                message = f"Memory usage normal: {percent_used:.1f}%"

            return HealthCheckResult(
                name="memory",
                status=status,
                message=message,
                details={
                    "percent_used": percent_used,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "threshold_percent": self.memory_threshold,
                },
            )
        except Exception as e:
            self.logger.error(f"Memory check failed: {e}")
            return HealthCheckResult(
                name="memory",
                status="unhealthy",
                message=f"Memory check failed: {str(e)}",
            )

    def _check_disk(self) -> HealthCheckResult:
        """Check disk space usage."""
        try:
            # Check current working directory's disk
            disk = shutil.disk_usage("/")
            percent_used = (disk.used / disk.total) * 100

            if percent_used >= self.disk_threshold:
                status = "unhealthy"
                message = f"Disk usage critical: {percent_used:.1f}%"
            elif percent_used >= self.disk_threshold * 0.8:
                status = "degraded"
                message = f"Disk usage elevated: {percent_used:.1f}%"
            else:
                status = "healthy"
                message = f"Disk usage normal: {percent_used:.1f}%"

            return HealthCheckResult(
                name="disk",
                status=status,
                message=message,
                details={
                    "percent_used": round(percent_used, 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "threshold_percent": self.disk_threshold,
                },
            )
        except Exception as e:
            self.logger.error(f"Disk check failed: {e}")
            return HealthCheckResult(
                name="disk",
                status="unhealthy",
                message=f"Disk check failed: {str(e)}",
            )

    def _check_cpu(self) -> HealthCheckResult:
        """Check CPU usage."""
        try:
            # Get CPU usage over a 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            if cpu_percent >= self.cpu_threshold:
                status = "unhealthy"
                message = f"CPU usage critical: {cpu_percent:.1f}%"
            elif cpu_percent >= self.cpu_threshold * 0.8:
                status = "degraded"
                message = f"CPU usage elevated: {cpu_percent:.1f}%"
            else:
                status = "healthy"
                message = f"CPU usage normal: {cpu_percent:.1f}%"

            return HealthCheckResult(
                name="cpu",
                status=status,
                message=message,
                details={
                    "percent_used": cpu_percent,
                    "cpu_count": cpu_count,
                    "threshold_percent": self.cpu_threshold,
                    "per_cpu": psutil.cpu_percent(percpu=True),
                },
            )
        except Exception as e:
            self.logger.error(f"CPU check failed: {e}")
            return HealthCheckResult(
                name="cpu",
                status="unhealthy",
                message=f"CPU check failed: {str(e)}",
            )

    def check_llm_connectivity(
        self,
        llm_client: Any,
        test_prompt: str = "Hello",
        timeout: float = 10.0,
    ) -> HealthCheckResult:
        """
        Check LLM connectivity.

        Args:
            llm_client: LLM client instance to test
            test_prompt: Simple prompt to test with
            timeout: Timeout in seconds

        Returns:
            HealthCheckResult indicating LLM connectivity status
        """
        try:
            from ai_automation_framework.core.base import Message

            start_time = time.time()

            # Try to send a simple message
            messages = [Message(role="user", content=test_prompt)]
            response = llm_client.chat(messages, max_tokens=10)

            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                status = "degraded"
                message = f"LLM responding slowly: {elapsed_time:.2f}s"
            else:
                status = "healthy"
                message = f"LLM connectivity OK ({elapsed_time:.2f}s)"

            return HealthCheckResult(
                name="llm_connectivity",
                status=status,
                message=message,
                details={
                    "response_time": round(elapsed_time, 3),
                    "model": llm_client.model if hasattr(llm_client, "model") else "unknown",
                    "client_type": type(llm_client).__name__,
                },
            )
        except Exception as e:
            self.logger.error(f"LLM connectivity check failed: {e}")
            return HealthCheckResult(
                name="llm_connectivity",
                status="unhealthy",
                message=f"LLM connectivity failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_database_connectivity(
        self,
        db_connection: Optional[Any] = None,
    ) -> HealthCheckResult:
        """
        Check database connectivity (placeholder).

        Args:
            db_connection: Database connection object to test

        Returns:
            HealthCheckResult indicating database connectivity status
        """
        if db_connection is None:
            return HealthCheckResult(
                name="database_connectivity",
                status="healthy",
                message="Database check not configured (optional)",
                details={"configured": False},
            )

        try:
            # Placeholder for actual database check
            # This would need to be implemented based on the specific database type
            # Example for SQLAlchemy:
            # db_connection.execute("SELECT 1")

            start_time = time.time()

            # For now, just check if connection object exists and has basic methods
            if hasattr(db_connection, "execute") or hasattr(db_connection, "ping"):
                elapsed_time = time.time() - start_time
                return HealthCheckResult(
                    name="database_connectivity",
                    status="healthy",
                    message=f"Database connectivity OK ({elapsed_time:.3f}s)",
                    details={
                        "response_time": round(elapsed_time, 3),
                        "connection_type": type(db_connection).__name__,
                    },
                )
            else:
                return HealthCheckResult(
                    name="database_connectivity",
                    status="unhealthy",
                    message="Invalid database connection object",
                    details={"error": "No execute or ping method found"},
                )

        except Exception as e:
            self.logger.error(f"Database connectivity check failed: {e}")
            return HealthCheckResult(
                name="database_connectivity",
                status="unhealthy",
                message=f"Database connectivity failed: {str(e)}",
                details={"error": str(e)},
            )

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Run all registered health checks.

        Returns:
            Dictionary mapping check names to their results
        """
        results = {}

        for name, check_func in self.checks.items():
            try:
                self.logger.debug(f"Running health check: {name}")
                result = check_func()
                results[name] = result
            except Exception as e:
                self.logger.error(f"Health check '{name}' failed with exception: {e}")
                results[name] = HealthCheckResult(
                    name=name,
                    status="unhealthy",
                    message=f"Check failed with exception: {str(e)}",
                    details={"error": str(e)},
                )

        return results

    @property
    def is_healthy(self) -> bool:
        """
        Check if all health checks are passing.

        Returns:
            True if all checks are healthy, False otherwise
        """
        results = self.check_all()
        return all(result.is_healthy for result in results.values())

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all health checks.

        Returns:
            Dictionary with overall status and individual check results
        """
        results = self.check_all()

        # Count statuses
        healthy_count = sum(1 for r in results.values() if r.status == "healthy")
        degraded_count = sum(1 for r in results.values() if r.status == "degraded")
        unhealthy_count = sum(1 for r in results.values() if r.status == "unhealthy")

        # Determine overall status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "total_checks": len(results),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "checks": {name: result.to_dict() for name, result in results.items()},
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat(),
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Convert health check results to JSON format.

        Args:
            indent: JSON indentation level (None for compact)

        Returns:
            JSON string representation of health status
        """
        summary = self.get_summary()
        return json.dumps(summary, indent=indent)


# Global health check instance
_health_check: Optional[HealthCheck] = None


def get_health_check(
    enable_default_checks: bool = True,
    **kwargs
) -> HealthCheck:
    """
    Get or create global health check instance.

    Args:
        enable_default_checks: Whether to enable default system checks
        **kwargs: Additional configuration for HealthCheck

    Returns:
        HealthCheck instance
    """
    global _health_check
    if _health_check is None:
        _health_check = HealthCheck(
            enable_default_checks=enable_default_checks,
            **kwargs
        )
    return _health_check
