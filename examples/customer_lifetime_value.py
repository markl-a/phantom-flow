"""
客戶生命週期價值 (CLV) 完整分析範例

這個範例展示如何計算和應用客戶生命週期價值，
用於制定差異化營銷策略和資源分配。

真實應用場景:
- 客戶獲取成本 (CAC) vs CLV 分析
- 客戶投資回報評估
- 高價值客戶識別和維護
- 營銷預算優化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import DataLoader, setup_logging
    from data_analysis_chatbots.clustering import RFMAnalyzer
    from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager
except ImportError:
    import sys
    sys.path.insert(0, '..')


@dataclass
class CustomerProfile:
    """客戶檔案"""
    customer_id: str
    clv: float
    clv_segment: str
    rfm_segment: str
    acquisition_cost: float
    ltv_cac_ratio: float
    predicted_churn_prob: float
    recommended_investment: float
    priority_score: float


class CLVAnalyzer:
    """
    客戶生命週期價值分析器

    功能:
    - 多種CLV計算方法
    - CLV分群
    - 投資回報分析
    - 個性化策略建議
    """

    def __init__(self, transactions_df: pd.DataFrame,
                 customer_df: Optional[pd.DataFrame] = None,
                 discount_rate: float = 0.1):
        """
        初始化分析器

        Args:
            transactions_df: 交易數據
            customer_df: 客戶主檔 (可選)
            discount_rate: 折現率
        """
        self.transactions = transactions_df.copy()
        self.customers = customer_df
        self.discount_rate = discount_rate
        self.clv_df = None

    def calculate_historical_clv(self,
                                  customer_id_col: str = 'customer_id',
                                  date_col: str = 'transaction_date',
                                  amount_col: str = 'amount') -> pd.DataFrame:
        """
        計算歷史CLV (過去實際貢獻)
        """
        historical = self.transactions.groupby(customer_id_col).agg({
            amount_col: ['sum', 'mean', 'count'],
            date_col: ['min', 'max']
        })

        historical.columns = ['total_revenue', 'avg_order_value', 'order_count',
                              'first_purchase', 'last_purchase']

        historical['customer_tenure_days'] = (
            historical['last_purchase'] - historical['first_purchase']
        ).dt.days

        historical['historical_clv'] = historical['total_revenue']

        return historical

    def calculate_predictive_clv(self,
                                  customer_id_col: str = 'customer_id',
                                  date_col: str = 'transaction_date',
                                  amount_col: str = 'amount',
                                  prediction_years: int = 3) -> pd.DataFrame:
        """
        計算預測CLV (未來預期價值)

        使用簡化的BG/NBD模型概念
        """
        # 先計算RFM
        analyzer = RFMAnalyzer(self.transactions)
        rfm = analyzer.calculate_rfm(
            customer_id_col=customer_id_col,
            date_col=date_col,
            amount_col=amount_col
        )

        # 計算基礎指標
        historical = self.calculate_historical_clv(customer_id_col, date_col, amount_col)

        # 合併數據
        clv_df = rfm.join(historical, how='left')

        # 預測購買頻率 (基於歷史頻率)
        clv_df['yearly_frequency'] = clv_df['Frequency'] / (clv_df['customer_tenure_days'] / 365).clip(lower=0.1)

        # 預測客戶存活率 (基於Recency)
        # Recency越大，流失可能性越高
        max_recency = clv_df['Recency'].max()
        clv_df['survival_prob'] = 1 - (clv_df['Recency'] / max_recency).clip(0, 0.9)

        # 計算預測CLV
        clv_df['predicted_clv'] = 0
        for year in range(1, prediction_years + 1):
            yearly_value = (
                clv_df['avg_order_value'] *
                clv_df['yearly_frequency'] *
                (clv_df['survival_prob'] ** year)
            )
            discounted_value = yearly_value / ((1 + self.discount_rate) ** year)
            clv_df['predicted_clv'] += discounted_value

        # 總CLV = 歷史 + 預測
        clv_df['total_clv'] = clv_df['historical_clv'] + clv_df['predicted_clv']

        self.clv_df = clv_df
        return clv_df

    def segment_by_clv(self, n_segments: int = 4) -> pd.DataFrame:
        """CLV分群"""
        if self.clv_df is None:
            raise ValueError("請先計算CLV")

        df = self.clv_df.copy()

        # 使用分位數分群
        df['clv_percentile'] = df['total_clv'].rank(pct=True)

        df['clv_segment'] = pd.cut(
            df['clv_percentile'],
            bins=[0, 0.25, 0.5, 0.75, 1.0],
            labels=['Bronze', 'Silver', 'Gold', 'Platinum']
        )

        return df

    def calculate_cac_ltv_ratio(self,
                                 cac_data: Optional[Dict[str, float]] = None) -> pd.DataFrame:
        """
        計算CAC/LTV比率

        Args:
            cac_data: 客戶獲取成本數據 {customer_id: cac}
        """
        if self.clv_df is None:
            raise ValueError("請先計算CLV")

        df = self.clv_df.copy()

        if cac_data:
            df['cac'] = df.index.map(lambda x: cac_data.get(x, 50))
        else:
            # 假設平均CAC
            df['cac'] = 50

        df['ltv_cac_ratio'] = df['total_clv'] / df['cac']

        # 評估
        df['investment_grade'] = pd.cut(
            df['ltv_cac_ratio'],
            bins=[0, 1, 3, 5, float('inf')],
            labels=['Poor', 'Fair', 'Good', 'Excellent']
        )

        return df

    def generate_investment_recommendations(self) -> Dict[str, List[Dict]]:
        """生成投資建議"""
        if self.clv_df is None:
            raise ValueError("請先計算CLV")

        df = self.segment_by_clv()
        df = self.calculate_cac_ltv_ratio()

        recommendations = {}

        for segment in ['Platinum', 'Gold', 'Silver', 'Bronze']:
            segment_df = df[df['clv_segment'] == segment]

            if len(segment_df) == 0:
                continue

            segment_info = {
                'count': len(segment_df),
                'avg_clv': segment_df['total_clv'].mean(),
                'total_value': segment_df['total_clv'].sum(),
                'avg_ltv_cac': segment_df['ltv_cac_ratio'].mean(),
                'customers': []
            }

            # 選擇代表性客戶
            top_customers = segment_df.nlargest(5, 'total_clv')

            for idx, row in top_customers.iterrows():
                customer_rec = {
                    'customer_id': idx,
                    'clv': round(row['total_clv'], 2),
                    'ltv_cac_ratio': round(row['ltv_cac_ratio'], 2),
                    'recency': row['Recency'],
                    'frequency': row['Frequency']
                }

                # 根據分群和狀態生成建議
                if segment == 'Platinum':
                    if row['Recency'] > 30:
                        customer_rec['action'] = "緊急挽留 - VIP電話關懷"
                        customer_rec['budget'] = min(row['total_clv'] * 0.1, 500)
                    else:
                        customer_rec['action'] = "VIP維護 - 專屬優惠"
                        customer_rec['budget'] = row['total_clv'] * 0.05

                elif segment == 'Gold':
                    if row['Recency'] > 60:
                        customer_rec['action'] = "喚醒活動 - 個人化Email"
                        customer_rec['budget'] = min(row['total_clv'] * 0.08, 200)
                    else:
                        customer_rec['action'] = "升級培養 - 會員權益"
                        customer_rec['budget'] = row['total_clv'] * 0.05

                elif segment == 'Silver':
                    customer_rec['action'] = "發展潛力 - 交叉銷售"
                    customer_rec['budget'] = row['total_clv'] * 0.03

                else:  # Bronze
                    if row['ltv_cac_ratio'] < 1:
                        customer_rec['action'] = "低成本維護 - 自動化Email"
                        customer_rec['budget'] = 10
                    else:
                        customer_rec['action'] = "基礎服務 - 促銷推送"
                        customer_rec['budget'] = row['total_clv'] * 0.02

                segment_info['customers'].append(customer_rec)

            recommendations[segment] = segment_info

        return recommendations

    def generate_report(self) -> str:
        """生成CLV分析報告"""
        if self.clv_df is None:
            self.calculate_predictive_clv()

        df = self.segment_by_clv()
        df = self.calculate_cac_ltv_ratio()
        recommendations = self.generate_investment_recommendations()

        report = f"""
{'='*80}
                客戶生命週期價值 (CLV) 分析報告
                {datetime.now().strftime('%Y-%m-%d')}
{'='*80}

