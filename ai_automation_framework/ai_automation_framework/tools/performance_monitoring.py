"""
性能監控和優化工具
Performance Monitoring and Optimization Tools

提供應用性能監控、性能分析、資源追蹤等功能。
"""

import time
import psutil
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
import json
import statistics

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指標收集器"""

    def __init__(self, window_size: int = 1000):
        """
        初始化性能指標收集器

        Args:
            window_size: 滑動窗口大小（保留最近的 N 個數據點）
        """
        self.window_size = window_size
        self.metrics = {
            'response_times': deque(maxlen=window_size),
            'request_counts': deque(maxlen=window_size),
            'error_counts': deque(maxlen=window_size),
            'cpu_usage': deque(maxlen=window_size),
            'memory_usage': deque(maxlen=window_size),
        }
        self.start_time = datetime.now()
        self._lock = threading.Lock()

    def record_response_time(self, duration: float, endpoint: str = "default"):
        """記錄響應時間"""
        with self._lock:
            self.metrics['response_times'].append({
                'timestamp': datetime.now(),
                'duration': duration,
                'endpoint': endpoint
            })

    def record_request(self, endpoint: str = "default"):
        """記錄請求"""
        with self._lock:
            self.metrics['request_counts'].append({
                'timestamp': datetime.now(),
                'endpoint': endpoint
            })

    def record_error(self, error_type: str = "unknown", endpoint: str = "default"):
        """記錄錯誤"""
        with self._lock:
            self.metrics['error_counts'].append({
                'timestamp': datetime.now(),
                'error_type': error_type,
                'endpoint': endpoint
            })

    def record_system_metrics(self):
        """記錄系統指標"""
        with self._lock:
            self.metrics['cpu_usage'].append({
                'timestamp': datetime.now(),
                'value': psutil.cpu_percent()
            })
            self.metrics['memory_usage'].append({
                'timestamp': datetime.now(),
                'value': psutil.virtual_memory().percent
            })

    def get_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        with self._lock:
            response_times = [m['duration'] for m in self.metrics['response_times']]

            summary = {
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'total_requests': len(self.metrics['request_counts']),
                'total_errors': len(self.metrics['error_counts']),
                'error_rate': len(self.metrics['error_counts']) / max(len(self.metrics['request_counts']), 1),
            }

            if response_times:
                summary.update({
                    'avg_response_time': statistics.mean(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'p50_response_time': statistics.median(response_times),
                    'p95_response_time': self._percentile(response_times, 0.95),
                    'p99_response_time': self._percentile(response_times, 0.99),
                })

            cpu_usage = [m['value'] for m in self.metrics['cpu_usage']]
            if cpu_usage:
                summary['avg_cpu_usage'] = statistics.mean(cpu_usage)
                summary['max_cpu_usage'] = max(cpu_usage)

            memory_usage = [m['value'] for m in self.metrics['memory_usage']]
            if memory_usage:
                summary['avg_memory_usage'] = statistics.mean(memory_usage)
                summary['max_memory_usage'] = max(memory_usage)

            return summary

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """計算百分位數"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]


