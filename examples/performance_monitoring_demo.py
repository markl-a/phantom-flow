"""
Performance Monitoring Demo

This script demonstrates how to use the performance monitoring decorators
in the data_analysis_chatbots package.
"""

import sys
from pathlib import Path
import time
import random
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_analysis_chatbots.utils import timer, memory_profiler, retry
from data_analysis_chatbots.utils.performance import monitor
from loguru import logger


def setup_demo_logging():
    """Setup logging for the demo."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )


# ============================================================================
# Example 1: Basic Timer Usage
# ============================================================================

@timer
def load_and_process_data(size: int = 10000) -> pd.DataFrame:
    """
    Load and process a DataFrame.

    This function demonstrates the @timer decorator for tracking
    execution time of data processing operations.
    """
    logger.info(f"Loading DataFrame with {size} rows...")

    # Simulate data loading
    df = pd.DataFrame({
        'id': range(size),
        'value': np.random.randn(size),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size),
        'timestamp': pd.date_range('2024-01-01', periods=size, freq='1min')
    })

    # Simulate processing
    time.sleep(0.5)
    df['value_squared'] = df['value'] ** 2
    df['moving_avg'] = df['value'].rolling(window=10).mean()

    logger.info("Data processing completed")
    return df


# ============================================================================
# Example 2: Memory Profiler Usage
# ============================================================================

@memory_profiler
def create_large_dataset(rows: int = 1000000) -> pd.DataFrame:
    """
    Create a large dataset and monitor memory usage.

    This function demonstrates the @memory_profiler decorator for
    tracking memory consumption during data creation.
    """
    logger.info(f"Creating large dataset with {rows} rows...")

    df = pd.DataFrame({
        'col1': np.random.randn(rows),
        'col2': np.random.randint(0, 100, rows),
        'col3': np.random.choice(['X', 'Y', 'Z'], rows),
        'col4': np.random.random(rows),
    })

    # Perform some operations
    df['col5'] = df['col1'] * df['col4']
    df['col6'] = df['col2'].apply(lambda x: x ** 2)

    logger.info("Dataset created")
    return df


# ============================================================================
# Example 3: Retry Decorator Usage
# ============================================================================

class UnstableAPISimulator:
    """Simulates an unstable API for demonstration."""

    def __init__(self, failure_rate: float = 0.7):
        self.failure_rate = failure_rate
        self.call_count = 0

    @retry(max_attempts=5, delay=0.5, backoff=2.0, exceptions=(ConnectionError, TimeoutError))
    def fetch_data(self) -> dict:
        """
        Fetch data from an unstable API.

        This method demonstrates the @retry decorator with exponential backoff
        for handling transient failures.
        """
        self.call_count += 1
        logger.info(f"API call #{self.call_count}")

        # Simulate random failures
        if random.random() < self.failure_rate:
            error_type = random.choice([ConnectionError, TimeoutError])
            raise error_type(f"API temporarily unavailable (call #{self.call_count})")

        return {
            "status": "success",
            "data": [i ** 2 for i in range(10)],
            "timestamp": time.time()
        }


# ============================================================================
# Example 4: Custom Retry Callback
# ============================================================================

def retry_callback(attempt: int, error: Exception):
    """Custom callback for retry operations."""
    logger.warning(f"🔄 Retry callback: Attempt {attempt} failed with {type(error).__name__}: {error}")


@retry(
    max_attempts=4,
    delay=0.3,
    backoff=1.5,
    exceptions=(ValueError, TypeError),
    on_retry=retry_callback
)
def validate_and_process(data: any) -> dict:
    """
    Validate and process data with custom retry callback.

    This function demonstrates using a custom callback function
    that gets called on each retry attempt.
    """
    # Simulate validation that might fail
    if not isinstance(data, (list, tuple)):
        raise TypeError(f"Expected list or tuple, got {type(data).__name__}")

    if len(data) < 3:
        raise ValueError(f"Data too short: {len(data)} items (minimum 3 required)")

    return {
        "length": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data)
    }


# ============================================================================
# Example 5: Combined Monitoring
# ============================================================================

@monitor(time_it=True, profile_memory=True)
def comprehensive_analysis(df: pd.DataFrame) -> dict:
    """
    Perform comprehensive data analysis with combined monitoring.

    This function uses the @monitor decorator to apply both
    timing and memory profiling simultaneously.
    """
    logger.info("Starting comprehensive analysis...")

    results = {
        "shape": df.shape,
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        "numeric_stats": df.select_dtypes(include=[np.number]).describe().to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }

    # Simulate some intensive computation
    time.sleep(0.3)

    logger.info("Analysis completed")
    return results


@monitor(
    time_it=True,
    profile_memory=True,
    retry_config={"max_attempts": 3, "delay": 0.5, "backoff": 2.0}
)
def fetch_and_analyze(api_endpoint: str, data_size: int = 1000) -> dict:
    """
    Fetch data from API and analyze it with full monitoring.

    This function demonstrates using all monitoring features together:
    timing, memory profiling, and retry logic.
    """
    logger.info(f"Fetching data from {api_endpoint}...")

    # Simulate API call with potential failure
    if random.random() < 0.3:
        raise ConnectionError("Network timeout")

    # Create sample data
    data = {
        "values": np.random.randn(data_size),
        "labels": np.random.choice(['A', 'B', 'C'], data_size)
    }

    # Analyze
    results = {
        "count": len(data["values"]),
        "mean": np.mean(data["values"]),
        "std": np.std(data["values"]),
        "distribution": {
            label: np.sum(data["labels"] == label)
            for label in ['A', 'B', 'C']
        }
    }

    return results


# ============================================================================
# Example 6: Real-World Scenario - Data Pipeline
# ============================================================================

class DataPipeline:
    """Example data pipeline with performance monitoring."""

    @timer
    def extract(self, source: str) -> pd.DataFrame:
        """Extract data from source."""
        logger.info(f"Extracting data from {source}...")
        time.sleep(0.2)  # Simulate I/O

        return pd.DataFrame({
            'id': range(5000),
            'value': np.random.randn(5000),
            'category': np.random.choice(['A', 'B', 'C'], 5000)
        })

    @timer
    @memory_profiler
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data."""
        logger.info("Transforming data...")

        # Apply transformations
        df = df.copy()
        df['value_normalized'] = (df['value'] - df['value'].mean()) / df['value'].std()
        df['value_log'] = np.log1p(df['value'].abs())

        # Add aggregations
        df['category_mean'] = df.groupby('category')['value'].transform('mean')

        time.sleep(0.3)  # Simulate processing
        return df

    @retry(max_attempts=3, delay=1.0)
    @timer
    def load(self, df: pd.DataFrame, destination: str) -> bool:
        """Load data to destination."""
        logger.info(f"Loading data to {destination}...")

        # Simulate occasional failures
        if random.random() < 0.2:
            raise IOError("Database connection failed")

        time.sleep(0.2)  # Simulate I/O
        logger.info(f"Successfully loaded {len(df)} records")
        return True

    def run(self, source: str, destination: str):
        """Run the complete pipeline."""
        logger.info("=" * 60)
        logger.info("Starting Data Pipeline")
        logger.info("=" * 60)

        # ETL process
        df = self.extract(source)
        df = self.transform(df)
        self.load(df, destination)

        logger.info("=" * 60)
        logger.info("Pipeline Completed Successfully")
        logger.info("=" * 60)


