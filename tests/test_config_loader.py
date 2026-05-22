"""ConfigLoader 模組測試"""
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import yaml
import tempfile
import os

from data_analysis_chatbots.config_loader import ConfigLoader


@pytest.fixture
def sample_config():
    """提供示例配置數據"""
    return {
        'paths': {
            'data_root': '/data',
            'output': '/output',
            'logs': '/logs'
        },
        'datasets': {
            'sales': {
                'path': '/data/sales.csv',
                'type': 'csv',
                'encoding': 'utf-8'
            },
            'customers': {
                'path': '/data/customers.csv',
                'type': 'csv'
            }
        },
        'analysis': {
            'rfm': {
                'enabled': True,
                'parameters': {
                    'recency_weight': 0.3,
                    'frequency_weight': 0.3,
                    'monetary_weight': 0.4
                }
            },
            'clustering': {
                'enabled': True,
                'algorithm': 'kmeans',
                'n_clusters': 5
            },
            'clv': {
                'enabled': False,
                'discount_rate': 0.1
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }


@pytest.fixture
def temp_config_file(sample_config):
    """創建臨時配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(sample_config, f)
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_yaml_file():
    """創建無效的 YAML 文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write("invalid: yaml: content:\n  - this is\n  - not: valid\n    - yaml")
        temp_path = f.name

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestConfigLoaderInit:
    """測試初始化"""

    def test_default_config_path(self):
        """測試默認配置路徑"""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='paths:\n  data_root: /data')):
                loader = ConfigLoader()

                # 驗證配置路徑包含 config/config.yaml
                assert 'config' in str(loader.config_path)
                assert 'config.yaml' in str(loader.config_path)

    def test_custom_config_path(self, temp_config_file):
        """測試自定義配置路徑"""
        loader = ConfigLoader(config_path=temp_config_file)

        assert loader.config_path == Path(temp_config_file)
        assert loader.config is not None
        assert isinstance(loader.config, dict)

    def test_config_file_not_found(self):
        """測試配置文件不存在的情況"""
        non_existent_path = '/tmp/non_existent_config_12345.yaml'

        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigLoader(config_path=non_existent_path)

        # Compare via Path.parts so the assertion is separator-agnostic.
        # Stringified path normalises '/tmp/...' to '\\tmp\\...' on Windows;
        # comparing parts avoids the slash mismatch.
        from pathlib import Path
        msg = str(exc_info.value)
        assert 'Configuration file not found' in msg
        # Last filename component should appear in the error message
        # regardless of path separator.
        assert 'non_existent_config_12345.yaml' in msg

    def test_config_loaded_on_init(self, temp_config_file):
        """測試初始化時配置已加載"""
        loader = ConfigLoader(config_path=temp_config_file)

        assert loader.config is not None
        assert 'paths' in loader.config
        assert 'datasets' in loader.config


