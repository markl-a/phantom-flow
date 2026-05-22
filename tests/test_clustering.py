"""測試聚類模塊"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data_analysis_chatbots.clustering import KMeansClusterer, RFMAnalyzer


class TestKMeansClusterer:
    """測試K-Means聚類器"""

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100),
            'Feature3': np.random.randn(100)
        })

    def test_initialization(self):
        """測試初始化"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        assert clusterer.n_clusters == 3
        assert clusterer.random_state == 42

    def test_fit_predict(self, sample_data):
        """測試擬合和預測"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        labels = clusterer.fit_predict(
            sample_data,
            ['Feature1', 'Feature2', 'Feature3']
        )

        assert len(labels) == len(sample_data)
        assert set(labels) == {0, 1, 2}  # 3個聚類

    def test_get_cluster_centers(self, sample_data):
        """測試獲取聚類中心"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        clusterer.fit(sample_data, ['Feature1', 'Feature2', 'Feature3'])

        centers = clusterer.get_cluster_centers()
        assert len(centers) == 3
        assert list(centers.columns) == ['Feature1', 'Feature2', 'Feature3']

    def test_evaluate_clustering(self, sample_data):
        """測試聚類評估"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        clusterer.fit(sample_data, ['Feature1', 'Feature2', 'Feature3'])

        metrics = clusterer.evaluate_clustering()
        assert 'inertia' in metrics
        assert 'silhouette_score' in metrics
        assert metrics['n_clusters'] == 3

    def test_find_optimal_clusters(self, sample_data):
        """測試尋找最佳聚類數"""
        clusterer = KMeansClusterer()
        results = clusterer.find_optimal_clusters(
            sample_data,
            ['Feature1', 'Feature2', 'Feature3'],
            k_range=[2, 3, 4]
        )

        assert len(results) == 3
        assert 2 in results
        assert 'inertia' in results[2]
        assert 'silhouette_score' in results[2]


class TestRFMAnalyzer:
    """測試RFM分析器"""

    @pytest.fixture
    def sample_transaction_data(self):
        """創建範例交易數據"""
        np.random.seed(42)
        end_date = datetime(2024, 11, 1)

        transactions = []
        for _ in range(1000):
            customer_id = f'CUST{np.random.randint(1, 101):03d}'
            days_ago = np.random.randint(0, 365)
            transaction_date = end_date - timedelta(days=days_ago)
            amount = np.random.uniform(10, 1000)

            transactions.append({
                'CustomerID': customer_id,
                'TransactionDate': transaction_date,
                'Amount': amount
            })

        return pd.DataFrame(transactions)

    def test_initialization(self, sample_transaction_data):
        """測試初始化"""
        analyzer = RFMAnalyzer(
            df=sample_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        assert analyzer.customer_id_col == 'CustomerID'
        assert analyzer.date_col == 'TransactionDate'
        assert analyzer.amount_col == 'Amount'

    def test_calculate_rfm(self, sample_transaction_data):
        """測試RFM計算"""
        analyzer = RFMAnalyzer(
            df=sample_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        rfm = analyzer.calculate_rfm()

        assert 'Recency' in rfm.columns
        assert 'Frequency' in rfm.columns
        assert 'Monetary' in rfm.columns
        assert len(rfm) > 0
        assert all(rfm['Recency'] >= 0)
        assert all(rfm['Frequency'] > 0)
        assert all(rfm['Monetary'] > 0)

    def test_assign_rfm_scores(self, sample_transaction_data):
        """測試RFM分數分配"""
        analyzer = RFMAnalyzer(
            df=sample_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        rfm_scores = analyzer.assign_rfm_scores()

        assert 'R_Score' in rfm_scores.columns
        assert 'F_Score' in rfm_scores.columns
        assert 'M_Score' in rfm_scores.columns
        assert 'RFM_Score' in rfm_scores.columns

        # 分數應該在1-5之間
        assert all(rfm_scores['R_Score'].between(1, 5))
        assert all(rfm_scores['F_Score'].between(1, 5))
        assert all(rfm_scores['M_Score'].between(1, 5))

    def test_segment_customers(self, sample_transaction_data):
        """測試客戶分群"""
        analyzer = RFMAnalyzer(
            df=sample_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        segments = analyzer.segment_customers()

        assert 'Segment' in segments.columns
        assert len(segments) > 0

        # 檢查是否有有效的分群
        valid_segments = [
            'Champions', 'Loyal Customers', 'Potential Loyalists',
            'Recent Customers', 'Promising', 'Need Attention',
            'About to Sleep', 'At Risk', "Can't Lose Them",
            'Hibernating', 'Lost'
        ]
        assert all(seg in valid_segments for seg in segments['Segment'].unique())

    def test_get_segment_summary(self, sample_transaction_data):
        """測試分群摘要"""
        analyzer = RFMAnalyzer(
            df=sample_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        analyzer.segment_customers()
        summary = analyzer.get_segment_summary()

        assert 'Segment' in summary.columns
        assert 'Customer_Count' in summary.columns
        assert 'Percentage' in summary.columns
        assert len(summary) > 0
