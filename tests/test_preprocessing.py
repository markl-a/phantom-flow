"""測試數據預處理模塊"""

import pytest
import pandas as pd
import numpy as np

from data_analysis_chatbots.preprocessing import TextCleaner, DataValidator


class TestTextCleaner:
    """測試文本清洗器"""

    def test_initialization_default(self):
        """測試默認初始化"""
        cleaner = TextCleaner()
        assert cleaner.lowercase is True
        assert cleaner.remove_urls is True
        assert cleaner.remove_mentions is True
        assert cleaner.remove_hashtags is False

    def test_initialization_custom(self):
        """測試自定義初始化"""
        cleaner = TextCleaner(
            lowercase=False,
            remove_urls=False,
            remove_mentions=False,
            remove_hashtags=True
        )
        assert cleaner.lowercase is False
        assert cleaner.remove_urls is False

    def test_clean_text_lowercase(self):
        """測試轉小寫"""
        cleaner = TextCleaner(lowercase=True)
        result = cleaner.clean_text("HELLO WORLD")
        assert result == "hello world"

    def test_clean_text_remove_urls(self):
        """測試移除URL"""
        cleaner = TextCleaner(remove_urls=True)
        text = "Check this http://example.com and https://test.org"
        result = cleaner.clean_text(text)
        assert "http://" not in result
        assert "https://" not in result

    def test_clean_text_remove_mentions(self):
        """測試移除@提及"""
        cleaner = TextCleaner(remove_mentions=True)
        text = "Hello @user123 and @another_user"
        result = cleaner.clean_text(text)
        assert "@user123" not in result
        assert "@another_user" not in result

    def test_clean_text_remove_hashtags(self):
        """測試移除#標籤"""
        cleaner = TextCleaner(remove_hashtags=True)
        text = "Great #python #coding experience"
        result = cleaner.clean_text(text)
        assert "#python" not in result
        assert "#coding" not in result

    def test_clean_text_remove_punctuation(self):
        """測試移除標點符號"""
        cleaner = TextCleaner(remove_punctuation=True)
        text = "Hello, world! How are you?"
        result = cleaner.clean_text(text)
        assert "," not in result
        assert "!" not in result
        assert "?" not in result

    def test_clean_text_remove_numbers(self):
        """測試移除數字"""
        cleaner = TextCleaner(remove_numbers=True)
        text = "I have 123 apples and 456 oranges"
        result = cleaner.clean_text(text)
        assert "123" not in result
        assert "456" not in result

    def test_clean_text_combined(self):
        """測試組合清洗"""
        cleaner = TextCleaner(
            lowercase=True,
            remove_urls=True,
            remove_mentions=True,
            remove_punctuation=True
        )
        text = "Hello @user! Check http://example.com NOW!"
        result = cleaner.clean_text(text)
        assert result.islower()
        assert "@user" not in result
        assert "http://" not in result

    def test_clean_dataframe_column(self):
        """測試清洗DataFrame列"""
        df = pd.DataFrame({
            'text': [
                'Hello @user!',
                'Check http://example.com',
                'UPPERCASE TEXT'
            ]
        })
        cleaner = TextCleaner(lowercase=True, remove_mentions=True)
        result_df = cleaner.clean_dataframe_column(df, 'text')

        assert all(result_df['text'].str.islower())
        assert not any(result_df['text'].str.contains('@'))

    def test_clean_text_empty_string(self):
        """測試空字符串"""
        cleaner = TextCleaner()
        result = cleaner.clean_text("")
        assert result == ""

    def test_clean_text_whitespace_only(self):
        """測試僅空白字符"""
        cleaner = TextCleaner()
        result = cleaner.clean_text("   \n\t   ")
        assert result.strip() == ""


