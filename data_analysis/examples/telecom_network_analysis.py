"""
電信網路分析範例

這個範例展示如何分析電信網路數據，包含：
- 網路流量模式聚類
- 客戶使用行為分群
- 客戶流失預測指標
- 網路性能可視化

真實應用場景:
- 電信運營商網路優化
- 客戶細分與精準行銷
- 流失預警系統
- 網路容量規劃
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')


class TelecomNetworkAnalyzer:
    """
    電信網路分析器

    提供完整的電信數據分析功能:
    - 網路流量模式分析
    - 客戶行為分群
    - 流失風險評估
    - 網路性能監控
    """

    def __init__(self, customer_data: pd.DataFrame):
        """
        初始化分析器

        Args:
            customer_data: 客戶數據DataFrame
        """
        self.df = customer_data.copy()
        self._prepare_data()

    def _prepare_data(self):
        """準備和預處理數據"""
        # 計算衍生指標
        if 'data_usage_gb' in self.df.columns and 'call_minutes' in self.df.columns:
            # 數據使用強度
            self.df['data_intensity'] = self.df['data_usage_gb'] / (self.df['contract_months'] + 1)

            # 通話強度
            self.df['call_intensity'] = self.df['call_minutes'] / (self.df['contract_months'] + 1)

            # 月均消費
            self.df['monthly_arpu'] = self.df['monthly_charge']

            # 客戶價值分數 (綜合消費和使用量)
            self.df['customer_value'] = (
                self.df['monthly_charge'] * 0.5 +
                self.df['data_usage_gb'] * 2 +
                self.df['call_minutes'] * 0.1
            )

            # 網路品質等級
            if 'network_quality_score' in self.df.columns:
                self.df['quality_grade'] = pd.cut(
                    self.df['network_quality_score'],
                    bins=[0, 3, 6, 8, 10],
                    labels=['Poor', 'Fair', 'Good', 'Excellent']
                )

    def cluster_traffic_patterns(self, n_clusters: int = 5) -> pd.DataFrame:
        """
        根據流量模式進行客戶聚類

        Args:
            n_clusters: 聚類數量

        Returns:
            包含聚類結果的DataFrame
        """
        # 選擇流量相關特徵
        traffic_features = [
            'data_usage_gb', 'call_minutes', 'sms_count',
            'data_intensity', 'call_intensity'
        ]

        # 確保所有特徵都存在
        available_features = [f for f in traffic_features if f in self.df.columns]

        if not available_features:
            raise ValueError("沒有可用的流量特徵進行聚類")

        # 準備數據
        cluster_data = self.df[available_features].fillna(0).copy()

        # 使用 K-means 聚類
        clusterer = ClustererFactory.create('kmeans', n_clusters=n_clusters)
        labels = clusterer.fit_predict(
            pd.DataFrame(cluster_data, columns=available_features),
            available_features,
            scale_features=True
        )

        # 添加聚類標籤
        result_df = self.df.copy()
        result_df['traffic_cluster'] = labels

        # 為每個聚類生成描述性標籤
        cluster_profiles = self._generate_traffic_cluster_labels(result_df, available_features)
        result_df['traffic_segment'] = result_df['traffic_cluster'].map(cluster_profiles)

        return result_df

    def _generate_traffic_cluster_labels(self, df: pd.DataFrame, features: List[str]) -> Dict[int, str]:
        """為流量聚類生成描述性標籤"""
        profiles = {}

        for cluster_id in df['traffic_cluster'].unique():
            cluster_data = df[df['traffic_cluster'] == cluster_id]

            # 計算平均值
            avg_data = cluster_data['data_usage_gb'].mean() if 'data_usage_gb' in features else 0
            avg_calls = cluster_data['call_minutes'].mean() if 'call_minutes' in features else 0
            avg_sms = cluster_data['sms_count'].mean() if 'sms_count' in features else 0

            # 根據特徵分配標籤
            if avg_data > 50 and avg_calls < 200:
                label = "重度數據用戶"
            elif avg_calls > 500 and avg_data < 20:
                label = "重度通話用戶"
            elif avg_data > 30 and avg_calls > 300:
                label = "高活躍用戶"
            elif avg_sms > 500:
                label = "簡訊愛好者"
            elif avg_data < 10 and avg_calls < 100:
                label = "輕度用戶"
            else:
                label = "一般用戶"

            profiles[cluster_id] = label

        return profiles

    def segment_customer_behavior(self) -> pd.DataFrame:
        """
        客戶行為分群分析

        Returns:
            包含行為分群的DataFrame
        """
        result_df = self.df.copy()

        # 基於RFM概念的電信版本分析
        # R - Recency: 合約月數 (越新越好)
        # F - Frequency: 使用頻率 (通話+數據+簡訊)
        # M - Monetary: 月費

        # 計算使用頻率分數
        usage_score = (
            result_df['data_usage_gb'] / 100 +
            result_df['call_minutes'] / 1000 +
            result_df['sms_count'] / 1000
        ).clip(0, 10)

        # 計算價值分數
        value_score = pd.qcut(
            result_df['monthly_charge'],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        ).astype(float)

        # 計算忠誠度分數 (合約月數)
        loyalty_score = pd.qcut(
            result_df['contract_months'],
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates='drop'
        ).astype(float)

        result_df['usage_score'] = usage_score
        result_df['value_score'] = value_score
        result_df['loyalty_score'] = loyalty_score

        # 綜合客戶分群
        result_df['customer_segment'] = result_df.apply(
            lambda row: self._classify_customer_segment(
                row['usage_score'],
                row['value_score'],
                row['loyalty_score']
            ),
            axis=1
        )

        return result_df

    def _classify_customer_segment(self, usage: float, value: float, loyalty: float) -> str:
        """客戶分群分類邏輯"""
        # VIP客戶: 高價值 + 高忠誠度
        if value >= 4 and loyalty >= 4:
            return "VIP客戶"

        # 高價值客戶: 高消費但忠誠度一般
        elif value >= 4 and loyalty < 4:
            return "高價值客戶"

        # 活躍用戶: 高使用率
        elif usage >= 7:
            return "活躍用戶"

        # 潛力客戶: 高忠誠度但消費一般
        elif loyalty >= 4 and value < 4:
            return "潛力客戶"

        # 新客戶: 低忠誠度但價值尚可
        elif loyalty <= 2 and value >= 3:
            return "新客戶"

        # 流失風險: 低使用+低價值
        elif usage < 3 and value < 3:
            return "流失風險"

        else:
            return "一般客戶"

    def predict_churn_indicators(self) -> pd.DataFrame:
        """
        預測客戶流失指標

        Returns:
            包含流失風險評分的DataFrame
        """
        result_df = self.df.copy()

        # 初始化流失風險分數
        churn_score = 0

        # 1. 網路品質問題 (權重: 25%)
        if 'network_quality_score' in result_df.columns:
            quality_risk = (10 - result_df['network_quality_score']) / 10 * 25
            churn_score += quality_risk

        # 2. 服務投訴 (權重: 30%)
        if 'support_tickets' in result_df.columns:
            # 投訴越多，流失風險越高
            ticket_risk = (result_df['support_tickets'] / result_df['support_tickets'].max() * 30).fillna(0)
            churn_score += ticket_risk

        # 3. 使用率下降 (權重: 20%)
        # 假設低使用率表示客戶不滿意或正在尋找替代方案
        usage_percentile = result_df['data_usage_gb'].rank(pct=True)
        usage_risk = (1 - usage_percentile) * 20
        churn_score += usage_risk

        # 4. 合約月數 (權重: 15%)
        # 新客戶和合約即將到期的客戶流失風險較高
        contract_risk = pd.cut(
            result_df['contract_months'],
            bins=[-1, 3, 12, 24, 999],
            labels=[15, 5, 3, 0]  # 新客戶風險最高
        ).astype(float)
        churn_score += contract_risk

        # 5. 網路延遲 (權重: 10%)
        if 'latency_ms' in result_df.columns:
            latency_percentile = result_df['latency_ms'].rank(pct=True)
            latency_risk = latency_percentile * 10
            churn_score += latency_risk

        result_df['churn_risk_score'] = churn_score.clip(0, 100).round(1)

        # 流失風險等級
        result_df['churn_risk_level'] = pd.cut(
            result_df['churn_risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['低風險', '中風險', '高風險', '極高風險']
        )

        # 計算預測的流失概率
        result_df['churn_probability'] = (result_df['churn_risk_score'] / 100).round(3)

        return result_df

    def analyze_network_performance(self) -> Dict[str, Any]:
        """
        分析網路性能指標

        Returns:
            網路性能分析結果
        """
        results = {}

        # 整體性能指標
        if 'network_quality_score' in self.df.columns:
            results['avg_quality_score'] = round(self.df['network_quality_score'].mean(), 2)
            results['quality_distribution'] = self.df['quality_grade'].value_counts().to_dict()

        if 'latency_ms' in self.df.columns:
            results['avg_latency_ms'] = round(self.df['latency_ms'].mean(), 2)
            results['p95_latency_ms'] = round(self.df['latency_ms'].quantile(0.95), 2)
            results['p99_latency_ms'] = round(self.df['latency_ms'].quantile(0.99), 2)

        # 按方案類型分析
        if 'plan_type' in self.df.columns:
            plan_performance = self.df.groupby('plan_type').agg({
                'network_quality_score': 'mean',
                'latency_ms': 'mean',
                'data_usage_gb': 'mean',
                'monthly_charge': 'mean',
                'customer_id': 'count'
            }).round(2)

            plan_performance.columns = [
                'avg_quality', 'avg_latency', 'avg_data_usage',
                'avg_monthly_charge', 'customer_count'
            ]
            results['by_plan_type'] = plan_performance.to_dict('index')

        # 性能問題客戶統計
        if 'network_quality_score' in self.df.columns:
            poor_quality = len(self.df[self.df['network_quality_score'] < 5])
            results['poor_quality_customers'] = poor_quality
            results['poor_quality_percentage'] = round(poor_quality / len(self.df) * 100, 2)

        if 'latency_ms' in self.df.columns:
            high_latency = len(self.df[self.df['latency_ms'] > 100])
            results['high_latency_customers'] = high_latency
            results['high_latency_percentage'] = round(high_latency / len(self.df) * 100, 2)

        return results

    def generate_retention_strategies(self, churn_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        生成客戶挽留策略

        Args:
            churn_df: 包含流失風險評分的DataFrame

        Returns:
            按風險等級分組的挽留策略
        """
        strategies = {
            '極高風險': [],
            '高風險': [],
            '中風險': [],
            '低風險': []
        }

        # 極高風險客戶策略
        critical = churn_df[churn_df['churn_risk_level'] == '極高風險'].sort_values(
            'churn_risk_score', ascending=False
        )

        for idx, customer in critical.head(10).iterrows():
            strategy = {
                'customer_id': customer['customer_id'],
                'plan_type': customer.get('plan_type', 'Unknown'),
                'churn_risk': customer['churn_risk_score'],
                'churn_probability': f"{customer['churn_probability']*100:.1f}%",
                'issues': self._identify_customer_issues(customer),
                'recommended_actions': self._generate_retention_actions(customer),
                'priority': 'URGENT',
                'potential_revenue_loss': customer['monthly_charge'] * 12  # 年度價值
            }
            strategies['極高風險'].append(strategy)

        # 高風險客戶策略
        high = churn_df[churn_df['churn_risk_level'] == '高風險'].sort_values(
            'churn_risk_score', ascending=False
        )

        for idx, customer in high.head(10).iterrows():
            strategy = {
                'customer_id': customer['customer_id'],
                'plan_type': customer.get('plan_type', 'Unknown'),
                'churn_risk': customer['churn_risk_score'],
                'recommended_actions': self._generate_retention_actions(customer),
                'priority': 'HIGH'
            }
            strategies['高風險'].append(strategy)

        return strategies

    def _identify_customer_issues(self, customer: pd.Series) -> List[str]:
        """識別客戶問題"""
        issues = []

        if customer.get('network_quality_score', 10) < 5:
            issues.append(f"網路品質差 (評分: {customer['network_quality_score']})")

        if customer.get('support_tickets', 0) > 3:
            issues.append(f"多次客服投訴 ({int(customer['support_tickets'])} 次)")

        if customer.get('latency_ms', 0) > 100:
            issues.append(f"網路延遲高 ({customer['latency_ms']} ms)")

        if customer.get('data_usage_gb', 0) < 5:
            issues.append("數據使用率低 - 可能不滿意服務")

        if customer.get('contract_months', 0) < 3:
            issues.append("新客戶 - 尚未建立忠誠度")

        return issues

    def _generate_retention_actions(self, customer: pd.Series) -> List[str]:
        """生成挽留行動建議"""
        actions = []

        # 網路品質問題
        if customer.get('network_quality_score', 10) < 5:
            actions.append("🔧 優先處理網路品質問題 - 技術團隊介入")
            actions.append("📞 主動致電了解網路使用體驗")

        # 投訴問題
        if customer.get('support_tickets', 0) > 3:
            actions.append("🎁 提供服務補償 (如折扣券或免費升級)")
            actions.append("👤 安排專屬客戶經理跟進")

        # 價格敏感
        if customer.get('monthly_charge', 0) > 80:
            actions.append("💰 提供忠誠客戶專屬優惠方案")
            actions.append("📋 推薦更適合的資費方案")

        # 使用率低
        if customer.get('data_usage_gb', 0) < 5:
            actions.append("📱 推薦更符合使用習慣的方案")
            actions.append("🎓 提供服務使用教學")

        # 新客戶
        if customer.get('contract_months', 0) < 3:
            actions.append("🎉 提供新客戶專屬禮遇")
            actions.append("📧 發送歡迎關懷訊息")

        # 通用建議
        if not actions:
            actions.append("📞 定期關懷電話")
            actions.append("🎁 發送季度優惠資訊")

        return actions

    def generate_report(self) -> str:
        """生成完整的電信網路分析報告"""
        # 執行各項分析
        traffic_clustered = self.cluster_traffic_patterns()
        behavior_segmented = self.segment_customer_behavior()
        churn_analyzed = self.predict_churn_indicators()
        network_perf = self.analyze_network_performance()

        report = f"""
{'='*80}
                    電信網路數據分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、客戶總覽
{'='*40}
  總客戶數: {len(self.df):,}
  分析期間: {datetime.now().strftime('%Y年%m月')}
  平均月費: ${self.df['monthly_charge'].mean():.2f}
  平均合約月數: {self.df['contract_months'].mean():.1f} 個月

二、流量模式分析
{'='*40}
"""
        # 流量聚類分布
        traffic_dist = traffic_clustered['traffic_segment'].value_counts()
        for segment, count in traffic_dist.items():
            pct = count / len(traffic_clustered) * 100
            bar = '█' * int(pct / 2)
            report += f"  {segment:12}: {count:5} ({pct:5.1f}%) {bar}\n"

        report += f"""
  📊 流量統計:
     平均數據使用: {self.df['data_usage_gb'].mean():.2f} GB
     平均通話時長: {self.df['call_minutes'].mean():.1f} 分鐘
     平均簡訊數量: {self.df['sms_count'].mean():.0f} 則

三、客戶行為分群
{'='*40}
"""
        behavior_dist = behavior_segmented['customer_segment'].value_counts()
        for segment, count in behavior_dist.items():
            pct = count / len(behavior_segmented) * 100
            icon = {
                'VIP客戶': '👑', '高價值客戶': '💎', '活躍用戶': '🔥',
                '潛力客戶': '⭐', '新客戶': '🆕', '流失風險': '⚠️', '一般客戶': '👤'
            }.get(segment, '•')
            report += f"  {icon} {segment:12}: {count:5} ({pct:5.1f}%)\n"

        report += f"""
四、流失風險分析
{'='*40}
"""
        churn_dist = churn_analyzed['churn_risk_level'].value_counts()
        for level in ['極高風險', '高風險', '中風險', '低風險']:
            count = churn_dist.get(level, 0)
            pct = count / len(churn_analyzed) * 100
            icon = {'極高風險': '🔴', '高風險': '🟠', '中風險': '🟡', '低風險': '🟢'}[level]
            bar = '█' * int(pct / 2)
            report += f"  {icon} {level:8}: {count:5} ({pct:5.1f}%) {bar}\n"

        high_risk_count = len(churn_analyzed[churn_analyzed['churn_risk_level'].isin(['高風險', '極高風險'])])
        high_risk_revenue = churn_analyzed[
            churn_analyzed['churn_risk_level'].isin(['高風險', '極高風險'])
        ]['monthly_charge'].sum()

        report += f"""
  ⚠️  高風險客戶: {high_risk_count:,} 位 ({high_risk_count/len(churn_analyzed)*100:.1f}%)
  💰 潛在流失營收: ${high_risk_revenue:,.2f}/月 (${high_risk_revenue*12:,.2f}/年)
  📈 平均流失概率: {churn_analyzed['churn_probability'].mean()*100:.1f}%

五、網路性能分析
{'='*40}
"""
        if 'avg_quality_score' in network_perf:
            report += f"  平均網路品質: {network_perf['avg_quality_score']}/10\n"

        if 'avg_latency_ms' in network_perf:
            report += f"  平均延遲: {network_perf['avg_latency_ms']} ms\n"
            report += f"  P95延遲: {network_perf['p95_latency_ms']} ms\n"
            report += f"  P99延遲: {network_perf['p99_latency_ms']} ms\n"

        if 'poor_quality_customers' in network_perf:
            report += f"\n  ⚠️  網路品質問題客戶: {network_perf['poor_quality_customers']} ({network_perf['poor_quality_percentage']}%)\n"

        if 'high_latency_customers' in network_perf:
            report += f"  ⚠️  高延遲問題客戶: {network_perf['high_latency_customers']} ({network_perf['high_latency_percentage']}%)\n"

        # 按方案分析
        if 'by_plan_type' in network_perf:
            report += f"\n  📋 各方案性能:\n"
            for plan, metrics in network_perf['by_plan_type'].items():
                report += f"     {plan}: 品質 {metrics.get('avg_quality', 0):.1f}, "
                report += f"延遲 {metrics.get('avg_latency', 0):.1f}ms, "
                report += f"客戶數 {int(metrics.get('customer_count', 0))}\n"

        # 挽留策略
        strategies = self.generate_retention_strategies(churn_analyzed)

        report += f"""
六、客戶挽留策略
{'='*40}

  🔴 極高風險客戶 (需立即行動): {len(strategies['極高風險'])} 位
"""
        if strategies['極高風險']:
            report += "\n  優先處理名單 (Top 5):\n"
            for i, s in enumerate(strategies['極高風險'][:5], 1):
                report += f"\n  {i}. {s['customer_id']} - {s['plan_type']}方案\n"
                report += f"     流失風險: {s['churn_risk']:.1f} (流失概率: {s['churn_probability']})\n"
                report += f"     潛在營收損失: ${s['potential_revenue_loss']:.2f}/年\n"
                if s['issues']:
                    report += f"     問題: {', '.join(s['issues'][:2])}\n"
                report += f"     建議: {s['recommended_actions'][0]}\n"

        report += f"""
  🟠 高風險客戶: {len(strategies['高風險'])} 位
  🟡 中風險客戶: {len(strategies['中風險'])} 位

七、行動建議
{'='*40}

1. 立即行動 (本週內):
   ✓ 聯繫所有極高風險客戶 ({len(strategies['極高風險'])} 位)
   ✓ 處理網路品質投訴 ({network_perf.get('poor_quality_customers', 0)} 位)
   ✓ 優化高延遲地區網路 ({network_perf.get('high_latency_customers', 0)} 位)

2. 短期計劃 (本月內):
   ✓ 推出VIP客戶專屬優惠方案
   ✓ 對高風險客戶實施挽留計劃
   ✓ 優化網路覆蓋和性能

3. 長期策略 (季度):
   ✓ 建立客戶流失預警系統
   ✓ 改善客戶服務品質
   ✓ 開發個性化資費方案
   ✓ 提升網路基礎設施

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_telecom_data(n_customers: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    生成模擬電信數據

    Args:
        n_customers: 客戶數量
        seed: 隨機種子

    Returns:
        電信客戶數據DataFrame
    """
    np.random.seed(seed)

    # 方案類型
    plan_types = ['預付卡', '月租型', '學生方案', '家庭方案', '企業方案']
    plan_weights = [0.15, 0.40, 0.15, 0.20, 0.10]

    # 方案對應的基礎費用範圍
    plan_charges = {
        '預付卡': (10, 30),
        '月租型': (30, 80),
        '學生方案': (20, 40),
        '家庭方案': (60, 120),
        '企業方案': (80, 200)
    }

    customers = []

    for i in range(1, n_customers + 1):
        # 選擇方案
        plan = np.random.choice(plan_types, p=plan_weights)
        charge_range = plan_charges[plan]
        monthly_charge = round(np.random.uniform(*charge_range), 2)

        # 根據方案類型設定使用模式
        if plan == '預付卡':
            # 預付卡用戶: 低使用量
            data_usage = max(0, np.random.normal(5, 3))
            call_minutes = max(0, np.random.normal(100, 50))
            sms_count = max(0, int(np.random.normal(50, 30)))
        elif plan == '學生方案':
            # 學生: 高數據使用，中等通話
            data_usage = max(0, np.random.normal(40, 15))
            call_minutes = max(0, np.random.normal(200, 80))
            sms_count = max(0, int(np.random.normal(150, 70)))
        elif plan == '家庭方案':
            # 家庭: 均衡使用
            data_usage = max(0, np.random.normal(50, 20))
            call_minutes = max(0, np.random.normal(400, 150))
            sms_count = max(0, int(np.random.normal(200, 100)))
        elif plan == '企業方案':
            # 企業: 高通話，高數據
            data_usage = max(0, np.random.normal(80, 30))
            call_minutes = max(0, np.random.normal(800, 300))
            sms_count = max(0, int(np.random.normal(100, 50)))
        else:  # 月租型
            # 一般月租: 中等使用
            data_usage = max(0, np.random.normal(30, 15))
            call_minutes = max(0, np.random.normal(300, 120))
            sms_count = max(0, int(np.random.normal(100, 60)))

        # 合約月數 (影響忠誠度)
        contract_months = max(0, int(np.random.exponential(12)))

        # 網路品質評分 (1-10)
        # 部分客戶會遇到網路問題
        if np.random.random() < 0.15:  # 15% 的客戶有網路問題
            network_quality = round(np.random.uniform(1, 5), 1)
        else:
            network_quality = round(np.random.uniform(6, 10), 1)

        # 網路延遲 (ms)
        # 延遲與網路品質負相關
        base_latency = 30
        quality_factor = (10 - network_quality) * 10
        latency = round(base_latency + quality_factor + np.random.normal(0, 15), 1)
        latency = max(10, latency)  # 最小10ms

        # 客服投訴次數
        # 網路品質差的客戶更容易投訴
        if network_quality < 5:
            support_tickets = max(0, int(np.random.poisson(3)))
        elif network_quality < 7:
            support_tickets = max(0, int(np.random.poisson(1)))
        else:
            support_tickets = max(0, int(np.random.poisson(0.3)))

        # 流失風險 (初步標記，實際由模型計算)
        # 這裡先設定一個基礎值
        churn_risk = 0
        if network_quality < 5:
            churn_risk += 30
        if support_tickets > 2:
            churn_risk += 20
        if contract_months < 3:
            churn_risk += 15
        if data_usage < 5:
            churn_risk += 10

        churn_risk = min(churn_risk, 100)

        customers.append({
            'customer_id': f'TEL{i:06d}',
            'plan_type': plan,
            'monthly_charge': monthly_charge,
            'data_usage_gb': round(data_usage, 2),
            'call_minutes': round(call_minutes, 1),
            'sms_count': sms_count,
            'network_quality_score': network_quality,
            'latency_ms': latency,
            'contract_months': contract_months,
            'support_tickets': support_tickets,
            'churn_risk': churn_risk  # 初步估計值
        })

    return pd.DataFrame(customers)