class TestConfigGet:
    """測試配置獲取"""

    def test_get_simple_key(self, temp_config_file):
        """測試簡單鍵獲取"""
        loader = ConfigLoader(config_path=temp_config_file)

        paths = loader.get('paths')
        assert paths is not None
        assert isinstance(paths, dict)
        assert 'data_root' in paths

    def test_get_nested_key_with_dot_notation(self, temp_config_file):
        """測試點符號嵌套鍵"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 測試兩層嵌套
        data_root = loader.get('paths.data_root')
        assert data_root == '/data'

        # 測試三層嵌套
        recency_weight = loader.get('analysis.rfm.parameters.recency_weight')
        assert recency_weight == 0.3

    def test_get_with_default_value(self, temp_config_file):
        """測試默認值"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 測試不存在的鍵返回默認值
        value = loader.get('non.existent.key', default='default_value')
        assert value == 'default_value'

        # 測試不存在的鍵返回自定義默認值
        value = loader.get('missing_key', default={'custom': 'default'})
        assert value == {'custom': 'default'}

    def test_get_missing_key_returns_none(self, temp_config_file):
        """測試缺失鍵返回 None"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 未提供默認值時返回 None
        value = loader.get('non_existent_key')
        assert value is None

        # 嵌套不存在的鍵
        value = loader.get('paths.non_existent.nested')
        assert value is None

    def test_get_with_various_types(self, temp_config_file):
        """測試獲取各種類型的值"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 字符串
        assert isinstance(loader.get('paths.data_root'), str)

        # 布爾值
        assert isinstance(loader.get('analysis.rfm.enabled'), bool)
        assert loader.get('analysis.rfm.enabled') is True

        # 數字
        assert isinstance(loader.get('analysis.clustering.n_clusters'), int)
        assert loader.get('analysis.clustering.n_clusters') == 5

        # 浮點數
        assert isinstance(loader.get('analysis.clv.discount_rate'), float)

    def test_get_empty_key(self, temp_config_file):
        """測試空鍵"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 空字符串應該返回整個配置
        result = loader.get('')
        assert result == loader.config


class TestDatasetConfig:
    """測試數據集配置"""

    def test_get_dataset_config(self, temp_config_file):
        """測試獲取數據集配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        sales_config = loader.get_dataset_config('sales')
        assert sales_config is not None
        assert sales_config['path'] == '/data/sales.csv'
        assert sales_config['type'] == 'csv'
        assert sales_config['encoding'] == 'utf-8'

    def test_get_dataset_config_not_found(self, temp_config_file):
        """測試數據集不存在的情況"""
        loader = ConfigLoader(config_path=temp_config_file)

        with pytest.raises(ValueError) as exc_info:
            loader.get_dataset_config('non_existent_dataset')

        assert "Dataset 'non_existent_dataset' not found" in str(exc_info.value)

    def test_get_multiple_datasets(self, temp_config_file):
        """測試獲取多個數據集"""
        loader = ConfigLoader(config_path=temp_config_file)

        sales = loader.get_dataset_config('sales')
        customers = loader.get_dataset_config('customers')

        assert sales['path'] == '/data/sales.csv'
        assert customers['path'] == '/data/customers.csv'

    def test_get_dataset_with_partial_config(self, temp_config_file):
        """測試獲取部分配置的數據集"""
        loader = ConfigLoader(config_path=temp_config_file)

        # customers 數據集沒有 encoding 字段
        customers = loader.get_dataset_config('customers')
        assert 'encoding' not in customers
        assert customers['type'] == 'csv'


class TestAnalysisConfig:
    """測試分析配置"""

    def test_get_analysis_config(self, temp_config_file):
        """測試獲取分析配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        rfm_config = loader.get_analysis_config('rfm')
        assert rfm_config is not None
        assert rfm_config['enabled'] is True
        assert 'parameters' in rfm_config

    def test_get_analysis_config_not_found(self, temp_config_file):
        """測試分析類型不存在的情況"""
        loader = ConfigLoader(config_path=temp_config_file)

        with pytest.raises(ValueError) as exc_info:
            loader.get_analysis_config('non_existent_analysis')

        assert "Analysis type 'non_existent_analysis' not found" in str(exc_info.value)

    def test_get_multiple_analysis_configs(self, temp_config_file):
        """測試獲取多個分析配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        rfm = loader.get_analysis_config('rfm')
        clustering = loader.get_analysis_config('clustering')
        clv = loader.get_analysis_config('clv')

        assert rfm['enabled'] is True
        assert clustering['algorithm'] == 'kmeans'
        assert clv['enabled'] is False


class TestPathsConfig:
    """測試路徑配置"""

    def test_get_paths(self, temp_config_file):
        """測試獲取路徑配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        paths = loader.get_paths()
        assert paths is not None
        assert isinstance(paths, dict)
        assert 'data_root' in paths
        assert 'output' in paths
        assert 'logs' in paths

    def test_get_paths_returns_empty_dict_if_not_found(self):
        """測試路徑配置不存在時返回空字典"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'other_config': 'value'}, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            paths = loader.get_paths()
            assert paths == {}
        finally:
            os.unlink(temp_path)

    def test_get_specific_path(self, temp_config_file):
        """測試獲取特定路徑"""
        loader = ConfigLoader(config_path=temp_config_file)

        data_root = loader.get('paths.data_root')
        assert data_root == '/data'

        output = loader.get('paths.output')
        assert output == '/output'


class TestConfigValidation:
    """測試配置驗證"""

    def test_valid_config(self, temp_config_file):
        """測試有效配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        assert loader.config is not None
        assert isinstance(loader.config, dict)
        assert len(loader.config) > 0

    def test_invalid_yaml_format(self, invalid_yaml_file):
        """測試無效 YAML 格式"""
        with pytest.raises(yaml.YAMLError):
            ConfigLoader(config_path=invalid_yaml_file)

    def test_empty_config_file(self):
        """測試空配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            # 空 YAML 文件會被解析為 None
            assert loader.config is None
        finally:
            os.unlink(temp_path)

    def test_config_with_comments(self):
        """測試包含註釋的配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
# 這是註釋
paths:
  data_root: /data  # 數據根目錄
  output: /output
# 另一個註釋
datasets:
  test:
    path: /test.csv
""")
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            assert loader.get('paths.data_root') == '/data'
            assert loader.get('paths.output') == '/output'
            assert loader.get('datasets.test.path') == '/test.csv'
        finally:
            os.unlink(temp_path)


