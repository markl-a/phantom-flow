"""
完整的客戶分析工作流程範例

這個腳本演示從數據載入到策略制定的完整分析流程。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data_analysis_chatbots import DataLoader, setup_logging
from data_analysis_chatbots.preprocessing import DataValidator
from data_analysis_chatbots.clustering import KMeansClusterer, RFMAnalyzer
from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager
from data_analysis_chatbots.visualization import Plotter


def main():
    """執行完整的分析工作流程"""
    # 設置日誌
    setup_logging(level="INFO")

    print("="*80)
    print(" "*20 + "客戶分析完整工作流程")
    print("="*80)

    # ===========================================
    # 步驟1: 數據載入
    # ===========================================
    print("\n[步驟 1/6] 載入數據...")

    loader = DataLoader()

    try:
        # 嘗試載入真實數據
        mall_df = loader.load_mall_customers()
        print(f"✓ 成功載入 {len(mall_df)} 筆購物中心客戶數據")
    except FileNotFoundError:
        # 生成範例數據
        print("⚠ 真實數據未找到,生成範例數據...")
        np.random.seed(42)
        mall_df = pd.DataFrame({
            'CustomerID': range(1, 201),
            'Gender': np.random.choice(['Male', 'Female'], 200),
            'Age': np.random.randint(18, 70, 200),
            'Annual Income (k$)': np.random.randint(15, 140, 200),
            'Spending Score (1-100)': np.random.randint(1, 100, 200)
        })
        print(f"✓ 生成 {len(mall_df)} 筆範例數據")

    # 生成交易數據用於RFM分析
    print("\n生成交易數據...")
    n_transactions = 5000
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    transactions = []
    for _ in range(n_transactions):
        customer_id = f'CUST{np.random.randint(1, 501):04d}'
        days_ago = np.random.randint(0, 365)
        transaction_date = end_date - timedelta(days=days_ago)
        amount = np.random.gamma(shape=2, scale=50)

        transactions.append({
            'CustomerID': customer_id,
            'TransactionDate': transaction_date,
            'Amount': round(amount, 2)
        })

    transaction_df = pd.DataFrame(transactions)
    transaction_df['TransactionDate'] = pd.to_datetime(transaction_df['TransactionDate'])
    print(f"✓ 生成 {len(transaction_df)} 筆交易記錄")

    # ===========================================
    # 步驟2: 數據驗證
    # ===========================================
    print("\n[步驟 2/6] 數據質量檢查...")

    validator = DataValidator(mall_df)
    validation_report = validator.generate_report()

    print(f"✓ 數據驗證完成")
    print(f"  - 總行數: {validation_report['summary']['total_rows']}")
    print(f"  - 總列數: {validation_report['summary']['total_columns']}")
    print(f"  - 缺失值: {validation_report['missing_values']['total_missing_cells']}")
    print(f"  - 重複行: {validation_report['duplicates']['duplicate_count']}")

    # ===========================================
    # 步驟3: K-means客戶聚類
    # ===========================================
    print("\n[步驟 3/6] K-means聚類分析...")

    feature_columns = ['Age', 'Annual Income (k$)', 'Spending Score (1-100)']

    # 尋找最佳K值
    clusterer = KMeansClusterer()
    print("  正在尋找最佳聚類數...")
    optimal_results = clusterer.find_optimal_clusters(
        df=mall_df,
        feature_columns=feature_columns,
        k_range=list(range(2, 9))
    )

    # 選擇最佳K
    best_k = max(optimal_results.keys(),
                 key=lambda k: optimal_results[k].get('silhouette_score', 0))
    print(f"  ✓ 建議最佳聚類數: K = {best_k}")

    # 執行聚類
    clusterer = KMeansClusterer(n_clusters=best_k, random_state=42)
    labels = clusterer.fit_predict(mall_df, feature_columns)
    mall_df['Cluster'] = labels

    metrics = clusterer.evaluate_clustering()
    print(f"  ✓ 聚類完成")
    print(f"    - 輪廓係數: {metrics.get('silhouette_score', 0):.3f}")
    print(f"    - 慣性: {metrics['inertia']:.2f}")

    # 顯示聚類分佈
    print(f"\n  聚類分佈:")
    for cluster_id in range(best_k):
        count = len(mall_df[mall_df['Cluster'] == cluster_id])
        percentage = count / len(mall_df) * 100
        print(f"    群組 {cluster_id}: {count:3d} 人 ({percentage:5.1f}%)")

    # ===========================================
    # 步驟4: RFM分析
    # ===========================================
    print("\n[步驟 4/6] RFM分析...")

    rfm_analyzer = RFMAnalyzer(
        df=transaction_df,
        customer_id_col='CustomerID',
        date_col='TransactionDate',
        amount_col='Amount'
    )

    # 計算RFM並分群
    rfm_data = rfm_analyzer.calculate_rfm()
    rfm_scores = rfm_analyzer.assign_rfm_scores()
    rfm_segments = rfm_analyzer.segment_customers()

    print(f"  ✓ RFM分析完成")
    print(f"    - 分析客戶數: {len(rfm_segments)}")

    # 顯示分群統計
    segment_summary = rfm_analyzer.get_segment_summary()
    print(f"\n  主要客戶分群:")
    top_segments = segment_summary.nlargest(5, 'Customer_Count')
    for _, row in top_segments.iterrows():
        print(f"    {row['Segment']:20s}: {int(row['Customer_Count']):4d} 人 "
              f"({row['Percentage']:5.1f}%)")

    # ===========================================
    # 步驟5: CLV預測
    # ===========================================
    print("\n[步驟 5/6] 客戶終身價值(CLV)預測...")

    clv_predictor = CLVPredictor(discount_rate=0.1, time_horizon_years=3)
    clv_results = clv_predictor.calculate_rfm_based_clv(rfm_segments)

    clv_summary = clv_predictor.get_clv_summary(
        clv_df=clv_results,
        segment_col='Segment'
    )

    print(f"  ✓ CLV預測完成")
    print(f"    - 總CLV: ${clv_summary['total_clv']:,.2f}")
    print(f"    - 平均CLV: ${clv_summary['average_clv']:.2f}")
    print(f"    - 中位數CLV: ${clv_summary['median_clv']:.2f}")
    print(f"    - 最高CLV: ${clv_summary['max_clv']:,.2f}")

    # 識別高價值客戶
    high_value_threshold = clv_results['Predicted_CLV'].quantile(0.9)
    high_value_customers = clv_results[
        clv_results['Predicted_CLV'] >= high_value_threshold
    ]
    print(f"\n  ✓ 識別出 {len(high_value_customers)} 位高價值客戶 (top 10%)")

    # 識別流失風險客戶
    at_risk = clv_results[
        (clv_results['Predicted_CLV'] > clv_results['Predicted_CLV'].median()) &
        (clv_results['Segment'].isin(['At Risk', "Can't Lose Them"]))
    ]
    if len(at_risk) > 0:
        print(f"  ⚠ 識別出 {len(at_risk)} 位高價值流失風險客戶")
        print(f"    潛在損失: ${at_risk['Predicted_CLV'].sum():,.2f}")

    # ===========================================
    # 步驟6: 營銷活動設計
    # ===========================================
    print("\n[步驟 6/6] 營銷活動設計...")

    # 合併數據
    campaign_data = mall_df.copy()
    campaign_data = campaign_data.merge(
        rfm_segments[['CustomerID', 'Segment', 'Monetary']],
        left_on='CustomerID',
        right_on='CustomerID',
        how='left',
        suffixes=('', '_rfm')
    )

    campaign_mgr = CampaignManager(campaign_data, 'CustomerID')

    # 創建VIP營銷活動
    vip_campaign = campaign_mgr.create_campaign(
        campaign_name='VIP專屬優惠',
        target_criteria={
            'Annual Income (k$)': {'min': 80},
            'Spending Score (1-100)': {'min': 70}
        },
        campaign_details={
            'discount': 0.25,
            'budget': 50000,
            'type': 'exclusive'
        }
    )

    print(f"  ✓ VIP營銷活動創建")
    print(f"    - 目標客戶: {len(vip_campaign)} 人")

    # 計算ROI
    vip_roi = campaign_mgr.calculate_campaign_roi(
        campaign_name='VIP專屬優惠',
        cost_per_customer=100,
        conversion_rate=0.20,
        avg_revenue_per_conversion=800
    )

    print(f"    - 預期轉換: {vip_roi['expected_conversions']:.0f} 人")
    print(f"    - 預期收入: ${vip_roi['expected_revenue']:,.2f}")
    print(f"    - 預期ROI: {vip_roi['roi_percentage']:.1f}%")

    # 創建挽回營銷活動 (針對流失風險客戶)
    if len(at_risk) > 0:
        at_risk_ids = at_risk['CustomerID'].tolist()
        winback_customers = campaign_data[
            campaign_data['CustomerID'].isin(at_risk_ids)
        ]

        if len(winback_customers) > 0:
            print(f"\n  ✓ 挽回營銷活動")
            print(f"    - 目標客戶: {len(winback_customers)} 人")
            print(f"    - 策略: 特別折扣 + 個人化關懷")

    # ===========================================
    # 保存結果
    # ===========================================
    print("\n" + "="*80)
    print("保存分析結果...")
    print("="*80)

    # 確保輸出目錄存在
    import os
    os.makedirs('data/outputs', exist_ok=True)

    # 保存結果
    mall_df.to_csv('data/outputs/customer_clusters.csv', index=False)
    print("✓ 客戶聚類結果: data/outputs/customer_clusters.csv")

    rfm_segments.to_csv('data/outputs/rfm_segments.csv', index=False)
    print("✓ RFM分群結果: data/outputs/rfm_segments.csv")

    clv_results.to_csv('data/outputs/clv_predictions.csv', index=False)
    print("✓ CLV預測結果: data/outputs/clv_predictions.csv")

    high_value_customers.to_csv('data/outputs/high_value_customers.csv', index=False)
    print("✓ 高價值客戶名單: data/outputs/high_value_customers.csv")

    if len(at_risk) > 0:
        at_risk.to_csv('data/outputs/at_risk_customers.csv', index=False)
        print("✓ 流失風險客戶名單: data/outputs/at_risk_customers.csv")

    campaign_mgr.export_campaign_list(
        'VIP專屬優惠',
        'data/outputs/vip_campaign_list.csv'
    )
    print("✓ VIP營銷名單: data/outputs/vip_campaign_list.csv")

    # 可視化 (可選)
    print("\n生成可視化圖表...")
    plotter = Plotter()

    # 聚類圖
    centers = clusterer.get_cluster_centers()
    plotter.plot_clusters(
        df=mall_df,
        x_col='Annual Income (k$)',
        y_col='Spending Score (1-100)',
        cluster_col='Cluster',
        centers=centers,
        title='客戶分群分析',
        save_path='data/outputs/customer_segments.png'
    )
    print("✓ 聚類可視化: data/outputs/customer_segments.png")

    # RFM分群分佈
    plotter.plot_segment_distribution(
        segments=rfm_segments['Segment'],
        title='RFM客戶分群分佈',
        save_path='data/outputs/rfm_distribution.png'
    )
    print("✓ RFM分佈圖: data/outputs/rfm_distribution.png")

    # 完成
    print("\n" + "="*80)
    print(" "*30 + "分析完成!")
    print("="*80)
    print("\n所有結果已保存到 data/outputs/ 目錄")
    print("\n下一步建議:")
    print("  1. 查看輸出文件了解詳細結果")
    print("  2. 根據分群結果制定具體營銷策略")
    print("  3. 實施VIP和挽回營銷活動")
    print("  4. 追蹤活動效果並持續優化")


if __name__ == '__main__':
    main()
