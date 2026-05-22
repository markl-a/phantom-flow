"""Data validation utilities."""

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from loguru import logger


class DataValidator:
    """Validate and check data quality.

    The check_*() methods return simple, directly-subscriptable shapes
    (per-column counts / dicts / int) so callers can do
    `validator.check_missing_values()['col_a']` without unwrapping
    metadata. The richer `generate_report()` aggregates them into a
    single summary dict.
    """

    def __init__(self, df: pd.DataFrame):
        # A DataFrame with no schema (zero columns, e.g. pd.DataFrame())
        # is invalid — every check_*() method would have nothing to operate
        # on. A DataFrame with a schema but zero rows IS valid: the user
        # may want to confirm "yes my schema is empty" via generate_report()
        # without crashing, and the per-column dicts are still well-defined.
        if df is None or len(df.columns) == 0:
            raise ValueError(
                "DataValidator requires a DataFrame with at least one column"
            )
        self.df = df

    # ── per-column / per-dataset checks ─────────────────────────────────

    def check_missing_values(self) -> Dict[str, int]:
        """Per-column missing-value counts.

        Returns a flat dict ``{column_name: missing_count}`` for every
        column in the frame. Use ``generate_report()`` if you also need
        percentages, totals, or which columns have missing values.
        """
        return {col: int(count) for col, count in self.df.isnull().sum().items()}

    def check_duplicates(self, subset: Optional[List[str]] = None) -> int:
        """Number of fully-duplicated rows.

        With ``subset`` only the listed columns are considered when
        deciding whether a row is a duplicate.
        """
        if subset:
            return int(self.df.duplicated(subset=subset).sum())
        return int(self.df.duplicated().sum())

    def check_data_types(self) -> Dict[str, str]:
        """Per-column dtype as a string (``'int64'``, ``'float64'``, ``'object'``)."""
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}

    def get_summary_statistics(self) -> pd.DataFrame:
        """Wrap pandas ``describe(include='all')`` for one-call access."""
        return self.df.describe(include='all')

    # ── richer per-column inspection ────────────────────────────────────

    def check_value_ranges(self, column: str) -> Dict[str, Any]:
        """Min/max/mean/quartiles for a numeric column."""
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            raise ValueError(f"Column '{column}' is not numeric")

        s = self.df[column]
        return {
            'column': column,
            'min':    float(s.min()),
            'max':    float(s.max()),
            'mean':   float(s.mean()),
            'median': float(s.median()),
            'std':    float(s.std()),
            'q25':    float(s.quantile(0.25)),
            'q75':    float(s.quantile(0.75)),
        }

    def check_outliers(self, column: str, method: str = 'iqr', threshold: float = 1.5) -> Dict[str, Any]:
        """Outlier detection using IQR (default) or z-score."""
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            raise ValueError(f"Column '{column}' is not numeric")

        s = self.df[column]
        if method == 'iqr':
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - threshold * iqr, q3 + threshold * iqr
            outliers = (s < lower) | (s > upper)
        elif method == 'zscore':
            z = np.abs((s - s.mean()) / s.std())
            outliers = z > threshold
        else:
            raise ValueError(f"Unknown method: {method}")

        outlier_count = int(outliers.sum())
        return {
            'column':              column,
            'method':              method,
            'outlier_count':       outlier_count,
            'outlier_percentage':  float((outlier_count / len(self.df) * 100).round(2)),
            'outlier_indices':     list(self.df[outliers].index) if outlier_count < 100 else [],
            'has_outliers':        outlier_count > 0,
        }

    def check_unique_values(self, column: str) -> Dict[str, Any]:
        """Unique-value statistics for a column."""
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found")

        unique_count = int(self.df[column].nunique())
        value_counts = self.df[column].value_counts()
        return {
            'column':            column,
            'unique_count':      unique_count,
            'total_count':       len(self.df),
            'unique_percentage': float((unique_count / len(self.df) * 100).round(2)),
            'most_common':       value_counts.head(10).to_dict() if unique_count < 1000 else {},
            'is_unique':         unique_count == len(self.df),
        }

    # ── lightweight validation predicates (return bool) ─────────────────

    def validate_column_exists(self, column: str) -> bool:
        """``True`` if ``column`` is in the frame's columns."""
        return column in self.df.columns

    def validate_no_nulls(self, column: str) -> bool:
        """``True`` if ``column`` has zero missing values."""
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found")
        return not bool(self.df[column].isnull().any())

    def validate_numeric_range(self, column: str, min_value: Union[int, float], max_value: Union[int, float]) -> bool:
        """``True`` if every value of ``column`` lies in [min_value, max_value]."""
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found")
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            raise ValueError(f"Column '{column}' is not numeric")
        s = self.df[column].dropna()
        return bool(s.min() >= min_value and s.max() <= max_value)

    # ── mutators (return a new DataFrame, never mutate self.df) ──────────

    def fix_missing_values(
        self,
        strategy: str = 'drop',
        fill_value: Optional[Union[int, float, str]] = None,
    ) -> pd.DataFrame:
        """Return a copy of ``self.df`` with missing values handled.

        ``strategy='drop'`` drops any row containing a NaN.
        ``strategy='fill'`` fills NaNs with ``fill_value``.
        """
        if strategy == 'drop':
            return self.df.dropna()
        if strategy == 'fill':
            return self.df.fillna(fill_value)
        raise ValueError(f"Unknown strategy: {strategy!r} (expected 'drop' or 'fill')")

    def remove_duplicates(self, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Return a copy of ``self.df`` with duplicate rows removed."""
        return self.df.drop_duplicates(subset=subset)

    # ── aggregate report ────────────────────────────────────────────────

    def generate_report(self) -> Dict[str, Any]:
        """One-call summary report — totals + per-column missing/dtypes + duplicate count."""
        return {
            'total_rows':     len(self.df),
            'total_columns':  len(self.df.columns),
            'missing_values': self.check_missing_values(),
            'duplicate_rows': self.check_duplicates(),
            'data_types':     self.check_data_types(),
        }

    def print_report(self) -> None:
        """Print a human-readable summary to the loguru logger."""
        report = self.generate_report()
        logger.info("=" * 60)
        logger.info("DATA QUALITY REPORT")
        logger.info("=" * 60)
        logger.info(f"Rows:    {report['total_rows']:,}")
        logger.info(f"Columns: {report['total_columns']}")

        missing = report['missing_values']
        cols_with_missing = [c for c, n in missing.items() if n > 0]
        logger.info(f"Missing: {sum(missing.values()):,} cells across {len(cols_with_missing)} columns")
        for col in cols_with_missing[:5]:
            pct = (missing[col] / report['total_rows'] * 100) if report['total_rows'] else 0
            logger.info(f"  - {col}: {missing[col]} ({pct:.2f}%)")

        logger.info(f"Duplicates: {report['duplicate_rows']:,} rows")
        logger.info("=" * 60)
