"""
運動數據分析範例

這個範例展示如何分析職業籃球運動員數據，包含：
- 球員表現聚類分析 (使用 KMeans)
- 球隊統計分析與比較
- 球員績效預測模型
- 球員對比視覺化

真實應用場景:
- 球隊選秀與交易決策
- 球員表現評估與薪資談判
- 戰術分析與陣容優化
- 球員發展路徑規劃
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory, KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')


class SportsAnalyzer:
    """
    運動數據分析器

    提供完整的球員數據分析功能:
    - 球員表現聚類 (角色定位)
    - 球隊統計分析
    - 績效預測
    - 球員價值評估
    - MVP 候選人識別
    """

    def __init__(self, players_df: pd.DataFrame, games_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            players_df: 球員數據 DataFrame，需包含:
                - player_name: 球員姓名
                - team: 球隊
                - position: 位置
                - points_per_game: 場均得分
                - assists: 助攻
                - rebounds: 籃板
                - steals: 抄截
                - blocks: 阻攻
                - minutes_played: 上場時間
                - field_goal_pct: 投籃命中率
                - three_point_pct: 三分命中率
                - player_efficiency_rating: 球員效率值 (PER)
            games_df: 比賽記錄 DataFrame (可選)
        """
        self.players = players_df.copy()
        self.games = games_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據，計算衍生指標"""
        # 計算綜合得分貢獻
        if all(col in self.players.columns for col in ['points_per_game', 'assists', 'rebounds']):
            self.players['offensive_contribution'] = (
                self.players['points_per_game'] +
                self.players['assists'] * 2 +  # 助攻產生的間接得分
                self.players['rebounds'] * 0.5
            ).round(2)

        # 計算防守貢獻
        if all(col in self.players.columns for col in ['steals', 'blocks', 'rebounds']):
            self.players['defensive_contribution'] = (
                self.players['steals'] * 2 +
                self.players['blocks'] * 2 +
                self.players['rebounds'] * 0.3
            ).round(2)

        # 計算效率分數
        if all(col in self.players.columns for col in ['points_per_game', 'minutes_played']):
            self.players['points_per_minute'] = (
                self.players['points_per_game'] / self.players['minutes_played']
            ).round(3)

        # 計算真實命中率 (True Shooting %)
        if all(col in self.players.columns for col in ['field_goal_pct', 'three_point_pct']):
            self.players['true_shooting_pct'] = (
                (self.players['field_goal_pct'] * 0.6 +
                 self.players['three_point_pct'] * 0.4)
            ).round(3)

        # 計算綜合價值分數
        if 'player_efficiency_rating' in self.players.columns:
            self.players['overall_value'] = (
                self.players['player_efficiency_rating'] * 0.4 +
                self.players['offensive_contribution'] * 0.3 +
                self.players['defensive_contribution'] * 0.3
            ).round(2)

    def cluster_players(self, n_clusters: int = 5) -> pd.DataFrame:
        """
        使用 KMeans 對球員進行聚類分析，識別不同的球員角色

        球員角色類型可能包含:
        - 得分型球員 (Scorer)
        - 組織型球員 (Playmaker)
        - 防守型球員 (Defender)
        - 全能型球員 (All-Around)
        - 角色球員 (Role Player)

        Args:
            n_clusters: 聚類數量，預設 5

        Returns:
            包含聚類標籤的球員 DataFrame
        """
        # 選擇聚類特徵
        cluster_features = [
            'points_per_game', 'assists', 'rebounds',
            'steals', 'blocks', 'field_goal_pct',
            'three_point_pct', 'player_efficiency_rating'
        ]

        # 確保所有特徵存在
        available_features = [f for f in cluster_features if f in self.players.columns]

        if len(available_features) < 3:
            raise ValueError("球員數據缺少必要的特徵欄位進行聚類分析")

        # 準備聚類數據 (填補缺失值)
        cluster_data = self.players[available_features].fillna(0)

        # 使用 ClustererFactory 創建 KMeans 聚類器
        clusterer = ClustererFactory.create('kmeans', n_clusters=n_clusters, random_state=42)

        # 執行聚類 (傳遞 DataFrame 和特徵欄位列表)
        labels = clusterer.fit_predict(cluster_data, available_features, scale_features=True)
        self.players['cluster'] = labels

        # 為每個聚類命名 (根據特徵平均值)
        cluster_profiles = self.players.groupby('cluster')[available_features].mean()
        cluster_names = self._name_clusters(cluster_profiles)

        self.players['player_role'] = self.players['cluster'].map(cluster_names)

        return self.players

    def _name_clusters(self, cluster_profiles: pd.DataFrame) -> Dict[int, str]:
        """
        根據聚類特徵配置檔案為聚類命名

        Args:
            cluster_profiles: 每個聚類的平均特徵值

        Returns:
            聚類ID到角色名稱的映射
        """
        cluster_names = {}

        for cluster_id, profile in cluster_profiles.iterrows():
            # 得分型: 高得分，中等助攻
            if profile.get('points_per_game', 0) > cluster_profiles['points_per_game'].median() * 1.5:
                role = '得分型球員 (Scorer)'

            # 組織型: 高助攻，中等得分
            elif profile.get('assists', 0) > cluster_profiles['assists'].median() * 1.3:
                role = '組織型球員 (Playmaker)'

            # 防守型: 高抄截+阻攻，低得分
            elif (profile.get('steals', 0) + profile.get('blocks', 0)) > \
                 (cluster_profiles['steals'].median() + cluster_profiles['blocks'].median()) * 1.2:
                role = '防守型球員 (Defender)'

            # 全能型: 各項數據都不錯
            elif profile.get('player_efficiency_rating', 0) > cluster_profiles['player_efficiency_rating'].median() * 1.2:
                role = '全能型球員 (All-Around)'

            # 角色球員: 其他
            else:
                role = '角色球員 (Role Player)'

            cluster_names[cluster_id] = role

        return cluster_names

    def analyze_team_statistics(self) -> pd.DataFrame:
        """
        分析球隊統計數據

        Returns:
            球隊統計摘要 DataFrame
        """
        if 'team' not in self.players.columns:
            return pd.DataFrame()

        # 球隊整體統計
        team_stats = self.players.groupby('team').agg({
            'points_per_game': ['sum', 'mean', 'std'],
            'assists': ['sum', 'mean'],
            'rebounds': ['sum', 'mean'],
            'steals': 'sum',
            'blocks': 'sum',
            'player_efficiency_rating': 'mean',
            'player_name': 'count'
        }).round(2)

        team_stats.columns = [
            'total_points', 'avg_points_per_player', 'points_std',
            'total_assists', 'avg_assists_per_player',
            'total_rebounds', 'avg_rebounds_per_player',
            'total_steals', 'total_blocks',
            'team_avg_per', 'roster_size'
        ]

        # 計算球隊進攻效率
        team_stats['offensive_rating'] = (
            team_stats['total_points'] * 0.5 +
            team_stats['total_assists'] * 0.3 +
            team_stats['total_rebounds'] * 0.2
        ).round(2)

        # 計算球隊防守效率
        team_stats['defensive_rating'] = (
            team_stats['total_steals'] * 0.6 +
            team_stats['total_blocks'] * 0.4
        ).round(2)

        # 計算球隊整體評分
        team_stats['overall_rating'] = (
            team_stats['offensive_rating'] * 0.6 +
            team_stats['defensive_rating'] * 0.4 +
            team_stats['team_avg_per'] * 2
        ).round(2)

        # 球隊排名
        team_stats['rank'] = team_stats['overall_rating'].rank(ascending=False).astype(int)

        return team_stats.sort_values('overall_rating', ascending=False)

    def predict_player_performance(self, player_features: pd.DataFrame) -> pd.DataFrame:
        """
        預測球員未來表現

        使用歷史數據和趨勢分析預測球員績效

        Args:
            player_features: 球員特徵數據

        Returns:
            包含預測分數的 DataFrame
        """
        df = player_features.copy()

        # 基於當前表現預測未來 PER (簡化版線性模型)
        if all(col in df.columns for col in ['player_efficiency_rating', 'minutes_played', 'age']):
            # 年齡因素: 25-29歲巔峰期
            age_factor = np.where(
                (df['age'] >= 25) & (df['age'] <= 29), 1.1,
                np.where((df['age'] < 25) | (df['age'] > 32), 0.95, 1.0)
            )

            # 上場時間因素: 穩定的上場時間有助於表現
            minutes_factor = np.where(df['minutes_played'] >= 30, 1.05, 0.98)

            # 預測下賽季 PER
            df['predicted_per'] = (
                df['player_efficiency_rating'] * age_factor * minutes_factor
            ).round(2)

            # 預測趨勢
            df['trend'] = np.where(
                df['predicted_per'] > df['player_efficiency_rating'] * 1.05, 'Improving',
                np.where(df['predicted_per'] < df['player_efficiency_rating'] * 0.95, 'Declining', 'Stable')
            )

        # 計算潛力分數 (針對年輕球員)
        if 'age' in df.columns:
            df['potential_score'] = np.where(
                df['age'] < 25,
                (30 - df['age']) / 5 * df.get('player_efficiency_rating', 15),
                df.get('player_efficiency_rating', 15) * 0.8
            ).round(2)

        return df

    def identify_mvp_candidates(self, top_n: int = 10) -> pd.DataFrame:
        """
        識別 MVP 候選球員

        綜合考量:
        - 球員效率值 (PER)
        - 場均得分
        - 助攻與籃板
        - 球隊表現 (如果有球隊數據)

        Args:
            top_n: 返回前 N 名候選人

        Returns:
            MVP 候選人 DataFrame
        """
        df = self.players.copy()

        # 計算 MVP 分數
        mvp_score = pd.Series(0.0, index=df.index)

        # PER 權重最高 (40%)
        if 'player_efficiency_rating' in df.columns:
            per_normalized = (df['player_efficiency_rating'] - df['player_efficiency_rating'].min()) / \
                           (df['player_efficiency_rating'].max() - df['player_efficiency_rating'].min())
            mvp_score += per_normalized * 40

        # 場均得分 (30%)
        if 'points_per_game' in df.columns:
            ppg_normalized = (df['points_per_game'] - df['points_per_game'].min()) / \
                           (df['points_per_game'].max() - df['points_per_game'].min())
            mvp_score += ppg_normalized * 30

        # 綜合貢獻 (20%)
        if 'overall_value' in df.columns:
            value_normalized = (df['overall_value'] - df['overall_value'].min()) / \
                             (df['overall_value'].max() - df['overall_value'].min())
            mvp_score += value_normalized * 20

        # 上場時間 (10%) - MVP 通常是主力球員
        if 'minutes_played' in df.columns:
            minutes_normalized = (df['minutes_played'] - df['minutes_played'].min()) / \
                               (df['minutes_played'].max() - df['minutes_played'].min())
            mvp_score += minutes_normalized * 10

        df['mvp_score'] = mvp_score.round(2)
        df['mvp_rank'] = df['mvp_score'].rank(ascending=False).astype(int)

        # 選擇 MVP 候選人
        mvp_candidates = df.nsmallest(top_n, 'mvp_rank')[[
            'player_name', 'team', 'position', 'points_per_game',
            'assists', 'rebounds', 'player_efficiency_rating',
            'mvp_score', 'mvp_rank'
        ]]

        return mvp_candidates.sort_values('mvp_rank')

    def compare_players(self, player_names: List[str]) -> pd.DataFrame:
        """
        比較多名球員的數據

        Args:
            player_names: 球員姓名列表

        Returns:
            球員對比 DataFrame
        """
        comparison_features = [
            'player_name', 'team', 'position', 'age',
            'points_per_game', 'assists', 'rebounds',
            'steals', 'blocks', 'field_goal_pct',
            'three_point_pct', 'player_efficiency_rating',
            'offensive_contribution', 'defensive_contribution'
        ]

        # 選擇存在的特徵
        available_features = [f for f in comparison_features if f in self.players.columns]

        # 篩選球員
        compared_players = self.players[
            self.players['player_name'].isin(player_names)
        ][available_features]

        return compared_players

    def analyze_position_benchmarks(self) -> pd.DataFrame:
        """
        分析各位置的基準數據

        Returns:
            位置基準統計 DataFrame
        """
        if 'position' not in self.players.columns:
            return pd.DataFrame()

        position_stats = self.players.groupby('position').agg({
            'points_per_game': ['mean', 'median', 'std', 'max'],
            'assists': ['mean', 'median', 'max'],
            'rebounds': ['mean', 'median', 'max'],
            'player_efficiency_rating': ['mean', 'median', 'std'],
            'player_name': 'count'
        }).round(2)

        position_stats.columns = ['_'.join(col) for col in position_stats.columns]

        return position_stats

    def generate_insights(self) -> List[str]:
        """生成關鍵洞察"""
        insights = []

        # 最佳球員洞察
        if 'player_efficiency_rating' in self.players.columns:
            top_player = self.players.nlargest(1, 'player_efficiency_rating').iloc[0]
            insights.append(
                f"🏆 效率王: {top_player['player_name']} "
                f"(PER: {top_player['player_efficiency_rating']:.1f})"
            )

        # 得分王洞察
        if 'points_per_game' in self.players.columns:
            top_scorer = self.players.nlargest(1, 'points_per_game').iloc[0]
            insights.append(
                f"⭐ 得分王: {top_scorer['player_name']} "
                f"(場均 {top_scorer['points_per_game']:.1f} 分)"
            )

        # 助攻王洞察
        if 'assists' in self.players.columns:
            top_assists = self.players.nlargest(1, 'assists').iloc[0]
            insights.append(
                f"🎯 助攻王: {top_assists['player_name']} "
                f"(場均 {top_assists['assists']:.1f} 次助攻)"
            )

        # 籃板王洞察
        if 'rebounds' in self.players.columns:
            top_rebounds = self.players.nlargest(1, 'rebounds').iloc[0]
            insights.append(
                f"💪 籃板王: {top_rebounds['player_name']} "
                f"(場均 {top_rebounds['rebounds']:.1f} 籃板)"
            )

        # 命中率洞察
        if 'field_goal_pct' in self.players.columns:
            high_fg = self.players[self.players['minutes_played'] >= 20].nlargest(1, 'field_goal_pct').iloc[0]
            insights.append(
                f"🎯 命中率之王: {high_fg['player_name']} "
                f"({high_fg['field_goal_pct']:.1%} 投籃命中率)"
            )

        # 球隊洞察
        if 'team' in self.players.columns:
            team_stats = self.analyze_team_statistics()
            if not team_stats.empty:
                best_team = team_stats.index[0]
                insights.append(
                    f"🏀 最強球隊: {best_team} "
                    f"(綜合評分: {team_stats.loc[best_team, 'overall_rating']:.1f})"
                )

        # 聚類洞察
        if 'player_role' in self.players.columns:
            role_dist = self.players['player_role'].value_counts()
            most_common_role = role_dist.index[0]
            insights.append(
                f"📊 最常見角色: {most_common_role} ({role_dist.iloc[0]} 名球員)"
            )

        return insights

    def generate_report(self) -> str:
        """生成完整的分析報告"""
        report = f"""
{'='*80}
                    職業籃球數據分析報告
                    {datetime.now().strftime('%Y-%m-%d')}
{'='*80}

