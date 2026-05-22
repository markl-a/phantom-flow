"""
欺詐檢測分析範例

這個範例展示如何分析交易數據進行欺詐檢測，包含：
- 異常交易識別
- 風險評分計算
- 行為模式分析
- 規則引擎實現

真實應用場景:
- 銀行信用卡欺詐檢測
- 電商平台交易監控
- 保險理賠欺詐識別
- 帳戶盜用防範
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class FraudDetector:
    """
    欺詐檢測器

    提供完整的欺詐檢測功能:
    - 規則引擎檢測
    - 統計異常檢測
    - 行為分析
    - 風險評分
    """

    def __init__(self, transactions_df: pd.DataFrame,
                 customers_df: Optional[pd.DataFrame] = None):
        """
        初始化檢測器

        Args:
            transactions_df: 交易數據DataFrame
            customers_df: 客戶資料DataFrame (可選)
        """
        self.transactions = transactions_df.copy()
        self.customers = customers_df
        self._prepare_data()
        self.rules = self._init_rules()

    def _prepare_data(self):
        """準備數據"""
        if 'transaction_time' in self.transactions.columns:
            self.transactions['transaction_time'] = pd.to_datetime(
                self.transactions['transaction_time']
            )
            self.transactions['hour'] = self.transactions['transaction_time'].dt.hour
            self.transactions['day_of_week'] = self.transactions['transaction_time'].dt.dayofweek
            self.transactions['is_weekend'] = self.transactions['day_of_week'].isin([5, 6])
            self.transactions['is_night'] = self.transactions['hour'].between(0, 6)

    def _init_rules(self) -> List[Dict]:
        """初始化欺詐檢測規則"""
        return [
            {
                'name': 'high_amount',
                'description': '單筆交易金額異常高',
                'weight': 25,
                'check': lambda row, stats: row['amount'] > stats['amount_p99']
            },
            {
                'name': 'night_transaction',
                'description': '深夜交易 (00:00-06:00)',
                'weight': 15,
                'check': lambda row, stats: row.get('is_night', False)
            },
            {
                'name': 'foreign_transaction',
                'description': '境外交易',
                'weight': 20,
                'check': lambda row, stats: row.get('is_international', False)
            },
            {
                'name': 'new_merchant',
                'description': '首次在此商戶消費',
                'weight': 10,
                'check': lambda row, stats: row.get('is_new_merchant', False)
            },
            {
                'name': 'rapid_succession',
                'description': '短時間內多筆交易',
                'weight': 30,
                'check': lambda row, stats: row.get('tx_count_1h', 0) >= 5
            },
            {
                'name': 'location_anomaly',
                'description': '交易地點異常 (與常用地點不符)',
                'weight': 25,
                'check': lambda row, stats: row.get('location_risk', 0) > 0.7
            },
            {
                'name': 'amount_spike',
                'description': '交易金額大幅超過個人平均',
                'weight': 20,
                'check': lambda row, stats: row['amount'] > row.get('customer_avg_amount', row['amount']) * 3
            },
            {
                'name': 'card_not_present',
                'description': '無卡交易 (線上/電話)',
                'weight': 10,
                'check': lambda row, stats: row.get('transaction_type') == 'CNP'
            },
        ]

    def calculate_statistics(self) -> Dict[str, float]:
        """計算統計基準"""
        df = self.transactions
        return {
            'amount_mean': df['amount'].mean(),
            'amount_std': df['amount'].std(),
            'amount_p95': df['amount'].quantile(0.95),
            'amount_p99': df['amount'].quantile(0.99),
            'amount_max': df['amount'].max(),
            'tx_count_mean': df.groupby('customer_id').size().mean(),
        }

    def apply_rules(self) -> pd.DataFrame:
        """應用規則引擎"""
        df = self.transactions.copy()
        stats = self.calculate_statistics()

        # 初始化風險分數
        df['risk_score'] = 0
        df['triggered_rules'] = [[] for _ in range(len(df))]

        # 計算客戶級別統計
        customer_stats = df.groupby('customer_id').agg({
            'amount': ['mean', 'std', 'count']
        })
        customer_stats.columns = ['customer_avg_amount', 'customer_std_amount', 'customer_tx_count']
        df = df.merge(customer_stats, left_on='customer_id', right_index=True, how='left')

        # 計算1小時內交易次數
        df = df.sort_values(['customer_id', 'transaction_time'])
        df['tx_count_1h'] = df.groupby('customer_id').rolling(
            '1H', on='transaction_time', min_periods=1
        )['transaction_id'].count().reset_index(level=0, drop=True)

        # 應用每條規則
        for rule in self.rules:
            mask = df.apply(lambda row: rule['check'](row, stats), axis=1)
            df.loc[mask, 'risk_score'] += rule['weight']

            # 記錄觸發的規則
            for idx in df[mask].index:
                df.at[idx, 'triggered_rules'].append(rule['name'])

        # 標準化風險分數到 0-100
        max_possible_score = sum(r['weight'] for r in self.rules)
        df['risk_score'] = (df['risk_score'] / max_possible_score * 100).round(1)

        # 風險等級
        df['risk_level'] = pd.cut(
            df['risk_score'],
            bins=[-1, 20, 40, 60, 80, 100],
            labels=['Very Low', 'Low', 'Medium', 'High', 'Critical']
        )

        return df

    def detect_anomalies_statistical(self) -> pd.DataFrame:
        """使用統計方法檢測異常"""
        df = self.transactions.copy()

        # Z-Score 方法
        df['amount_zscore'] = (
            (df['amount'] - df['amount'].mean()) / df['amount'].std()
        ).round(2)

        # IQR 方法
        Q1 = df['amount'].quantile(0.25)
        Q3 = df['amount'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df['is_iqr_outlier'] = (df['amount'] < lower_bound) | (df['amount'] > upper_bound)
        df['is_zscore_outlier'] = df['amount_zscore'].abs() > 3

        # 綜合異常標記
        df['is_statistical_anomaly'] = df['is_iqr_outlier'] | df['is_zscore_outlier']

        return df

    def analyze_customer_behavior(self) -> pd.DataFrame:
        """分析客戶行為模式"""
        df = self.transactions

        behavior = df.groupby('customer_id').agg({
            'amount': ['mean', 'std', 'min', 'max', 'sum', 'count'],
            'transaction_id': 'count',
            'is_night': 'mean' if 'is_night' in df.columns else 'count',
            'is_international': 'mean' if 'is_international' in df.columns else 'count',
        })

        behavior.columns = [
            'avg_amount', 'std_amount', 'min_amount', 'max_amount',
            'total_amount', 'tx_count', 'tx_count_dup',
            'night_tx_ratio', 'intl_tx_ratio'
        ]
        behavior = behavior.drop('tx_count_dup', axis=1)

        # 計算變異係數
        behavior['amount_cv'] = (behavior['std_amount'] / behavior['avg_amount']).round(2)

        # 計算風險指標
        behavior['behavior_risk_score'] = (
            behavior['night_tx_ratio'] * 20 +
            behavior['intl_tx_ratio'] * 15 +
            (behavior['amount_cv'].clip(upper=2) / 2) * 15 +
            (behavior['max_amount'] / behavior['avg_amount'].replace(0, 1)).clip(upper=10) * 10
        ).round(1)

        return behavior.sort_values('behavior_risk_score', ascending=False)

    def get_high_risk_transactions(self, threshold: float = 60) -> pd.DataFrame:
        """獲取高風險交易"""
        df = self.apply_rules()
        high_risk = df[df['risk_score'] >= threshold].copy()

        return high_risk[['transaction_id', 'customer_id', 'amount',
                          'transaction_time', 'risk_score', 'risk_level',
                          'triggered_rules']].sort_values('risk_score', ascending=False)

    def calculate_fraud_metrics(self) -> Dict[str, any]:
        """計算欺詐檢測指標"""
        df = self.apply_rules()

        total_transactions = len(df)
        total_amount = df['amount'].sum()

        # 各風險等級分佈
        risk_distribution = df['risk_level'].value_counts().to_dict()

        # 高風險交易統計
        high_risk = df[df['risk_level'].isin(['High', 'Critical'])]
        high_risk_count = len(high_risk)
        high_risk_amount = high_risk['amount'].sum()

        # 規則觸發統計
        rule_triggers = defaultdict(int)
        for rules in df['triggered_rules']:
            for rule in rules:
                rule_triggers[rule] += 1

        return {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'risk_distribution': risk_distribution,
            'high_risk_count': high_risk_count,
            'high_risk_ratio': high_risk_count / total_transactions * 100,
            'high_risk_amount': high_risk_amount,
            'high_risk_amount_ratio': high_risk_amount / total_amount * 100,
            'rule_triggers': dict(rule_triggers),
            'avg_risk_score': df['risk_score'].mean()
        }

    def generate_alert(self, transaction: pd.Series) -> Dict:
        """為單筆交易生成警報"""
        stats = self.calculate_statistics()

        alerts = []
        total_score = 0

        for rule in self.rules:
            if rule['check'](transaction, stats):
                alerts.append({
                    'rule': rule['name'],
                    'description': rule['description'],
                    'severity': rule['weight']
                })
                total_score += rule['weight']

        max_score = sum(r['weight'] for r in self.rules)
        normalized_score = total_score / max_score * 100

        return {
            'transaction_id': transaction['transaction_id'],
            'risk_score': round(normalized_score, 1),
            'risk_level': 'Critical' if normalized_score >= 80 else
                         ('High' if normalized_score >= 60 else
                          ('Medium' if normalized_score >= 40 else
                           ('Low' if normalized_score >= 20 else 'Very Low'))),
            'alerts': alerts,
            'recommendation': 'Block' if normalized_score >= 80 else
                             ('Review' if normalized_score >= 40 else 'Allow')
        }

    def generate_report(self) -> str:
        """生成欺詐檢測報告"""
        metrics = self.calculate_fraud_metrics()
        behavior = self.analyze_customer_behavior()
        high_risk_tx = self.get_high_risk_transactions()

        report = f"""
{'='*80}
                    欺詐檢測分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、交易概覽
{'='*40}
  交易總數: {metrics['total_transactions']:,}
  交易總額: ${metrics['total_amount']:,.2f}
  平均風險分數: {metrics['avg_risk_score']:.1f}

