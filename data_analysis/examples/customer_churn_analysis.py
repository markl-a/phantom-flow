"""
電商客戶流失分析範例

這個範例展示如何使用真實的電商數據進行客戶流失預測和分析。
透過RFM分析識別高風險流失客戶，並制定挽留策略。

真實應用場景:
- 電商平台識別可能流失的客戶
- 訂閱服務預測取消風險
- 零售業客戶關係管理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 導入專案模組
try:
    from data_analysis_chatbots import DataLoader, setup_logging
    from data_analysis_chatbots.clustering import RFMAnalyzer, KMeansClusterer
    from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager
    from data_analysis_chatbots.preprocessing import DataValidator
    from data_analysis_chatbots.visualization import Plotter
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from data_analysis_chatbots import DataLoader, setup_logging


def generate_realistic_ecommerce_data(n_customers: int = 1000,
                                       n_transactions: int = 10000) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    生成真實的電商數據，模擬實際業務場景

    包含:
    - 客戶基本資料 (年齡、性別、地區、會員等級)
    - 交易記錄 (日期、金額、產品類別、支付方式)
    - 客戶行為模式 (活躍用戶、流失用戶、新用戶)
    """
    np.random.seed(42)
    today = datetime.now()

    # ========================================
    # 客戶基本資料
    # ========================================
    regions = ['北部', '中部', '南部', '東部', '離島']
    region_weights = [0.35, 0.25, 0.25, 0.10, 0.05]

    membership_levels = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    membership_weights = [0.40, 0.30, 0.15, 0.10, 0.05]

    customers = pd.DataFrame({
        'customer_id': [f'CUST{i:06d}' for i in range(1, n_customers + 1)],
        'gender': np.random.choice(['M', 'F'], n_customers, p=[0.45, 0.55]),
        'age': np.clip(np.random.normal(35, 12, n_customers), 18, 75).astype(int),
        'region': np.random.choice(regions, n_customers, p=region_weights),
        'membership_level': np.random.choice(membership_levels, n_customers, p=membership_weights),
        'registration_date': [today - timedelta(days=np.random.randint(30, 1095))
                             for _ in range(n_customers)],
        'email_subscribed': np.random.choice([True, False], n_customers, p=[0.7, 0.3]),
        'app_installed': np.random.choice([True, False], n_customers, p=[0.4, 0.6]),
    })

    # ========================================
    # 交易記錄 (模擬真實購買行為)
    # ========================================
    product_categories = ['電子產品', '服飾配件', '家居用品', '美妝保養', '食品飲料', '運動戶外', '書籍文具']
    category_avg_prices = {'電子產品': 2500, '服飾配件': 800, '家居用品': 500,
                          '美妝保養': 600, '食品飲料': 300, '運動戶外': 1200, '書籍文具': 250}

    payment_methods = ['信用卡', '行動支付', '貨到付款', '轉帳']
    payment_weights = [0.45, 0.35, 0.15, 0.05]

    transactions = []

    # 為每個客戶生成交易
    for _, customer in customers.iterrows():
        customer_id = customer['customer_id']
        reg_date = customer['registration_date']

        # 根據會員等級決定購買頻率
        level_frequency = {
            'Bronze': (1, 5), 'Silver': (3, 10), 'Gold': (5, 20),
            'Platinum': (10, 30), 'Diamond': (15, 50)
        }
        min_tx, max_tx = level_frequency[customer['membership_level']]
        n_tx = np.random.randint(min_tx, max_tx + 1)

        # 模擬客戶購買行為類型
        behavior_type = np.random.choice(['active', 'declining', 'churned', 'new'],
                                         p=[0.4, 0.25, 0.2, 0.15])

        for _ in range(n_tx):
            # 根據行為類型決定購買時間分佈
            if behavior_type == 'active':
                # 活躍客戶: 交易分佈在整個期間
                days_ago = np.random.randint(0, min(365, (today - reg_date).days + 1))
            elif behavior_type == 'declining':
                # 衰退客戶: 最近交易減少
                days_ago = np.random.randint(30, min(365, (today - reg_date).days + 1))
            elif behavior_type == 'churned':
                # 流失客戶: 最近90天沒有交易
                days_ago = np.random.randint(90, min(365, (today - reg_date).days + 1))
            else:  # new
                # 新客戶: 只有最近的交易
                days_ago = np.random.randint(0, 60)

            tx_date = today - timedelta(days=days_ago)
            if tx_date < reg_date:
                tx_date = reg_date + timedelta(days=np.random.randint(1, 30))

            category = np.random.choice(product_categories)
            base_price = category_avg_prices[category]
            amount = np.clip(np.random.normal(base_price, base_price * 0.3), 50, base_price * 3)

            transactions.append({
                'transaction_id': f'TXN{len(transactions)+1:08d}',
                'customer_id': customer_id,
                'transaction_date': tx_date,
                'amount': round(amount, 2),
                'product_category': category,
                'payment_method': np.random.choice(payment_methods, p=payment_weights),
                'is_promotion': np.random.choice([True, False], p=[0.25, 0.75]),
                'quantity': np.random.randint(1, 5)
            })

    transactions_df = pd.DataFrame(transactions)
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])

    return customers, transactions_df


