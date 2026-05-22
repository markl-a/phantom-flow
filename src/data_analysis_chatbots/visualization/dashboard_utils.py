"""Utility functions for dashboard creation."""

from typing import Dict, Any, List
import pandas as pd


class DashboardUtils:
    """Utilities for creating interactive dashboards."""

    @staticmethod
    def format_metric(value: float, format_type: str = 'number') -> str:
        """
        Format a metric for display.

        Args:
            value: Value to format
            format_type: Type of formatting ('number', 'currency', 'percentage')

        Returns:
            Formatted string
        """
        if format_type == 'currency':
            return f"${value:,.2f}"
        elif format_type == 'percentage':
            return f"{value:.1f}%"
        elif format_type == 'number':
            return f"{value:,.0f}"
        else:
            return str(value)

    @staticmethod
    def create_summary_stats(df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """
        Create summary statistics for numeric columns.

        Args:
            df: DataFrame
            numeric_columns: List of numeric column names

        Returns:
            Dictionary with summary statistics
        """
        stats = {}
        for col in numeric_columns:
            if col in df.columns:
                stats[col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                }
        return stats
