"""
保險風險分析範例

這個範例展示如何分析保險客戶風險，包含：
- 客戶風險分群分析
- 理賠預測分析
- 保費優化策略
- 風險分群視覺化

真實應用場景:
- 保險公司客戶風險評估
- 保費定價策略優化
- 理賠欺詐檢測
- 客戶細分與產品推薦
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory, GMMClusterer, KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')


class InsuranceRiskAnalyzer:
    """
    保險風險分析器

    提供完整的保險風險分析功能:
    - 客戶風險評分
    - 理賠預測模型
    - 保費優化建議
    - 風險分群識別
    """

    def __init__(self, customers_df: pd.DataFrame, claims_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            customers_df: 客戶資料DataFrame
            claims_df: 理賠記錄DataFrame (可選)
        """
        self.customers = customers_df.copy()
        self.claims = claims_df.copy() if claims_df is not None else None
        self.risk_scores = None
        self.clusters = None

    def calculate_risk_score(self) -> pd.DataFrame:
        """
        計算客戶綜合風險評分

        風險評分因素:
        - 年齡風險 (年輕和高齡風險較高)
        - 理賠歷史 (理賠次數和金額)
        - 駕駛記錄 (違規次數)
        - 健康狀況
        - 信用評分
        """
        df = self.customers.copy()

        # 年齡風險評分 (U型曲線: 年輕和老年風險高)
        df['age_risk'] = df['age'].apply(lambda x:
            min(100, max(0, 20 if x < 25 else (15 if x < 30 else (
                5 if 30 <= x <= 55 else (10 if x <= 65 else 25)
            ))))
        )

        # 理賠歷史風險評分 (0-30分)
        df['claim_risk'] = (
            df['claim_history'].clip(0, 5) * 5 +  # 理賠次數
            (df['claim_amount'] / 10000).clip(0, 5) * 1  # 理賠金額
        ).clip(0, 30)

        # 駕駛記錄風險評分 (0-20分)
        df['driving_risk'] = (df['driving_record'] * 4).clip(0, 20)

        # 健康風險評分 (100-健康分數，標準化到0-15分)
        df['health_risk'] = ((100 - df['health_score']) / 100 * 15).clip(0, 15)

        # 信用風險評分 (800-信用分數，標準化到0-15分)
        df['credit_risk'] = ((800 - df['credit_score']) / 800 * 15).clip(0, 15)

        # 保障金額風險 (高保額相對風險)
        mean_coverage = df['coverage_amount'].mean()
        df['coverage_risk'] = ((df['coverage_amount'] - mean_coverage) / mean_coverage * 10).clip(-5, 15)

        # 綜合風險評分 (0-100)
        df['risk_score'] = (
            df['age_risk'] * 0.20 +
            df['claim_risk'] * 0.30 +
            df['driving_risk'] * 0.20 +
            df['health_risk'] * 0.15 +
            df['credit_risk'] * 0.10 +
            df['coverage_risk'] * 0.05
        ).round(1)

        # 風險等級分類
        df['risk_level'] = pd.cut(
            df['risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Very High']
        )

        self.risk_scores = df
        return df

    def cluster_customers(self, n_clusters: int = 4, method: str = 'gmm') -> pd.DataFrame:
        """
        使用聚類算法對客戶進行風險分群

        Args:
            n_clusters: 聚類數量
            method: 聚類方法 ('gmm', 'kmeans')

        Returns:
            包含聚類標籤的DataFrame
        """
        if self.risk_scores is None:
            self.calculate_risk_score()

        # 選擇聚類特徵
        cluster_features = [
            'age', 'claim_history', 'claim_amount', 'driving_record',
            'health_score', 'credit_score', 'coverage_amount', 'premium'
        ]

        # 創建聚類器
        if method == 'gmm':
            clusterer = GMMClusterer(n_components=n_clusters, random_state=42)
        else:
            clusterer = KMeansClusterer(n_clusters=n_clusters, random_state=42)

        # 執行聚類
        labels = clusterer.fit_predict(self.risk_scores, cluster_features)
        self.risk_scores['cluster'] = labels

        # 獲取聚類摘要
        summary = clusterer.get_cluster_summary(self.risk_scores, cluster_features)

        # 為每個聚類命名 (基於平均風險分數)
        cluster_names = {}
        for cluster_id in range(n_clusters):
            cluster_data = self.risk_scores[self.risk_scores['cluster'] == cluster_id]
            avg_risk = cluster_data['risk_score'].mean()

            if avg_risk < 25:
                name = '低風險客群'
            elif avg_risk < 50:
                name = '中等風險客群'
            elif avg_risk < 75:
                name = '高風險客群'
            else:
                name = '極高風險客群'

            cluster_names[cluster_id] = name

        self.risk_scores['cluster_name'] = self.risk_scores['cluster'].map(cluster_names)
        self.clusters = summary

        return self.risk_scores

    def predict_claim_probability(self) -> pd.DataFrame:
        """
        預測客戶未來理賠概率

        使用邏輯回歸模型預測:
        - 基於歷史理賠數據
        - 考慮客戶特徵
        - 輸出理賠概率和預期損失
        """
        if self.risk_scores is None:
            self.calculate_risk_score()

        df = self.risk_scores

        # 簡化的理賠概率計算 (基於風險因素)
        # 在實際應用中，這裡會使用機器學習模型

        # 基礎理賠率
        base_rate = 0.15

        # 根據各項風險因素調整
        age_factor = df['age'].apply(lambda x:
            1.5 if x < 25 else (1.3 if x < 30 else (0.8 if 30 <= x <= 55 else 1.2))
        )

        claim_history_factor = 1 + (df['claim_history'] * 0.2).clip(0, 1.5)
        driving_factor = 1 + (df['driving_record'] * 0.15).clip(0, 1.0)
        health_factor = (100 - df['health_score']) / 100 * 0.5 + 0.5

        # 計算理賠概率
        df['claim_probability'] = (
            base_rate * age_factor * claim_history_factor *
            driving_factor * health_factor
        ).clip(0, 0.95).round(3)

        # 預期理賠金額 (基於歷史平均和保障金額)
        avg_claim = df['claim_amount'].mean() if df['claim_amount'].mean() > 0 else 50000
        df['expected_claim_amount'] = (
            df['claim_probability'] *
            (df['claim_amount'] * 0.7 + avg_claim * 0.3)
        ).round(2)

        # 理賠風險等級
        df['claim_risk_level'] = pd.cut(
            df['claim_probability'],
            bins=[0, 0.1, 0.25, 0.5, 1.0],
            labels=['Very Low', 'Low', 'Medium', 'High']
        )

        self.risk_scores = df
        return df

    def optimize_premium(self, target_profit_margin: float = 0.15) -> pd.DataFrame:
        """
        優化保費定價策略

        Args:
            target_profit_margin: 目標利潤率

        Returns:
            包含建議保費的DataFrame
        """
        if 'claim_probability' not in self.risk_scores.columns:
            self.predict_claim_probability()

        df = self.risk_scores

        # 計算風險成本 (預期理賠 + 管理費用)
        management_cost_ratio = 0.10  # 管理費用比率
        df['risk_cost'] = df['expected_claim_amount'] * (1 + management_cost_ratio)

        # 建議保費 (風險成本 + 利潤)
        df['recommended_premium'] = (df['risk_cost'] * (1 + target_profit_margin)).round(2)

        # 當前保費充足性分析
        df['premium_adequacy_ratio'] = (df['premium'] / df['recommended_premium']).round(2)
        df['premium_gap'] = (df['recommended_premium'] - df['premium']).round(2)

        # 保費調整建議
        df['premium_action'] = df.apply(lambda row:
            '需調漲' if row['premium_adequacy_ratio'] < 0.9 else
            ('可調降' if row['premium_adequacy_ratio'] > 1.15 else '維持'),
            axis=1
        )

        # 計算調整後的預期利潤
        df['current_expected_profit'] = (
            df['premium'] - df['expected_claim_amount']
        ).round(2)

        df['optimized_expected_profit'] = (
            df['recommended_premium'] - df['expected_claim_amount']
        ).round(2)

        self.risk_scores = df
        return df

    def segment_analysis(self) -> pd.DataFrame:
        """
        風險分群詳細分析

        Returns:
            各分群的統計摘要
        """
        if self.risk_scores is None or 'cluster' not in self.risk_scores.columns:
            self.cluster_customers()

        # 確保有理賠預測數據
        if 'claim_probability' not in self.risk_scores.columns:
            self.predict_claim_probability()

        # 確保有保費優化數據
        if 'recommended_premium' not in self.risk_scores.columns:
            self.optimize_premium()

        df = self.risk_scores

        # 按聚類分組統計
        segment_stats = df.groupby('cluster_name').agg({
            'customer_id': 'count',
            'age': 'mean',
            'risk_score': ['mean', 'min', 'max'],
            'claim_history': 'mean',
            'claim_amount': 'mean',
            'claim_probability': 'mean',
            'premium': ['mean', 'sum'],
            'coverage_amount': 'mean',
            'expected_claim_amount': 'sum',
            'health_score': 'mean',
            'credit_score': 'mean'
        }).round(2)

        # 重命名列
        segment_stats.columns = [
            'customer_count', 'avg_age', 'avg_risk_score', 'min_risk_score',
            'max_risk_score', 'avg_claim_history', 'avg_claim_amount',
            'avg_claim_probability', 'avg_premium', 'total_premium',
            'avg_coverage', 'total_expected_claims', 'avg_health_score', 'avg_credit_score'
        ]

        # 計算額外指標
        segment_stats['expected_loss_ratio'] = (
            segment_stats['total_expected_claims'] / segment_stats['total_premium']
        ).round(3)

        segment_stats['customer_pct'] = (
            segment_stats['customer_count'] / segment_stats['customer_count'].sum() * 100
        ).round(1)

        return segment_stats.sort_values('avg_risk_score', ascending=False)

    def generate_recommendations(self) -> Dict[str, List[str]]:
        """
        根據分析結果生成業務建議

        Returns:
            各風險分群的業務建議
        """
        segment_stats = self.segment_analysis()
        recommendations = {}

        for segment_name, stats in segment_stats.iterrows():
            advice = []

            # 基於損失率的建議
            loss_ratio = stats['expected_loss_ratio']
            if loss_ratio > 0.8:
                advice.append(f"⚠️ 損失率高達 {loss_ratio:.1%}，建議調漲保費或限制承保")
            elif loss_ratio > 0.6:
                advice.append(f"⚡ 損失率 {loss_ratio:.1%}，建議審慎審核新申請案件")
            else:
                advice.append(f"✓ 損失率 {loss_ratio:.1%}，風險可控")

            # 基於理賠概率的建議
            claim_prob = stats['avg_claim_probability']
            if claim_prob > 0.3:
                advice.append(f"建議加強風險管控措施，提供預防性服務")

            # 基於客戶健康的建議
            health = stats['avg_health_score']
            if health < 60:
                advice.append(f"健康分數較低 ({health:.0f})，建議推出健康管理計劃")

            # 基於信用的建議
            credit = stats['avg_credit_score']
            if credit < 600:
                advice.append(f"信用分數偏低 ({credit:.0f})，建議要求更高保證金")

            # 市場策略建議
            if loss_ratio < 0.5 and stats['customer_count'] < segment_stats['customer_count'].mean():
                advice.append("可考慮降低保費吸引更多類似客戶")

            recommendations[segment_name] = advice

        return recommendations

    def calculate_portfolio_metrics(self) -> Dict[str, float]:
        """
        計算整體投資組合指標

        Returns:
            投資組合績效指標
        """
        if 'recommended_premium' not in self.risk_scores.columns:
            self.optimize_premium()

        df = self.risk_scores

        total_customers = len(df)
        total_premium = df['premium'].sum()
        total_expected_claims = df['expected_claim_amount'].sum()
        total_coverage = df['coverage_amount'].sum()

        # 損失率 (預期理賠/保費收入)
        loss_ratio = total_expected_claims / total_premium if total_premium > 0 else 0

        # 平均風險分數
        avg_risk_score = df['risk_score'].mean()

        # 高風險客戶比例
        high_risk_pct = len(df[df['risk_level'].isin(['High', 'Very High'])]) / total_customers

        # 需調整保費的客戶比例
        need_adjustment_pct = len(df[df['premium_action'] != '維持']) / total_customers

        # 預期利潤
        current_profit = df['current_expected_profit'].sum()
        optimized_profit = df['optimized_expected_profit'].sum()

        return {
            'total_customers': total_customers,
            'total_premium': total_premium,
            'total_expected_claims': total_expected_claims,
            'total_coverage': total_coverage,
            'loss_ratio': loss_ratio,
            'avg_risk_score': avg_risk_score,
            'high_risk_ratio': high_risk_pct,
            'need_adjustment_ratio': need_adjustment_pct,
            'current_expected_profit': current_profit,
            'optimized_expected_profit': optimized_profit,
            'profit_improvement': optimized_profit - current_profit
        }