一、數據概覽
{'='*40}
  球員總數: {len(self.players):,}
  球隊數量: {self.players['team'].nunique() if 'team' in self.players.columns else 'N/A'}
  平均效率值 (PER): {self.players['player_efficiency_rating'].mean():.2f}
  平均場均得分: {self.players['points_per_game'].mean():.2f}
  平均場均助攻: {self.players['assists'].mean():.2f}
  平均場均籃板: {self.players['rebounds'].mean():.2f}

二、關鍵洞察
{'='*40}
"""
        insights = self.generate_insights()
        for insight in insights:
            report += f"  {insight}\n"

        # MVP 候選人
        report += f"""
三、MVP 候選人 (Top 10)
{'='*40}
"""
        mvp_candidates = self.identify_mvp_candidates(top_n=10)
        for i, (_, player) in enumerate(mvp_candidates.iterrows(), 1):
            report += f"  {i}. {player['player_name']} ({player['team']})\n"
            report += f"     位置: {player['position']}, PER: {player['player_efficiency_rating']:.1f}, "
            report += f"場均: {player['points_per_game']:.1f}分/{player['assists']:.1f}助/{player['rebounds']:.1f}籃\n"
            report += f"     MVP分數: {player['mvp_score']:.2f}\n"

        # 球隊排名
        team_stats = self.analyze_team_statistics()
        if not team_stats.empty:
            report += f"""
