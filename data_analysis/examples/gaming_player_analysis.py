"""
遊戲玩家行為分析範例

這個範例展示如何分析遊戲玩家數據，包含：
- 玩家行為聚類分析（休閒玩家 vs 核心玩家）
- 遊戲內購買模式分析
- 玩家參與度和留存率指標
- 遊戲會話視覺化分析
- 玩家生命週期價值預測

真實應用場景:
- 遊戲營運優化和玩家分群
- 遊戲內購系統設計
- 玩家留存策略制定
- 遊戲平衡性調整
- 個性化推薦系統

注意: 此為模擬數據，僅供學習使用
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory, HierarchicalClusterer, KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')


class GamingPlayerAnalyzer:
    """
    遊戲玩家分析器

    提供完整的遊戲玩家數據分析功能:
    - 玩家行為分群
    - 付費模式分析
    - 參與度評估
    - 留存預測
    - 價值分析
    """

    def __init__(self, players_df: pd.DataFrame):
        """
        初始化分析器

        Args:
            players_df: 玩家數據DataFrame
        """
        self.players = players_df.copy()
        self._prepare_data()

    def _prepare_data(self):
        """準備和清理數據"""
        # 計算額外的衍生指標
        if 'total_playtime_hours' in self.players.columns and 'sessions_per_week' in self.players.columns:
            # 平均每次遊戲時長（小時）
            self.players['avg_session_length'] = (
                self.players['total_playtime_hours'] /
                (self.players['sessions_per_week'] * 4).replace(0, 1)
            ).round(2)

        if 'virtual_currency_spent' in self.players.columns and 'in_app_purchases' in self.players.columns:
            # 平均每次購買金額
            self.players['avg_purchase_amount'] = (
                self.players['virtual_currency_spent'] /
                self.players['in_app_purchases'].replace(0, 1)
            ).round(2)

        if 'account_age_days' in self.players.columns and 'total_playtime_hours' in self.players.columns:
            # 每天平均遊戲時長
            self.players['daily_playtime'] = (
                self.players['total_playtime_hours'] /
                self.players['account_age_days'].replace(0, 1)
            ).round(2)

    def segment_players(self, n_clusters: int = 4, method: str = 'kmeans') -> pd.DataFrame:
        """
        使用聚類算法將玩家分群

        Args:
            n_clusters: 聚類數量
            method: 聚類方法 ('kmeans', 'hierarchical', 'gmm')

        Returns:
            包含聚類標籤的DataFrame
        """
        # 選擇用於聚類的特徵
        cluster_features = [
            'total_playtime_hours', 'sessions_per_week',
            'in_app_purchases', 'virtual_currency_spent',
            'achievements_unlocked', 'level'
        ]

        # 確保所有特徵都存在
        available_features = [f for f in cluster_features if f in self.players.columns]

        if len(available_features) < 3:
            raise ValueError(f"至少需要3個特徵進行聚類，目前只有: {available_features}")

        # 創建聚類器
        if method == 'hierarchical':
            clusterer = HierarchicalClusterer(n_clusters=n_clusters, linkage='ward')
        else:
            clusterer = ClustererFactory.create(
                algorithm=method,
                n_clusters=n_clusters,
                random_state=42
            )

        # 執行聚類
        labels = clusterer.fit_predict(self.players, available_features)
        self.players['cluster'] = labels

        # 為每個聚類添加描述性標籤
        self.players['player_segment'] = self.players['cluster'].map(
            self._generate_segment_labels()
        )

        return self.players

    def _generate_segment_labels(self) -> Dict[int, str]:
        """
        根據聚類特徵生成描述性標籤

        Returns:
            聚類ID到標籤的映射
        """
        segment_stats = self.players.groupby('cluster').agg({
            'total_playtime_hours': 'mean',
            'virtual_currency_spent': 'mean',
            'sessions_per_week': 'mean'
        })

        labels = {}
        for cluster_id in segment_stats.index:
            stats = segment_stats.loc[cluster_id]

            # 根據特徵組合判斷玩家類型
            playtime = stats['total_playtime_hours']
            spending = stats['virtual_currency_spent']
            frequency = stats['sessions_per_week']

            if spending > segment_stats['virtual_currency_spent'].quantile(0.75):
                if playtime > segment_stats['total_playtime_hours'].quantile(0.75):
                    labels[cluster_id] = "鯨魚玩家 (Whales)"  # 高付費高投入
                else:
                    labels[cluster_id] = "付費休閒玩家"  # 高付費低投入
            elif playtime > segment_stats['total_playtime_hours'].quantile(0.75):
                if frequency > segment_stats['sessions_per_week'].quantile(0.75):
                    labels[cluster_id] = "核心玩家 (Hardcore)"  # 高投入高頻率
                else:
                    labels[cluster_id] = "沉浸玩家 (Engaged)"  # 高投入低頻率
            elif frequency > segment_stats['sessions_per_week'].quantile(0.5):
                labels[cluster_id] = "活躍休閒玩家"  # 中等頻率
            else:
                labels[cluster_id] = "輕度玩家 (Casual)"  # 低投入

        return labels

    def analyze_purchase_patterns(self) -> Dict[str, any]:
        """
        分析遊戲內購買模式

        Returns:
            購買模式分析結果
        """
        results = {}

        # 付費玩家比例
        if 'in_app_purchases' in self.players.columns:
            paying_players = self.players[self.players['in_app_purchases'] > 0]
            results['paying_player_ratio'] = len(paying_players) / len(self.players) * 100
            results['total_paying_players'] = len(paying_players)

            # 付費玩家分級
            if len(paying_players) > 0:
                spending = paying_players['virtual_currency_spent']
                results['spending_tiers'] = {
                    'Minnows (小額)': len(spending[spending < spending.quantile(0.5)]),
                    'Dolphins (中額)': len(spending[(spending >= spending.quantile(0.5)) &
                                                    (spending < spending.quantile(0.9))]),
                    'Whales (大額)': len(spending[spending >= spending.quantile(0.9)])
                }

                # 購買頻率分析
                results['avg_purchases_per_player'] = paying_players['in_app_purchases'].mean()
                results['avg_spending_per_player'] = paying_players['virtual_currency_spent'].mean()
                results['total_revenue'] = paying_players['virtual_currency_spent'].sum()

                # 鯨魚玩家貢獻度
                whales = paying_players[
                    paying_players['virtual_currency_spent'] >= spending.quantile(0.9)
                ]
                results['whale_revenue_contribution'] = (
                    whales['virtual_currency_spent'].sum() / results['total_revenue'] * 100
                )

        # 按玩家等級分析付費
        if 'level' in self.players.columns:
            level_spending = self.players.groupby(
                pd.cut(self.players['level'], bins=[0, 20, 40, 60, 80, 100],
                       labels=['1-20', '21-40', '41-60', '61-80', '81-100'])
            ).agg({
                'virtual_currency_spent': ['mean', 'sum'],
                'in_app_purchases': 'mean',
                'player_id': 'count'
            }).round(2)
            level_spending.columns = ['avg_spending', 'total_spending', 'avg_purchases', 'player_count']
            results['by_level'] = level_spending

        return results

    def calculate_engagement_metrics(self) -> pd.DataFrame:
        """
        計算玩家參與度指標

        Returns:
            包含參與度分數的DataFrame
        """
        df = self.players.copy()
        engagement_score = pd.Series(0.0, index=df.index)

        # 遊戲時長貢獻 (30%)
        if 'total_playtime_hours' in df.columns:
            playtime_score = (df['total_playtime_hours'] / df['total_playtime_hours'].max() * 30)
            engagement_score += playtime_score

        # 遊戲頻率貢獻 (25%)
        if 'sessions_per_week' in df.columns:
            frequency_score = (df['sessions_per_week'] / df['sessions_per_week'].max() * 25)
            engagement_score += frequency_score

        # 成就解鎖貢獻 (20%)
        if 'achievements_unlocked' in df.columns:
            achievement_score = (df['achievements_unlocked'] / df['achievements_unlocked'].max() * 20)
            engagement_score += achievement_score

        # 社交互動貢獻 (15%)
        if 'social_interactions' in df.columns:
            social_score = (df['social_interactions'] / df['social_interactions'].max() * 15)
            engagement_score += social_score

        # 等級進度貢獻 (10%)
        if 'level' in df.columns:
            level_score = (df['level'] / df['level'].max() * 10)
            engagement_score += level_score

        df['engagement_score'] = engagement_score.round(1)
        df['engagement_tier'] = pd.cut(
            df['engagement_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['低參與度', '中參與度', '高參與度', '超高參與度']
        )

        return df

    def predict_retention_risk(self) -> pd.DataFrame:
        """
        預測玩家流失風險

        考慮因素:
        - 最近遊戲活躍度下降
        - 會話頻率變化
        - 付費行為
        - 社交互動程度
        """
        df = self.players.copy()
        churn_risk = pd.Series(0.0, index=df.index)

        # 低遊戲頻率風險
        if 'sessions_per_week' in df.columns:
            low_frequency_risk = np.where(
                df['sessions_per_week'] < df['sessions_per_week'].quantile(0.25),
                30, 0
            )
            churn_risk += low_frequency_risk

        # 帳號年齡但低等級（早期流失風險）
        if 'account_age_days' in df.columns and 'level' in df.columns:
            expected_level = df['account_age_days'] / 10  # 假設每10天升1級
            underperforming = df['level'] < expected_level * 0.5
            churn_risk += np.where(underperforming, 25, 0)

        # 無付費玩家（較低黏性）
        if 'in_app_purchases' in df.columns:
            no_purchase_risk = np.where(df['in_app_purchases'] == 0, 20, 0)
            churn_risk += no_purchase_risk

        # 低社交互動
        if 'social_interactions' in df.columns:
            low_social_risk = np.where(
                df['social_interactions'] < df['social_interactions'].quantile(0.25),
                15, 0
            )
            churn_risk += low_social_risk

        # 非公會成員
        if 'guild_membership' in df.columns:
            no_guild_risk = np.where(df['guild_membership'] == False, 10, 0)
            churn_risk += no_guild_risk

        df['churn_risk_score'] = churn_risk.clip(0, 100).round(1)
        df['retention_status'] = pd.cut(
            df['churn_risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['穩定', '注意', '高風險', '極高風險']
        )

        return df

    def calculate_player_lifetime_value(self) -> pd.DataFrame:
        """
        計算玩家生命週期價值 (LTV)

        LTV = 平均每日消費 × 預期留存天數
        """
        df = self.players.copy()

        # 計算每日平均消費
        if 'virtual_currency_spent' in df.columns and 'account_age_days' in df.columns:
            df['daily_spending'] = (
                df['virtual_currency_spent'] / df['account_age_days'].replace(0, 1)
            ).round(2)

            # 預期留存天數（基於參與度和流失風險）
            base_retention = 365  # 基礎預期天數

            if 'engagement_score' in df.columns:
                engagement_multiplier = df['engagement_score'] / 50
            else:
                engagement_multiplier = 1.0

            if 'churn_risk_score' in df.columns:
                churn_multiplier = 1 - (df['churn_risk_score'] / 200)
            else:
                churn_multiplier = 1.0

            df['expected_retention_days'] = (
                base_retention * engagement_multiplier * churn_multiplier
            ).clip(lower=30).round(0)

            # 計算LTV
            df['player_ltv'] = (df['daily_spending'] * df['expected_retention_days']).round(2)

            # LTV分級
            df['ltv_tier'] = pd.cut(
                df['player_ltv'],
                bins=[0, df['player_ltv'].quantile(0.5),
                      df['player_ltv'].quantile(0.85),
                      df['player_ltv'].quantile(0.95),
                      float('inf')],
                labels=['Bronze', 'Silver', 'Gold', 'Platinum']
            )

        return df

    def generate_segment_report(self) -> str:
        """生成玩家分群報告"""
        if 'player_segment' not in self.players.columns:
            return "請先執行 segment_players() 進行玩家分群"

        report = f"""
{'='*80}
                        玩家分群分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、分群概覽
{'='*40}
"""
        segment_counts = self.players['player_segment'].value_counts()
        for segment, count in segment_counts.items():
            pct = count / len(self.players) * 100
            report += f"  {segment}: {count:,} 位 ({pct:.1f}%)\n"

        report += f"""
