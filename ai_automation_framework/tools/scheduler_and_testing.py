"""Task scheduling and API testing automation tools."""

import threading
import time
import schedule
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
import requests
import json


class TaskScheduler:
    """Cron-like task scheduler for automation."""

    def __init__(self):
        """Initialize task scheduler."""
        self.jobs = []
        self.running = False
        self.thread = None

    def schedule_task(
        self,
        task_func: Callable,
        schedule_type: str,
        interval: int = 1,
        at_time: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Schedule a task to run periodically.

        Args:
            task_func: Function to execute
            schedule_type: Type of schedule ('seconds', 'minutes', 'hours', 'days', 'weekly', 'daily')
            interval: Interval for the schedule
            at_time: Specific time for daily/weekly tasks (HH:MM format)
            **kwargs: Arguments to pass to task_func

        Returns:
            Scheduling result
        """
        try:
            job = None

            if schedule_type == 'seconds':
                job = schedule.every(interval).seconds.do(task_func, **kwargs)
            elif schedule_type == 'minutes':
                job = schedule.every(interval).minutes.do(task_func, **kwargs)
            elif schedule_type == 'hours':
                job = schedule.every(interval).hours.do(task_func, **kwargs)
            elif schedule_type == 'days':
                job = schedule.every(interval).days.do(task_func, **kwargs)
            elif schedule_type == 'daily':
                job = schedule.every().day.at(at_time).do(task_func, **kwargs) if at_time else None
            elif schedule_type == 'weekly':
                job = schedule.every().week.do(task_func, **kwargs)
            else:
                return {"success": False, "error": f"Unknown schedule type: {schedule_type}"}

            if job:
                self.jobs.append(job)
                return {
                    "success": True,
                    "message": f"Task scheduled: {schedule_type} (interval: {interval})",
                    "job_count": len(self.jobs)
                }
            else:
                return {"success": False, "error": "Failed to create job"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def start(self) -> Dict[str, Any]:
        """Start the scheduler in a background thread."""
        if self.running:
            return {"success": False, "error": "Scheduler already running"}

        self.running = True

        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)

        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()

        return {
            "success": True,
            "message": "Scheduler started",
            "jobs": len(self.jobs)
        }

    def stop(self) -> Dict[str, Any]:
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

        return {
            "success": True,
            "message": "Scheduler stopped"
        }

    def clear_all(self) -> Dict[str, Any]:
        """Clear all scheduled jobs."""
        schedule.clear()
        self.jobs = []
        return {
            "success": True,
            "message": "All jobs cleared"
        }

    def list_jobs(self) -> Dict[str, Any]:
        """List all scheduled jobs."""
        job_list = []
        for job in schedule.get_jobs():
            job_list.append({
                "next_run": str(job.next_run),
                "interval": str(job.interval),
                "unit": str(job.unit)
            })

        return {
            "success": True,
            "job_count": len(job_list),
            "jobs": job_list
        }


class APITestingTool:
    """Tool for automated API testing."""

    def __init__(self):
        """Initialize API testing tool."""
        self.test_results = []

    def test_endpoint(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        data: Any = None,
        expected_status: int = 200,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Test an API endpoint.

        Args:
            url: API endpoint URL
            method: HTTP method
            headers: Request headers
            data: Request data
            expected_status: Expected HTTP status code
            timeout: Request timeout

        Returns:
            Test result
        """
        try:
            start_time = time.time()

            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
                timeout=timeout
            )

            elapsed_time = time.time() - start_time

            result = {
                "success": response.status_code == expected_status,
                "url": url,
                "method": method.upper(),
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time": round(elapsed_time, 3),
                "headers": dict(response.headers),
                "timestamp": datetime.now().isoformat()
            }

            # Try to parse JSON response
            try:
                result["response"] = response.json()
            except (ValueError, json.JSONDecodeError):
                result["response"] = response.text[:500]  # Limit text size

            self.test_results.append(result)
            return result

        except Exception as e:
            result = {
                "success": False,
                "url": url,
                "method": method,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(result)
            return result

    def test_multiple_endpoints(
        self,
        endpoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Test multiple API endpoints.

        Args:
            endpoints: List of endpoint configurations

        Returns:
            Aggregated test results
        """
        results = []
        passed = 0
        failed = 0

        for endpoint in endpoints:
            result = self.test_endpoint(**endpoint)
            results.append(result)

            if result.get("success"):
                passed += 1
            else:
                failed += 1

        return {
            "total_tests": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / len(results)) * 100, 2) if results else 0,
            "results": results
        }

    def load_test(
        self,
        url: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrent: bool = False
    ) -> Dict[str, Any]:
        """
        Perform load testing on an endpoint.

        Args:
            url: API endpoint URL
            method: HTTP method
            num_requests: Number of requests to send
            concurrent: Whether to send requests concurrently

        Returns:
            Load test results
        """
        response_times = []
        errors = 0
        start_time = time.time()

        def single_request():
            try:
                req_start = time.time()
                response = requests.request(method, url)
                elapsed = time.time() - req_start
                response_times.append(elapsed)
                return response.status_code
            except (requests.RequestException, Exception):
                nonlocal errors
                errors += 1

        if concurrent:
            threads = []
            for _ in range(num_requests):
                thread = threading.Thread(target=single_request)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
        else:
            for _ in range(num_requests):
                single_request()

        total_time = time.time() - start_time

        return {
            "success": True,
            "url": url,
            "total_requests": num_requests,
            "errors": errors,
            "success_rate": round(((num_requests - errors) / num_requests) * 100, 2),
            "total_time": round(total_time, 3),
            "avg_response_time": round(sum(response_times) / len(response_times), 3) if response_times else 0,
            "min_response_time": round(min(response_times), 3) if response_times else 0,
            "max_response_time": round(max(response_times), 3) if response_times else 0,
            "requests_per_second": round(num_requests / total_time, 2)
        }

    def validate_response_schema(
        self,
        response: Dict[str, Any],
        expected_schema: Dict[str, type]
    ) -> Dict[str, Any]:
        """
        Validate response against expected schema.

        Args:
            response: API response
            expected_schema: Expected schema {field: type}

        Returns:
            Validation result
        """
        errors = []

        for field, expected_type in expected_schema.items():
            if field not in response:
                errors.append(f"Missing field: {field}")
            elif not isinstance(response[field], expected_type):
                errors.append(
                    f"Field '{field}' type mismatch. "
                    f"Expected {expected_type.__name__}, got {type(response[field]).__name__}"
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "checked_fields": len(expected_schema)
        }

    def get_test_report(self) -> Dict[str, Any]:
        """Generate test report from all test results."""
        if not self.test_results:
            return {"message": "No tests run yet"}

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get("success"))
        failed = total - passed

        avg_response_time = sum(
            r.get("response_time", 0) for r in self.test_results
        ) / total if total > 0 else 0

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total) * 100, 2),
            "avg_response_time": round(avg_response_time, 3),
            "results": self.test_results
        }


# Tool schemas
SCHEDULER_TESTING_SCHEMAS = {
    "schedule_task": {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Schedule a task to run periodically",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_type": {
                        "type": "string",
                        "enum": ["seconds", "minutes", "hours", "days", "daily", "weekly"]
                    },
                    "interval": {"type": "integer", "default": 1}
                },
                "required": ["schedule_type"]
            }
        }
    },
    "test_api": {
        "type": "function",
        "function": {
            "name": "test_api",
            "description": "Test an API endpoint",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "expected_status": {"type": "integer", "default": 200}
                },
                "required": ["url"]
            }
        }
    }
}