四、球隊實力排名 (Top 10)
{'='*40}
"""
            for i, (team, row) in enumerate(team_stats.head(10).iterrows(), 1):
                report += f"  {i}. {team}\n"
                report += f"     總得分: {row['total_points']:.1f}, 進攻效率: {row['offensive_rating']:.1f}\n"
                report += f"     防守效率: {row['defensive_rating']:.1f}, 綜合評分: {row['overall_rating']:.1f}\n"

        # 位置基準
        position_benchmarks = self.analyze_position_benchmarks()
        if not position_benchmarks.empty:
            report += f"""
五、位置數據基準
{'='*40}
"""
            for position, row in position_benchmarks.iterrows():
                report += f"\n  {position}:\n"
                report += f"    場均得分: {row['points_per_game_mean']:.1f} (中位數: {row['points_per_game_median']:.1f})\n"
                report += f"    場均助攻: {row['assists_mean']:.1f} (中位數: {row['assists_median']:.1f})\n"
                report += f"    場均籃板: {row['rebounds_mean']:.1f} (中位數: {row['rebounds_median']:.1f})\n"

        # 球員角色分佈
        if 'player_role' in self.players.columns:
            report += f"""
六、球員角色分佈
{'='*40}
"""
            role_dist = self.players['player_role'].value_counts()
            for role, count in role_dist.items():
                pct = count / len(self.players) * 100
                bar = '█' * int(pct / 2)
                report += f"  {role}: {count} ({pct:.1f}%) {bar}\n"

        # 建議
        report += f"""