# ============================================================================
# Main Demo
# ============================================================================

def main():
    """Run all demonstration examples."""
    setup_demo_logging()

    print("\n" + "=" * 70)
    print("PERFORMANCE MONITORING DEMONSTRATION")
    print("=" * 70 + "\n")

    # Example 1: Timer
    print("\n--- Example 1: Basic Timer ---")
    df = load_and_process_data(5000)
    print(f"Processed DataFrame shape: {df.shape}\n")

    # Example 2: Memory Profiler
    print("\n--- Example 2: Memory Profiler ---")
    large_df = create_large_dataset(500000)
    print(f"Created DataFrame shape: {large_df.shape}\n")
    del large_df  # Free memory

    # Example 3: Retry
    print("\n--- Example 3: Retry with Exponential Backoff ---")
    api = UnstableAPISimulator(failure_rate=0.6)
    try:
        result = api.fetch_data()
        print(f"API call succeeded after {api.call_count} attempts")
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"API call failed: {e}\n")

    # Example 4: Custom Retry Callback
    print("\n--- Example 4: Retry with Custom Callback ---")
    try:
        result = validate_and_process([1, 2, 3, 4, 5])
        print(f"Validation result: {result}\n")
    except Exception as e:
        print(f"Validation failed: {e}\n")

    # Example 5: Combined Monitoring
    print("\n--- Example 5: Combined Monitoring ---")
    analysis_df = pd.DataFrame({
        'a': np.random.randn(10000),
        'b': np.random.randn(10000),
        'c': np.random.choice(['X', 'Y'], 10000)
    })
    results = comprehensive_analysis(analysis_df)
    print(f"Analysis results keys: {list(results.keys())}\n")

    # Example 6: Data Pipeline
    print("\n--- Example 6: Complete Data Pipeline ---")
    pipeline = DataPipeline()
    pipeline.run("source_database", "target_database")

    print("\n" + "=" * 70)
    print("ALL DEMONSTRATIONS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
