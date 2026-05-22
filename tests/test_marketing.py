"""測試營銷模塊"""

import pytest
import pandas as pd
import numpy as np

from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager


class TestCLVPredictor:
    """測試CLV預測器"""

    @pytest.fixture
    def sample_rfm_data(self):
        """創建範例RFM數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'CustomerID': [f'CUST{i:03d}' for i in range(1, 101)],
            'Recency': np.random.randint(1, 365, 100),
            'Frequency': np.random.randint(1, 50, 100),
            'Monetary': np.random.uniform(100, 10000, 100)
        })

    def test_initialization(self):
        """測試初始化"""
        predictor = CLVPredictor(discount_rate=0.1, time_horizon_years=3)
        assert predictor.discount_rate == 0.1
        assert predictor.time_horizon_years == 3

    def test_calculate_predictive_clv(self):
        """測試預測CLV計算"""
        predictor = CLVPredictor()
        clv = predictor.calculate_predictive_clv(
            avg_purchase_value=100,
            purchase_frequency=10,
            customer_lifespan_years=3
        )

        assert clv > 0
        assert isinstance(clv, float)

    def test_calculate_rfm_based_clv(self, sample_rfm_data):
        """測試基於RFM的CLV計算"""
        predictor = CLVPredictor()
        results = predictor.calculate_rfm_based_clv(sample_rfm_data)

        assert 'Predicted_CLV' in results.columns
        assert len(results) == len(sample_rfm_data)
        assert all(results['Predicted_CLV'] > 0)

    def test_segment_by_clv(self, sample_rfm_data):
        """測試CLV分群"""
        predictor = CLVPredictor()
        clv_data = predictor.calculate_rfm_based_clv(sample_rfm_data)
        segments = predictor.segment_by_clv(clv_data, n_segments=4)

        assert 'CLV_Segment' in segments.columns
        assert len(segments['CLV_Segment'].unique()) <= 4

    def test_get_clv_summary(self, sample_rfm_data):
        """測試CLV摘要"""
        predictor = CLVPredictor()
        clv_data = predictor.calculate_rfm_based_clv(sample_rfm_data)
        summary = predictor.get_clv_summary(clv_data)

        assert 'total_customers' in summary
        assert 'total_clv' in summary
        assert 'average_clv' in summary
        assert summary['total_customers'] == len(clv_data)


class TestCampaignManager:
    """測試營銷活動管理器"""

    @pytest.fixture
    def sample_customer_data(self):
        """創建範例客戶數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'CustomerID': [f'CUST{i:03d}' for i in range(1, 101)],
            'Age': np.random.randint(18, 70, 100),
            'Income': np.random.randint(20, 150, 100),
            'Spending': np.random.randint(1, 100, 100),
            'Segment': np.random.choice(['Champions', 'Loyal', 'At Risk'], 100)
        })

    def test_initialization(self, sample_customer_data):
        """測試初始化"""
        manager = CampaignManager(sample_customer_data, 'CustomerID')
        assert len(manager.customer_df) == 100

    def test_create_campaign(self, sample_customer_data):
        """測試創建營銷活動"""
        manager = CampaignManager(sample_customer_data, 'CustomerID')

        targeted = manager.create_campaign(
            campaign_name='VIP Campaign',
            target_criteria={
                'Income': {'min': 80},
                'Spending': {'min': 60}
            }
        )

        assert len(targeted) >= 0
        assert 'VIP Campaign' in manager.campaigns

    def test_target_high_value_customers(self, sample_customer_data):
        """測試定位高價值客戶"""
        manager = CampaignManager(sample_customer_data, 'CustomerID')

        top_customers = manager.target_high_value_customers(
            value_column='Income',
            top_n=10
        )

        assert len(top_customers) == 10

    def test_calculate_campaign_roi(self, sample_customer_data):
        """測試ROI計算"""
        manager = CampaignManager(sample_customer_data, 'CustomerID')

        manager.create_campaign(
            campaign_name='Test Campaign',
            target_criteria={'Income': {'min': 50}}
        )

        roi = manager.calculate_campaign_roi(
            campaign_name='Test Campaign',
            cost_per_customer=50,
            conversion_rate=0.15,
            avg_revenue_per_conversion=500
        )

        assert 'roi_percentage' in roi
        assert 'expected_revenue' in roi
        assert 'expected_profit' in roi

    def test_get_campaign_summary(self, sample_customer_data):
        """測試活動摘要"""
        manager = CampaignManager(sample_customer_data, 'CustomerID')

        manager.create_campaign(
            'Campaign1',
            {'Income': {'min': 50}}
        )
        manager.create_campaign(
            'Campaign2',
            {'Spending': {'min': 50}}
        )

        summary = manager.get_campaign_summary()
        assert len(summary) == 2
        assert 'Campaign' in summary.columns