class TestDataValidator:
    """測試數據驗證器"""

    @pytest.fixture
    def sample_clean_data(self):
        """創建乾淨的範例數據"""
        return pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10.0, 20.0, 30.0, 40.0, 50.0],
            'C': ['a', 'b', 'c', 'd', 'e']
        })

    @pytest.fixture
    def sample_dirty_data(self):
        """創建有問題的範例數據"""
        return pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [10.0, 20.0, 30.0, 30.0, 50.0],  # 有重複
            'C': ['a', None, 'c', 'd', 'e']  # 有缺失
        })

    def test_initialization(self, sample_clean_data):
        """測試初始化"""
        validator = DataValidator(sample_clean_data)
        assert validator.df is not None
        assert len(validator.df) == 5

    def test_check_missing_values_clean(self, sample_clean_data):
        """測試檢查缺失值（乾淨數據）"""
        validator = DataValidator(sample_clean_data)
        missing = validator.check_missing_values()

        assert missing['A'] == 0
        assert missing['B'] == 0
        assert missing['C'] == 0

    def test_check_missing_values_dirty(self, sample_dirty_data):
        """測試檢查缺失值（有問題數據）"""
        validator = DataValidator(sample_dirty_data)
        missing = validator.check_missing_values()

        assert missing['A'] > 0
        assert missing['C'] > 0

    def test_check_duplicates_clean(self, sample_clean_data):
        """測試檢查重複值（乾淨數據）"""
        validator = DataValidator(sample_clean_data)
        duplicates = validator.check_duplicates()

        assert duplicates == 0

    def test_check_duplicates_dirty(self):
        """測試檢查重複值（有重複數據）"""
        df = pd.DataFrame({
            'A': [1, 2, 1, 2],
            'B': [10, 20, 10, 20]
        })
        validator = DataValidator(df)
        duplicates = validator.check_duplicates()

        assert duplicates > 0

    def test_check_data_types(self, sample_clean_data):
        """測試檢查數據類型"""
        validator = DataValidator(sample_clean_data)
        dtypes = validator.check_data_types()

        assert 'A' in dtypes
        assert 'B' in dtypes
        assert 'C' in dtypes

    def test_get_summary_statistics(self, sample_clean_data):
        """測試獲取摘要統計"""
        validator = DataValidator(sample_clean_data)
        summary = validator.get_summary_statistics()

        assert 'A' in summary.columns or 'A' in summary.index
        assert summary is not None

    def test_generate_report(self, sample_clean_data):
        """測試生成報告"""
        validator = DataValidator(sample_clean_data)
        report = validator.generate_report()

        assert 'total_rows' in report
        assert 'total_columns' in report
        assert 'missing_values' in report
        assert 'duplicate_rows' in report
        assert report['total_rows'] == 5
        assert report['total_columns'] == 3

    def test_validate_column_exists(self, sample_clean_data):
        """測試驗證列是否存在"""
        validator = DataValidator(sample_clean_data)

        assert validator.validate_column_exists('A')
        assert validator.validate_column_exists('B')
        assert not validator.validate_column_exists('Z')

    def test_validate_no_nulls(self, sample_clean_data, sample_dirty_data):
        """測試驗證無空值"""
        validator_clean = DataValidator(sample_clean_data)
        validator_dirty = DataValidator(sample_dirty_data)

        assert validator_clean.validate_no_nulls('A')
        assert not validator_dirty.validate_no_nulls('A')

    def test_validate_numeric_range(self, sample_clean_data):
        """測試驗證數值範圍"""
        validator = DataValidator(sample_clean_data)

        assert validator.validate_numeric_range('A', min_value=1, max_value=5)
        assert not validator.validate_numeric_range('A', min_value=10, max_value=20)

    def test_fix_missing_values_drop(self, sample_dirty_data):
        """測試修復缺失值（刪除）"""
        validator = DataValidator(sample_dirty_data)
        fixed_df = validator.fix_missing_values(strategy='drop')

        assert len(fixed_df) < len(sample_dirty_data)
        assert fixed_df.isnull().sum().sum() == 0

    def test_fix_missing_values_fill(self, sample_dirty_data):
        """測試修復缺失值（填充）"""
        validator = DataValidator(sample_dirty_data)
        fixed_df = validator.fix_missing_values(strategy='fill', fill_value=0)

        # 數值列應該被填充
        assert fixed_df['A'].isnull().sum() == 0

    def test_remove_duplicates(self):
        """測試移除重複值"""
        df = pd.DataFrame({
            'A': [1, 2, 1, 3],
            'B': [10, 20, 10, 30]
        })
        validator = DataValidator(df)
        unique_df = validator.remove_duplicates()

        assert len(unique_df) < len(df)
        assert len(unique_df) == len(unique_df.drop_duplicates())