一、整體概況
{'='*40}

  總客戶數: {len(df):,}
  總CLV價值: ${df['total_clv'].sum():,.2f}
  平均CLV: ${df['total_clv'].mean():,.2f}
  中位數CLV: ${df['total_clv'].median():,.2f}

  CLV分佈:
    - Top 10% 客戶貢獻: {df.nlargest(int(len(df)*0.1), 'total_clv')['total_clv'].sum() / df['total_clv'].sum() * 100:.1f}% 營收
    - Top 20% 客戶貢獻: {df.nlargest(int(len(df)*0.2), 'total_clv')['total_clv'].sum() / df['total_clv'].sum() * 100:.1f}% 營收

二、CLV分群分析
{'='*40}
"""

        for segment in ['Platinum', 'Gold', 'Silver', 'Bronze']:
            if segment in recommendations:
                info = recommendations[segment]
                pct = info['count'] / len(df) * 100
                value_pct = info['total_value'] / df['total_clv'].sum() * 100

                report += f"""
【{segment}】
  客戶數: {info['count']:,} ({pct:.1f}%)
  平均CLV: ${info['avg_clv']:,.2f}
  價值佔比: {value_pct:.1f}%
  平均LTV/CAC: {info['avg_ltv_cac']:.2f}x
"""

        report += f"""