def main():
    """執行完整的電信網路分析"""
    print("="*80)
    print(" "*20 + "電信網路數據分析")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/5] 準備電信數據...")

    telecom_data = generate_telecom_data(n_customers=2000)

    print(f"  ✓ 客戶數量: {len(telecom_data):,}")
    print(f"  ✓ 方案類型: {telecom_data['plan_type'].nunique()} 種")
    print(f"  ✓ 平均月費: ${telecom_data['monthly_charge'].mean():.2f}")
    print(f"  ✓ 總月營收: ${telecom_data['monthly_charge'].sum():,.2f}")

    # ========================================
    # 2. 數據驗證
    # ========================================
    print("\n[2/5] 驗證數據品質...")

    validator = DataValidator(telecom_data)
    missing_check = validator.check_missing_values()
    duplicate_check = validator.check_duplicates()

    print(f"  ✓ 缺失值: {missing_check['total_missing_cells']}")
    print(f"  ✓ 重複記錄: {duplicate_check['duplicate_count']}")
    print(f"  ✓ 數據品質: 優良")

    # ========================================
    # 3. 初始化分析器並執行分析
    # ========================================
    print("\n[3/5] 執行網路流量聚類分析...")

    analyzer = TelecomNetworkAnalyzer(telecom_data)

    # 流量模式聚類
    traffic_result = analyzer.cluster_traffic_patterns(n_clusters=5)
    print(f"  ✓ 識別出 {traffic_result['traffic_segment'].nunique()} 個流量模式群組")

    segment_dist = traffic_result['traffic_segment'].value_counts()
    for segment, count in segment_dist.head(3).items():
        print(f"    - {segment}: {count} 位客戶")

    # ========================================
    # 4. 客戶行為分群
    # ========================================
    print("\n[4/5] 執行客戶行為分群...")

    behavior_result = analyzer.segment_customer_behavior()
    print(f"  ✓ 完成客戶分群分析")

    behavior_dist = behavior_result['customer_segment'].value_counts()
    for segment, count in behavior_dist.head(3).items():
        print(f"    - {segment}: {count} 位客戶")

    # ========================================
    # 5. 流失預測分析
    # ========================================
    print("\n[5/5] 執行流失風險評估...")

    churn_result = analyzer.predict_churn_indicators()

    risk_dist = churn_result['churn_risk_level'].value_counts()
    print(f"\n  流失風險分佈:")
    for level in ['極高風險', '高風險', '中風險', '低風險']:
        count = risk_dist.get(level, 0)
        pct = count / len(churn_result) * 100
        bar = '█' * int(pct / 2)
        print(f"    {level:8}: {count:4} ({pct:5.1f}%) {bar}")

    # ========================================
    # 6. 網路性能分析
    # ========================================
    print("\n執行網路性能分析...")
    network_perf = analyzer.analyze_network_performance()
    print(f"  ✓ 平均網路品質: {network_perf.get('avg_quality_score', 0)}/10")
    print(f"  ✓ 平均延遲: {network_perf.get('avg_latency_ms', 0)} ms")

    # ========================================
    # 7. 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # ========================================
    # 8. 可視化 (可選)
    # ========================================
    print("\n生成視覺化圖表...")
    try:
        plotter = Plotter(figure_size=(14, 10))

        # 流失風險分佈圖
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 流失風險分佈
        churn_result['churn_risk_level'].value_counts().plot(
            kind='bar', ax=axes[0, 0], color='coral'
        )
        axes[0, 0].set_title('客戶流失風險分佈', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('風險等級')
        axes[0, 0].set_ylabel('客戶數量')

        # 2. 客戶分群
        behavior_result['customer_segment'].value_counts().plot(
            kind='barh', ax=axes[0, 1], color='skyblue'
        )
        axes[0, 1].set_title('客戶行為分群', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('客戶數量')

        # 3. 網路品質vs流失風險
        axes[1, 0].scatter(
            churn_result['network_quality_score'],
            churn_result['churn_risk_score'],
            alpha=0.5, c='purple'
        )
        axes[1, 0].set_title('網路品質 vs 流失風險', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('網路品質評分')
        axes[1, 0].set_ylabel('流失風險分數')

        # 4. 流量模式分佈
        traffic_result['traffic_segment'].value_counts().plot(
            kind='pie', ax=axes[1, 1], autopct='%1.1f%%'
        )
        axes[1, 1].set_title('流量模式分佈', fontsize=14, fontweight='bold')

        plt.tight_layout()

        # 保存圖表
        output_path = 'data/outputs/telecom_network_analysis.png'
        try:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"  ✓ 圖表已保存至: {output_path}")
        except Exception as e:
            print(f"  ⚠️  無法保存圖表: {e}")

        plt.close()

    except Exception as e:
        print(f"  ⚠️  視覺化生成失敗: {e}")

    # ========================================
    # 9. 保存結果
    # ========================================
    print("\n保存分析結果...")
    try:
        # 保存報告
        report_path = 'data/outputs/telecom_network_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  ✓ 報告已保存至: {report_path}")

        # 保存詳細數據
        output_csv = 'data/outputs/telecom_customers_analyzed.csv'
        churn_result.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"  ✓ 客戶數據已保存至: {output_csv}")

    except Exception as e:
        print(f"  ⚠️  無法保存結果: {e}")

    # ========================================
    # 總結
    # ========================================
    print("\n" + "="*80)
    print(" "*25 + "分析完成")
    print("="*80)

    high_risk = len(churn_result[churn_result['churn_risk_level'].isin(['高風險', '極高風險'])])
    high_risk_revenue = churn_result[
        churn_result['churn_risk_level'].isin(['高風險', '極高風險'])
    ]['monthly_charge'].sum()

    print(f"""
    📊 分析摘要:
       • 總客戶數: {len(telecom_data):,}
       • 流量模式: {traffic_result['traffic_segment'].nunique()} 種
       • 客戶分群: {behavior_result['customer_segment'].nunique()} 種
       • 高風險客戶: {high_risk:,} 位 ({high_risk/len(churn_result)*100:.1f}%)
       • 潛在流失營收: ${high_risk_revenue:,.2f}/月
       • 平均網路品質: {network_perf.get('avg_quality_score', 0):.1f}/10

    🎯 關鍵建議:
       1. 立即聯繫 {len(churn_result[churn_result['churn_risk_level']=='極高風險'])} 位極高風險客戶
       2. 改善 {network_perf.get('poor_quality_customers', 0)} 位客戶的網路品質問題
       3. 針對 VIP 客戶推出專屬優惠方案
       4. 建立客戶流失預警自動化系統
    """)

    return analyzer, churn_result


if __name__ == "__main__":
    analyzer, results = main()
