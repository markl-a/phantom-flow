"""測試工具函數模塊"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path

from data_analysis_chatbots.utils import (
    ensure_dir,
    get_project_root,
    get_data_path,
    format_currency,
    format_percentage,
    safe_divide,
    truncate_string,
    memoize,
    LRUCache,
    cached_property_with_ttl
)


class TestEnsureDir:
    """測試目錄確保功能"""

    def test_create_new_directory(self):
        """測試創建新目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "new_dir"
            result = ensure_dir(test_dir)

            assert result.exists()
            assert result.is_dir()
            assert result == test_dir

    def test_existing_directory(self):
        """測試已存在的目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)

            assert result.exists()
            assert result.is_dir()

    def test_nested_directory_creation(self):
        """測試創建嵌套目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "level1" / "level2" / "level3"
            result = ensure_dir(nested_dir)

            assert result.exists()
            assert result.is_dir()
            assert result == nested_dir

    def test_with_string_path(self):
        """測試使用字符串路徑"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = str(Path(tmpdir) / "string_dir")
            result = ensure_dir(test_dir)

            assert result.exists()
            assert isinstance(result, Path)


class TestGetProjectRoot:
    """測試獲取項目根目錄"""

    def test_returns_path_object(self):
        """測試返回Path對象"""
        root = get_project_root()
        assert isinstance(root, Path)

    def test_root_exists(self):
        """測試根目錄存在"""
        root = get_project_root()
        assert root.exists()

    def test_root_is_directory(self):
        """測試根目錄是目錄"""
        root = get_project_root()
        assert root.is_dir()


class TestGetDataPath:
    """測試獲取數據路徑"""

    def test_raw_data_path(self):
        """測試原始數據路徑"""
        path = get_data_path("test.csv", data_type="raw")

        assert isinstance(path, Path)
        assert "raw" in str(path)
        assert path.name == "test.csv"

    def test_processed_data_path(self):
        """測試處理後數據路徑"""
        path = get_data_path("processed.csv", data_type="processed")

        assert isinstance(path, Path)
        assert "processed" in str(path)
        assert path.name == "processed.csv"

    def test_outputs_data_path(self):
        """測試輸出數據路徑"""
        path = get_data_path("result.csv", data_type="outputs")

        assert isinstance(path, Path)
        assert "outputs" in str(path)
        assert path.name == "result.csv"

    def test_default_data_type(self):
        """測試默認數據類型"""
        path = get_data_path("default.csv")

        assert isinstance(path, Path)
        assert "raw" in str(path)  # 默認應該是raw

    def test_creates_data_directory(self):
        """測試自動創建數據目錄"""
        # 這個測試確保get_data_path會創建必要的目錄
        path = get_data_path("test_file.csv", data_type="raw")
        assert path.parent.exists()


class TestFormatCurrency:
    """測試貨幣格式化"""

    def test_positive_amount(self):
        """測試正數金額"""
        result = format_currency(1234.56)
        assert result == "$1,234.56"

    def test_large_amount(self):
        """測試大額金額"""
        result = format_currency(1234567.89)
        assert result == "$1,234,567.89"

    def test_zero_amount(self):
        """測試零金額"""
        result = format_currency(0)
        assert result == "$0.00"

    def test_negative_amount(self):
        """測試負數金額"""
        result = format_currency(-500.25)
        assert result == "$-500.25"

    def test_custom_currency_symbol(self):
        """測試自定義貨幣符號"""
        result = format_currency(100, currency="€")
        assert result == "€100.00"

    def test_small_amount(self):
        """測試小額金額"""
        result = format_currency(0.99)
        assert result == "$0.99"

    def test_rounding(self):
        """測試四捨五入"""
        result = format_currency(1234.567)
        assert result == "$1,234.57"


class TestFormatPercentage:
    """測試百分比格式化"""

    def test_basic_percentage(self):
        """測試基本百分比"""
        result = format_percentage(0.15)
        assert result == "15.00%"

    def test_zero_percentage(self):
        """測試零百分比"""
        result = format_percentage(0)
        assert result == "0.00%"

    def test_one_hundred_percent(self):
        """測試100%"""
        result = format_percentage(1.0)
        assert result == "100.00%"

    def test_custom_decimals(self):
        """測試自定義小數位數"""
        result = format_percentage(0.12345, decimals=3)
        assert result == "12.345%"

    def test_one_decimal(self):
        """測試一位小數"""
        result = format_percentage(0.156, decimals=1)
        assert result == "15.6%"

    def test_no_decimals(self):
        """測試無小數"""
        result = format_percentage(0.156, decimals=0)
        assert result == "16%"

    def test_large_percentage(self):
        """測試大於100%的百分比"""
        result = format_percentage(2.5)
        assert result == "250.00%"

    def test_negative_percentage(self):
        """測試負百分比"""
        result = format_percentage(-0.25)
        assert result == "-25.00%"


class TestSafeDivide:
    """測試安全除法"""

    def test_normal_division(self):
        """測試正常除法"""
        result = safe_divide(10, 2)
        assert result == 5.0

    def test_division_by_zero(self):
        """測試除以零"""
        result = safe_divide(10, 0)
        assert result == 0.0

    def test_division_by_zero_custom_default(self):
        """測試除以零返回自定義默認值"""
        result = safe_divide(10, 0, default=-1.0)
        assert result == -1.0

    def test_float_division(self):
        """測試浮點除法"""
        result = safe_divide(7, 3)
        assert abs(result - 2.333333) < 0.00001

    def test_negative_numbers(self):
        """測試負數除法"""
        result = safe_divide(-10, 2)
        assert result == -5.0

    def test_both_negative(self):
        """測試兩個負數"""
        result = safe_divide(-10, -2)
        assert result == 5.0

    def test_zero_numerator(self):
        """測試分子為零"""
        result = safe_divide(0, 5)
        assert result == 0.0

    def test_type_error_handling(self):
        """測試類型錯誤處理"""
        result = safe_divide("10", 2, default=0.0)
        assert result == 0.0

    def test_none_values(self):
        """測試None值"""
        result = safe_divide(None, 5, default=-1.0)
        assert result == -1.0


class TestTruncateString:
    """測試字符串截斷"""

    def test_short_string(self):
        """測試短字符串（無需截斷）"""
        text = "Hello"
        result = truncate_string(text, max_length=50)
        assert result == "Hello"

    def test_long_string(self):
        """測試長字符串（需要截斷）"""
        text = "This is a very long string that needs to be truncated"
        result = truncate_string(text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_exact_length(self):
        """測試恰好等於最大長度"""
        text = "Exactly twenty chars"
        result = truncate_string(text, max_length=20)
        assert result == text

    def test_custom_suffix(self):
        """測試自定義後綴"""
        text = "This is a very long string that needs to be truncated"
        result = truncate_string(text, max_length=20, suffix=">>")
        assert len(result) == 20
        assert result.endswith(">>")

    def test_empty_string(self):
        """測試空字符串"""
        result = truncate_string("", max_length=10)
        assert result == ""

    def test_single_character(self):
        """測試單字符"""
        result = truncate_string("A", max_length=10)
        assert result == "A"

    def test_suffix_longer_than_max_length(self):
        """測試後綴長度大於最大長度的情況"""
        text = "Hello World"
        result = truncate_string(text, max_length=5, suffix="...")
        # 應該截斷到2個字符 + "..."
        assert len(result) == 5

    def test_unicode_characters(self):
        """測試Unicode字符"""
        text = "你好世界，這是一個測試字符串"
        result = truncate_string(text, max_length=10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_max_length_one(self):
        """測試最大長度為1"""
        text = "Hello"
        result = truncate_string(text, max_length=1, suffix="")
        assert result == "H"


class TestLoggingSetup:
    """測試日誌設置"""

    def test_setup_logging_exists(self):
        """測試setup_logging函數存在"""
        from data_analysis_chatbots.utils import setup_logging
        assert callable(setup_logging)

    # Note: 實際測試日誌設置會修改全局狀態，這裡僅測試函數存在性
    # 在實際應用中，可以使用mock來測試日誌配置


class TestPathIntegration:
    """路徑相關集成測試"""

    def test_project_structure_consistency(self):
        """測試項目結構一致性"""
        root = get_project_root()

        # 檢查常見的項目目錄是否存在或可以創建
        assert root.exists()

        # 測試數據路徑創建
        raw_path = get_data_path("test.csv", "raw")
        assert raw_path.parent.exists()

    def test_multiple_data_types(self):
        """測試多種數據類型路徑"""
        data_types = ["raw", "processed", "outputs"]

        for data_type in data_types:
            path = get_data_path("test.csv", data_type)
            assert isinstance(path, Path)
            assert data_type in str(path)
            assert path.parent.exists()


class TestLRUCache:
    """Test LRU Cache functionality."""

    def test_basic_set_get(self):
        """Test basic set and get operations."""
        cache = LRUCache(maxsize=10)
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

    def test_missing_key(self):
        """Test getting a non-existent key."""
        cache = LRUCache(maxsize=10)

        assert cache.get("missing") is None

    def test_maxsize_eviction(self):
        """Test that oldest items are evicted when maxsize is reached."""
        cache = LRUCache(maxsize=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # This should evict "a"

        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_lru_order(self):
        """Test that recently used items are kept."""
        cache = LRUCache(maxsize=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access "a" to make it recently used
        cache.get("a")

        # Add new item - should evict "b" (least recently used)
        cache.set("d", 4)

        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_ttl_expiration(self):
        """Test time-to-live expiration."""
        cache = LRUCache(maxsize=10, ttl=0.1)  # 100ms TTL

        cache.set("key", "value")
        assert cache.get("key") == "value"

        time.sleep(0.15)  # Wait for TTL to expire
        assert cache.get("key") is None

    def test_clear(self):
        """Test cache clearing."""
        cache = LRUCache(maxsize=10)

        cache.set("a", 1)
        cache.set("b", 2)

        cache.clear()

        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_stats(self):
        """Test cache statistics."""
        cache = LRUCache(maxsize=10)

        cache.set("a", 1)
        cache.get("a")  # Hit
        cache.get("b")  # Miss

        stats = cache.stats()

        assert stats['size'] == 1
        assert stats['maxsize'] == 10
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5


class TestMemoizeDecorator:
    """Test memoize decorator functionality."""

    def test_basic_memoization(self):
        """Test that function results are cached."""
        call_count = 0

        @memoize(maxsize=10)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Should only be called once

    def test_different_arguments(self):
        """Test that different arguments are cached separately."""
        @memoize(maxsize=10)
        def add(x, y):
            return x + y

        assert add(1, 2) == 3
        assert add(3, 4) == 7
        assert add(1, 2) == 3

    def test_cache_stats_access(self):
        """Test accessing cache statistics through the decorated function."""
        @memoize(maxsize=10)
        def func(x):
            return x

        func(1)
        func(1)
        func(2)

        stats = func.cache_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 2

    def test_cache_clear(self):
        """Test clearing the cache through the decorated function."""
        call_count = 0

        @memoize(maxsize=10)
        def func(x):
            nonlocal call_count
            call_count += 1
            return x

        func(1)
        func(1)  # Cached
        func.cache_clear()
        func(1)  # Not cached after clear

        assert call_count == 2

    def test_keyword_arguments(self):
        """Test memoization with keyword arguments."""
        @memoize(maxsize=10)
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        assert greet("Alice") == "Hello, Alice!"
        assert greet("Bob", greeting="Hi") == "Hi, Bob!"
        assert greet(name="Charlie", greeting="Hey") == "Hey, Charlie!"


class TestCachedPropertyWithTTL:
    """Test cached property with TTL functionality."""

    def test_basic_caching(self):
        """Test that property is cached."""
        class Counter:
            def __init__(self):
                self.count = 0

            @cached_property_with_ttl(ttl=1.0)
            def value(self):
                self.count += 1
                return self.count

        obj = Counter()
        assert obj.value == 1
        assert obj.value == 1  # Cached
        assert obj.count == 1  # Only computed once

    def test_ttl_expiration(self):
        """Test that property expires after TTL."""
        class Counter:
            def __init__(self):
                self.count = 0

            @cached_property_with_ttl(ttl=0.1)
            def value(self):
                self.count += 1
                return self.count

        obj = Counter()
        assert obj.value == 1
        time.sleep(0.15)  # Wait for TTL
        assert obj.value == 2  # Recomputed after expiration

    def test_different_instances(self):
        """Test that each instance has its own cache."""
        class Counter:
            def __init__(self):
                self.count = 0

            @cached_property_with_ttl(ttl=1.0)
            def value(self):
                self.count += 1
                return self.count

        obj1 = Counter()
        obj2 = Counter()

        assert obj1.value == 1
        assert obj2.value == 1
        assert obj1.count == 1
        assert obj2.count == 1
