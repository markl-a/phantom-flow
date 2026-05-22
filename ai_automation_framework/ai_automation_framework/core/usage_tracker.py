"""Usage tracking and cost monitoring for LLM calls."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from ai_automation_framework.core.logger import get_logger


logger = get_logger(__name__)


@dataclass
class UsageRecord:
    """Record of a single LLM usage."""

    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    provider: str
    success: bool
    error: Optional[str] = None


class UsageTracker:
    """
    Track LLM usage and costs.

    Monitors token usage and calculates costs for different LLM providers.
    """

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, save_path: Optional[str] = None):
        """
        Initialize usage tracker.

        Args:
            save_path: Path to save usage records (JSON file)
        """
        self.records: List[UsageRecord] = []
        self.save_path = Path(save_path) if save_path else None

        if self.save_path and self.save_path.exists():
            self._load_records()

    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str = "openai",
        success: bool = True,
        error: Optional[str] = None
    ) -> UsageRecord:
        """
        Track a usage event.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            provider: Provider name (openai, anthropic, etc.)
            success: Whether the call was successful
            error: Error message if failed

        Returns:
            Usage record
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            provider=provider,
            success=success,
            error=error
        )

        self.records.append(record)

        if self.save_path:
            self._save_records()

        logger.debug(f"Tracked usage: {model} - {total_tokens} tokens - ${cost:.4f}")

        return record

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a usage event."""
        pricing = self.PRICING.get(model)

        if not pricing:
            logger.warning(f"No pricing info for model: {model}")
            return 0.0

        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_stats(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics.

        Args:
            provider: Filter by provider
            model: Filter by model
            since: Filter by timestamp (ISO format)

        Returns:
            Statistics dictionary
        """
        # Filter records
        filtered = self.records

        if provider:
            filtered = [r for r in filtered if r.provider == provider]

        if model:
            filtered = [r for r in filtered if r.model == model]

        if since:
            filtered = [r for r in filtered if r.timestamp >= since]

        if not filtered:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }

        # Calculate stats
        total_calls = len(filtered)
        successful_calls = sum(1 for r in filtered if r.success)
        failed_calls = total_calls - successful_calls
        total_tokens = sum(r.total_tokens for r in filtered)
        total_cost = sum(r.cost for r in filtered)
        total_prompt_tokens = sum(r.prompt_tokens for r in filtered)
        total_completion_tokens = sum(r.completion_tokens for r in filtered)

        # Model breakdown
        model_stats = {}
        for record in filtered:
            if record.model not in model_stats:
                model_stats[record.model] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }

            model_stats[record.model]["calls"] += 1
            model_stats[record.model]["tokens"] += record.total_tokens
            model_stats[record.model]["cost"] += record.cost

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "total_tokens": total_tokens,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_cost": round(total_cost, 4),
            "average_tokens_per_call": total_tokens // total_calls if total_calls > 0 else 0,
            "average_cost_per_call": round(total_cost / total_calls, 4) if total_calls > 0 else 0,
            "by_model": model_stats
        }

    def get_cost_summary(self) -> str:
        """Get a formatted cost summary."""
        stats = self.get_stats()

        summary = f"""
Usage Summary
{"="*50}
Total Calls: {stats['total_calls']}
Successful: {stats['successful_calls']}
Failed: {stats['failed_calls']}

Token Usage:
  Prompt: {stats['total_prompt_tokens']:,}
  Completion: {stats['total_completion_tokens']:,}
  Total: {stats['total_tokens']:,}

Costs:
  Total: ${stats['total_cost']:.4f}
  Average per call: ${stats['average_cost_per_call']:.4f}

By Model:
"""

        for model, model_stats in stats['by_model'].items():
            summary += f"  {model}:\n"
            summary += f"    Calls: {model_stats['calls']}\n"
            summary += f"    Tokens: {model_stats['tokens']:,}\n"
            summary += f"    Cost: ${model_stats['cost']:.4f}\n"

        return summary

    def _save_records(self) -> None:
        """Save records to file."""
        if not self.save_path:
            return

        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)

            data = [asdict(record) for record in self.records]

            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage records: {e}")

    def _load_records(self) -> None:
        """Load records from file."""
        if not self.save_path or not self.save_path.exists():
            return

        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)

            self.records = [UsageRecord(**record) for record in data]
            logger.info(f"Loaded {len(self.records)} usage records")
        except Exception as e:
            logger.error(f"Failed to load usage records: {e}")

    def reset(self) -> None:
        """Reset all records."""
        self.records = []

        if self.save_path and self.save_path.exists():
            self.save_path.unlink()

        logger.info("Usage records reset")


# Global tracker instance
_tracker: Optional[UsageTracker] = None


def get_usage_tracker(save_path: Optional[str] = None) -> UsageTracker:
    """
    Get or create global usage tracker.

    Args:
        save_path: Path to save usage records

    Returns:
        UsageTracker instance
    """
    global _tracker

    if _tracker is None:
        if save_path is None:
            save_path = "./logs/usage_tracking.json"
        _tracker = UsageTracker(save_path=save_path)

    return _tracker