二、風險分佈
{'='*40}
"""
        for level in ['Critical', 'High', 'Medium', 'Low', 'Very Low']:
            count = metrics['risk_distribution'].get(level, 0)
            pct = count / metrics['total_transactions'] * 100
            icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡',
                   'Low': '🟢', 'Very Low': '⚪'}[level]
            bar = '█' * int(pct)
            report += f"  {icon} {level:10}: {count:5} ({pct:5.1f}%) {bar}\n"

        report += f"""
三、高風險交易
{'='*40}
  高風險交易數: {metrics['high_risk_count']:,} ({metrics['high_risk_ratio']:.2f}%)
  高風險交易金額: ${metrics['high_risk_amount']:,.2f} ({metrics['high_risk_amount_ratio']:.2f}%)

  需立即審查的交易 (Top 10):
"""
        for _, tx in high_risk_tx.head(10).iterrows():
            report += f"    [{tx['risk_level']}] {tx['transaction_id']}: "
            report += f"${tx['amount']:,.2f}, 風險分數 {tx['risk_score']}\n"
            report += f"           觸發規則: {', '.join(tx['triggered_rules'])}\n"

        report += f"""
四、規則觸發統計
{'='*40}
"""
        sorted_rules = sorted(metrics['rule_triggers'].items(),
                             key=lambda x: x[1], reverse=True)
        for rule, count in sorted_rules:
            pct = count / metrics['total_transactions'] * 100
            bar = '█' * int(pct * 2)
            report += f"  {rule:25}: {count:5} ({pct:.1f}%) {bar}\n"

        report += f"""
