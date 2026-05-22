"""集成測試 - 測試完整工作流"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data_analysis_chatbots.data_loader import DataLoader
from data_analysis_chatbots.preprocessing import TextCleaner, DataValidator
from data_analysis_chatbots.clustering import KMeansClusterer, RFMAnalyzer
from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager


class TestEndToEndWorkflow:
    """端到端工作流測試"""

    @pytest.fixture
    def sample_customer_transaction_data(self):
        """創建完整的客戶交易數據集"""
        np.random.seed(42)
        end_date = datetime(2024, 11, 1)

        # 生成100個客戶的1000筆交易
        transactions = []
        for _ in range(1000):
            customer_id = f'CUST{np.random.randint(1, 101):03d}'
            days_ago = np.random.randint(0, 365)
            transaction_date = end_date - timedelta(days=days_ago)
            amount = np.random.uniform(10, 1000)
            product = np.random.choice(['A', 'B', 'C', 'D'])

            transactions.append({
                'CustomerID': customer_id,
                'TransactionDate': transaction_date,
                'Amount': amount,
                'Product': product
            })

        return pd.DataFrame(transactions)

    @pytest.mark.integration
    def test_complete_rfm_to_campaign_workflow(self, sample_customer_transaction_data):
        """
        測試完整工作流：
        1. 數據驗證
        2. RFM分析
        3. CLV預測
        4. 客戶分群
        5. 營銷活動創建
        """
        # 步驟1: 數據驗證
        validator = DataValidator(sample_customer_transaction_data)
        report = validator.generate_report()

        assert report['total_rows'] > 0
        assert 'CustomerID' in sample_customer_transaction_data.columns

        # 步驟2: RFM分析
        rfm_analyzer = RFMAnalyzer(
            df=sample_customer_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        rfm_data = rfm_analyzer.calculate_rfm()
        assert len(rfm_data) > 0
        assert all(col in rfm_data.columns for col in ['Recency', 'Frequency', 'Monetary'])

        # 步驟3: 客戶分群
        segmented_data = rfm_analyzer.segment_customers()
        assert 'Segment' in segmented_data.columns

        # 步驟4: CLV預測
        clv_predictor = CLVPredictor(discount_rate=0.1)
        clv_data = clv_predictor.calculate_rfm_based_clv(rfm_data)

        assert 'Predicted_CLV' in clv_data.columns
        assert all(clv_data['Predicted_CLV'] > 0)

        # 步驟5: 合併數據並創建營銷活動
        customer_summary = segmented_data.merge(
            clv_data[['Predicted_CLV']],
            left_index=True,
            right_index=True
        )

        campaign_manager = CampaignManager(customer_summary.reset_index(), 'CustomerID')

        # 創建高價值客戶活動
        high_value_campaign = campaign_manager.create_campaign(
            campaign_name='High Value VIP',
            target_criteria={
                'Predicted_CLV': {'min': customer_summary['Predicted_CLV'].quantile(0.75)}
            }
        )

        assert len(high_value_campaign) > 0

        # 計算ROI
        roi = campaign_manager.calculate_campaign_roi(
            campaign_name='High Value VIP',
            cost_per_customer=100,
            conversion_rate=0.2,
            avg_revenue_per_conversion=1000
        )

        assert 'roi_percentage' in roi
        assert roi['total_cost'] > 0

    @pytest.mark.integration
    def test_clustering_to_campaign_workflow(self):
        """
        測試聚類到營銷活動工作流：
        1. K-means聚類
        2. 基於聚類創建營銷活動
        """
        # 創建客戶數據
        np.random.seed(42)
        customer_data = pd.DataFrame({
            'CustomerID': [f'CUST{i:03d}' for i in range(1, 201)],
            'Age': np.random.randint(18, 70, 200),
            'Income': np.random.randint(20, 150, 200),
            'Spending': np.random.randint(1, 100, 200)
        })

        # 步驟1: K-means聚類
        clusterer = KMeansClusterer(n_clusters=4, random_state=42)
        labels = clusterer.fit_predict(
            customer_data,
            ['Age', 'Income', 'Spending']
        )

        customer_data['Cluster'] = labels

        # 驗證聚類
        assert len(customer_data['Cluster'].unique()) == 4
        metrics = clusterer.evaluate_clustering()
        assert 'silhouette_score' in metrics

        # 步驟2: 分析每個聚類的特徵
        cluster_summary = customer_data.groupby('Cluster').agg({
            'Age': 'mean',
            'Income': 'mean',
            'Spending': 'mean',
            'CustomerID': 'count'
        }).round(2)

        assert len(cluster_summary) == 4

        # 步驟3: 為每個聚類創建定制化活動
        campaign_manager = CampaignManager(customer_data, 'CustomerID')

        for cluster_id in range(4):
            campaign_manager.create_campaign(
                campaign_name=f'Cluster_{cluster_id}_Campaign',
                target_criteria={'Cluster': {'exact': cluster_id}}
            )

        summary = campaign_manager.get_campaign_summary()
        assert len(summary) == 4

    @pytest.mark.integration
    def test_data_quality_improvement_workflow(self):
        """
        測試數據質量改進工作流：
        1. 檢測數據問題
        2. 清洗數據
        3. 驗證改進
        """
        # 創建有問題的數據
        dirty_data = pd.DataFrame({
            'CustomerID': [1, 2, 3, 4, 5, 5],  # 有重複
            'Name': ['John', 'Jane', None, 'Bob', 'Alice', 'Alice'],  # 有缺失
            'Email': [
                'john@example.com',
                'JANE@EXAMPLE.COM',  # 需要標準化
                'invalid',  # 無效
                'bob@example.com',
                'alice@example.com',
                'alice@example.com'
            ],
            'Age': [25, 30, np.nan, 40, 35, 35],  # 有缺失
            'Income': [50000, 60000, 70000, -1000, 80000, 80000]  # 有異常值
        })

        # 步驟1: 初始驗證
        validator = DataValidator(dirty_data)
        initial_report = validator.generate_report()

        # generate_report()['missing_values'] is a per-column dict {col: count}
        # (post-PR #30). Sum across columns to get total missing-cell count.
        initial_missing_total = sum(initial_report['missing_values'].values())

        assert initial_report['duplicate_rows'] > 0
        assert initial_missing_total > 0

        # 步驟2: 清洗數據
        # 移除重複
        cleaned_data = validator.remove_duplicates()
        assert len(cleaned_data) < len(dirty_data)

        # 處理缺失值
        validator_cleaned = DataValidator(cleaned_data)
        cleaned_data = validator_cleaned.fix_missing_values(strategy='drop')

        # 步驟3: 驗證改進
        final_validator = DataValidator(cleaned_data)
        final_report = final_validator.generate_report()
        final_missing_total = sum(final_report['missing_values'].values())

        assert final_report['duplicate_rows'] == 0
        assert final_missing_total < initial_missing_total

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_pipeline_performance(self, sample_customer_transaction_data):
        """測試完整管道的性能"""
        import time

        start_time = time.time()

        # 執行完整分析管道
        validator = DataValidator(sample_customer_transaction_data)
        validator.generate_report()

        rfm_analyzer = RFMAnalyzer(
            df=sample_customer_transaction_data,
            customer_id_col='CustomerID',
            date_col='TransactionDate',
            amount_col='Amount'
        )

        rfm_data = rfm_analyzer.calculate_rfm()
        segmented = rfm_analyzer.segment_customers()

        clv_predictor = CLVPredictor()
        clv_data = clv_predictor.calculate_rfm_based_clv(rfm_data)

        end_time = time.time()
        execution_time = end_time - start_time

        # 應該在合理時間內完成（5秒）
        assert execution_time < 5.0

        # 驗證結果
        assert len(segmented) > 0
        assert len(clv_data) > 0


class TestErrorHandling:
    """錯誤處理測試"""

    def test_invalid_input_handling(self):
        """測試無效輸入處理"""
        with pytest.raises(Exception):
            # 空DataFrame
            validator = DataValidator(pd.DataFrame())
            validator.check_missing_values()

    def test_missing_columns_handling(self):
        """測試缺少必需列的處理"""
        df = pd.DataFrame({'A': [1, 2, 3]})

        with pytest.raises((KeyError, ValueError, Exception)):
            rfm_analyzer = RFMAnalyzer(
                df=df,
                customer_id_col='NonExistent',
                date_col='AlsoNonExistent',
                amount_col='StillNonExistent'
            )
            rfm_analyzer.calculate_rfm()

    def test_empty_dataframe_handling(self):
        """測試空DataFrame處理"""
        empty_df = pd.DataFrame(columns=['A', 'B', 'C'])

        validator = DataValidator(empty_df)
        report = validator.generate_report()

        assert report['total_rows'] == 0

    def test_negative_values_in_clustering(self):
        """測試聚類中的負值處理"""
        df = pd.DataFrame({
            'Feature1': [-1, -2, -3],
            'Feature2': [1, 2, 3]
        })

        # 應該能處理負值
        clusterer = KMeansClusterer(n_clusters=2)
        labels = clusterer.fit_predict(df, ['Feature1', 'Feature2'])

        assert len(labels) == 3