def calculate_churn_risk(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    基於RFM分數計算客戶流失風險

    流失風險評估邏輯:
    - R分數低 (很久沒購買) = 高風險
    - F分數高但R分數低 (曾經活躍但現在沉寂) = 最高風險
    - M分數高但R分數低 (高價值客戶流失中) = 需要優先挽留
    """
    df = rfm_df.copy()

    # 計算流失風險分數 (0-100)
    # R分數反向計算 (R越低，風險越高)
    r_risk = (5 - df['R_Score']) / 4 * 40  # 最高40分

    # F分數考量 (曾經活躍的客戶流失風險更高)
    f_risk = df['F_Score'] / 5 * 20  # 最高20分

    # M分數考量 (高價值客戶流失更嚴重)
    m_risk = df['M_Score'] / 5 * 20  # 最高20分

    # 綜合考量: 如果R低但F高，說明是活躍客戶開始流失
    decline_risk = ((5 - df['R_Score']) * df['F_Score']) / 20 * 20  # 最高20分

    df['churn_risk_score'] = (r_risk + f_risk + m_risk + decline_risk).clip(0, 100).round(1)

    # 風險等級分類
    df['churn_risk_level'] = pd.cut(
        df['churn_risk_score'],
        bins=[0, 25, 50, 75, 100],
        labels=['Low', 'Medium', 'High', 'Critical']
    )

    return df


def generate_retention_strategies(churn_df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """
    根據客戶流失風險和RFM分群生成個性化挽留策略
    """
    strategies = {
        'Critical': [],
        'High': [],
        'Medium': [],
        'Low': []
    }

    # Critical 風險客戶策略
    critical_customers = churn_df[churn_df['churn_risk_level'] == 'Critical']
    for _, customer in critical_customers.head(10).iterrows():
        strategy = {
            'customer_id': customer.name if isinstance(customer.name, str) else f"CUST{customer.name}",
            'segment': customer.get('Segment', 'Unknown'),
            'churn_risk': customer['churn_risk_score'],
            'recommended_actions': [
                f"立即電話聯繫 - 最後消費已超過{int(customer['Recency'])}天",
                f"提供專屬折扣券 (建議20-30%)",
                "安排VIP專屬客服跟進",
                "發送「我們想念您」個人化Email"
            ],
            'priority': 'URGENT',
            'estimated_revenue_at_risk': customer['Monetary'] * 3  # 預估年度價值
        }
        strategies['Critical'].append(strategy)

    # High 風險客戶策略
    high_customers = churn_df[churn_df['churn_risk_level'] == 'High']
    for _, customer in high_customers.head(10).iterrows():
        strategy = {
            'customer_id': customer.name if isinstance(customer.name, str) else f"CUST{customer.name}",
            'segment': customer.get('Segment', 'Unknown'),
            'churn_risk': customer['churn_risk_score'],
            'recommended_actions': [
                "發送個人化促銷Email",
                f"提供限時優惠 (建議10-15%)",
                "推送App通知提醒",
                "加入再行銷廣告受眾"
            ],
            'priority': 'HIGH'
        }
        strategies['High'].append(strategy)

    return strategies


def analyze_churn_by_segment(churn_df: pd.DataFrame) -> pd.DataFrame:
    """
    按客戶分群分析流失風險分佈
    """
    if 'Segment' not in churn_df.columns:
        return pd.DataFrame()

    segment_analysis = churn_df.groupby('Segment').agg({
        'churn_risk_score': ['mean', 'median', 'std'],
        'Monetary': ['sum', 'mean'],
        'Recency': 'mean',
        'Frequency': 'mean'
    }).round(2)

    segment_analysis.columns = ['_'.join(col) for col in segment_analysis.columns]
    segment_analysis['customer_count'] = churn_df.groupby('Segment').size()
    segment_analysis['pct_high_risk'] = (
        churn_df[churn_df['churn_risk_level'].isin(['High', 'Critical'])]
        .groupby('Segment').size() / segment_analysis['customer_count'] * 100
    ).round(1)

    return segment_analysis.sort_values('churn_risk_score_mean', ascending=False)


def main():
    """執行完整的客戶流失分析"""
    print("="*80)
    print(" "*20 + "電商客戶流失分析")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/5] 準備數據...")

    customers, transactions = generate_realistic_ecommerce_data(
        n_customers=1000,
        n_transactions=15000
    )

    print(f"  ✓ 客戶數量: {len(customers):,}")
    print(f"  ✓ 交易記錄: {len(transactions):,}")
    print(f"  ✓ 交易期間: {transactions['transaction_date'].min().date()} ~ {transactions['transaction_date'].max().date()}")
    print(f"  ✓ 總營收: ${transactions['amount'].sum():,.2f}")

    # ========================================
    # 2. RFM 分析
    # ========================================
    print("\n[2/5] 執行RFM分析...")

    analyzer = RFMAnalyzer(transactions)
    rfm_df = analyzer.calculate_rfm(
        customer_id_col='customer_id',
        date_col='transaction_date',
        amount_col='amount'
    )

    # 客戶分群
    rfm_df = analyzer.segment_customers(rfm_df)

    print(f"  ✓ RFM分析完成，共 {len(rfm_df)} 位客戶")
    print("\n  客戶分群分佈:")
    segment_counts = rfm_df['Segment'].value_counts()
    for segment, count in segment_counts.items():
        print(f"    - {segment}: {count} ({count/len(rfm_df)*100:.1f}%)")

    # ========================================
    # 3. 流失風險評估
    # ========================================
    print("\n[3/5] 評估流失風險...")

    churn_df = calculate_churn_risk(rfm_df)

    risk_distribution = churn_df['churn_risk_level'].value_counts()
    print("\n  流失風險分佈:")
    for level in ['Critical', 'High', 'Medium', 'Low']:
        count = risk_distribution.get(level, 0)
        pct = count / len(churn_df) * 100
        bar = '█' * int(pct / 2)
        print(f"    {level:10}: {count:4} ({pct:5.1f}%) {bar}")

    # ========================================
    # 4. 生成挽留策略
    # ========================================
    print("\n[4/5] 生成挽留策略...")

    strategies = generate_retention_strategies(churn_df)

    print(f"\n  Critical風險客戶 (需立即行動): {len(strategies['Critical'])} 位")
    if strategies['Critical']:
        print("\n  優先處理名單 (Top 5):")
        for i, s in enumerate(strategies['Critical'][:5], 1):
            print(f"    {i}. {s['customer_id']}")
            print(f"       分群: {s['segment']}, 風險分數: {s['churn_risk']}")
            print(f"       建議: {s['recommended_actions'][0]}")

    # ========================================
    # 5. 分群流失分析
    # ========================================
    print("\n[5/5] 分群流失分析...")

    segment_churn = analyze_churn_by_segment(churn_df)
    if not segment_churn.empty:
        print("\n  各分群流失風險:")
        print(segment_churn[['customer_count', 'churn_risk_score_mean', 'pct_high_risk', 'Monetary_sum']].to_string())

    # ========================================
    # 總結報告
    # ========================================
    print("\n" + "="*80)
    print(" "*25 + "分析摘要")
    print("="*80)

    high_risk_count = len(churn_df[churn_df['churn_risk_level'].isin(['High', 'Critical'])])
    high_risk_revenue = churn_df[churn_df['churn_risk_level'].isin(['High', 'Critical'])]['Monetary'].sum()

    print(f"""
    📊 客戶總數: {len(churn_df):,}

    ⚠️  高風險客戶: {high_risk_count:,} ({high_risk_count/len(churn_df)*100:.1f}%)
    💰 風險營收: ${high_risk_revenue:,.2f}

    🎯 建議優先行動:
       1. 立即聯繫 {len(strategies['Critical'])} 位Critical風險客戶
       2. 對 {len(strategies['High'])} 位High風險客戶發送促銷
       3. 建立自動化預警系統監控客戶活躍度
    """)

    # 保存結果
    output_path = 'data/outputs/churn_analysis_results.csv'
    try:
        churn_df.to_csv(output_path)
        print(f"\n  📁 結果已保存至: {output_path}")
    except Exception as e:
        print(f"\n  ⚠️ 無法保存結果: {e}")

    return churn_df, strategies


if __name__ == "__main__":
    churn_df, strategies = main()
