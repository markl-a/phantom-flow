"""測試高級聚類算法(DBSCAN, GMM, Hierarchical)"""

import pytest
import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs, make_moons

from data_analysis_chatbots.clustering import (
    DBSCANClusterer,
    GMMClusterer,
    HierarchicalClusterer
)
from data_analysis_chatbots.exceptions import (
    ClusteringError,
    ValidationError
)


# === 測試數據生成 ===

@pytest.fixture
def sample_blob_data():
    """生成簡單的blob數據"""
    X, y = make_blobs(n_samples=300, centers=3, random_state=42)
    df = pd.DataFrame(X, columns=['feature1', 'feature2'])
    return df


@pytest.fixture
def sample_moon_data():
    """生成月牙形數據(適合DBSCAN)"""
    X, y = make_moons(n_samples=200, noise=0.05, random_state=42)
    df = pd.DataFrame(X, columns=['feature1', 'feature2'])
    return df


@pytest.fixture
def empty_dataframe():
    """空DataFrame"""
    return pd.DataFrame()


# === DBSCAN測試 ===

class TestDBSCANClusterer:
    """測試DBSCAN聚類器"""

    def test_initialization(self):
        """測試初始化"""
        clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        assert clusterer.eps == 0.5
        assert clusterer.min_samples == 5
        assert clusterer.model is None

    def test_invalid_eps(self):
        """測試無效的eps參數"""
        with pytest.raises(ClusteringError):
            DBSCANClusterer(eps=-1)

    def test_invalid_min_samples(self):
        """測試無效的min_samples參數"""
        with pytest.raises(ClusteringError):
            DBSCANClusterer(min_samples=0)

    def test_fit(self, sample_blob_data):
        """測試訓練"""
        clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        assert clusterer.model is not None
        assert clusterer.labels_ is not None
        assert len(clusterer.labels_) == len(sample_blob_data)
        assert clusterer.n_clusters_ >= 0

    def test_fit_predict(self, sample_blob_data):
        """測試fit_predict"""
        clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        labels = clusterer.fit_predict(sample_blob_data, ['feature1', 'feature2'])

        assert len(labels) == len(sample_blob_data)
        assert isinstance(labels, np.ndarray)

    def test_moon_data(self, sample_moon_data):
        """測試月牙形數據(DBSCAN應該表現良好)"""
        clusterer = DBSCANClusterer(eps=0.3, min_samples=10)
        labels = clusterer.fit_predict(sample_moon_data, ['feature1', 'feature2'])

        # DBSCAN應該能發現2個月牙形聚類
        assert clusterer.n_clusters_ >= 1

    def test_empty_dataframe(self, empty_dataframe):
        """測試空DataFrame"""
        clusterer = DBSCANClusterer()
        with pytest.raises(ValidationError):
            clusterer.fit(empty_dataframe, ['feature1', 'feature2'])

    def test_missing_columns(self, sample_blob_data):
        """測試缺失列"""
        clusterer = DBSCANClusterer()
        with pytest.raises(ValidationError):
            clusterer.fit(sample_blob_data, ['nonexistent_column'])

    def test_evaluate_clustering(self, sample_blob_data):
        """測試聚類評估"""
        clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        metrics = clusterer.evaluate_clustering(sample_blob_data, ['feature1', 'feature2'])

        assert 'n_clusters' in metrics
        assert 'n_noise' in metrics
        assert 'noise_percentage' in metrics
        assert metrics['n_samples'] == len(sample_blob_data)

    def test_get_cluster_summary(self, sample_blob_data):
        """測試聚類摘要"""
        clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        summary = clusterer.get_cluster_summary(sample_blob_data, ['feature1', 'feature2'])

        assert isinstance(summary, pd.DataFrame)
        assert 'Cluster' in summary.columns
        assert 'Size' in summary.columns

    def test_find_optimal_eps(self, sample_blob_data):
        """測試尋找最優eps"""
        clusterer = DBSCANClusterer(min_samples=5)
        eps, distances = clusterer.find_optimal_eps(
            sample_blob_data,
            ['feature1', 'feature2']
        )

        assert isinstance(eps, float)
        assert eps > 0
        assert len(distances) == len(sample_blob_data)


