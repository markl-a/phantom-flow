"""測試聚類器工廠模塊"""

import pytest
import pandas as pd
import numpy as np

from data_analysis_chatbots.clustering import ClustererFactory
from data_analysis_chatbots.clustering.base import BaseClusterer
from data_analysis_chatbots.clustering.kmeans_clusterer import KMeansClusterer
from data_analysis_chatbots.clustering.dbscan_clusterer import DBSCANClusterer
from data_analysis_chatbots.clustering.gmm_clusterer import GMMClusterer
from data_analysis_chatbots.clustering.hierarchical_clusterer import HierarchicalClusterer


class TestClustererFactory:
    """測試 ClustererFactory 類"""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """每次測試前重置註冊表"""
        # 清空註冊表以確保測試獨立性
        ClustererFactory._registry = {}
        yield
        # 測試後清空註冊表
        ClustererFactory._registry = {}

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100),
            'Feature3': np.random.randn(100)
        })

    def test_create_kmeans(self):
        """測試創建 KMeans 聚類器"""
        clusterer = ClustererFactory.create('kmeans', n_clusters=3)

        assert clusterer is not None
        assert isinstance(clusterer, KMeansClusterer)
        assert clusterer.n_clusters == 3

    def test_create_kmeans_case_insensitive(self):
        """測試創建 KMeans 聚類器（大小寫不敏感）"""
        clusterer1 = ClustererFactory.create('KMeans', n_clusters=4)
        clusterer2 = ClustererFactory.create('KMEANS', n_clusters=4)
        clusterer3 = ClustererFactory.create('kmeans', n_clusters=4)

        assert isinstance(clusterer1, KMeansClusterer)
        assert isinstance(clusterer2, KMeansClusterer)
        assert isinstance(clusterer3, KMeansClusterer)

    def test_create_dbscan(self):
        """測試創建 DBSCAN 聚類器"""
        clusterer = ClustererFactory.create('dbscan', eps=0.5, min_samples=5)

        assert clusterer is not None
        assert isinstance(clusterer, DBSCANClusterer)
        assert clusterer.eps == 0.5
        assert clusterer.min_samples == 5

    def test_create_gmm(self):
        """測試創建 GMM 聚類器"""
        clusterer = ClustererFactory.create('gmm', n_components=4)

        assert clusterer is not None
        assert isinstance(clusterer, GMMClusterer)
        assert clusterer.n_components == 4

    def test_create_hierarchical(self):
        """測試創建 Hierarchical 聚類器"""
        clusterer = ClustererFactory.create('hierarchical', n_clusters=5)

        assert clusterer is not None
        assert isinstance(clusterer, HierarchicalClusterer)
        assert clusterer.n_clusters == 5

    def test_create_with_default_params(self):
        """測試使用默認參數創建聚類器"""
        clusterer = ClustererFactory.create('kmeans')

        assert clusterer is not None
        assert isinstance(clusterer, KMeansClusterer)
        # 應該使用 KMeansClusterer 的默認參數
        assert clusterer.n_clusters == 5  # KMeansClusterer 默認值

    def test_create_unknown_algorithm(self):
        """測試創建未知算法時拋出錯誤"""
        with pytest.raises(ValueError) as exc_info:
            ClustererFactory.create('unknown_algorithm')

        assert "Unknown algorithm" in str(exc_info.value)
        assert "unknown_algorithm" in str(exc_info.value)
        assert "Available" in str(exc_info.value)

    def test_create_empty_algorithm_name(self):
        """測試空算法名稱"""
        with pytest.raises(ValueError) as exc_info:
            ClustererFactory.create('')

        # 驗證錯誤訊息包含適當的提示
        error_msg = str(exc_info.value)
        assert "non-empty string" in error_msg or "Unknown algorithm" in error_msg

    def test_register_custom_algorithm(self):
        """測試註冊自定義聚類算法"""
        # 創建一個簡單的自定義聚類器
        class CustomClusterer(BaseClusterer):
            """自定義聚類器用於測試"""

            def __init__(self, param1=10, **kwargs):
                super().__init__(**kwargs)
                self.param1 = param1

            def fit(self, df, feature_columns):
                self.feature_columns = feature_columns
                self._X_fitted = df[feature_columns].values
                self.labels_ = np.zeros(len(df), dtype=int)
                return self

            def predict(self, df, feature_columns):
                return np.zeros(len(df), dtype=int)

        # 註冊自定義算法
        ClustererFactory.register('custom', CustomClusterer)

        # 驗證已註冊
        algorithms = ClustererFactory.list_algorithms()
        assert 'custom' in algorithms

        # 創建自定義聚類器實例
        clusterer = ClustererFactory.create('custom', param1=20)
        assert isinstance(clusterer, CustomClusterer)
        assert clusterer.param1 == 20

    def test_register_override_existing_algorithm(self):
        """測試覆蓋已存在的算法"""
        # 創建一個自定義聚類器
        class NewKMeans(BaseClusterer):
            """新的 KMeans 實現"""

            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            def fit(self, df, feature_columns):
                self.labels_ = np.zeros(len(df), dtype=int)
                return self

            def predict(self, df, feature_columns):
                return np.zeros(len(df), dtype=int)

        # 覆蓋現有的 kmeans
        ClustererFactory.register('kmeans', NewKMeans)

        # 創建聚類器應該是新的類型
        clusterer = ClustererFactory.create('kmeans')
        assert isinstance(clusterer, NewKMeans)
        assert not isinstance(clusterer, KMeansClusterer)

    def test_list_algorithms(self):
        """測試列出所有可用算法"""
        algorithms = ClustererFactory.list_algorithms()

        assert isinstance(algorithms, list)
        assert len(algorithms) == 4
        assert 'kmeans' in algorithms
        assert 'dbscan' in algorithms
        assert 'gmm' in algorithms
        assert 'hierarchical' in algorithms

    def test_list_algorithms_after_registration(self):
        """測試註冊後列出算法"""
        # 創建自定義聚類器
        class CustomClusterer(BaseClusterer):
            def fit(self, df, feature_columns):
                return self

            def predict(self, df, feature_columns):
                return np.zeros(len(df), dtype=int)

        # 註冊兩個新算法
        ClustererFactory.register('custom1', CustomClusterer)
        ClustererFactory.register('custom2', CustomClusterer)

        algorithms = ClustererFactory.list_algorithms()

        assert len(algorithms) == 6  # 4個原始 + 2個自定義
        assert 'custom1' in algorithms
        assert 'custom2' in algorithms

    def test_get_algorithm_info_kmeans(self):
        """測試獲取 KMeans 算法信息"""
        info = ClustererFactory.get_algorithm_info('kmeans')

        assert info is not None
        assert isinstance(info, dict)
        assert info['name'] == 'kmeans'
        assert info['class'] == 'KMeansClusterer'
        assert 'doc' in info
        assert info['doc'] is not None

    def test_get_algorithm_info_dbscan(self):
        """測試獲取 DBSCAN 算法信息"""
        info = ClustererFactory.get_algorithm_info('dbscan')

        assert info is not None
        assert info['name'] == 'dbscan'
        assert info['class'] == 'DBSCANClusterer'
        assert 'doc' in info

    def test_get_algorithm_info_gmm(self):
        """測試獲取 GMM 算法信息"""
        info = ClustererFactory.get_algorithm_info('gmm')

        assert info is not None
        assert info['name'] == 'gmm'
        assert info['class'] == 'GMMClusterer'
        assert 'doc' in info

    def test_get_algorithm_info_hierarchical(self):
        """測試獲取 Hierarchical 算法信息"""
        info = ClustererFactory.get_algorithm_info('hierarchical')

        assert info is not None
        assert info['name'] == 'hierarchical'
        assert info['class'] == 'HierarchicalClusterer'
        assert 'doc' in info

    def test_get_algorithm_info_case_insensitive(self):
        """測試獲取算法信息（大小寫不敏感）"""
        info1 = ClustererFactory.get_algorithm_info('KMeans')
        info2 = ClustererFactory.get_algorithm_info('KMEANS')
        info3 = ClustererFactory.get_algorithm_info('kmeans')

        assert info1 is not None
        assert info2 is not None
        assert info3 is not None
        assert info1['class'] == info2['class'] == info3['class']

    def test_get_algorithm_info_unknown(self):
        """測試獲取未知算法信息"""
        info = ClustererFactory.get_algorithm_info('unknown_algorithm')

        assert info is None

    def test_get_algorithm_info_empty_name(self):
        """測試獲取空算法名稱的信息"""
        info = ClustererFactory.get_algorithm_info('')

        assert info is None

    def test_created_clusterer_can_fit(self, sample_data):
        """測試創建的聚類器可以正常擬合數據"""
        clusterer = ClustererFactory.create('kmeans', n_clusters=3)

        # 應該能夠正常擬合數據
        clusterer.fit(sample_data, ['Feature1', 'Feature2', 'Feature3'])

        assert clusterer.labels_ is not None
        assert len(clusterer.labels_) == len(sample_data)
        assert set(clusterer.labels_) == {0, 1, 2}

    def test_created_dbscan_can_fit(self, sample_data):
        """測試創建的 DBSCAN 聚類器可以正常擬合數據"""
        clusterer = ClustererFactory.create('dbscan', eps=0.5, min_samples=5)

        clusterer.fit(sample_data, ['Feature1', 'Feature2', 'Feature3'])

        assert clusterer.labels_ is not None
        assert len(clusterer.labels_) == len(sample_data)

    def test_multiple_instances_are_independent(self):
        """測試多個實例是獨立的"""
        clusterer1 = ClustererFactory.create('kmeans', n_clusters=3)
        clusterer2 = ClustererFactory.create('kmeans', n_clusters=5)

        assert clusterer1.n_clusters == 3
        assert clusterer2.n_clusters == 5
        assert clusterer1 is not clusterer2

    def test_registry_persistence(self):
        """測試註冊表持久性"""
        # 創建自定義聚類器
        class CustomClusterer(BaseClusterer):
            def fit(self, df, feature_columns):
                return self

            def predict(self, df, feature_columns):
                return np.zeros(len(df), dtype=int)

        # 註冊算法
        ClustererFactory.register('custom', CustomClusterer)

        # 多次創建應該都成功
        clusterer1 = ClustererFactory.create('custom')
        clusterer2 = ClustererFactory.create('custom')

        assert isinstance(clusterer1, CustomClusterer)
        assert isinstance(clusterer2, CustomClusterer)

    def test_create_with_multiple_kwargs(self):
        """測試使用多個關鍵字參數創建聚類器"""
        clusterer = ClustererFactory.create(
            'kmeans',
            n_clusters=4,
            random_state=123,
            max_iter=500,
            n_init=20,
            normalize=False
        )

        assert clusterer.n_clusters == 4
        assert clusterer.random_state == 123
        assert clusterer.max_iter == 500
        assert clusterer.n_init == 20
        assert clusterer.normalize == False

    def test_ensure_registry_called_automatically(self):
        """測試註冊表自動初始化"""
        # 第一次調用應該自動初始化註冊表
        algorithms = ClustererFactory.list_algorithms()

        assert len(algorithms) > 0
        assert 'kmeans' in algorithms

    def test_algorithm_info_contains_all_fields(self):
        """測試算法信息包含所有必需字段"""
        info = ClustererFactory.get_algorithm_info('kmeans')

        assert 'name' in info
        assert 'class' in info
        assert 'doc' in info
        assert len(info) == 3

    def test_register_with_different_case(self):
        """測試使用不同大小寫註冊算法"""
        class CustomClusterer(BaseClusterer):
            def fit(self, df, feature_columns):
                return self

            def predict(self, df, feature_columns):
                return np.zeros(len(df), dtype=int)

        # 註冊時使用大寫
        ClustererFactory.register('MyCustom', CustomClusterer)

        # 創建時應該轉換為小寫
        clusterer = ClustererFactory.create('mycustom')
        assert isinstance(clusterer, CustomClusterer)

        # 檢查算法列表
        algorithms = ClustererFactory.list_algorithms()
        assert 'mycustom' in algorithms

    def test_create_all_algorithm_types(self):
        """測試創建所有類型的聚類器"""
        algorithms = {
            'kmeans': KMeansClusterer,
            'dbscan': DBSCANClusterer,
            'gmm': GMMClusterer,
            'hierarchical': HierarchicalClusterer
        }

        for algo_name, expected_class in algorithms.items():
            clusterer = ClustererFactory.create(algo_name)
            assert isinstance(clusterer, expected_class), \
                f"Expected {expected_class.__name__} for {algo_name}"

    def test_invalid_kwargs_passed_to_create(self):
        """測試傳遞無效參數時的行為"""
        # 某些聚類器可能會拋出錯誤，某些可能會忽略
        # 這取決於具體實現，這裡測試至少不會導致工廠崩潰
        try:
            clusterer = ClustererFactory.create('kmeans', invalid_param=999)
            # 如果成功創建，參數應該被忽略
            assert clusterer is not None
        except TypeError:
            # 如果拋出 TypeError，這也是可接受的行為
            pass
