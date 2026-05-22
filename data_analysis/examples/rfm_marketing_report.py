"""
RFM自動化營銷報告生成器

這個範例展示如何自動生成專業的RFM分析報告，
可直接用於行銷團隊的決策會議。

真實應用場景:
- 每週/每月自動生成客戶分析報告
- 行銷策略制定依據
- 管理層決策支援
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots.clustering import RFMAnalyzer
    from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from data_analysis_chatbots.clustering import RFMAnalyzer
    from data_analysis_chatbots.marketing import CLVPredictor, CampaignManager


class RFMMarketingReport:
    """
    RFM營銷報告生成器

    自動生成包含以下內容的完整報告:
    - 客戶分群概覽
    - 各分群詳細分析
    - 營銷策略建議
    - 行動計劃
    """

    def __init__(self, transactions_df: pd.DataFrame,
                 customer_id_col: str = 'customer_id',
                 date_col: str = 'transaction_date',
                 amount_col: str = 'amount'):
        """
        初始化報告生成器

        Args:
            transactions_df: 交易數據DataFrame
            customer_id_col: 客戶ID欄位名
            date_col: 日期欄位名
            amount_col: 金額欄位名
        """
        self.transactions = transactions_df
        self.customer_id_col = customer_id_col
        self.date_col = date_col
        self.amount_col = amount_col
        self.rfm_df = None
        self.report_data = {}

    def run_analysis(self) -> pd.DataFrame:
        """執行RFM分析"""
        analyzer = RFMAnalyzer(self.transactions)
        self.rfm_df = analyzer.calculate_rfm(
            customer_id_col=self.customer_id_col,
            date_col=self.date_col,
            amount_col=self.amount_col
        )
        self.rfm_df = analyzer.segment_customers(self.rfm_df)
        return self.rfm_df

    def generate_executive_summary(self) -> Dict:
        """生成執行摘要"""
        if self.rfm_df is None:
            self.run_analysis()

        df = self.rfm_df

        summary = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'analysis_period': {
                'start': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            },
            'total_customers': len(df),
            'total_revenue': float(df['Monetary'].sum()),
            'avg_customer_value': float(df['Monetary'].mean()),
            'key_metrics': {
                'avg_recency_days': float(df['Recency'].mean()),
                'avg_frequency': float(df['Frequency'].mean()),
                'avg_monetary': float(df['Monetary'].mean()),
                'median_monetary': float(df['Monetary'].median())
            },
            'customer_health': self._calculate_customer_health(df)
        }

        self.report_data['executive_summary'] = summary
        return summary

    def _calculate_customer_health(self, df: pd.DataFrame) -> Dict:
        """計算客戶健康度指標"""
        # 活躍客戶 (30天內有購買)
        active = len(df[df['Recency'] <= 30])
        # 休眠客戶 (30-90天)
        dormant = len(df[(df['Recency'] > 30) & (df['Recency'] <= 90)])
        # 流失風險 (90-180天)
        at_risk = len(df[(df['Recency'] > 90) & (df['Recency'] <= 180)])
        # 已流失 (180天以上)
        churned = len(df[df['Recency'] > 180])

        total = len(df)
        return {
            'active': {'count': active, 'percentage': round(active/total*100, 1)},
            'dormant': {'count': dormant, 'percentage': round(dormant/total*100, 1)},
            'at_risk': {'count': at_risk, 'percentage': round(at_risk/total*100, 1)},
            'churned': {'count': churned, 'percentage': round(churned/total*100, 1)},
            'health_score': round((active + dormant*0.5) / total * 100, 1)
        }

    def generate_segment_analysis(self) -> Dict:
        """生成各分群詳細分析"""
        if self.rfm_df is None:
            self.run_analysis()

        df = self.rfm_df
        segments = {}

        for segment in df['Segment'].unique():
            segment_df = df[df['Segment'] == segment]

            segments[segment] = {
                'count': len(segment_df),
                'percentage': round(len(segment_df) / len(df) * 100, 1),
                'metrics': {
                    'avg_recency': round(segment_df['Recency'].mean(), 1),
                    'avg_frequency': round(segment_df['Frequency'].mean(), 1),
                    'avg_monetary': round(segment_df['Monetary'].mean(), 2),
                    'total_revenue': round(segment_df['Monetary'].sum(), 2),
                    'revenue_share': round(segment_df['Monetary'].sum() / df['Monetary'].sum() * 100, 1)
                },
                'rfm_scores': {
                    'avg_r_score': round(segment_df['R_Score'].mean(), 2),
                    'avg_f_score': round(segment_df['F_Score'].mean(), 2),
                    'avg_m_score': round(segment_df['M_Score'].mean(), 2)
                }
            }

        self.report_data['segment_analysis'] = segments
        return segments

    def generate_marketing_recommendations(self) -> Dict:
        """生成營銷策略建議"""
        recommendations = {
            'Champions': {
                'priority': 'HIGH',
                'objective': '維持忠誠度，提升推薦意願',
                'strategies': [
                    {'action': 'VIP專屬優惠', 'channel': 'Email + App Push', 'timing': '每月'},
                    {'action': '新品優先體驗', 'channel': '專屬活動邀請', 'timing': '新品上市時'},
                    {'action': '推薦獎勵計劃', 'channel': '社群媒體', 'timing': '持續'},
                    {'action': '專屬客服通道', 'channel': '電話/Line', 'timing': '即時'}
                ],
                'kpis': ['客戶終身價值', '推薦轉換率', 'NPS評分']
            },
            'Loyal Customers': {
                'priority': 'HIGH',
                'objective': '提升消費金額，培養成為Champions',
                'strategies': [
                    {'action': '交叉銷售推薦', 'channel': 'Email + 網站', 'timing': '每週'},
                    {'action': '會員升級優惠', 'channel': 'App推播', 'timing': '消費達標時'},
                    {'action': '生日/節日專屬折扣', 'channel': 'Email', 'timing': '特定日期'}
                ],
                'kpis': ['客單價提升', '購買頻率', '會員升級率']
            },
            'Potential Loyalists': {
                'priority': 'MEDIUM',
                'objective': '增加購買頻率，建立習慣',
                'strategies': [
                    {'action': '首購回饋優惠', 'channel': 'Email', 'timing': '首購後7天'},
                    {'action': '商品推薦', 'channel': '網站/App', 'timing': '瀏覽時'},
                    {'action': '限時優惠', 'channel': 'SMS', 'timing': '每兩週'}
                ],
                'kpis': ['回購率', '平均購買週期', '品類擴展']
            },
            'At Risk': {
                'priority': 'URGENT',
                'objective': '重新激活，防止流失',
                'strategies': [
                    {'action': '專屬回歸優惠(15-20% off)', 'channel': 'Email + SMS', 'timing': '立即'},
                    {'action': '滿意度調查', 'channel': 'Email', 'timing': '發送優惠後3天'},
                    {'action': '個人化推薦', 'channel': 'Retargeting Ads', 'timing': '持續2週'}
                ],
                'kpis': ['回歸率', '流失挽回成本', '二次購買率']
            },
            'Hibernating': {
                'priority': 'LOW',
                'objective': '嘗試喚醒，評估成本效益',
                'strategies': [
                    {'action': '大幅優惠(30% off)', 'channel': 'Email', 'timing': '每季度'},
                    {'action': '問卷調查', 'channel': 'Email', 'timing': '首次聯繫'},
                    {'action': '清理不活躍用戶', 'channel': '內部', 'timing': '每半年'}
                ],
                'kpis': ['喚醒成本', 'ROI', '清理數量']
            }
        }

        self.report_data['recommendations'] = recommendations
        return recommendations

    def generate_action_plan(self) -> List[Dict]:
        """生成30天行動計劃"""
        if 'segment_analysis' not in self.report_data:
            self.generate_segment_analysis()

        segments = self.report_data['segment_analysis']

        action_plan = [
            {
                'week': 1,
                'focus': 'At Risk 客戶挽留',
                'actions': [
                    {'day': 1, 'task': '篩選At Risk客戶名單', 'owner': '數據團隊'},
                    {'day': 2, 'task': '準備個人化優惠碼', 'owner': '行銷團隊'},
                    {'day': 3, 'task': '發送挽留Email', 'owner': '行銷團隊'},
                    {'day': 5, 'task': '追蹤開信率與點擊率', 'owner': '數據團隊'},
                    {'day': 7, 'task': '對未開信者發送SMS', 'owner': '行銷團隊'}
                ],
                'target_segment': 'At Risk',
                'expected_outcome': '挽回10-15%流失風險客戶'
            },
            {
                'week': 2,
                'focus': 'Champions 維護',
                'actions': [
                    {'day': 8, 'task': '整理VIP客戶名單', 'owner': '客服團隊'},
                    {'day': 9, 'task': '準備專屬優惠內容', 'owner': '行銷團隊'},
                    {'day': 10, 'task': '發送VIP專屬Email', 'owner': '行銷團隊'},
                    {'day': 12, 'task': '電話回訪Top 50客戶', 'owner': '客服團隊'},
                    {'day': 14, 'task': '收集反饋並記錄', 'owner': '客服團隊'}
                ],
                'target_segment': 'Champions',
                'expected_outcome': '維持VIP客戶滿意度95%+'
            },
            {
                'week': 3,
                'focus': 'Potential Loyalists 培養',
                'actions': [
                    {'day': 15, 'task': '分析潛力客戶購買偏好', 'owner': '數據團隊'},
                    {'day': 16, 'task': '設計交叉銷售方案', 'owner': '行銷團隊'},
                    {'day': 17, 'task': '建立自動化推薦流程', 'owner': '技術團隊'},
                    {'day': 19, 'task': '啟動推薦引擎', 'owner': '技術團隊'},
                    {'day': 21, 'task': '監控轉換數據', 'owner': '數據團隊'}
                ],
                'target_segment': 'Potential Loyalists',
                'expected_outcome': '提升回購率15-20%'
            },
            {
                'week': 4,
                'focus': '效果評估與優化',
                'actions': [
                    {'day': 22, 'task': '收集各活動數據', 'owner': '數據團隊'},
                    {'day': 23, 'task': '計算ROI', 'owner': '數據團隊'},
                    {'day': 25, 'task': '召開成效檢討會議', 'owner': '全團隊'},
                    {'day': 27, 'task': '調整下月策略', 'owner': '行銷團隊'},
                    {'day': 30, 'task': '更新RFM分析', 'owner': '數據團隊'}
                ],
                'target_segment': 'All',
                'expected_outcome': '完成月度分析報告'
            }
        ]

        self.report_data['action_plan'] = action_plan
        return action_plan

    def generate_full_report(self) -> str:
        """生成完整的文字報告"""
        if self.rfm_df is None:
            self.run_analysis()

        summary = self.generate_executive_summary()
        segments = self.generate_segment_analysis()
        recommendations = self.generate_marketing_recommendations()
        action_plan = self.generate_action_plan()

        report = f"""
{'='*80}
                    RFM 客戶分析營銷報告
                    {summary['report_date']}
{'='*80}

