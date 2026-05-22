"""測試數據加載器"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from data_analysis_chatbots.data_loader import DataLoader


class TestDataLoader:
    """測試數據加載器"""

    @pytest.fixture
    def temp_csv_file(self):
        """創建臨時CSV文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('A,B,C\n')
            f.write('1,2,3\n')
            f.write('4,5,6\n')
            f.write('7,8,9\n')
            temp_path = f.name

        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_excel_file(self):
        """創建臨時Excel文件"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name

        df.to_excel(temp_path, index=False)
        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_initialization(self):
        """測試初始化"""
        loader = DataLoader()
        assert loader is not None

    def test_load_csv(self, temp_csv_file):
        """測試加載CSV文件"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ['A', 'B', 'C']

    def test_load_excel(self, temp_excel_file):
        """測試加載Excel文件"""
        loader = DataLoader()
        df = loader.load_excel(temp_excel_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'A' in df.columns
        assert 'B' in df.columns

    def test_load_nonexistent_file(self):
        """測試加載不存在的文件"""
        loader = DataLoader()

        with pytest.raises((FileNotFoundError, Exception)):
            loader.load_csv('nonexistent_file.csv')

    def test_auto_detect_delimiter(self, temp_csv_file):
        """測試自動檢測分隔符"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file)

        assert len(df.columns) == 3

    def test_load_with_custom_encoding(self, temp_csv_file):
        """測試自定義編碼"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file, encoding='utf-8')

        assert isinstance(df, pd.DataFrame)

    def test_validate_required_columns(self, temp_csv_file):
        """測試驗證必需列"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file)

        # 應該通過驗證
        assert loader.validate_required_columns(df, ['A', 'B'])

        # 應該失敗
        assert not loader.validate_required_columns(df, ['A', 'Z'])

    def test_get_data_info(self, temp_csv_file):
        """測試獲取數據信息"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file)
        info = loader.get_data_info(df)

        assert 'shape' in info
        assert 'columns' in info
        assert 'dtypes' in info
        assert info['shape'] == (3, 3)

    def test_sample_data(self, temp_csv_file):
        """測試數據採樣"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file)
        sample = loader.sample_data(df, n=2)

        assert len(sample) == 2
        assert list(sample.columns) == list(df.columns)

    def test_load_data_with_date_parsing(self):
        """測試日期解析"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('date,value\n')
            f.write('2024-01-01,100\n')
            f.write('2024-01-02,200\n')
            temp_path = f.name

        try:
            loader = DataLoader()
            df = loader.load_csv(temp_path, parse_dates=['date'])

            assert pd.api.types.is_datetime64_any_dtype(df['date'])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_data_with_index_col(self, temp_csv_file):
        """測試設置索引列"""
        loader = DataLoader()
        df = loader.load_csv(temp_csv_file, index_col=0)

        assert df.index.name == 'A' or len(df.columns) == 2

    def test_handle_missing_values(self):
        """測試處理缺失值"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('A,B,C\n')
            f.write('1,2,3\n')
            f.write('4,,6\n')
            f.write('7,8,\n')
            temp_path = f.name

        try:
            loader = DataLoader()
            df = loader.load_csv(temp_path)

            assert df['B'].isnull().sum() > 0
            assert df['C'].isnull().sum() > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestDataLoaderIntegration:
    """數據加載器集成測試"""

    def test_load_and_validate_workflow(self):
        """測試加載和驗證工作流"""
        # 創建測試數據
        df = pd.DataFrame({
            'CustomerID': [1, 2, 3],
            'Age': [25, 30, 35],
            'Income': [50000, 60000, 70000]
        })

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            df.to_csv(temp_path, index=False)

            loader = DataLoader()
            loaded_df = loader.load_csv(temp_path)

            # 驗證
            assert loader.validate_required_columns(
                loaded_df,
                ['CustomerID', 'Age', 'Income']
            )

            info = loader.get_data_info(loaded_df)
            assert info['shape'][0] == 3
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_multiple_format_support(self):
        """測試多種格式支持"""
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        # CSV
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            csv_path = f.name
        df.to_csv(csv_path, index=False)

        # Excel
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        df.to_excel(excel_path, index=False)

        try:
            loader = DataLoader()

            df_csv = loader.load_csv(csv_path)
            df_excel = loader.load_excel(excel_path)

            assert df_csv.shape == df_excel.shape
            assert list(df_csv.columns) == list(df_excel.columns)
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)
            if os.path.exists(excel_path):
                os.unlink(excel_path)