class TestConfigReload:
    """測試配置重載"""

    def test_reload_config(self, temp_config_file):
        """測試重新加載配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        original_data_root = loader.get('paths.data_root')
        assert original_data_root == '/data'

        # 修改配置文件
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'paths': {
                    'data_root': '/new_data',
                    'output': '/output'
                }
            }, f)

        # 重新加載
        loader.reload()

        new_data_root = loader.get('paths.data_root')
        assert new_data_root == '/new_data'

    def test_reload_after_file_modification(self, temp_config_file):
        """測試文件修改後重載"""
        loader = ConfigLoader(config_path=temp_config_file)

        assert 'sales' in loader.get('datasets', {})

        # 修改配置
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump({
                'datasets': {
                    'new_dataset': {
                        'path': '/new.csv'
                    }
                }
            }, f)

        loader.reload()

        datasets = loader.get('datasets', {})
        assert 'new_dataset' in datasets
        assert 'sales' not in datasets

    def test_reload_with_invalid_config(self, temp_config_file):
        """測試重載無效配置"""
        loader = ConfigLoader(config_path=temp_config_file)

        # 確保初始配置有效
        assert loader.get('paths') is not None

        # 寫入無效 YAML
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: [content")

        # 重載應該拋出異常
        with pytest.raises(yaml.YAMLError):
            loader.reload()


class TestConfigRepr:
    """測試字符串表示"""

    def test_repr(self, temp_config_file):
        """測試 __repr__ 方法"""
        loader = ConfigLoader(config_path=temp_config_file)

        repr_str = repr(loader)
        assert 'ConfigLoader' in repr_str
        assert 'config_path' in repr_str
        assert temp_config_file in repr_str

    def test_repr_with_default_path(self):
        """測試默認路徑的字符串表示"""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='paths:\n  data: /data')):
                loader = ConfigLoader()

                repr_str = repr(loader)
                assert 'ConfigLoader' in repr_str
                assert 'config.yaml' in repr_str


class TestEdgeCases:
    """測試邊界情況"""

    def test_config_with_null_values(self):
        """測試包含 null 值的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump({
                'paths': {
                    'data_root': None,
                    'output': '/output'
                }
            }, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            assert loader.get('paths.data_root') is None
            assert loader.get('paths.output') == '/output'
        finally:
            os.unlink(temp_path)

    def test_config_with_list_values(self):
        """測試包含列表值的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump({
                'features': ['feature1', 'feature2', 'feature3'],
                'nested': {
                    'items': [1, 2, 3]
                }
            }, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            features = loader.get('features')
            assert isinstance(features, list)
            assert len(features) == 3
            assert features[0] == 'feature1'

            items = loader.get('nested.items')
            assert items == [1, 2, 3]
        finally:
            os.unlink(temp_path)

    def test_config_with_deep_nesting(self):
        """測試深度嵌套的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump({
                'level1': {
                    'level2': {
                        'level3': {
                            'level4': {
                                'level5': 'deep_value'
                            }
                        }
                    }
                }
            }, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            value = loader.get('level1.level2.level3.level4.level5')
            assert value == 'deep_value'
        finally:
            os.unlink(temp_path)

    def test_get_with_numeric_keys_in_dict(self):
        """測試包含數字鍵的字典"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump({
                'config': {
                    '2024': 'year_value',
                    'name': 'test'
                }
            }, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            value = loader.get('config.2024')
            assert value == 'year_value'
        finally:
            os.unlink(temp_path)

    def test_config_with_special_characters(self):
        """測試包含特殊字符的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            yaml.dump({
                'message': 'Hello, 世界! 🌍',
                'path': 'C:\\Users\\測試\\data',
                'special': '@#$%^&*()'
            }, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=temp_path)
            assert loader.get('message') == 'Hello, 世界! 🌍'
            assert loader.get('path') == 'C:\\Users\\測試\\data'
            assert loader.get('special') == '@#$%^&*()'
        finally:
            os.unlink(temp_path)

    def test_path_object_handling(self, temp_config_file):
        """測試 Path 對象處理"""
        # 使用 Path 對象初始化
        loader = ConfigLoader(config_path=Path(temp_config_file))
        assert loader.config_path == Path(temp_config_file)

        # 使用字符串初始化
        loader2 = ConfigLoader(config_path=str(temp_config_file))
        assert loader2.config_path == Path(temp_config_file)