五、高風險客戶
{'='*40}
"""
        high_risk_customers = behavior.head(10)
        for customer_id, row in high_risk_customers.iterrows():
            report += f"  {customer_id}:\n"
            report += f"    交易次數: {row['tx_count']:.0f}, 總金額: ${row['total_amount']:,.2f}\n"
            report += f"    行為風險分數: {row['behavior_risk_score']:.1f}\n"
            report += f"    深夜交易比例: {row['night_tx_ratio']*100:.1f}%\n"

        report += f"""
六、建議措施
{'='*40}

1. 立即行動:
   - 審查 {min(metrics['high_risk_count'], 50)} 筆高風險交易
   - 聯繫高風險客戶確認交易真實性
   - 暫時凍結可疑帳戶

2. 規則優化:
   - 調整觸發率最高的規則閾值
   - 新增針對特定模式的規則
   - 定期審查規則有效性

3. 系統改進:
   - 實施即時監控告警
   - 整合更多數據源 (設備、位置)
   - 考慮機器學習模型輔助

4. 長期策略:
   - 建立客戶行為基線
   - 實施多因素認證
   - 加強員工詐騙意識培訓

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_transaction_data(n_transactions: int = 10000,
                              n_customers: int = 1000,
                              fraud_rate: float = 0.02,
                              seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """生成模擬交易數據"""
    np.random.seed(seed)
    today = datetime.now()

    # 客戶資料
    customers = []
    for i in range(1, n_customers + 1):
        customers.append({
            'customer_id': f'CUST{i:05d}',
            'customer_since': today - timedelta(days=np.random.randint(30, 1000)),
            'avg_monthly_spend': np.random.lognormal(6, 1),
            'risk_tier': np.random.choice(['Low', 'Medium', 'High'], p=[0.7, 0.2, 0.1])
        })
    customers_df = pd.DataFrame(customers)

    # 商戶類型
    merchant_categories = [
        'Grocery', 'Restaurant', 'Gas Station', 'Online Shopping',
        'Entertainment', 'Travel', 'Electronics', 'Healthcare'
    ]

    # 交易記錄
    transactions = []
    for i in range(1, n_transactions + 1):
        customer = customers_df.sample(1).iloc[0]
        customer_id = customer['customer_id']

        # 判斷是否為欺詐交易
        is_fraud = np.random.random() < fraud_rate

        # 交易時間
        days_ago = np.random.randint(0, 90)
        if is_fraud:
            # 欺詐交易更可能發生在深夜
            hour = np.random.choice(range(24), p=[
                0.08, 0.08, 0.08, 0.07, 0.06, 0.05, 0.03, 0.03,
                0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03,
                0.03, 0.03, 0.03, 0.03, 0.03, 0.04, 0.05, 0.06
            ])
        else:
            hour = np.random.choice(range(24), p=[
                0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05,
                0.06, 0.07, 0.08, 0.08, 0.08, 0.07, 0.06, 0.06,
                0.05, 0.05, 0.05, 0.04, 0.04, 0.03, 0.02, 0.01
            ])

        tx_time = today - timedelta(days=days_ago, hours=24-hour,
                                    minutes=np.random.randint(0, 60))

        # 交易金額
        if is_fraud:
            # 欺詐交易金額通常較高
            amount = np.random.lognormal(7, 1.5)
        else:
            amount = np.random.lognormal(4, 1)
        amount = max(1, min(amount, 50000))

        # 商戶
        merchant_category = np.random.choice(merchant_categories)
        merchant_id = f'MERCH{np.random.randint(1, 500):04d}'

        # 交易類型
        if is_fraud:
            tx_type = np.random.choice(['POS', 'CNP', 'ATM'], p=[0.2, 0.7, 0.1])
        else:
            tx_type = np.random.choice(['POS', 'CNP', 'ATM'], p=[0.6, 0.3, 0.1])

        # 位置風險
        if is_fraud:
            location_risk = np.random.uniform(0.5, 1.0)
            is_international = np.random.random() < 0.4
        else:
            location_risk = np.random.uniform(0, 0.3)
            is_international = np.random.random() < 0.05

        # 是否新商戶
        is_new_merchant = np.random.random() < (0.3 if is_fraud else 0.05)

        transactions.append({
            'transaction_id': f'TX{i:08d}',
            'customer_id': customer_id,
            'merchant_id': merchant_id,
            'merchant_category': merchant_category,
            'amount': round(amount, 2),
            'transaction_time': tx_time,
            'transaction_type': tx_type,
            'is_international': is_international,
            'is_new_merchant': is_new_merchant,
            'location_risk': round(location_risk, 2),
            'is_fraud': is_fraud  # 標記 (實際場景中這是未知的)
        })

    transactions_df = pd.DataFrame(transactions)

    return transactions_df, customers_df


def main():
    """執行欺詐檢測分析範例"""
    print("="*80)
    print(" "*20 + "欺詐檢測分析")
    print("="*80)

    # 準備數據
    print("\n[1/4] 準備交易數據...")
    transactions, customers = generate_transaction_data(
        n_transactions=10000, n_customers=1000, fraud_rate=0.02
    )

    actual_fraud = transactions['is_fraud'].sum()
    print(f"  ✓ 交易總數: {len(transactions):,}")
    print(f"  ✓ 客戶數: {len(customers)}")
    print(f"  ✓ 實際欺詐交易: {actual_fraud} ({actual_fraud/len(transactions)*100:.2f}%)")

    # 初始化檢測器
    print("\n[2/4] 初始化欺詐檢測器...")
    detector = FraudDetector(transactions, customers)
    print("  ✓ 檢測器初始化完成")
    print(f"  ✓ 載入 {len(detector.rules)} 條檢測規則")

    # 應用規則檢測
    print("\n[3/4] 應用規則引擎...")
    results = detector.apply_rules()
    metrics = detector.calculate_fraud_metrics()

    print(f"\n  📊 檢測結果:")
    print(f"     高風險交易: {metrics['high_risk_count']} ({metrics['high_risk_ratio']:.2f}%)")
    print(f"     高風險金額: ${metrics['high_risk_amount']:,.2f}")

    # 評估檢測效果
    print("\n[4/4] 評估檢測效果...")
    high_risk = results[results['risk_level'].isin(['High', 'Critical'])]
    true_positives = high_risk['is_fraud'].sum()
    false_positives = len(high_risk) - true_positives

    actual_fraud_detected = true_positives
    recall = true_positives / actual_fraud * 100 if actual_fraud > 0 else 0
    precision = true_positives / len(high_risk) * 100 if len(high_risk) > 0 else 0

    print(f"\n  ✓ 檢出率 (Recall): {recall:.1f}%")
    print(f"  ✓ 精確率 (Precision): {precision:.1f}%")
    print(f"  ✓ 真陽性: {true_positives}, 假陽性: {false_positives}")

    # 生成報告
    print("\n" + "="*80)
    report = detector.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/fraud_detection_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/fraud_detection_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return detector


if __name__ == "__main__":
    detector = main()