七、戰略建議
{'='*40}

1. 球員發展:
   - 重點培養高潛力年輕球員 (25歲以下，PER > 15)
   - 為老將提供更多休息時間以延長職業生涯

2. 陣容優化:
   - 確保各位置都有明星級和角色球員的平衡
   - 注意得分型與組織型球員的配比

3. 交易策略:
   - 關注表現趨勢下滑但仍有市場價值的球員
   - 尋找被低估的防守型球員補強陣容

4. 薪資管理:
   - 基於 PER 和綜合貢獻評估球員市場價值
   - 優先續約核心球員和高潛力年輕球員

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_basketball_data(n_players: int = 150,
                            n_teams: int = 10) -> pd.DataFrame:
    """
    生成真實的籃球運動員數據

    模擬 NBA 級別的球員數據，包含各種位置和技能類型

    Args:
        n_players: 球員數量
        n_teams: 球隊數量

    Returns:
        球員數據 DataFrame
    """
    np.random.seed(42)

    # 球隊名稱
    team_names = [
        '勇士隊', '湖人隊', '公牛隊', '熱火隊', '馬刺隊',
        '塞爾提克隊', '籃網隊', '快艇隊', '火箭隊', '雷霆隊'
    ][:n_teams]

    # 位置分佈
    positions = ['PG', 'SG', 'SF', 'PF', 'C']  # 控球後衛, 得分後衛, 小前鋒, 大前鋒, 中鋒
    position_weights = [0.20, 0.20, 0.25, 0.20, 0.15]

    # 生成球員姓名
    first_names = [
        'Michael', 'LeBron', 'Kobe', 'Stephen', 'Kevin', 'James', 'Chris', 'Russell',
        'Kawhi', 'Giannis', 'Luka', 'Anthony', 'Damian', 'Joel', 'Nikola', 'Paul',
        'Kyrie', 'Jimmy', 'Jayson', 'Devin', 'Trae', 'Donovan', 'Bradley', 'Khris',
        'Pascal', 'Ben', 'De\'Aaron', 'Zion', 'Ja', 'Shai'
    ]

    last_names = [
        'Jordan', 'James', 'Bryant', 'Curry', 'Durant', 'Harden', 'Paul', 'Westbrook',
        'Leonard', 'Antetokounmpo', 'Doncic', 'Davis', 'Lillard', 'Embiid', 'Jokic', 'George',
        'Irving', 'Butler', 'Tatum', 'Booker', 'Young', 'Mitchell', 'Beal', 'Middleton',
        'Siakam', 'Simmons', 'Fox', 'Williamson', 'Morant', 'Gilgeous-Alexander'
    ]

    players = []

    for i in range(n_players):
        # 基本資訊
        position = np.random.choice(positions, p=position_weights)
        team = np.random.choice(team_names)
        age = np.random.randint(19, 38)

        # 生成球員姓名 (組合 + 編號避免重複)
        player_name = f"{np.random.choice(first_names)} {np.random.choice(last_names)} #{i+1}"

        # 根據位置生成不同的數據分佈
        if position == 'PG':  # 控球後衛: 高助攻, 中等得分
            ppg = np.clip(np.random.normal(15, 5), 5, 35)
            assists = np.clip(np.random.normal(7, 2), 2, 12)
            rebounds = np.clip(np.random.normal(4, 1.5), 1, 10)
            steals = np.clip(np.random.normal(1.5, 0.5), 0.5, 3)
            blocks = np.clip(np.random.normal(0.3, 0.2), 0, 1.5)

        elif position == 'SG':  # 得分後衛: 高得分, 中等助攻
            ppg = np.clip(np.random.normal(18, 6), 8, 35)
            assists = np.clip(np.random.normal(4, 1.5), 1, 8)
            rebounds = np.clip(np.random.normal(4, 1.5), 1, 8)
            steals = np.clip(np.random.normal(1.2, 0.4), 0.5, 2.5)
            blocks = np.clip(np.random.normal(0.4, 0.2), 0, 1.5)

        elif position == 'SF':  # 小前鋒: 全能型
            ppg = np.clip(np.random.normal(17, 5), 8, 32)
            assists = np.clip(np.random.normal(4, 2), 1, 9)
            rebounds = np.clip(np.random.normal(6, 2), 2, 12)
            steals = np.clip(np.random.normal(1.3, 0.5), 0.5, 2.8)
            blocks = np.clip(np.random.normal(0.6, 0.3), 0, 2)

        elif position == 'PF':  # 大前鋒: 高籃板, 中等得分
            ppg = np.clip(np.random.normal(16, 5), 6, 28)
            assists = np.clip(np.random.normal(2.5, 1), 0.5, 6)
            rebounds = np.clip(np.random.normal(8, 2), 3, 15)
            steals = np.clip(np.random.normal(1.0, 0.4), 0.3, 2)
            blocks = np.clip(np.random.normal(1.2, 0.5), 0.2, 3)

        else:  # C - 中鋒: 高籃板, 高阻攻
            ppg = np.clip(np.random.normal(14, 5), 5, 28)
            assists = np.clip(np.random.normal(2, 1), 0.5, 6)
            rebounds = np.clip(np.random.normal(10, 2.5), 4, 16)
            steals = np.clip(np.random.normal(0.8, 0.3), 0.2, 1.8)
            blocks = np.clip(np.random.normal(2, 0.8), 0.5, 4)

        # 上場時間 (分鐘)
        minutes_played = np.clip(np.random.normal(28, 8), 10, 40)

        # 投籃命中率 (基於位置有所不同)
        if position in ['C', 'PF']:  # 內線球員命中率較高
            fg_pct = np.clip(np.random.normal(0.48, 0.08), 0.35, 0.65)
            three_pt_pct = np.clip(np.random.normal(0.30, 0.08), 0.15, 0.45)
        else:  # 外線球員
            fg_pct = np.clip(np.random.normal(0.44, 0.07), 0.35, 0.60)
            three_pt_pct = np.clip(np.random.normal(0.36, 0.08), 0.20, 0.50)

        # 計算 PER (球員效率值)
        # 簡化版 PER 計算公式
        per = (ppg * 1.0 + assists * 1.5 + rebounds * 1.2 +
               steals * 2 + blocks * 2 -
               (ppg / fg_pct if fg_pct > 0 else 0) * 0.3)
        per = np.clip(per, 8, 32)

        # 年齡調整 PER (巔峰期 25-29 歲)
        if 25 <= age <= 29:
            per *= 1.1
        elif age < 23 or age > 32:
            per *= 0.95

        players.append({
            'player_id': f'PLAYER{i+1:04d}',
            'player_name': player_name,
            'team': team,
            'position': position,
            'age': age,
            'points_per_game': round(ppg, 1),
            'assists': round(assists, 1),
            'rebounds': round(rebounds, 1),
            'steals': round(steals, 1),
            'blocks': round(blocks, 1),
            'minutes_played': round(minutes_played, 1),
            'field_goal_pct': round(fg_pct, 3),
            'three_point_pct': round(three_pt_pct, 3),
            'player_efficiency_rating': round(per, 1),
            'salary_millions': round(np.clip(per * 1.5 + np.random.normal(0, 5), 1, 45), 2)
        })

    return pd.DataFrame(players)