三、投資回報分析
{'='*40}

LTV/CAC 比率分佈:
"""
        for grade in ['Excellent', 'Good', 'Fair', 'Poor']:
            count = len(df[df['investment_grade'] == grade])
            pct = count / len(df) * 100
            report += f"  {grade}: {count:,} ({pct:.1f}%)\n"

        report += f"""
四、策略建議
{'='*40}

1. Platinum 客戶 (高價值):
   - 投入VIP維護資源
   - 建立個人化服務
   - 預算建議: CLV的5-10%

2. Gold 客戶 (成長潛力):
   - 培養升級為Platinum
   - 提供會員權益
   - 預算建議: CLV的5-8%

3. Silver 客戶 (發展中):
   - 交叉銷售提升價值
   - 自動化營銷
   - 預算建議: CLV的3%

4. Bronze 客戶 (低價值):
   - 低成本維護
   - 評估放棄低於CAC客戶
   - 預算建議: 固定$10-20

五、關鍵行動項
{'='*40}

□ 識別 {len(df[(df['clv_segment'] == 'Platinum') & (df['Recency'] > 30)])} 位需緊急挽留的Platinum客戶
□ 規劃 Gold → Platinum 升級計劃
□ 優化 LTV/CAC < 1 的客戶獲取渠道
□ 建立自動化CLV追蹤儀表板