class PerformanceMonitor:
    """性能監控器"""

    def __init__(self, enable_prometheus: bool = True, prometheus_port: int = 9090):
        """
        初始化性能監控器

        Args:
            enable_prometheus: 是否啟用 Prometheus
            prometheus_port: Prometheus HTTP 服務器端口
        """
        self.metrics = PerformanceMetrics()
        self.enable_prometheus = enable_prometheus and HAS_PROMETHEUS

        # 初始化 Prometheus 指標
        if self.enable_prometheus:
            self.prom_request_count = Counter(
                'app_requests_total',
                'Total number of requests',
                ['endpoint', 'method', 'status']
            )
            self.prom_request_duration = Histogram(
                'app_request_duration_seconds',
                'Request duration in seconds',
                ['endpoint', 'method']
            )
            self.prom_error_count = Counter(
                'app_errors_total',
                'Total number of errors',
                ['endpoint', 'error_type']
            )
            self.prom_active_requests = Gauge(
                'app_active_requests',
                'Number of active requests'
            )
            self.prom_cpu_usage = Gauge(
                'app_cpu_usage_percent',
                'CPU usage percentage'
            )
            self.prom_memory_usage = Gauge(
                'app_memory_usage_percent',
                'Memory usage percentage'
            )

            # 啟動 Prometheus HTTP 服務器
            try:
                start_http_server(prometheus_port)
                logger.info(f"Prometheus metrics available at http://localhost:{prometheus_port}/metrics")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")

        # 啟動系統指標收集線程
        self._start_system_metrics_collector()

    def _start_system_metrics_collector(self):
        """啟動系統指標收集線程"""
        def collect():
            while True:
                self.metrics.record_system_metrics()
                if self.enable_prometheus:
                    self.prom_cpu_usage.set(psutil.cpu_percent())
                    self.prom_memory_usage.set(psutil.virtual_memory().percent)
                # Using time.sleep() instead of asyncio.sleep() because this runs in a daemon thread,
                # not in an async context. Daemon threads are designed for background tasks and
                # blocking sleep is appropriate here as it doesn't interfere with the event loop.
                time.sleep(5)  # 每 5 秒收集一次

        thread = threading.Thread(target=collect, daemon=True)
        thread.start()

    def track_request(self, endpoint: str = "default", method: str = "GET"):
        """
        追蹤請求的裝飾器

        Args:
            endpoint: 端點名稱
            method: HTTP 方法
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                if self.enable_prometheus:
                    self.prom_active_requests.inc()

                self.metrics.record_request(endpoint)

                try:
                    result = func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    self.metrics.record_error(type(e).__name__, endpoint)
                    if self.enable_prometheus:
                        self.prom_error_count.labels(
                            endpoint=endpoint,
                            error_type=type(e).__name__
                        ).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    self.metrics.record_response_time(duration, endpoint)

                    if self.enable_prometheus:
                        self.prom_active_requests.dec()
                        self.prom_request_count.labels(
                            endpoint=endpoint,
                            method=method,
                            status=status
                        ).inc()
                        self.prom_request_duration.labels(
                            endpoint=endpoint,
                            method=method
                        ).observe(duration)

            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """獲取所有指標"""
        return self.metrics.get_summary()

    def export_metrics(self, format: str = "json") -> str:
        """
        導出指標

        Args:
            format: 導出格式 (json, prometheus)

        Returns:
            導出的指標字符串
        """
        if format == "json":
            return json.dumps(self.get_metrics(), indent=2, default=str)
        elif format == "prometheus":
            # Prometheus 格式由 prometheus_client 自動處理
            return "Prometheus metrics available at /metrics endpoint"
        else:
            raise ValueError(f"Unsupported format: {format}")


class ResourceOptimizer:
    """資源優化器"""

    def __init__(self, cache_backend: str = "memory", redis_url: Optional[str] = None):
        """
        初始化資源優化器

        Args:
            cache_backend: 緩存後端 (memory, redis)
            redis_url: Redis 連接 URL
        """
        self.cache_backend = cache_backend

        if cache_backend == "redis" and HAS_REDIS:
            self.redis_client = redis.from_url(redis_url) if redis_url else redis.Redis()
            self.cache = None
        else:
            self.redis_client = None
            self.cache = {}

        self._lock = threading.Lock()

    def memoize(self, ttl: int = 3600):
        """
        記憶化裝飾器（帶過期時間）

        Args:
            ttl: 緩存生存時間（秒）
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成緩存鍵
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # 檢查緩存
                if self.cache_backend == "redis" and self.redis_client:
                    cached = self.redis_client.get(cache_key)
                    if cached:
                        return json.loads(cached)
                else:
                    with self._lock:
                        if cache_key in self.cache:
                            cached_data, expiry = self.cache[cache_key]
                            if datetime.now() < expiry:
                                return cached_data
                            else:
                                del self.cache[cache_key]

                # 執行函數
                result = func(*args, **kwargs)

                # 保存到緩存
                if self.cache_backend == "redis" and self.redis_client:
                    self.redis_client.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                else:
                    with self._lock:
                        self.cache[cache_key] = (result, datetime.now() + timedelta(seconds=ttl))

                return result

            return wrapper
        return decorator

    def clear_cache(self):
        """清除所有緩存"""
        if self.cache_backend == "redis" and self.redis_client:
            self.redis_client.flushdb()
        else:
            with self._lock:
                self.cache.clear()

    @staticmethod
    def batch_process(items: List[Any], batch_size: int = 100,
                     process_func: Callable = None) -> List[Any]:
        """
        批量處理以優化性能

        Args:
            items: 要處理的項目列表
            batch_size: 批次大小
            process_func: 處理函數

        Returns:
            處理結果列表
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            if process_func:
                batch_results = process_func(batch)
                results.extend(batch_results)
            else:
                results.extend(batch)
        return results


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        """初始化性能分析器"""
        self.profiles = {}
        self._lock = threading.Lock()

    def profile(self, name: str = None):
        """
        性能分析裝飾器

        Args:
            name: 分析名稱（默認使用函數名）
        """
        def decorator(func: Callable):
            profile_name = name or func.__name__

            @wraps(func)
            def wrapper(*args, **kwargs):
                import cProfile
                import pstats
                from io import StringIO

                profiler = cProfile.Profile()
                profiler.enable()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable()

                    # 生成統計信息
                    stream = StringIO()
                    stats = pstats.Stats(profiler, stream=stream)
                    stats.sort_stats('cumulative')
                    stats.print_stats(20)  # 顯示前 20 個函數

                    with self._lock:
                        self.profiles[profile_name] = stream.getvalue()

            return wrapper
        return decorator

    def get_profile(self, name: str) -> str:
        """獲取分析結果"""
        with self._lock:
            return self.profiles.get(name, "No profile found")

    def get_all_profiles(self) -> Dict[str, str]:
        """獲取所有分析結果"""
        with self._lock:
            return self.profiles.copy()

    @staticmethod
    def memory_profile(func: Callable):
        """
        內存分析裝飾器

        需要安裝 memory_profiler: pip install memory-profiler
        """
        try:
            from memory_profiler import profile as mem_profile
            return mem_profile(func)
        except ImportError:
            logger.warning("memory_profiler not installed. Install with: pip install memory-profiler")
            return func


class HealthChecker:
    """健康檢查器"""

    def __init__(self):
        """初始化健康檢查器"""
        self.checks = {}
        self._lock = threading.Lock()

    def register_check(self, name: str, check_func: Callable):
        """
        註冊健康檢查

        Args:
            name: 檢查名稱
            check_func: 檢查函數（應返回 True/False）
        """
        with self._lock:
            self.checks[name] = check_func

    def run_checks(self) -> Dict[str, Any]:
        """
        運行所有健康檢查

        Returns:
            檢查結果字典
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }

        with self._lock:
            for name, check_func in self.checks.items():
                try:
                    is_healthy = check_func()
                    results['checks'][name] = {
                        'status': 'pass' if is_healthy else 'fail',
                        'healthy': is_healthy
                    }

                    if not is_healthy:
                        results['status'] = 'unhealthy'

                except Exception as e:
                    results['checks'][name] = {
                        'status': 'error',
                        'error': str(e),
                        'healthy': False
                    }
                    results['status'] = 'unhealthy'

        return results

    @staticmethod
    def check_database(connection) -> bool:
        """檢查數據庫連接"""
        try:
            connection.ping()
            return True
        except (ConnectionError, OSError, Exception):
            return False

    @staticmethod
    def check_redis(redis_client) -> bool:
        """檢查 Redis 連接"""
        try:
            redis_client.ping()
            return True
        except (ConnectionError, OSError, Exception):
            return False

    @staticmethod
    def check_disk_space(threshold: float = 90.0) -> bool:
        """
        檢查磁盤空間

        Args:
            threshold: 使用率閾值（百分比）
        """
        usage = psutil.disk_usage('/').percent
        return usage < threshold

    @staticmethod
    def check_memory(threshold: float = 90.0) -> bool:
        """
        檢查內存使用

        Args:
            threshold: 使用率閾值（百分比）
        """
        usage = psutil.virtual_memory().percent
        return usage < threshold


# 導出工具函數
def create_performance_monitor(enable_prometheus: bool = True) -> PerformanceMonitor:
    """創建性能監控器"""
    return PerformanceMonitor(enable_prometheus=enable_prometheus)


def create_resource_optimizer(use_redis: bool = False, redis_url: Optional[str] = None) -> ResourceOptimizer:
    """創建資源優化器"""
    backend = "redis" if use_redis else "memory"
    return ResourceOptimizer(cache_backend=backend, redis_url=redis_url)


def create_health_checker() -> HealthChecker:
    """創建健康檢查器"""
    return HealthChecker()


__all__ = [
    'PerformanceMetrics',
    'PerformanceMonitor',
    'ResourceOptimizer',
    'PerformanceProfiler',
    'HealthChecker',
    'create_performance_monitor',
    'create_resource_optimizer',
    'create_health_checker',
]