# === GMM測試 ===

class TestGMMClusterer:
    """測試GMM聚類器"""

    def test_initialization(self):
        """測試初始化"""
        clusterer = GMMClusterer(n_components=3)
        assert clusterer.n_components == 3
        assert clusterer.model is None

    def test_invalid_n_components(self):
        """測試無效的聚類數"""
        with pytest.raises(ClusteringError):
            GMMClusterer(n_components=0)

    def test_invalid_covariance_type(self):
        """測試無效的協方差類型"""
        with pytest.raises(ClusteringError):
            GMMClusterer(covariance_type='invalid')

    def test_fit(self, sample_blob_data):
        """測試訓練"""
        clusterer = GMMClusterer(n_components=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        assert clusterer.model is not None
        assert clusterer.labels_ is not None
        assert clusterer.probabilities_ is not None
        assert clusterer.probabilities_.shape == (len(sample_blob_data), 3)

    def test_fit_predict(self, sample_blob_data):
        """測試fit_predict"""
        clusterer = GMMClusterer(n_components=3)
        labels = clusterer.fit_predict(sample_blob_data, ['feature1', 'feature2'])

        assert len(labels) == len(sample_blob_data)
        assert labels.max() < 3

    def test_predict_proba(self, sample_blob_data):
        """測試概率預測"""
        clusterer = GMMClusterer(n_components=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        probs = clusterer.predict_proba(sample_blob_data, ['feature1', 'feature2'])

        assert probs.shape == (len(sample_blob_data), 3)
        assert np.allclose(probs.sum(axis=1), 1.0)  # 概率和為1
        assert (probs >= 0).all() and (probs <= 1).all()  # 概率在0-1之間

    def test_evaluate_clustering(self, sample_blob_data):
        """測試聚類評估"""
        clusterer = GMMClusterer(n_components=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        metrics = clusterer.evaluate_clustering(sample_blob_data, ['feature1', 'feature2'])

        assert 'bic' in metrics
        assert 'aic' in metrics
        assert 'silhouette_score' in metrics
        assert 'converged' in metrics

    def test_get_uncertain_samples(self, sample_blob_data):
        """測試獲取不確定樣本"""
        clusterer = GMMClusterer(n_components=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        uncertain = clusterer.get_uncertain_samples(
            sample_blob_data,
            ['feature1', 'feature2'],
            threshold=0.7
        )

        assert isinstance(uncertain, pd.DataFrame)
        assert 'Max_Probability' in uncertain.columns
        if len(uncertain) > 0:
            assert (uncertain['Max_Probability'] < 0.7).all()

    def test_find_optimal_components(self, sample_blob_data):
        """測試尋找最優聚類數"""
        clusterer = GMMClusterer()
        optimal_n, scores = clusterer.find_optimal_components(
            sample_blob_data,
            ['feature1', 'feature2'],
            max_components=5
        )

        assert isinstance(optimal_n, int)
        assert 1 <= optimal_n <= 5
        assert len(scores) > 0


# === Hierarchical測試 ===

class TestHierarchicalClusterer:
    """測試層次聚類器"""

    def test_initialization(self):
        """測試初始化"""
        clusterer = HierarchicalClusterer(n_clusters=3, linkage='ward')
        assert clusterer.n_clusters == 3
        assert clusterer.linkage == 'ward'
        assert clusterer.model is None

    def test_invalid_n_clusters(self):
        """測試無效的聚類數"""
        with pytest.raises(ClusteringError):
            HierarchicalClusterer(n_clusters=0)

    def test_invalid_linkage(self):
        """測試無效的連接方法"""
        with pytest.raises(ClusteringError):
            HierarchicalClusterer(linkage='invalid')

    def test_fit(self, sample_blob_data):
        """測試訓練"""
        clusterer = HierarchicalClusterer(n_clusters=3, linkage='ward')
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        assert clusterer.model is not None
        assert clusterer.labels_ is not None
        assert clusterer.linkage_matrix_ is not None
        assert len(clusterer.labels_) == len(sample_blob_data)

    def test_fit_predict(self, sample_blob_data):
        """測試fit_predict"""
        clusterer = HierarchicalClusterer(n_clusters=3)
        labels = clusterer.fit_predict(sample_blob_data, ['feature1', 'feature2'])

        assert len(labels) == len(sample_blob_data)
        assert len(np.unique(labels)) == 3

    def test_different_linkages(self, sample_blob_data):
        """測試不同的連接方法"""
        for linkage in ['ward', 'complete', 'average', 'single']:
            clusterer = HierarchicalClusterer(n_clusters=3, linkage=linkage)
            labels = clusterer.fit_predict(sample_blob_data, ['feature1', 'feature2'])
            assert len(labels) == len(sample_blob_data)

    def test_evaluate_clustering(self, sample_blob_data):
        """測試聚類評估"""
        clusterer = HierarchicalClusterer(n_clusters=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        metrics = clusterer.evaluate_clustering(sample_blob_data, ['feature1', 'feature2'])

        assert 'n_clusters' in metrics
        assert 'silhouette_score' in metrics
        assert 'cluster_distribution' in metrics

    def test_get_cluster_summary(self, sample_blob_data):
        """測試聚類摘要"""
        clusterer = HierarchicalClusterer(n_clusters=3)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        summary = clusterer.get_cluster_summary(sample_blob_data, ['feature1', 'feature2'])

        assert isinstance(summary, pd.DataFrame)
        assert len(summary) == 3
        assert 'Cluster' in summary.columns

    def test_cut_tree(self, sample_blob_data):
        """測試切割樹"""
        clusterer = HierarchicalClusterer(n_clusters=2)
        clusterer.fit(sample_blob_data, ['feature1', 'feature2'])

        # 重新切割為4個聚類
        new_labels = clusterer.cut_tree(4)

        assert len(new_labels) == len(sample_blob_data)
        assert len(np.unique(new_labels)) == 4
        assert clusterer.n_clusters == 4

    def test_find_optimal_clusters(self, sample_blob_data):
        """測試尋找最優聚類數"""
        clusterer = HierarchicalClusterer()
        optimal_n, scores = clusterer.find_optimal_clusters(
            sample_blob_data,
            ['feature1', 'feature2'],
            max_clusters=5
        )

        assert isinstance(optimal_n, int)
        assert 2 <= optimal_n <= 5
        assert len(scores) > 0


# === 比較測試 ===

class TestClustererComparison:
    """比較不同聚類算法的表現"""

    def test_all_clusterers_on_blobs(self, sample_blob_data):
        """在blob數據上測試所有聚類器"""
        features = ['feature1', 'feature2']

        # K-Means已在其他測試中覆蓋,這裡測試新算法
        dbscan = DBSCANClusterer(eps=0.5, min_samples=5)
        dbscan_labels = dbscan.fit_predict(sample_blob_data, features)

        gmm = GMMClusterer(n_components=3)
        gmm_labels = gmm.fit_predict(sample_blob_data, features)

        hierarchical = HierarchicalClusterer(n_clusters=3)
        hierarchical_labels = hierarchical.fit_predict(sample_blob_data, features)

        # 所有算法都應該成功運行
        assert len(dbscan_labels) == len(sample_blob_data)
        assert len(gmm_labels) == len(sample_blob_data)
        assert len(hierarchical_labels) == len(sample_blob_data)

    def test_normalization_effect(self, sample_blob_data):
        """測試標準化的影響"""
        features = ['feature1', 'feature2']

        # 有標準化
        gmm_norm = GMMClusterer(n_components=3, normalize=True)
        gmm_norm.fit(sample_blob_data, features)

        # 無標準化
        gmm_no_norm = GMMClusterer(n_components=3, normalize=False)
        gmm_no_norm.fit(sample_blob_data, features)

        # 兩者都應該成功
        assert gmm_norm.model is not None
        assert gmm_no_norm.model is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
