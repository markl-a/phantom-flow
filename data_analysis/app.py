"""
Streamlit 互動式客戶分析儀表板

執行方式:
    streamlit run app.py
"""

from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from data_analysis_chatbots import DataLoader
from data_analysis_chatbots.preprocessing import DataValidator
from data_analysis_chatbots.clustering import KMeansClusterer, RFMAnalyzer
from data_analysis_chatbots.marketing import CLVPredictor
from data_analysis_chatbots.visualization import Plotter

# 設置頁面配置
st.set_page_config(
    page_title="客戶分析儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_sample_data():
    """載入或生成範例數據"""
    loader = DataLoader()

    try:
        # 嘗試載入真實數據
        df = loader.load_mall_customers()
        data_source = "真實數據"
    except FileNotFoundError:
        # 生成範例數據
        np.random.seed(42)
        df = pd.DataFrame({
            'CustomerID': range(1, 201),
            'Gender': np.random.choice(['Male', 'Female'], 200),
            'Age': np.random.randint(18, 70, 200),
            'Annual Income (k$)': np.random.randint(15, 140, 200),
            'Spending Score (1-100)': np.random.randint(1, 100, 200)
        })
        data_source = "範例數據"

    return df, data_source


@st.cache_data
def generate_transaction_data(n_transactions=5000):
    """生成交易數據"""
    np.random.seed(42)
    end_date = datetime.now()

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

    df = pd.DataFrame(transactions)
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
    return df


def main():
    # 標題
    st.markdown('<p class="main-header">📊 客戶分析儀表板</p>',
                unsafe_allow_html=True)

    # 側邊欄
    st.sidebar.title("🎯 分析設置")

    analysis_type = st.sidebar.selectbox(
        "選擇分析類型",
        ["數據概覽", "K-means聚類", "RFM分析", "CLV預測", "營銷策略"]
    )

    # 載入數據
    with st.spinner("載入數據中..."):
        customer_df, data_source = load_sample_data()
        transaction_df = generate_transaction_data()

    st.sidebar.success(f"✓ 已載入{data_source}")
    st.sidebar.info(f"客戶數: {len(customer_df)}\n交易數: {len(transaction_df)}")

    # ===================================
    # 數據概覽
    # ===================================
    if analysis_type == "數據概覽":
        st.header("📋 數據概覽")

        tab1, tab2, tab3 = st.tabs(["基本信息", "數據質量", "統計分析"])

        with tab1:
            st.subheader("客戶數據預覽")
            st.dataframe(customer_df.head(20), use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("總客戶數", len(customer_df))
            with col2:
                st.metric("平均年齡", f"{customer_df['Age'].mean():.1f}歲")
            with col3:
                st.metric("平均收入", f"${customer_df['Annual Income (k$)'].mean():.1f}k")
            with col4:
                st.metric("平均消費分數", f"{customer_df['Spending Score (1-100)'].mean():.1f}")

        with tab2:
            st.subheader("數據質量檢查")

            validator = DataValidator(customer_df)
            report = validator.generate_report()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("缺失值", report['missing_values']['total_missing_cells'])
            with col2:
                st.metric("重複行", report['duplicates']['duplicate_count'])

            if report['missing_values']['total_missing_cells'] == 0:
                st.success("✓ 數據質量良好,無缺失值")
            else:
                st.warning(f"發現 {report['missing_values']['total_missing_cells']} 個缺失值")

        with tab3:
            st.subheader("統計分析")
            st.dataframe(customer_df.describe(), use_container_width=True)

            # 分佈圖
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))

            axes[0, 0].hist(customer_df['Age'], bins=20, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('年齡分佈')
            axes[0, 0].set_xlabel('年齡')

            axes[0, 1].hist(customer_df['Annual Income (k$)'], bins=20, color='lightgreen', edgecolor='black')
            axes[0, 1].set_title('收入分佈')
            axes[0, 1].set_xlabel('年收入 (k$)')

            axes[1, 0].hist(customer_df['Spending Score (1-100)'], bins=20, color='lightcoral', edgecolor='black')
            axes[1, 0].set_title('消費分數分佈')
            axes[1, 0].set_xlabel('消費分數')

            gender_counts = customer_df['Gender'].value_counts()
            axes[1, 1].pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%')
            axes[1, 1].set_title('性別分佈')

            plt.tight_layout()
            st.pyplot(fig)

    # ===================================
    # K-means聚類
    # ===================================
    elif analysis_type == "K-means聚類":
        st.header("🎯 K-means客戶聚類")

        # 參數設置
        st.sidebar.subheader("聚類參數")
        n_clusters = st.sidebar.slider("聚類數量", 2, 10, 5)

        feature_columns = ['Age', 'Annual Income (k$)', 'Spending Score (1-100)']

        if st.button("執行聚類分析", type="primary"):
            with st.spinner("正在執行聚類..."):
                # 聚類
                clusterer = KMeansClusterer(n_clusters=n_clusters, random_state=42)
                labels = clusterer.fit_predict(customer_df, feature_columns)
                customer_df['Cluster'] = labels

                # 評估
                metrics = clusterer.evaluate_clustering()

                # 顯示結果
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("聚類數", n_clusters)
                with col2:
                    st.metric("輪廓係數", f"{metrics.get('silhouette_score', 0):.3f}")
                with col3:
                    st.metric("慣性", f"{metrics['inertia']:.2f}")

                # 聚類分佈
                st.subheader("聚類分佈")
                cluster_dist = customer_df['Cluster'].value_counts().sort_index()

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

                ax1.bar(cluster_dist.index, cluster_dist.values, color='steelblue')
                ax1.set_xlabel('群組')
                ax1.set_ylabel('客戶數')
                ax1.set_title('各群組客戶數量')

                ax2.pie(cluster_dist.values, labels=[f'群組 {i}' for i in cluster_dist.index],
                       autopct='%1.1f%%')
                ax2.set_title('群組佔比')

                plt.tight_layout()
                st.pyplot(fig)

                # 可視化聚類
                st.subheader("聚類可視化")
                fig, ax = plt.subplots(figsize=(12, 8))

                colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
                for i in range(n_clusters):
                    cluster_data = customer_df[customer_df['Cluster'] == i]
                    ax.scatter(cluster_data['Annual Income (k$)'],
                              cluster_data['Spending Score (1-100)'],
                              c=[colors[i]], label=f'群組 {i}', s=100, alpha=0.6)

                ax.set_xlabel('年收入 (k$)', fontsize=12)
                ax.set_ylabel('消費分數', fontsize=12)
                ax.set_title('客戶分群: 收入 vs 消費分數', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)

                st.pyplot(fig)

                # 聚類特徵
                st.subheader("各群組特徵")
                cluster_summary = customer_df.groupby('Cluster')[feature_columns].mean().round(2)
                st.dataframe(cluster_summary, use_container_width=True)

    # ===================================
    # RFM分析
    # ===================================
    elif analysis_type == "RFM分析":
        st.header("💎 RFM客戶分析")

        with st.spinner("執行RFM分析..."):
            # RFM分析
            rfm_analyzer = RFMAnalyzer(
                df=transaction_df,
                customer_id_col='CustomerID',
                date_col='TransactionDate',
                amount_col='Amount'
            )

            rfm_data = rfm_analyzer.calculate_rfm()
            rfm_segments = rfm_analyzer.segment_customers()
            segment_summary = rfm_analyzer.get_segment_summary()

            # 關鍵指標
            st.subheader("關鍵指標")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("分析客戶數", len(rfm_segments))
            with col2:
                st.metric("平均Recency", f"{rfm_data['Recency'].mean():.1f}天")
            with col3:
                st.metric("平均Frequency", f"{rfm_data['Frequency'].mean():.1f}次")
            with col4:
                st.metric("平均Monetary", f"${rfm_data['Monetary'].mean():.2f}")

            # 分群統計
            st.subheader("客戶分群統計")
            st.dataframe(segment_summary, use_container_width=True)

            # 分群分佈
            st.subheader("分群分佈")
            segment_counts = rfm_segments['Segment'].value_counts()

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

            ax1.barh(segment_counts.index, segment_counts.values, color='steelblue')
            ax1.set_xlabel('客戶數')
            ax1.set_title('各分群客戶數量')

            ax2.pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%', startangle=90)
            ax2.set_title('分群佔比')

            plt.tight_layout()
            st.pyplot(fig)

            # RFM散點圖
            st.subheader("RFM可視化")
            fig, ax = plt.subplots(figsize=(12, 8))

            for segment in rfm_segments['Segment'].unique():
                segment_data = rfm_segments[rfm_segments['Segment'] == segment]
                ax.scatter(segment_data['Recency'], segment_data['Monetary'],
                          label=segment, alpha=0.6, s=100)

            ax.set_xlabel('Recency (天)', fontsize=12)
            ax.set_ylabel('Monetary ($)', fontsize=12)
            ax.set_title('RFM分析: Recency vs Monetary', fontsize=14, fontweight='bold')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

    # ===================================
    # CLV預測
    # ===================================
    elif analysis_type == "CLV預測":
        st.header("💰 客戶終身價值預測")

        # 參數設置
        st.sidebar.subheader("CLV參數")
        discount_rate = st.sidebar.slider("折扣率", 0.0, 0.3, 0.1, 0.01)
        time_horizon = st.sidebar.slider("預測年限", 1, 5, 3)

        with st.spinner("計算CLV..."):
            # RFM分析
            rfm_analyzer = RFMAnalyzer(
                df=transaction_df,
                customer_id_col='CustomerID',
                date_col='TransactionDate',
                amount_col='Amount'
            )
            rfm_segments = rfm_analyzer.segment_customers()

            # CLV預測
            clv_predictor = CLVPredictor(
                discount_rate=discount_rate,
                time_horizon_years=time_horizon
            )
            clv_results = clv_predictor.calculate_rfm_based_clv(rfm_segments, time_horizon)
            clv_summary = clv_predictor.get_clv_summary(clv_results, segment_col='Segment')

            # 關鍵指標
            st.subheader("CLV摘要")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("總CLV", f"${clv_summary['total_clv']:,.2f}")
            with col2:
                st.metric("平均CLV", f"${clv_summary['average_clv']:.2f}")
            with col3:
                st.metric("中位數CLV", f"${clv_summary['median_clv']:.2f}")
            with col4:
                st.metric("最高CLV", f"${clv_summary['max_clv']:,.2f}")

            # CLV分佈
            st.subheader("CLV分佈")
            fig, ax = plt.subplots(figsize=(12, 6))

            ax.hist(clv_results['Predicted_CLV'], bins=50, color='steelblue', edgecolor='black')
            ax.axvline(clv_summary['average_clv'], color='red', linestyle='--',
                      linewidth=2, label='平均值')
            ax.axvline(clv_summary['median_clv'], color='green', linestyle='--',
                      linewidth=2, label='中位數')
            ax.set_xlabel('預測CLV ($)', fontsize=12)
            ax.set_ylabel('客戶數', fontsize=12)
            ax.set_title('客戶終身價值分佈', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)

            st.pyplot(fig)

            # 高價值客戶
            st.subheader("高價值客戶 (Top 10%)")
            threshold = clv_results['Predicted_CLV'].quantile(0.9)
            top_customers = clv_results[clv_results['Predicted_CLV'] >= threshold].sort_values(
                'Predicted_CLV', ascending=False
            )

            st.dataframe(
                top_customers[['CustomerID', 'Segment', 'Monetary', 'Predicted_CLV']].head(20),
                use_container_width=True
            )

            st.info(f"✓ 識別出 {len(top_customers)} 位高價值客戶,總CLV: ${top_customers['Predicted_CLV'].sum():,.2f}")

    # ===================================
    # 營銷策略
    # ===================================
    elif analysis_type == "營銷策略":
        st.header("🎯 營銷策略建議")

        # RFM和CLV分析
        with st.spinner("生成策略建議..."):
            rfm_analyzer = RFMAnalyzer(
                df=transaction_df,
                customer_id_col='CustomerID',
                date_col='TransactionDate',
                amount_col='Amount'
            )
            rfm_segments = rfm_analyzer.segment_customers()

            clv_predictor = CLVPredictor()
            clv_results = clv_predictor.calculate_rfm_based_clv(rfm_segments)

            # 識別關鍵客戶群
            champions = clv_results[clv_results['Segment'] == 'Champions']
            at_risk = clv_results[clv_results['Segment'].isin(['At Risk', "Can't Lose Them"])]
            high_clv_at_risk = at_risk[at_risk['Predicted_CLV'] > at_risk['Predicted_CLV'].median()]

            # 顯示策略
            st.subheader("優先行動計劃")

            # 1. Champions
            with st.expander("🏆 Champions (冠軍客戶)", expanded=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("客戶數", len(champions))
                    st.metric("總CLV", f"${champions['Predicted_CLV'].sum():,.2f}")
                with col2:
                    st.write("**策略建議:**")
                    st.write("- 🎁 VIP專屬優惠和服務")
                    st.write("- 📧 個人化溝通和關懷")
                    st.write("- 🎪 邀請參加獨家活動")
                    st.write("- 💎 優先體驗新產品")

            # 2. 流失風險
            with st.expander("⚠️ 高價值流失風險客戶", expanded=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("客戶數", len(high_clv_at_risk))
                    st.metric("潛在損失", f"${high_clv_at_risk['Predicted_CLV'].sum():,.2f}")
                with col2:
                    st.write("**緊急行動:**")
                    st.write("- 📞 立即電話聯繫了解需求")
                    st.write("- 🎫 特別折扣券挽回")
                    st.write("- 🤝 解決可能的問題")
                    st.write("- 💌 個人化關懷郵件")

            # 3. 各分群策略總覽
            st.subheader("完整分群策略")

            strategies = {
                'Champions': {
                    '目標': '維持忠誠度',
                    '策略': 'VIP服務、獨家優惠',
                    '渠道': '個人化郵件、專線'
                },
                'Loyal Customers': {
                    '目標': '提升價值',
                    '策略': '交叉銷售、推薦計劃',
                    '渠道': '會員通訊、APP'
                },
                'At Risk': {
                    '目標': '挽回',
                    '策略': '特別優惠、調查反饋',
                    '渠道': '電話、郵件'
                },
                'Potential Loyalists': {
                    '目標': '培養忠誠',
                    '策略': '會員計劃、教育內容',
                    '渠道': '社交媒體、郵件'
                }
            }

            strategy_df = pd.DataFrame(strategies).T
            st.dataframe(strategy_df, use_container_width=True)


if __name__ == '__main__':
    main()