一、執行摘要
{'='*40}

分析期間: {summary['analysis_period']['start']} ~ {summary['analysis_period']['end']}

關鍵指標:
  • 總客戶數: {summary['total_customers']:,}
  • 總營收: ${summary['total_revenue']:,.2f}
  • 平均客戶價值: ${summary['avg_customer_value']:,.2f}
  • 平均購買頻率: {summary['key_metrics']['avg_frequency']:.1f} 次
  • 平均消費間隔: {summary['key_metrics']['avg_recency_days']:.0f} 天

客戶健康度評分: {summary['customer_health']['health_score']}/100

客戶狀態分佈:
  • 活躍客戶 (30天內): {summary['customer_health']['active']['count']:,} ({summary['customer_health']['active']['percentage']}%)
  • 休眠客戶 (30-90天): {summary['customer_health']['dormant']['count']:,} ({summary['customer_health']['dormant']['percentage']}%)
  • 流失風險 (90-180天): {summary['customer_health']['at_risk']['count']:,} ({summary['customer_health']['at_risk']['percentage']}%)
  • 已流失 (180天+): {summary['customer_health']['churned']['count']:,} ({summary['customer_health']['churned']['percentage']}%)

二、客戶分群分析
{'='*40}
"""

        # 排序分群
        sorted_segments = sorted(segments.items(),
                                 key=lambda x: x[1]['metrics']['total_revenue'],
                                 reverse=True)

        for segment_name, data in sorted_segments:
            report += f"""