def generate_insurance_data(n_customers: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    生成模擬保險客戶數據

    Args:
        n_customers: 客戶數量
        seed: 隨機種子

    Returns:
        客戶資料DataFrame
    """
    np.random.seed(seed)

    # 基本資料
    customers = []

    for i in range(1, n_customers + 1):
        # 年齡分佈 (18-75歲)
        age = int(np.clip(np.random.normal(42, 15), 18, 75))

        # 性別
        gender = np.random.choice(['M', 'F'], p=[0.52, 0.48])

        # 地區
        regions = ['北部', '中部', '南部', '東部']
        region = np.random.choice(regions, p=[0.40, 0.25, 0.25, 0.10])

        # 保單類型
        policy_types = ['汽車保險', '健康保險', '壽險', '財產保險']
        policy_weights = [0.35, 0.30, 0.20, 0.15]
        policy_type = np.random.choice(policy_types, p=policy_weights)

        # 保障金額 (依保單類型而定)
        if policy_type == '汽車保險':
            coverage_amount = np.random.lognormal(12, 0.5) * 10000
        elif policy_type == '健康保險':
            coverage_amount = np.random.lognormal(13, 0.6) * 10000
        elif policy_type == '壽險':
            coverage_amount = np.random.lognormal(14, 0.7) * 10000
        else:  # 財產保險
            coverage_amount = np.random.lognormal(13.5, 0.6) * 10000

        coverage_amount = max(100000, min(coverage_amount, 10000000))

        # 理賠歷史 (次數)
        # 年輕人和老年人理賠較多
        if age < 25 or age > 65:
            claim_history = np.random.poisson(2)
        else:
            claim_history = np.random.poisson(0.8)
        claim_history = min(claim_history, 10)

        # 理賠金額 (基於理賠次數)
        if claim_history > 0:
            claim_amount = claim_history * np.random.lognormal(10, 1) * 1000
            claim_amount = max(0, min(claim_amount, coverage_amount * 0.8))
        else:
            claim_amount = 0

        # 駕駛記錄 (違規次數，0-5次)
        if policy_type == '汽車保險':
            if age < 25:
                driving_record = np.random.poisson(1.5)
            elif age < 30:
                driving_record = np.random.poisson(1.0)
            else:
                driving_record = np.random.poisson(0.4)
        else:
            driving_record = 0
        driving_record = min(driving_record, 5)

        # 健康評分 (0-100，分數越高越健康)
        base_health = 75
        age_penalty = max(0, (age - 40) * 0.3)
        health_score = max(20, min(100, np.random.normal(base_health - age_penalty, 12)))

        # 信用評分 (300-850)
        credit_score = int(np.clip(np.random.normal(680, 80), 300, 850))

        # 保費計算 (基於多個因素)
        base_premium = coverage_amount * 0.015

        # 調整因子
        age_factor = 1.3 if age < 25 else (1.2 if age < 30 else (0.9 if 30 <= age <= 55 else 1.1))
        claim_factor = 1 + (claim_history * 0.15)
        driving_factor = 1 + (driving_record * 0.1)
        health_factor = (100 - health_score) / 100 * 0.3 + 0.85
        credit_factor = (800 - credit_score) / 500 * 0.2 + 0.9

        premium = base_premium * age_factor * claim_factor * driving_factor * health_factor * credit_factor
        premium = max(5000, min(premium, 500000))

        # 風險分數 (初步，將由分析器重新計算)
        risk_score = (
            (1 if age < 25 or age > 65 else 0) * 20 +
            claim_history * 10 +
            driving_record * 8 +
            (100 - health_score) / 5 +
            (750 - credit_score) / 50
        )
        risk_score = max(0, min(100, risk_score))

        customers.append({
            'customer_id': f'INS{i:06d}',
            'age': age,
            'gender': gender,
            'region': region,
            'policy_type': policy_type,
            'coverage_amount': round(coverage_amount, 2),
            'premium': round(premium, 2),
            'claim_history': claim_history,
            'claim_amount': round(claim_amount, 2),
            'driving_record': driving_record,
            'health_score': round(health_score, 1),
            'credit_score': credit_score,
            'risk_score': round(risk_score, 1)
        })

    return pd.DataFrame(customers)


def visualize_risk_segments(analyzer: InsuranceRiskAnalyzer, save_path: Optional[str] = None):
    """
    視覺化風險分群結果

    Args:
        analyzer: 保險風險分析器
        save_path: 圖表保存路徑
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    df = analyzer.risk_scores

    # 設置繪圖樣式
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette('husl')

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('保險客戶風險分群分析', fontsize=18, fontweight='bold', y=1.00)

    # 1. 風險分數分佈 (按聚類)
    ax1 = axes[0, 0]
    for cluster_name in df['cluster_name'].unique():
        cluster_data = df[df['cluster_name'] == cluster_name]
        ax1.hist(cluster_data['risk_score'], alpha=0.6, label=cluster_name, bins=20)
    ax1.set_xlabel('風險分數', fontsize=12)
    ax1.set_ylabel('客戶數量', fontsize=12)
    ax1.set_title('各風險分群的風險分數分佈', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. 年齡 vs 風險分數散點圖
    ax2 = axes[0, 1]
    for cluster_name in df['cluster_name'].unique():
        cluster_data = df[df['cluster_name'] == cluster_name]
        ax2.scatter(cluster_data['age'], cluster_data['risk_score'],
                   alpha=0.6, label=cluster_name, s=50)
    ax2.set_xlabel('年齡', fontsize=12)
    ax2.set_ylabel('風險分數', fontsize=12)
    ax2.set_title('年齡與風險分數關係', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. 各分群客戶數量和平均保費
    ax3 = axes[1, 0]
    segment_stats = analyzer.segment_analysis()
    x_pos = np.arange(len(segment_stats))

    ax3_twin = ax3.twinx()
    bars1 = ax3.bar(x_pos - 0.2, segment_stats['customer_count'], 0.4,
                    label='客戶數量', alpha=0.7, color='skyblue')
    bars2 = ax3_twin.bar(x_pos + 0.2, segment_stats['avg_premium'], 0.4,
                        label='平均保費', alpha=0.7, color='coral')

    ax3.set_xlabel('客戶分群', fontsize=12)
    ax3.set_ylabel('客戶數量', fontsize=12, color='skyblue')
    ax3_twin.set_ylabel('平均保費 (元)', fontsize=12, color='coral')
    ax3.set_title('各分群規模與平均保費', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(segment_stats.index, rotation=15, ha='right')
    ax3.tick_params(axis='y', labelcolor='skyblue')
    ax3_twin.tick_params(axis='y', labelcolor='coral')
    ax3.grid(True, alpha=0.3)

    # 添加圖例
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # 4. 理賠概率 vs 保費充足性
    ax4 = axes[1, 1]
    scatter = ax4.scatter(df['claim_probability'], df['premium_adequacy_ratio'],
                         c=df['risk_score'], cmap='RdYlGn_r', alpha=0.6, s=50)
    ax4.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='保費平衡線')
    ax4.set_xlabel('理賠概率', fontsize=12)
    ax4.set_ylabel('保費充足率', fontsize=12)
    ax4.set_title('理賠風險與保費充足性分析', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # 添加顏色條
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('風險分數', fontsize=10)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 圖表已保存至: {save_path}")

    # 不要在非交互式環境中顯示圖表
    # plt.show()
    plt.close()


def print_analysis_report(analyzer: InsuranceRiskAnalyzer):
    """
    打印分析報告

    Args:
        analyzer: 保險風險分析器
    """
    print("\n" + "="*80)
    print(" "*25 + "保險風險分析報告")
    print(" "*25 + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 整體指標
    metrics = analyzer.calculate_portfolio_metrics()

    print("\n【一、投資組合整體指標】")
    print("-" * 80)
    print(f"  總客戶數:        {metrics['total_customers']:,} 人")
    print(f"  保費收入:        ${metrics['total_premium']:,.2f}")
    print(f"  預期理賠:        ${metrics['total_expected_claims']:,.2f}")
    print(f"  總保障金額:      ${metrics['total_coverage']:,.2f}")
    print(f"  損失率:          {metrics['loss_ratio']:.1%}")
    print(f"  平均風險分數:    {metrics['avg_risk_score']:.1f}/100")
    print(f"  高風險客戶比例:  {metrics['high_risk_ratio']:.1%}")

    # 利潤分析
    print(f"\n【二、利潤分析】")
    print("-" * 80)
    print(f"  當前預期利潤:    ${metrics['current_expected_profit']:,.2f}")
    print(f"  優化後預期利潤:  ${metrics['optimized_expected_profit']:,.2f}")
    print(f"  利潤改善空間:    ${metrics['profit_improvement']:,.2f}")
    print(f"  需調整保費客戶:  {metrics['need_adjustment_ratio']:.1%}")

    # 風險分群分析
    print(f"\n【三、風險分群詳細分析】")
    print("-" * 80)
    segment_stats = analyzer.segment_analysis()

    for segment_name, stats in segment_stats.iterrows():
        print(f"\n  ▶ {segment_name}")
        print(f"     客戶數量:     {stats['customer_count']} 人 ({stats['customer_pct']:.1f}%)")
        print(f"     平均年齡:     {stats['avg_age']:.1f} 歲")
        print(f"     風險分數:     {stats['avg_risk_score']:.1f} (範圍: {stats['min_risk_score']:.1f}-{stats['max_risk_score']:.1f})")
        print(f"     理賠概率:     {stats['avg_claim_probability']:.1%}")
        print(f"     平均保費:     ${stats['avg_premium']:,.2f}")
        print(f"     保費總額:     ${stats['total_premium']:,.2f}")
        print(f"     預期損失率:   {stats['expected_loss_ratio']:.1%}")
        print(f"     健康分數:     {stats['avg_health_score']:.1f}")
        print(f"     信用分數:     {stats['avg_credit_score']:.0f}")

    # 業務建議
    print(f"\n【四、業務策略建議】")
    print("-" * 80)
    recommendations = analyzer.generate_recommendations()

    for segment_name, advice_list in recommendations.items():
        print(f"\n  ▶ {segment_name}")
        for i, advice in enumerate(advice_list, 1):
            print(f"     {i}. {advice}")

    # 高風險客戶預警
    print(f"\n【五、高風險客戶預警】")
    print("-" * 80)
    high_risk_customers = analyzer.risk_scores[
        analyzer.risk_scores['risk_level'] == 'Very High'
    ].nlargest(10, 'risk_score')

    if len(high_risk_customers) > 0:
        print(f"\n  需特別關注的高風險客戶 (Top 10):\n")
        for idx, customer in high_risk_customers.iterrows():
            print(f"  • {customer['customer_id']}")
            print(f"    風險分數: {customer['risk_score']:.1f}, " +
                  f"理賠次數: {customer['claim_history']}, " +
                  f"理賠概率: {customer['claim_probability']:.1%}")
            print(f"    當前保費: ${customer['premium']:,.0f}, " +
                  f"建議保費: ${customer['recommended_premium']:,.0f}, " +
                  f"調整建議: {customer['premium_action']}")
            print()
    else:
        print("  ✓ 無極高風險客戶")

    # 保費優化摘要
    print(f"\n【六、保費優化摘要】")
    print("-" * 80)

    action_summary = analyzer.risk_scores['premium_action'].value_counts()
    total = len(analyzer.risk_scores)

    print(f"\n  保費調整建議分佈:")
    for action, count in action_summary.items():
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"    {action:6}: {count:4} ({pct:5.1f}%) {bar}")

    # 潛在收益
    need_increase = analyzer.risk_scores[analyzer.risk_scores['premium_action'] == '需調漲']
    if len(need_increase) > 0:
        potential_increase = need_increase['premium_gap'].sum()
        print(f"\n  💰 調漲保費的潛在增加收入: ${potential_increase:,.2f}")

    print("\n" + "="*80)
    print(" "*28 + "報告結束")
    print("="*80 + "\n")


def main():
    """執行完整的保險風險分析"""
    print("="*80)
    print(" "*20 + "保險風險分析系統")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/5] 準備數據...")

    customers_df = generate_insurance_data(n_customers=2000, seed=42)

    print(f"  ✓ 客戶數量: {len(customers_df):,}")
    print(f"  ✓ 保單類型: {customers_df['policy_type'].nunique()} 種")
    print(f"  ✓ 年齡範圍: {customers_df['age'].min()}-{customers_df['age'].max()} 歲")
    print(f"  ✓ 總保費收入: ${customers_df['premium'].sum():,.2f}")
    print(f"  ✓ 總保障金額: ${customers_df['coverage_amount'].sum():,.2f}")

    # 數據驗證
    validator = DataValidator(customers_df)
    missing_check = validator.check_missing_values()
    duplicate_check = validator.check_duplicates(subset=['customer_id'])
    is_valid = (missing_check['total_missing_cells'] == 0 and
                not duplicate_check['has_duplicates'])
    print(f"  ✓ 數據驗證: {'通過' if is_valid else '失敗'}")

    # ========================================
    # 2. 初始化分析器並計算風險評分
    # ========================================
    print("\n[2/5] 計算客戶風險評分...")

    analyzer = InsuranceRiskAnalyzer(customers_df)
    risk_df = analyzer.calculate_risk_score()

    risk_distribution = risk_df['risk_level'].value_counts()
    print("\n  風險等級分佈:")
    for level in ['Very High', 'High', 'Medium', 'Low']:
        count = risk_distribution.get(level, 0)
        pct = count / len(risk_df) * 100
        bar = '█' * int(pct / 2)
        print(f"    {level:10}: {count:4} ({pct:5.1f}%) {bar}")

    # ========================================
    # 3. 客戶風險分群
    # ========================================
    print("\n[3/5] 執行客戶風險分群...")

    clustered_df = analyzer.cluster_customers(n_clusters=4, method='gmm')

    print("\n  客戶分群結果:")
    cluster_counts = clustered_df['cluster_name'].value_counts()
    for cluster_name, count in cluster_counts.items():
        pct = count / len(clustered_df) * 100
        print(f"    {cluster_name}: {count} ({pct:.1f}%)")

    # ========================================
    # 4. 理賠預測與保費優化
    # ========================================
    print("\n[4/5] 理賠預測與保費優化...")

    optimized_df = analyzer.optimize_premium(target_profit_margin=0.15)

    # 理賠風險統計
    claim_risk_dist = optimized_df['claim_risk_level'].value_counts()
    print("\n  理賠風險分佈:")
    for level in ['High', 'Medium', 'Low', 'Very Low']:
        count = claim_risk_dist.get(level, 0)
        print(f"    {level}: {count}")

    # 保費調整統計
    premium_action_dist = optimized_df['premium_action'].value_counts()
    print("\n  保費調整建議:")
    for action, count in premium_action_dist.items():
        print(f"    {action}: {count}")

    # ========================================
    # 5. 視覺化與報告
    # ========================================
    print("\n[5/5] 生成視覺化圖表與報告...")

    # 生成視覺化圖表
    try:
        output_path = 'data/outputs/insurance_risk_segments.png'
        visualize_risk_segments(analyzer, save_path=output_path)
        print(f"  ✓ 圖表已生成")
    except Exception as e:
        print(f"  ⚠️ 圖表生成失敗: {e}")

    # 打印詳細報告
    print_analysis_report(analyzer)

    # 保存結果
    try:
        output_csv = 'data/outputs/insurance_risk_analysis.csv'
        optimized_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"📁 分析結果已保存至: {output_csv}")
    except Exception as e:
        print(f"⚠️ 無法保存結果: {e}")

    return analyzer, optimized_df


if __name__ == "__main__":
    analyzer, results = main()
