"""
Token Budget Management System.

This module provides tools for tracking and limiting token usage
to control costs when using LLM APIs.

Features:
- Daily, weekly, monthly token limits
- Per-model budget allocation
- Real-time usage tracking
- Alert thresholds
- Usage analytics and reporting
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading


class BudgetPeriod(Enum):
    """Budget period types."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BudgetExceededError(Exception):
    """Raised when token budget is exceeded."""

    def __init__(
        self,
        message: str,
        period: BudgetPeriod,
        limit: int,
        used: int,
        model: Optional[str] = None
    ):
        super().__init__(message)
        self.period = period
        self.limit = limit
        self.used = used
        self.model = model


@dataclass
class TokenUsage:
    """Token usage record."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    cost_usd: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConfig:
    """Budget configuration."""
    hourly_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    weekly_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    alert_threshold: float = 0.8  # Alert at 80% usage
    model_limits: Dict[str, int] = field(default_factory=dict)  # Per-model limits


@dataclass
class UsageStats:
    """Usage statistics for a period."""
    period: BudgetPeriod
    start_time: str
    end_time: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    request_count: int
    limit: Optional[int]
    usage_percentage: float
    by_model: Dict[str, int] = field(default_factory=dict)


# Token costs per 1K tokens (approximate, as of 2024)
TOKEN_COSTS = {
    # OpenAI models
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # Anthropic models
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    # Google models
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-pro": {"input": 0.0005, "output": 0.0015},
}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> Optional[float]:
    """
    Calculate the cost for a given usage.

    Args:
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens

    Returns:
        Cost in USD or None if model not found
    """
    # Normalize model name
    model_lower = model.lower()
    costs = None

    for model_key, model_costs in TOKEN_COSTS.items():
        if model_key in model_lower or model_lower in model_key:
            costs = model_costs
            break

    if not costs:
        return None

    input_cost = (prompt_tokens / 1000) * costs["input"]
    output_cost = (completion_tokens / 1000) * costs["output"]
    return round(input_cost + output_cost, 6)


class BaseUsageStore(ABC):
    """Abstract base class for usage storage."""

    @abstractmethod
    def record_usage(self, usage: TokenUsage) -> None:
        """Record token usage."""
        pass

    @abstractmethod
    def get_usage(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> int:
        """Get total tokens used in a period."""
        pass

    @abstractmethod
    def get_usage_stats(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> UsageStats:
        """Get detailed usage statistics."""
        pass

    @abstractmethod
    def get_usage_history(
        self,
        start_time: datetime,
        end_time: datetime,
        model: Optional[str] = None
    ) -> List[TokenUsage]:
        """Get usage history for a time range."""
        pass


class SQLiteUsageStore(BaseUsageStore):
    """SQLite-based usage storage."""

    def __init__(self, db_path: str = "./data/token_usage.db"):
        """Initialize SQLite usage store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    cost_usd REAL,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_timestamp
                ON token_usage(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_model
                ON token_usage(model)
            """)
            conn.commit()

    def _get_period_range(self, period: BudgetPeriod) -> tuple:
        """Get start and end time for a period."""
        now = datetime.utcnow()

        if period == BudgetPeriod.HOURLY:
            start = now.replace(minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.WEEKLY:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now

        return start.isoformat(), now.isoformat()

    def record_usage(self, usage: TokenUsage) -> None:
        """Record token usage."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO token_usage
                    (prompt_tokens, completion_tokens, total_tokens, model, timestamp, cost_usd, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    usage.model,
                    usage.timestamp,
                    usage.cost_usd,
                    json.dumps(usage.metadata)
                ))
                conn.commit()

    def get_usage(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> int:
        """Get total tokens used in a period."""
        start_time, end_time = self._get_period_range(period)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if model:
                cursor.execute("""
                    SELECT COALESCE(SUM(total_tokens), 0) as total
                    FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ? AND model = ?
                """, (start_time, end_time, model))
            else:
                cursor.execute("""
                    SELECT COALESCE(SUM(total_tokens), 0) as total
                    FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ?
                """, (start_time, end_time))

            result = cursor.fetchone()
            return result['total'] if result else 0

    def get_usage_stats(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> UsageStats:
        """Get detailed usage statistics."""
        start_time, end_time = self._get_period_range(period)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Base query
            if model:
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(total_tokens), 0) as total_tokens,
                        COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                        COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                        COUNT(*) as request_count
                    FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ? AND model = ?
                """, (start_time, end_time, model))
            else:
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(total_tokens), 0) as total_tokens,
                        COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                        COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                        COUNT(*) as request_count
                    FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ?
                """, (start_time, end_time))

            row = cursor.fetchone()

            # Get by-model breakdown
            cursor.execute("""
                SELECT model, COALESCE(SUM(total_tokens), 0) as tokens
                FROM token_usage
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY model
            """, (start_time, end_time))

            by_model = {r['model']: r['tokens'] for r in cursor.fetchall()}

            return UsageStats(
                period=period,
                start_time=start_time,
                end_time=end_time,
                total_tokens=row['total_tokens'],
                prompt_tokens=row['prompt_tokens'],
                completion_tokens=row['completion_tokens'],
                request_count=row['request_count'],
                limit=None,
                usage_percentage=0.0,
                by_model=by_model
            )

    def get_usage_history(
        self,
        start_time: datetime,
        end_time: datetime,
        model: Optional[str] = None
    ) -> List[TokenUsage]:
        """Get usage history for a time range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if model:
                cursor.execute("""
                    SELECT * FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ? AND model = ?
                    ORDER BY timestamp DESC
                """, (start_time.isoformat(), end_time.isoformat(), model))
            else:
                cursor.execute("""
                    SELECT * FROM token_usage
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp DESC
                """, (start_time.isoformat(), end_time.isoformat()))

            return [
                TokenUsage(
                    prompt_tokens=row['prompt_tokens'],
                    completion_tokens=row['completion_tokens'],
                    total_tokens=row['total_tokens'],
                    model=row['model'],
                    timestamp=row['timestamp'],
                    cost_usd=row['cost_usd'],
                    metadata=json.loads(row['metadata'] or '{}')
                )
                for row in cursor.fetchall()
            ]


class InMemoryUsageStore(BaseUsageStore):
    """In-memory usage storage (for testing or temporary use)."""

    def __init__(self):
        """Initialize in-memory store."""
        self._usage: List[TokenUsage] = []
        self._lock = threading.Lock()

    def _get_period_range(self, period: BudgetPeriod) -> tuple:
        """Get start and end time for a period."""
        now = datetime.utcnow()

        if period == BudgetPeriod.HOURLY:
            start = now.replace(minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.WEEKLY:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now

        return start, now

    def record_usage(self, usage: TokenUsage) -> None:
        """Record token usage."""
        with self._lock:
            self._usage.append(usage)

    def get_usage(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> int:
        """Get total tokens used in a period."""
        start, end = self._get_period_range(period)
        total = 0

        with self._lock:
            for usage in self._usage:
                usage_time = datetime.fromisoformat(usage.timestamp)
                if start <= usage_time <= end:
                    if model is None or usage.model == model:
                        total += usage.total_tokens

        return total

    def get_usage_stats(
        self,
        period: BudgetPeriod,
        model: Optional[str] = None
    ) -> UsageStats:
        """Get detailed usage statistics."""
        start, end = self._get_period_range(period)
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        request_count = 0
        by_model: Dict[str, int] = {}

        with self._lock:
            for usage in self._usage:
                usage_time = datetime.fromisoformat(usage.timestamp)
                if start <= usage_time <= end:
                    if model is None or usage.model == model:
                        total_tokens += usage.total_tokens
                        prompt_tokens += usage.prompt_tokens
                        completion_tokens += usage.completion_tokens
                        request_count += 1
                        by_model[usage.model] = by_model.get(usage.model, 0) + usage.total_tokens

        return UsageStats(
            period=period,
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            request_count=request_count,
            limit=None,
            usage_percentage=0.0,
            by_model=by_model
        )

    def get_usage_history(
        self,
        start_time: datetime,
        end_time: datetime,
        model: Optional[str] = None
    ) -> List[TokenUsage]:
        """Get usage history for a time range."""
        result = []

        with self._lock:
            for usage in self._usage:
                usage_time = datetime.fromisoformat(usage.timestamp)
                if start_time <= usage_time <= end_time:
                    if model is None or usage.model == model:
                        result.append(usage)

        return sorted(result, key=lambda x: x.timestamp, reverse=True)


class TokenBudgetManager:
    """
    Token Budget Manager for controlling LLM API costs.

    Tracks token usage and enforces budget limits across different
    time periods (hourly, daily, weekly, monthly).

    Example:
        >>> from ai_automation_framework.core import TokenBudgetManager, BudgetConfig
        >>>
        >>> # Create manager with daily limit
        >>> manager = TokenBudgetManager(
        ...     config=BudgetConfig(daily_limit=100000)
        ... )
        >>>
        >>> # Check budget before making API call
        >>> if manager.can_use_tokens(1000, "gpt-4"):
        ...     # Make API call
        ...     response = client.chat(messages)
        ...     # Record usage
        ...     manager.record_usage(
        ...         prompt_tokens=response.usage["prompt_tokens"],
        ...         completion_tokens=response.usage["completion_tokens"],
        ...         model="gpt-4"
        ...     )
    """

    def __init__(
        self,
        config: Optional[BudgetConfig] = None,
        usage_store: Optional[BaseUsageStore] = None,
        on_alert: Optional[Callable[[BudgetPeriod, int, int, float], None]] = None,
        on_exceed: Optional[Callable[[BudgetPeriod, int, int], None]] = None,
        enforce_limits: bool = True
    ):
        """
        Initialize Token Budget Manager.

        Args:
            config: Budget configuration
            usage_store: Custom usage store (default: SQLite)
            on_alert: Callback when approaching limit (period, limit, used, percentage)
            on_exceed: Callback when limit exceeded (period, limit, used)
            enforce_limits: If True, raises BudgetExceededError when limits exceeded
        """
        self.config = config or BudgetConfig()
        self.usage_store = usage_store or SQLiteUsageStore()
        self.on_alert = on_alert
        self.on_exceed = on_exceed
        self.enforce_limits = enforce_limits
        self._alert_sent: Dict[str, bool] = {}

    def _get_limit_for_period(self, period: BudgetPeriod) -> Optional[int]:
        """Get the configured limit for a period."""
        if period == BudgetPeriod.HOURLY:
            return self.config.hourly_limit
        elif period == BudgetPeriod.DAILY:
            return self.config.daily_limit
        elif period == BudgetPeriod.WEEKLY:
            return self.config.weekly_limit
        elif period == BudgetPeriod.MONTHLY:
            return self.config.monthly_limit
        return None

    def _check_and_alert(
        self,
        period: BudgetPeriod,
        current_usage: int,
        limit: int
    ) -> None:
        """Check usage and trigger alerts if needed."""
        percentage = current_usage / limit if limit > 0 else 0.0
        alert_key = f"{period.value}_{datetime.utcnow().strftime('%Y%m%d%H')}"

        # Check for alert threshold
        if percentage >= self.config.alert_threshold:
            if alert_key not in self._alert_sent and self.on_alert:
                self.on_alert(period, limit, current_usage, percentage)
                self._alert_sent[alert_key] = True

        # Check if limit exceeded
        if current_usage >= limit:
            if self.on_exceed:
                self.on_exceed(period, limit, current_usage)

    def check_budget(
        self,
        tokens_needed: int = 0,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check current budget status.

        Args:
            tokens_needed: Number of tokens about to be used
            model: Model to check (for per-model limits)

        Returns:
            Dictionary with budget status for each period
        """
        status = {}

        for period in BudgetPeriod:
            limit = self._get_limit_for_period(period)
            if limit is None:
                continue

            current_usage = self.usage_store.get_usage(period, model)
            remaining = max(0, limit - current_usage)
            percentage = (current_usage / limit) * 100 if limit > 0 else 0.0

            status[period.value] = {
                "limit": limit,
                "used": current_usage,
                "remaining": remaining,
                "percentage": round(percentage, 2),
                "can_proceed": current_usage + tokens_needed <= limit
            }

            # Trigger alerts
            self._check_and_alert(period, current_usage, limit)

        # Check per-model limits
        if model and model in self.config.model_limits:
            model_limit = self.config.model_limits[model]
            model_usage = self.usage_store.get_usage(BudgetPeriod.DAILY, model)
            status[f"model_{model}"] = {
                "limit": model_limit,
                "used": model_usage,
                "remaining": max(0, model_limit - model_usage),
                "percentage": round((model_usage / model_limit) * 100, 2) if model_limit > 0 else 0.0,
                "can_proceed": model_usage + tokens_needed <= model_limit
            }

        return status

    def can_use_tokens(
        self,
        tokens_needed: int,
        model: Optional[str] = None
    ) -> bool:
        """
        Check if tokens can be used without exceeding budget.

        Args:
            tokens_needed: Number of tokens to use
            model: Model name (for per-model limits)

        Returns:
            True if tokens can be used

        Raises:
            BudgetExceededError: If enforce_limits=True and limit exceeded
        """
        for period in BudgetPeriod:
            limit = self._get_limit_for_period(period)
            if limit is None:
                continue

            current_usage = self.usage_store.get_usage(period)

            if current_usage + tokens_needed > limit:
                if self.enforce_limits:
                    raise BudgetExceededError(
                        f"Token budget exceeded for {period.value}: "
                        f"{current_usage}/{limit} tokens used, "
                        f"cannot use {tokens_needed} more tokens",
                        period=period,
                        limit=limit,
                        used=current_usage,
                        model=model
                    )
                return False

        # Check per-model limits
        if model and model in self.config.model_limits:
            model_limit = self.config.model_limits[model]
            model_usage = self.usage_store.get_usage(BudgetPeriod.DAILY, model)

            if model_usage + tokens_needed > model_limit:
                if self.enforce_limits:
                    raise BudgetExceededError(
                        f"Model budget exceeded for {model}: "
                        f"{model_usage}/{model_limit} tokens used",
                        period=BudgetPeriod.DAILY,
                        limit=model_limit,
                        used=model_usage,
                        model=model
                    )
                return False

        return True

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenUsage:
        """
        Record token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name
            metadata: Optional metadata

        Returns:
            TokenUsage record
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            cost_usd=cost,
            metadata=metadata or {}
        )

        self.usage_store.record_usage(usage)

        # Check alerts after recording
        for period in BudgetPeriod:
            limit = self._get_limit_for_period(period)
            if limit:
                current_usage = self.usage_store.get_usage(period)
                self._check_and_alert(period, current_usage, limit)

        return usage

    def get_stats(
        self,
        period: BudgetPeriod = BudgetPeriod.DAILY,
        model: Optional[str] = None
    ) -> UsageStats:
        """
        Get usage statistics for a period.

        Args:
            period: Budget period
            model: Optional model filter

        Returns:
            UsageStats object
        """
        stats = self.usage_store.get_usage_stats(period, model)
        limit = self._get_limit_for_period(period)

        if limit:
            stats.limit = limit
            stats.usage_percentage = (stats.total_tokens / limit) * 100 if limit > 0 else 0.0

        return stats

    def get_cost_summary(
        self,
        period: BudgetPeriod = BudgetPeriod.DAILY
    ) -> Dict[str, Any]:
        """
        Get cost summary for a period.

        Args:
            period: Budget period

        Returns:
            Cost summary dictionary
        """
        now = datetime.utcnow()

        if period == BudgetPeriod.HOURLY:
            start = now.replace(minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == BudgetPeriod.WEEKLY:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        history = self.usage_store.get_usage_history(start, now)

        total_cost = sum(u.cost_usd or 0 for u in history)
        by_model: Dict[str, Dict[str, Any]] = {}

        for usage in history:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "requests": 0
                }
            by_model[usage.model]["tokens"] += usage.total_tokens
            by_model[usage.model]["cost_usd"] += usage.cost_usd or 0
            by_model[usage.model]["requests"] += 1

        return {
            "period": period.value,
            "start_time": start.isoformat(),
            "end_time": now.isoformat(),
            "total_cost_usd": round(total_cost, 4),
            "total_requests": len(history),
            "by_model": by_model
        }

    def reset_alerts(self) -> None:
        """Reset alert tracking (allows alerts to be sent again)."""
        self._alert_sent.clear()


# Global budget manager instance
_budget_manager: Optional[TokenBudgetManager] = None


def get_budget_manager(
    config: Optional[BudgetConfig] = None,
    reset: bool = False
) -> TokenBudgetManager:
    """
    Get or create global budget manager.

    Args:
        config: Optional budget configuration
        reset: If True, create new instance

    Returns:
        TokenBudgetManager instance
    """
    global _budget_manager

    if _budget_manager is None or reset:
        _budget_manager = TokenBudgetManager(config=config)

    return _budget_manager