【{segment_name}】
  客戶數: {data['count']:,} ({data['percentage']}%)
  營收貢獻: ${data['metrics']['total_revenue']:,.2f} ({data['metrics']['revenue_share']}%)
  平均消費: ${data['metrics']['avg_monetary']:,.2f}
  購買頻率: {data['metrics']['avg_frequency']:.1f} 次
  最近購買: {data['metrics']['avg_recency']:.0f} 天前
  RFM分數: R={data['rfm_scores']['avg_r_score']:.1f} F={data['rfm_scores']['avg_f_score']:.1f} M={data['rfm_scores']['avg_m_score']:.1f}
"""

        report += f"""
三、營銷策略建議
{'='*40}
"""
        for segment_name, rec in recommendations.items():
            if segment_name in segments:
                report += f"""
【{segment_name}】優先級: {rec['priority']}
  目標: {rec['objective']}
  策略:
"""
                for i, strategy in enumerate(rec['strategies'][:3], 1):
                    report += f"    {i}. {strategy['action']} ({strategy['channel']})\n"

        report += f"""
四、30天行動計劃
{'='*40}
"""
        for week in action_plan:
            report += f"""
第{week['week']}週 - {week['focus']}
  目標分群: {week['target_segment']}
  預期成效: {week['expected_outcome']}
  關鍵任務:
"""
            for action in week['actions'][:3]:
                report += f"    Day {action['day']}: {action['task']} ({action['owner']})\n"

        report += f"""
{'='*80}
                        報告結束
                    Generated by RFM Marketing Report System
{'='*80}
"""

        return report

    def export_to_json(self, filepath: str = 'rfm_report.json'):
        """將報告數據導出為JSON"""
        if not self.report_data:
            self.generate_full_report()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"報告已導出至: {filepath}")


def generate_sample_transactions(n_customers=500, n_transactions=5000):
    """生成範例交易數據"""
    np.random.seed(42)
    today = datetime.now()

    customers = [f'CUST{i:05d}' for i in range(1, n_customers + 1)]

    transactions = []
    for _ in range(n_transactions):
        customer_id = np.random.choice(customers)
        days_ago = np.random.exponential(60)  # 指數分佈模擬購買間隔
        tx_date = today - timedelta(days=min(days_ago, 365))
        amount = np.random.lognormal(4, 1)  # 對數正態分佈模擬消費金額

        transactions.append({
            'customer_id': customer_id,
            'transaction_date': tx_date,
            'amount': round(amount, 2)
        })

    return pd.DataFrame(transactions)


def main():
    """執行報告生成範例"""
    print("生成範例交易數據...")
    transactions = generate_sample_transactions(n_customers=500, n_transactions=5000)
    print(f"✓ 生成 {len(transactions)} 筆交易記錄")

    print("\n初始化報告生成器...")
    report_generator = RFMMarketingReport(transactions)

    print("執行RFM分析...")
    rfm_df = report_generator.run_analysis()
    print(f"✓ 分析完成，共 {len(rfm_df)} 位客戶")

    print("\n生成完整報告...")
    report = report_generator.generate_full_report()
    print(report)

    # 保存報告
    try:
        report_generator.export_to_json('data/outputs/rfm_marketing_report.json')

        with open('data/outputs/rfm_marketing_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n📄 文字報告已保存至: data/outputs/rfm_marketing_report.txt")
    except Exception as e:
        print(f"\n⚠️ 保存報告時發生錯誤: {e}")

    return report_generator


if __name__ == "__main__":
    report_generator = main()