二、各分群特徵
{'='*40}
"""

        # 計算各分群的關鍵指標
        segment_stats = self.players.groupby('player_segment').agg({
            'total_playtime_hours': 'mean',
            'sessions_per_week': 'mean',
            'virtual_currency_spent': ['mean', 'sum'],
            'level': 'mean',
            'achievements_unlocked': 'mean',
            'player_id': 'count'
        }).round(1)

        for segment in segment_counts.index:
            stats = segment_stats.loc[segment]
            report += f"\n  【{segment}】\n"
            report += f"    玩家數: {int(stats[('player_id', 'count')]):,}\n"
            report += f"    平均遊戲時長: {stats[('total_playtime_hours', 'mean')]:.1f} 小時\n"
            report += f"    每週會話數: {stats[('sessions_per_week', 'mean')]:.1f}\n"
            report += f"    平均消費: ${stats[('virtual_currency_spent', 'mean')]:.2f}\n"
            report += f"    總貢獻營收: ${stats[('virtual_currency_spent', 'sum')]:.2f}\n"
            report += f"    平均等級: {stats[('level', 'mean')]:.1f}\n"

        report += f"""
三、營運建議
{'='*40}
"""

        # 為每個分群提供建議
        for segment in segment_counts.index:
            report += f"\n  {segment}:\n"

            if "鯨魚" in segment:
                report += "    ✓ 提供VIP專屬內容和特權\n"
                report += "    ✓ 優先客服支援和個人化服務\n"
                report += "    ✓ 限定商品和早期訪問權\n"
            elif "核心玩家" in segment:
                report += "    ✓ 提供挑戰性內容和競技模式\n"
                report += "    ✓ 引導加入高級公會和社群\n"
                report += "    ✓ 推送高價值付費轉換優惠\n"
            elif "輕度" in segment or "休閒" in segment:
                report += "    ✓ 簡化遊戲流程，降低上手難度\n"
                report += "    ✓ 提供小額首購優惠\n"
                report += "    ✓ 增加社交功能引導\n"

        report += f"""
{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_gaming_player_data(n_players: int = 2000, seed: int = 42) -> pd.DataFrame:
    """
    生成模擬遊戲玩家數據

    Args:
        n_players: 玩家數量
        seed: 隨機種子

    Returns:
        玩家數據DataFrame
    """
    np.random.seed(seed)

    # ========================================
    # 定義玩家行為模式
    # ========================================
    # 不同類型玩家的基礎特徵
    player_types = {
        'whale': {  # 鯨魚玩家 (5%)
            'weight': 0.05,
            'playtime_range': (200, 1000),
            'sessions_range': (15, 35),
            'purchases_range': (50, 200),
            'spending_range': (5000, 50000),
            'level_range': (70, 100)
        },
        'hardcore': {  # 核心玩家 (15%)
            'weight': 0.15,
            'playtime_range': (300, 800),
            'sessions_range': (20, 40),
            'purchases_range': (5, 30),
            'spending_range': (500, 5000),
            'level_range': (60, 95)
        },
        'engaged': {  # 沉浸玩家 (20%)
            'weight': 0.20,
            'playtime_range': (100, 400),
            'sessions_range': (10, 25),
            'purchases_range': (3, 20),
            'spending_range': (200, 2000),
            'level_range': (40, 75)
        },
        'casual_paying': {  # 付費休閒玩家 (15%)
            'weight': 0.15,
            'playtime_range': (50, 150),
            'sessions_range': (5, 15),
            'purchases_range': (1, 10),
            'spending_range': (50, 500),
            'level_range': (20, 50)
        },
        'casual_free': {  # 免費休閒玩家 (45%)
            'weight': 0.45,
            'playtime_range': (10, 100),
            'sessions_range': (2, 10),
            'purchases_range': (0, 2),
            'spending_range': (0, 50),
            'level_range': (5, 40)
        }
    }

    players = []

    for i in range(1, n_players + 1):
        # 隨機選擇玩家類型
        player_type = np.random.choice(
            list(player_types.keys()),
            p=[pt['weight'] for pt in player_types.values()]
        )

        type_config = player_types[player_type]

        # 生成帳號年齡（天數）
        account_age_days = int(np.random.lognormal(4.5, 1.2))
        account_age_days = np.clip(account_age_days, 7, 1095)  # 7天到3年

        # 根據類型生成特徵
        total_playtime_hours = int(np.random.uniform(*type_config['playtime_range']))
        sessions_per_week = int(np.random.uniform(*type_config['sessions_range']))
        in_app_purchases = int(np.random.uniform(*type_config['purchases_range']))
        virtual_currency_spent = int(np.random.uniform(*type_config['spending_range']))
        level = int(np.random.uniform(*type_config['level_range']))

        # 成就解鎖數（與等級和遊戲時長相關）
        achievements_base = (level * 0.8 + total_playtime_hours * 0.05)
        achievements_unlocked = int(np.clip(
            np.random.normal(achievements_base, achievements_base * 0.3),
            0, 150
        ))

        # PVP勝場數（核心玩家較高）
        if player_type in ['whale', 'hardcore']:
            pvp_wins = int(np.random.lognormal(4, 1.5))
        else:
            pvp_wins = int(np.random.lognormal(2, 1.8))
        pvp_wins = np.clip(pvp_wins, 0, 5000)

        # PVE完成數
        pve_completions = int(total_playtime_hours * np.random.uniform(2, 8))

        # 社交互動次數
        if player_type in ['whale', 'hardcore', 'engaged']:
            social_interactions = int(np.random.lognormal(5, 1.5))
        else:
            social_interactions = int(np.random.lognormal(3, 2))
        social_interactions = np.clip(social_interactions, 0, 10000)

        # 公會成員（高參與玩家更可能加入）
        guild_prob = {
            'whale': 0.95, 'hardcore': 0.85, 'engaged': 0.70,
            'casual_paying': 0.40, 'casual_free': 0.20
        }
        guild_membership = np.random.random() < guild_prob[player_type]

        players.append({
            'player_id': f'P{i:07d}',
            'account_age_days': account_age_days,
            'level': level,
            'total_playtime_hours': total_playtime_hours,
            'sessions_per_week': sessions_per_week,
            'in_app_purchases': in_app_purchases,
            'virtual_currency_spent': virtual_currency_spent,
            'achievements_unlocked': achievements_unlocked,
            'pvp_wins': pvp_wins,
            'pve_completions': pve_completions,
            'social_interactions': social_interactions,
            'guild_membership': guild_membership,
            'player_type_actual': player_type  # 實際類型（用於驗證）
        })

    df = pd.DataFrame(players)

    return df


def visualize_player_segments(analyzer: GamingPlayerAnalyzer,
                              output_dir: str = 'data/outputs'):
    """
    視覺化玩家分群結果

    Args:
        analyzer: 遊戲玩家分析器實例
        output_dir: 輸出目錄
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False

        # 創建畫布
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('遊戲玩家分群視覺化分析', fontsize=16, fontweight='bold')

        df = analyzer.players

        # 1. 遊戲時長 vs 消費金額（按分群著色）
        if 'player_segment' in df.columns:
            ax1 = axes[0, 0]
            for segment in df['player_segment'].unique():
                segment_data = df[df['player_segment'] == segment]
                ax1.scatter(
                    segment_data['total_playtime_hours'],
                    segment_data['virtual_currency_spent'],
                    label=segment, alpha=0.6, s=50
                )
            ax1.set_xlabel('總遊戲時長（小時）', fontsize=11)
            ax1.set_ylabel('虛擬貨幣消費', fontsize=11)
            ax1.set_title('遊戲時長 vs 消費金額', fontsize=12, fontweight='bold')
            ax1.legend(fontsize=9)
            ax1.grid(True, alpha=0.3)

        # 2. 玩家分群分佈
        if 'player_segment' in df.columns:
            ax2 = axes[0, 1]
            segment_counts = df['player_segment'].value_counts()
            colors = sns.color_palette('husl', len(segment_counts))
            ax2.pie(segment_counts.values, labels=segment_counts.index,
                   autopct='%1.1f%%', colors=colors, startangle=90)
            ax2.set_title('玩家分群分佈', fontsize=12, fontweight='bold')

        # 3. 參與度分數分佈
        if 'engagement_score' in df.columns:
            ax3 = axes[1, 0]
            ax3.hist(df['engagement_score'], bins=30, edgecolor='black', alpha=0.7)
            ax3.axvline(df['engagement_score'].mean(), color='red',
                       linestyle='--', linewidth=2, label=f'平均值: {df["engagement_score"].mean():.1f}')
            ax3.set_xlabel('參與度分數', fontsize=11)
            ax3.set_ylabel('玩家數量', fontsize=11)
            ax3.set_title('玩家參與度分佈', fontsize=12, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3, axis='y')

        # 4. 流失風險 vs LTV
        if 'churn_risk_score' in df.columns and 'player_ltv' in df.columns:
            ax4 = axes[1, 1]
            scatter = ax4.scatter(
                df['churn_risk_score'],
                df['player_ltv'],
                c=df['engagement_score'] if 'engagement_score' in df.columns else 'blue',
                cmap='RdYlGn', alpha=0.6, s=50
            )
            ax4.set_xlabel('流失風險分數', fontsize=11)
            ax4.set_ylabel('玩家生命週期價值 (LTV)', fontsize=11)
            ax4.set_title('流失風險 vs 玩家價值', fontsize=12, fontweight='bold')
            ax4.grid(True, alpha=0.3)

            # 添加顏色條
            if 'engagement_score' in df.columns:
                cbar = plt.colorbar(scatter, ax=ax4)
                cbar.set_label('參與度分數', fontsize=10)

        plt.tight_layout()

        # 保存圖表
        import os
        os.makedirs(output_dir, exist_ok=True)
        output_path = f'{output_dir}/gaming_player_analysis.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"  ✓ 視覺化圖表已保存至: {output_path}")

        plt.close()

    except Exception as e:
        print(f"  ⚠️ 視覺化過程發生錯誤: {e}")


def main():
    """執行完整的遊戲玩家行為分析"""
    print("="*80)
    print(" "*20 + "遊戲玩家行為分析")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/7] 生成遊戲玩家數據...")

    players_df = generate_gaming_player_data(n_players=2000, seed=42)

    print(f"  ✓ 玩家總數: {len(players_df):,}")
    print(f"  ✓ 付費玩家: {len(players_df[players_df['in_app_purchases'] > 0]):,}")
    print(f"  ✓ 公會成員: {players_df['guild_membership'].sum():,}")
    print(f"  ✓ 總遊戲時長: {players_df['total_playtime_hours'].sum():,.0f} 小時")

    # ========================================
    # 2. 數據驗證
    # ========================================
    print("\n[2/7] 執行數據驗證...")

    validator = DataValidator(players_df)
    missing_check = validator.check_missing_values()
    duplicate_check = validator.check_duplicates()

    print(f"  ✓ 缺失值檢查: {missing_check['total_missing_cells']} 個缺失值")
    print(f"  ✓ 重複值檢查: {duplicate_check['duplicate_count']} 筆重複")
    print(f"  ✓ 數值欄位: {len(validator.check_data_types()['numeric_columns'])} 個")

    # ========================================
    # 3. 初始化分析器
    # ========================================
    print("\n[3/7] 初始化玩家分析器...")

    analyzer = GamingPlayerAnalyzer(players_df)
    print("  ✓ 分析器初始化完成")
    print(f"  ✓ 衍生特徵: 平均會話時長, 平均購買金額, 每日遊戲時長")

    # ========================================
    # 4. 玩家分群分析
    # ========================================
    print("\n[4/7] 執行玩家分群分析...")

    segmented_df = analyzer.segment_players(n_clusters=5, method='kmeans')

    print("\n  玩家分群結果:")
    segment_counts = segmented_df['player_segment'].value_counts()
    for segment, count in segment_counts.items():
        pct = count / len(segmented_df) * 100
        bar = '█' * int(pct / 2)
        print(f"    {segment:20}: {count:4} ({pct:5.1f}%) {bar}")

    # ========================================
    # 5. 購買模式分析
    # ========================================
    print("\n[5/7] 分析遊戲內購買模式...")

    purchase_analysis = analyzer.analyze_purchase_patterns()

    print(f"\n  💰 購買模式摘要:")
    print(f"     付費玩家比例: {purchase_analysis['paying_player_ratio']:.1f}%")
    print(f"     總營收: ${purchase_analysis['total_revenue']:,.2f}")
    print(f"     平均每位付費玩家消費: ${purchase_analysis['avg_spending_per_player']:.2f}")
    print(f"     鯨魚玩家營收貢獻: {purchase_analysis['whale_revenue_contribution']:.1f}%")

    print("\n  付費玩家分級:")
    for tier, count in purchase_analysis['spending_tiers'].items():
        print(f"     {tier}: {count} 位")

    # ========================================
    # 6. 參與度和留存分析
    # ========================================
    print("\n[6/7] 計算參與度和留存指標...")

    # 計算參與度
    engagement_df = analyzer.calculate_engagement_metrics()
    analyzer.players = engagement_df

    print(f"\n  📊 參與度分析:")
    engagement_dist = engagement_df['engagement_tier'].value_counts()
    for tier in ['超高參與度', '高參與度', '中參與度', '低參與度']:
        count = engagement_dist.get(tier, 0)
        pct = count / len(engagement_df) * 100
        print(f"     {tier}: {count} ({pct:.1f}%)")

    # 預測流失風險
    retention_df = analyzer.predict_retention_risk()
    analyzer.players = retention_df

    print(f"\n  ⚠️  流失風險評估:")
    retention_dist = retention_df['retention_status'].value_counts()
    for status in ['極高風險', '高風險', '注意', '穩定']:
        count = retention_dist.get(status, 0)
        pct = count / len(retention_df) * 100
        print(f"     {status}: {count} ({pct:.1f}%)")

    # 計算LTV
    ltv_df = analyzer.calculate_player_lifetime_value()
    analyzer.players = ltv_df

    print(f"\n  💎 玩家價值分析:")
    print(f"     平均LTV: ${ltv_df['player_ltv'].mean():.2f}")
    print(f"     中位數LTV: ${ltv_df['player_ltv'].median():.2f}")
    print(f"     Top 10% LTV: ${ltv_df['player_ltv'].quantile(0.9):.2f}")

    # ========================================
    # 7. 生成報告和視覺化
    # ========================================
    print("\n[7/7] 生成分析報告和視覺化...")

    # 生成文字報告
    report = analyzer.generate_segment_report()
    print(report)

    # 保存報告
    try:
        import os
        os.makedirs('data/outputs', exist_ok=True)

        with open('data/outputs/gaming_player_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n  📄 報告已保存至: data/outputs/gaming_player_report.txt")

        # 保存詳細數據
        analyzer.players.to_csv('data/outputs/gaming_player_analysis.csv', index=False)
        print("  📊 詳細數據已保存至: data/outputs/gaming_player_analysis.csv")

    except Exception as e:
        print(f"\n  ⚠️ 無法保存報告: {e}")

    # 生成視覺化
    visualize_player_segments(analyzer)

    # ========================================
    # 總結與建議
    # ========================================
    print("\n" + "="*80)
    print(" "*25 + "分析總結")
    print("="*80)

    high_value_players = ltv_df[ltv_df['ltv_tier'].isin(['Gold', 'Platinum'])]
    at_risk_valuable = ltv_df[
        (ltv_df['ltv_tier'].isin(['Gold', 'Platinum'])) &
        (ltv_df['retention_status'].isin(['高風險', '極高風險']))
    ]

    print(f"""
    🎮 玩家總數: {len(players_df):,}
    💰 總營收: ${purchase_analysis['total_revenue']:,.2f}

    📈 高價值玩家 (Gold/Platinum): {len(high_value_players):,} ({len(high_value_players)/len(players_df)*100:.1f}%)
    ⚠️  高價值但有流失風險: {len(at_risk_valuable):,} 位

    🎯 關鍵營運建議:
       1. 優先關注 {len(at_risk_valuable)} 位高價值流失風險玩家
       2. 針對 {segment_counts.index[0]} 設計專屬活動和獎勵
       3. 提升免費玩家的付費轉換率（目前 {purchase_analysis['paying_player_ratio']:.1f}%）
       4. 強化社交功能，提高公會參與度
       5. 根據玩家分群設計個性化推薦系統

    📊 下一步分析方向:
       - A/B測試不同的遊戲內購優惠方案
       - 分析高流失風險玩家的共同行為模式
       - 建立玩家留存預測模型
       - 優化新手引導流程，提升早期留存
    """)

    print("="*80)
    print(" "*25 + "分析完成！")
    print("="*80)

    return analyzer


if __name__ == "__main__":
    analyzer = main()