def main():
    """執行完整的運動數據分析範例"""
    print("="*80)
    print(" "*25 + "職業籃球數據分析")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/6] 生成球員數據...")

    players_df = generate_basketball_data(n_players=150, n_teams=10)

    print(f"  ✓ 球員數量: {len(players_df):,}")
    print(f"  ✓ 球隊數量: {players_df['team'].nunique()}")
    print(f"  ✓ 位置分佈: {dict(players_df['position'].value_counts())}")
    print(f"  ✓ 平均 PER: {players_df['player_efficiency_rating'].mean():.2f}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/6] 初始化分析器...")
    analyzer = SportsAnalyzer(players_df)
    print("  ✓ 分析器初始化完成")
    print(f"  ✓ 計算衍生指標: offensive_contribution, defensive_contribution, overall_value")

    # ========================================
    # 3. 球員聚類分析
    # ========================================
    print("\n[3/6] 執行球員聚類分析 (識別球員角色)...")

    clustered_players = analyzer.cluster_players(n_clusters=5)

    print("\n  球員角色分佈:")
    role_dist = clustered_players['player_role'].value_counts()
    for role, count in role_dist.items():
        pct = count / len(clustered_players) * 100
        bar = '█' * int(pct / 2)
        print(f"    {role:25}: {count:3} ({pct:5.1f}%) {bar}")

    # ========================================
    # 4. 球隊統計分析
    # ========================================
    print("\n[4/6] 分析球隊統計...")

    team_stats = analyzer.analyze_team_statistics()
    print("\n  球隊實力排名 (Top 5):")
    for i, (team, row) in enumerate(team_stats.head(5).iterrows(), 1):
        print(f"    {i}. {team:12} - 綜合評分: {row['overall_rating']:6.2f} "
              f"(進攻: {row['offensive_rating']:5.1f}, 防守: {row['defensive_rating']:5.1f})")

    # ========================================
    # 5. MVP 候選人識別
    # ========================================
    print("\n[5/6] 識別 MVP 候選人...")

    mvp_candidates = analyzer.identify_mvp_candidates(top_n=10)
    print("\n  MVP 候選人 (Top 5):")
    for i, (_, player) in enumerate(mvp_candidates.head(5).iterrows(), 1):
        print(f"    {i}. {player['player_name']:25} ({player['team']:12})")
        print(f"       位置: {player['position']}, PER: {player['player_efficiency_rating']:5.1f}, "
              f"場均: {player['points_per_game']:4.1f}分/{player['assists']:3.1f}助/{player['rebounds']:3.1f}籃")

    # ========================================
    # 6. 球員對比分析
    # ========================================
    print("\n[6/6] 球員對比分析...")

    # 選擇 Top 3 MVP 候選人進行對比
    top_3_players = mvp_candidates.head(3)['player_name'].tolist()
    comparison = analyzer.compare_players(top_3_players)

    print(f"\n  對比球員: {', '.join(top_3_players[:3])}")
    if not comparison.empty:
        print("\n  數據對比:")
        key_stats = ['player_name', 'team', 'points_per_game', 'assists',
                    'rebounds', 'player_efficiency_rating']
        available_stats = [col for col in key_stats if col in comparison.columns]
        print(comparison[available_stats].to_string(index=False))

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    print(" "*30 + "分析摘要")
    print("="*80)

    insights = analyzer.generate_insights()
    for insight in insights:
        print(f"\n  {insight}")

    # 生成並保存報告
    report = analyzer.generate_report()
    print("\n" + report)

    # 保存結果
    output_files = {
        'data/outputs/sports_players_analysis.csv': clustered_players,
        'data/outputs/sports_team_stats.csv': team_stats,
        'data/outputs/sports_mvp_candidates.csv': mvp_candidates
    }

    print("\n" + "="*80)
    print("保存分析結果...")
    print("="*80)

    for filepath, df in output_files.items():
        try:
            df.to_csv(filepath, index=True)
            print(f"  ✓ {filepath}")
        except Exception as e:
            print(f"  ✗ {filepath}: {e}")

    try:
        with open('data/outputs/sports_analytics_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  ✓ data/outputs/sports_analytics_report.txt")
    except Exception as e:
        print(f"  ✗ data/outputs/sports_analytics_report.txt: {e}")

    print("\n" + "="*80)
    print("分析完成！")
    print("="*80)

    return analyzer, clustered_players, team_stats, mvp_candidates


if __name__ == "__main__":
    analyzer, players, team_stats, mvp_candidates = main()