{'='*80}
                        報告結束
{'='*80}
"""

        return report


def generate_sample_data(n_customers: int = 500,
                         n_transactions: int = 5000) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """生成範例數據"""
    np.random.seed(42)
    today = datetime.now()

    # 客戶主檔
    customers = pd.DataFrame({
        'customer_id': [f'CUST{i:05d}' for i in range(1, n_customers + 1)],
        'acquisition_date': [today - timedelta(days=np.random.randint(30, 730))
                            for _ in range(n_customers)],
        'acquisition_channel': np.random.choice(
            ['Organic', 'Paid Search', 'Social', 'Referral', 'Email'],
            n_customers,
            p=[0.25, 0.30, 0.20, 0.15, 0.10]
        ),
        'acquisition_cost': np.random.choice(
            [0, 20, 50, 80, 100],
            n_customers,
            p=[0.25, 0.25, 0.25, 0.15, 0.10]
        )
    })

    # 交易記錄
    transactions = []
    customer_behavior = {}

    for _, cust in customers.iterrows():
        cid = cust['customer_id']
        acq_date = cust['acquisition_date']

        # 隨機分配客戶類型
        cust_type = np.random.choice(
            ['high_value', 'regular', 'occasional', 'one_time'],
            p=[0.1, 0.3, 0.4, 0.2]
        )

        customer_behavior[cid] = cust_type

        if cust_type == 'high_value':
            n_tx = np.random.randint(10, 50)
            avg_amount = np.random.uniform(100, 500)
        elif cust_type == 'regular':
            n_tx = np.random.randint(5, 15)
            avg_amount = np.random.uniform(50, 150)
        elif cust_type == 'occasional':
            n_tx = np.random.randint(2, 6)
            avg_amount = np.random.uniform(30, 100)
        else:
            n_tx = 1
            avg_amount = np.random.uniform(20, 80)

        for _ in range(n_tx):
            days_since_acq = (today - acq_date).days
            if days_since_acq <= 0:
                days_since_acq = 1
            tx_days = np.random.randint(0, days_since_acq)
            tx_date = acq_date + timedelta(days=tx_days)

            amount = np.random.normal(avg_amount, avg_amount * 0.3)
            amount = max(10, amount)

            transactions.append({
                'transaction_id': f'TXN{len(transactions)+1:08d}',
                'customer_id': cid,
                'transaction_date': tx_date,
                'amount': round(amount, 2)
            })

    transactions_df = pd.DataFrame(transactions)
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])

    return customers, transactions_df


def main():
    """執行CLV分析範例"""
    print("="*80)
    print(" "*20 + "客戶生命週期價值 (CLV) 分析")
    print("="*80)

    # 生成數據
    print("\n生成範例數據...")
    customers, transactions = generate_sample_data(n_customers=500, n_transactions=5000)
    print(f"✓ 客戶數: {len(customers):,}")
    print(f"✓ 交易數: {len(transactions):,}")

    # 初始化分析器
    analyzer = CLVAnalyzer(transactions, customers, discount_rate=0.1)

    # 計算CLV
    print("\n[1/4] 計算歷史CLV...")
    historical = analyzer.calculate_historical_clv()
    print(f"  平均歷史CLV: ${historical['historical_clv'].mean():,.2f}")

    print("\n[2/4] 計算預測CLV...")
    predictive = analyzer.calculate_predictive_clv(prediction_years=3)
    print(f"  平均預測CLV: ${predictive['predicted_clv'].mean():,.2f}")
    print(f"  平均總CLV: ${predictive['total_clv'].mean():,.2f}")

    print("\n[3/4] CLV分群...")
    segmented = analyzer.segment_by_clv()
    segment_counts = segmented['clv_segment'].value_counts()
    for seg, count in segment_counts.items():
        print(f"  {seg}: {count} ({count/len(segmented)*100:.1f}%)")

    print("\n[4/4] 投資回報分析...")
    with_cac = analyzer.calculate_cac_ltv_ratio()
    print(f"  平均LTV/CAC比率: {with_cac['ltv_cac_ratio'].mean():.2f}x")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/clv_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n📄 報告已保存至: data/outputs/clv_analysis_report.txt")

        segmented.to_csv('data/outputs/customer_clv_data.csv')
        print("📊 CLV數據已保存至: data/outputs/customer_clv_data.csv")
    except Exception as e:
        print(f"\n⚠️ 無法保存: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
