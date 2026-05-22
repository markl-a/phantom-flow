"""
電商推薦系統範例

這個範例展示如何構建完整的電商推薦系統，包含:
1. 用戶行為聚類分析 - 識別購物模式
2. 商品親和度分析 - 基於關聯規則挖掘
3. 協同過濾推薦 - 基於用戶和商品相似度
4. 客戶分群推薦 - 針對不同客群的個性化推薦

真實應用場景:
- 電商平台個性化商品推薦
- 購物車關聯商品推薦
- 用戶分群精準營銷
- 商品組合優化
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# 導入專案模組
try:
    from data_analysis_chatbots.clustering import ClustererFactory, KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from data_analysis_chatbots.clustering import ClustererFactory, KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator


def generate_ecommerce_data(n_users: int = 500,
                            n_products: int = 100,
                            n_interactions: int = 5000) -> pd.DataFrame:
    """
    生成真實的電商用戶行為數據

    模擬用戶在電商平台的各種行為:
    - 瀏覽商品 (browsing_time)
    - 加入購物車 (add_to_cart)
    - 購買商品 (purchase_count, purchase_amount)
    - 商品評分 (rating)
    - 退貨行為 (return_rate)

    Args:
        n_users: 用戶數量
        n_products: 商品數量
        n_interactions: 互動記錄數量

    Returns:
        包含用戶行為數據的DataFrame
    """
    np.random.seed(42)

    # ========================================
    # 商品類別定義
    # ========================================
    categories = [
        '電子產品', '服飾配件', '家居用品', '美妝保養',
        '食品飲料', '運動戶外', '書籍文具', '母嬰用品'
    ]

    # 不同類別的平均價格
    category_prices = {
        '電子產品': 3000, '服飾配件': 800, '家居用品': 500,
        '美妝保養': 600, '食品飲料': 200, '運動戶外': 1200,
        '書籍文具': 250, '母嬰用品': 400
    }

    # 商品資料
    products = pd.DataFrame({
        'product_id': [f'P{i:04d}' for i in range(1, n_products + 1)],
        'category': np.random.choice(categories, n_products),
    })
    products['base_price'] = products['category'].map(category_prices)

    # ========================================
    # 生成用戶行為數據
    # ========================================
    interactions = []

    # 定義用戶類型，影響其行為模式
    user_types = ['impulse_buyer', 'researcher', 'bargain_hunter', 'loyal_customer', 'browser']
    user_type_probs = [0.15, 0.25, 0.20, 0.25, 0.15]

    for _ in range(n_interactions):
        user_id = f'U{np.random.randint(1, n_users + 1):05d}'
        product = products.sample(1).iloc[0]
        product_id = product['product_id']
        category = product['category']
        base_price = product['base_price']

        # 隨機分配用戶類型
        user_type = np.random.choice(user_types, p=user_type_probs)

        # 根據用戶類型設定行為參數
        if user_type == 'impulse_buyer':
            # 衝動型買家: 短時間瀏覽，高購買率，高退貨率
            browsing_time = np.random.uniform(1, 5)
            purchase_prob = 0.6
            add_to_cart_prob = 0.7
            return_rate = 0.25
            rating_bias = 0
        elif user_type == 'researcher':
            # 研究型買家: 長時間瀏覽，中等購買率，低退貨率
            browsing_time = np.random.uniform(10, 30)
            purchase_prob = 0.4
            add_to_cart_prob = 0.5
            return_rate = 0.05
            rating_bias = 0.5
        elif user_type == 'bargain_hunter':
            # 撿便宜型: 中等瀏覽時間，價格敏感，中等退貨率
            browsing_time = np.random.uniform(5, 15)
            purchase_prob = 0.3
            add_to_cart_prob = 0.6
            return_rate = 0.15
            rating_bias = -0.3
        elif user_type == 'loyal_customer':
            # 忠誠客戶: 快速決策，高購買率，低退貨率
            browsing_time = np.random.uniform(3, 10)
            purchase_prob = 0.7
            add_to_cart_prob = 0.8
            return_rate = 0.03
            rating_bias = 0.8
        else:  # browser
            # 純瀏覽型: 長時間瀏覽，低購買率
            browsing_time = np.random.uniform(2, 20)
            purchase_prob = 0.1
            add_to_cart_prob = 0.2
            return_rate = 0.1
            rating_bias = 0

        # 生成具體行為數據
        add_to_cart = 1 if np.random.random() < add_to_cart_prob else 0
        purchase_count = 0
        purchase_amount = 0
        rating = 0

        if add_to_cart and np.random.random() < purchase_prob:
            purchase_count = np.random.randint(1, 4)
            # 價格變動 (促銷、會員折扣等)
            price_variation = np.random.uniform(0.7, 1.2)
            purchase_amount = base_price * price_variation * purchase_count
            # 生成評分 (1-5分)
            rating = np.clip(np.random.normal(4 + rating_bias, 0.8), 1, 5)

        interactions.append({
            'user_id': user_id,
            'product_id': product_id,
            'category': category,
            'browsing_time': round(browsing_time, 2),
            'add_to_cart': add_to_cart,
            'purchase_count': purchase_count,
            'purchase_amount': round(purchase_amount, 2),
            'rating': round(rating, 1) if rating > 0 else 0,
            'return_rate': return_rate if purchase_count > 0 else 0,
            'user_type': user_type,
            'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 90))
        })

    df = pd.DataFrame(interactions)
    return df


class UserBehaviorAnalyzer:
    """
    用戶行為分析器

    基於用戶的瀏覽、購買、評分等行為進行聚類分析，
    識別不同的用戶購物模式
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.user_features = None
        self.clusterer = None

    def create_user_features(self) -> pd.DataFrame:
        """
        創建用戶特徵向量

        聚合每個用戶的行為特徵:
        - 平均瀏覽時間
        - 購買頻率
        - 平均購買金額
        - 加購率
        - 平均評分
        - 退貨率
        """
        user_agg = self.df.groupby('user_id').agg({
            'browsing_time': 'mean',
            'purchase_count': 'sum',
            'purchase_amount': ['sum', 'mean'],
            'add_to_cart': 'mean',
            'rating': lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0,
            'return_rate': 'mean',
            'product_id': 'count'  # 互動次數
        }).round(2)

        user_agg.columns = [
            'avg_browsing_time', 'total_purchases', 'total_spent',
            'avg_purchase_amount', 'add_to_cart_rate', 'avg_rating',
            'avg_return_rate', 'interaction_count'
        ]

        # 計算衍生特徵
        user_agg['purchase_rate'] = (
            user_agg['total_purchases'] / user_agg['interaction_count']
        ).round(3)

        user_agg['conversion_rate'] = (
            (user_agg['total_purchases'] > 0).astype(int)
        )

        self.user_features = user_agg.fillna(0)
        return self.user_features

    def cluster_users(self, n_clusters: int = 5) -> pd.DataFrame:
        """
        對用戶進行聚類分析

        Args:
            n_clusters: 聚類數量

        Returns:
            包含聚類標籤的用戶特徵DataFrame
        """
        if self.user_features is None:
            self.create_user_features()

        # 選擇用於聚類的特徵
        cluster_features = [
            'avg_browsing_time', 'purchase_rate', 'avg_purchase_amount',
            'add_to_cart_rate', 'avg_rating', 'avg_return_rate'
        ]

        # 使用KMeans聚類
        self.clusterer = KMeansClusterer(n_clusters=n_clusters, random_state=42)
        labels = self.clusterer.fit_predict(self.user_features, cluster_features)

        self.user_features['cluster'] = labels

        return self.user_features

    def describe_clusters(self) -> pd.DataFrame:
        """
        描述各個用戶群組的特徵

        Returns:
            各群組的統計摘要
        """
        if 'cluster' not in self.user_features.columns:
            raise ValueError("請先執行 cluster_users() 方法")

        cluster_summary = self.user_features.groupby('cluster').agg({
            'avg_browsing_time': 'mean',
            'purchase_rate': 'mean',
            'avg_purchase_amount': 'mean',
            'add_to_cart_rate': 'mean',
            'avg_rating': 'mean',
            'avg_return_rate': 'mean',
            'total_spent': 'sum',
        }).round(2)

        cluster_summary['user_count'] = self.user_features.groupby('cluster').size()

        return cluster_summary


class ProductAffinityAnalyzer:
    """
    商品親和度分析器

    使用關聯規則挖掘(Association Rule Mining)分析商品之間的購買關聯，
    實現 "購買了A的用戶也購買了B" 的推薦邏輯
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df[df['purchase_count'] > 0].copy()  # 只分析實際購買記錄
        self.affinity_rules = None

    def calculate_affinity(self, min_support: float = 0.01) -> pd.DataFrame:
        """
        計算商品間的親和度

        使用簡化的Apriori算法概念:
        - Support: 兩件商品同時購買的頻率
        - Confidence: 購買A後購買B的條件機率
        - Lift: 關聯強度 (>1表示正相關)

        Args:
            min_support: 最小支持度閾值

        Returns:
            商品關聯規則DataFrame
        """
        # 創建用戶-商品購買矩陣
        user_products = self.df.groupby('user_id')['product_id'].apply(set).to_dict()

        # 統計單個商品的支持度
        product_counts = defaultdict(int)
        total_users = len(user_products)

        for products in user_products.values():
            for product in products:
                product_counts[product] += 1

        # 計算商品對的共現頻率
        rules = []
        products = list(product_counts.keys())

        for i, product_a in enumerate(products):
            for product_b in products[i+1:]:
                # 計算同時購買兩件商品的用戶數
                co_occurrence = sum(
                    1 for user_products_set in user_products.values()
                    if product_a in user_products_set and product_b in user_products_set
                )

                if co_occurrence == 0:
                    continue

                # Support: P(A ∩ B)
                support = co_occurrence / total_users

                if support < min_support:
                    continue

                # Confidence: P(B|A) = P(A ∩ B) / P(A)
                confidence_a_to_b = co_occurrence / product_counts[product_a]
                confidence_b_to_a = co_occurrence / product_counts[product_b]

                # Lift: P(A ∩ B) / (P(A) * P(B))
                expected = (product_counts[product_a] / total_users) * \
                          (product_counts[product_b] / total_users)
                lift = support / expected if expected > 0 else 0

                rules.append({
                    'product_a': product_a,
                    'product_b': product_b,
                    'support': round(support, 4),
                    'confidence_a_to_b': round(confidence_a_to_b, 4),
                    'confidence_b_to_a': round(confidence_b_to_a, 4),
                    'lift': round(lift, 2),
                    'co_purchases': co_occurrence
                })

        self.affinity_rules = pd.DataFrame(rules)

        # 按lift排序，找出最強的關聯規則
        if not self.affinity_rules.empty:
            self.affinity_rules = self.affinity_rules.sort_values('lift', ascending=False)

        return self.affinity_rules

    def get_recommendations(self, product_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        為指定商品獲取關聯推薦

        Args:
            product_id: 商品ID
            top_n: 返回top N推薦

        Returns:
            推薦商品列表 [(product_id, score), ...]
        """
        if self.affinity_rules is None or self.affinity_rules.empty:
            return []

        # 找出與該商品相關的規則
        related = self.affinity_rules[
            (self.affinity_rules['product_a'] == product_id) |
            (self.affinity_rules['product_b'] == product_id)
        ].copy()

        if related.empty:
            return []

        # 整理推薦商品及其分數 (使用lift作為推薦分數)
        recommendations = []
        for _, row in related.iterrows():
            if row['product_a'] == product_id:
                recommendations.append((row['product_b'], row['lift']))
            else:
                recommendations.append((row['product_a'], row['lift']))

        # 去重並排序
        recommendations = sorted(
            list(set(recommendations)),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return recommendations


class CollaborativeFilteringRecommender:
    """
    協同過濾推薦器

    實現兩種協同過濾方法:
    1. User-Based CF: 找到相似用戶，推薦他們喜歡的商品
    2. Item-Based CF: 找到相似商品，推薦給喜歡類似商品的用戶
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None

    def create_user_item_matrix(self) -> pd.DataFrame:
        """
        創建用戶-商品評分矩陣

        使用綜合評分 = (rating * 0.7) + (normalized_purchase_amount * 0.3)
        考慮用戶評分和購買金額兩個因素
        """
        # 過濾出有購買記錄的數據
        purchase_df = self.df[self.df['purchase_count'] > 0].copy()

        # 標準化購買金額到1-5分
        if not purchase_df.empty and purchase_df['purchase_amount'].max() > 0:
            purchase_df['normalized_amount'] = (
                (purchase_df['purchase_amount'] - purchase_df['purchase_amount'].min()) /
                (purchase_df['purchase_amount'].max() - purchase_df['purchase_amount'].min()) * 4 + 1
            )
        else:
            purchase_df['normalized_amount'] = 3

        # 綜合評分
        purchase_df['composite_score'] = (
            purchase_df['rating'] * 0.7 +
            purchase_df['normalized_amount'] * 0.3
        )

        # 如果有多次購買，取平均值
        matrix = purchase_df.groupby(['user_id', 'product_id'])['composite_score'].mean()
        self.user_item_matrix = matrix.unstack(fill_value=0)

        return self.user_item_matrix

    def calculate_user_similarity(self) -> pd.DataFrame:
        """
        計算用戶相似度

        使用餘弦相似度(Cosine Similarity)衡量用戶間的相似程度
        """
        if self.user_item_matrix is None:
            self.create_user_item_matrix()

        # 計算餘弦相似度
        from sklearn.metrics.pairwise import cosine_similarity

        similarity = cosine_similarity(self.user_item_matrix)
        self.user_similarity = pd.DataFrame(
            similarity,
            index=self.user_item_matrix.index,
            columns=self.user_item_matrix.index
        )

        return self.user_similarity

    def calculate_item_similarity(self) -> pd.DataFrame:
        """
        計算商品相似度

        基於用戶對商品的評分模式計算商品間相似度
        """
        if self.user_item_matrix is None:
            self.create_user_item_matrix()

        from sklearn.metrics.pairwise import cosine_similarity

        # 轉置矩陣，讓商品成為行
        similarity = cosine_similarity(self.user_item_matrix.T)
        self.item_similarity = pd.DataFrame(
            similarity,
            index=self.user_item_matrix.columns,
            columns=self.user_item_matrix.columns
        )

        return self.item_similarity

    def recommend_for_user(self, user_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        為用戶生成推薦 (User-Based CF)

        找到相似用戶喜歡但該用戶未購買的商品

        Args:
            user_id: 用戶ID
            top_n: 推薦數量

        Returns:
            推薦列表 [(product_id, predicted_score), ...]
        """
        if self.user_similarity is None:
            self.calculate_user_similarity()

        if user_id not in self.user_similarity.index:
            return []

        # 找到相似用戶 (排除自己)
        similar_users = self.user_similarity[user_id].sort_values(ascending=False)[1:11]

        # 該用戶已購買的商品
        user_purchased = set(
            self.user_item_matrix.loc[user_id][self.user_item_matrix.loc[user_id] > 0].index
        )

        # 計算推薦分數
        recommendations = {}
        for similar_user, similarity_score in similar_users.items():
            if similarity_score <= 0:
                continue

            # 獲取相似用戶喜歡的商品
            similar_user_items = self.user_item_matrix.loc[similar_user]
            similar_user_items = similar_user_items[similar_user_items > 0]

            for product_id, rating in similar_user_items.items():
                if product_id not in user_purchased:
                    if product_id not in recommendations:
                        recommendations[product_id] = 0
                    # 加權評分
                    recommendations[product_id] += rating * similarity_score

        # 排序並返回top N
        recommendations = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return recommendations

    def recommend_similar_items(self, product_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        推薦相似商品 (Item-Based CF)

        Args:
            product_id: 商品ID
            top_n: 推薦數量

        Returns:
            相似商品列表 [(product_id, similarity_score), ...]
        """
        if self.item_similarity is None:
            self.calculate_item_similarity()

        if product_id not in self.item_similarity.index:
            return []

        # 獲取相似商品 (排除自己)
        similar_items = self.item_similarity[product_id].sort_values(ascending=False)[1:top_n+1]

        return list(similar_items.items())


class SegmentBasedRecommender:
    """
    基於客戶分群的推薦系統

    結合用戶聚類結果，為不同群組提供個性化推薦策略
    """

    def __init__(self, df: pd.DataFrame, user_features: pd.DataFrame):
        self.df = df
        self.user_features = user_features

    def get_segment_preferences(self) -> Dict[int, pd.DataFrame]:
        """
        分析各個用戶群組的商品偏好

        Returns:
            各群組的商品偏好統計
        """
        # 合併用戶群組資訊
        df_with_cluster = self.df.merge(
            self.user_features[['cluster']],
            left_on='user_id',
            right_index=True,
            how='left'
        )

        segment_prefs = {}

        for cluster_id in df_with_cluster['cluster'].unique():
            if pd.isna(cluster_id):
                continue

            cluster_data = df_with_cluster[df_with_cluster['cluster'] == cluster_id]

            # 分析該群組的商品偏好
            category_pref = cluster_data.groupby('category').agg({
                'purchase_count': 'sum',
                'purchase_amount': 'sum',
                'rating': lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0,
                'product_id': 'count'
            }).round(2)

            category_pref.columns = ['total_purchases', 'total_revenue', 'avg_rating', 'interactions']
            category_pref['purchase_rate'] = (
                category_pref['total_purchases'] / category_pref['interactions']
            ).round(3)

            segment_prefs[int(cluster_id)] = category_pref.sort_values(
                'total_revenue', ascending=False
            )

        return segment_prefs

    def recommend_for_segment(self, cluster_id: int, top_n: int = 10) -> pd.DataFrame:
        """
        為特定用戶群組推薦商品

        Args:
            cluster_id: 群組ID
            top_n: 推薦數量

        Returns:
            推薦商品及其指標
        """
        # 獲取該群組用戶
        segment_users = self.user_features[
            self.user_features['cluster'] == cluster_id
        ].index

        # 該群組的購買記錄
        segment_data = self.df[
            (self.df['user_id'].isin(segment_users)) &
            (self.df['purchase_count'] > 0)
        ]

        # 統計商品表現
        product_stats = segment_data.groupby('product_id').agg({
            'purchase_count': 'sum',
            'purchase_amount': 'sum',
            'rating': lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0,
            'user_id': 'nunique'
        }).round(2)

        product_stats.columns = ['total_purchases', 'total_revenue', 'avg_rating', 'unique_buyers']

        # 計算推薦分數 (綜合考慮銷量、評分、購買人數)
        if not product_stats.empty:
            product_stats['recommendation_score'] = (
                (product_stats['total_purchases'] / product_stats['total_purchases'].max() * 0.4) +
                (product_stats['avg_rating'] / 5 * 0.3) +
                (product_stats['unique_buyers'] / product_stats['unique_buyers'].max() * 0.3)
            ).round(3)
        else:
            product_stats['recommendation_score'] = 0

        # 合併類別資訊
        product_category = self.df[['product_id', 'category']].drop_duplicates()
        product_stats = product_stats.merge(
            product_category,
            left_index=True,
            right_on='product_id',
            how='left'
        )

        return product_stats.nlargest(top_n, 'recommendation_score')


def main():
    """執行完整的電商推薦系統分析"""
    print("="*80)
    print(" "*25 + "電商推薦系統分析")
    print("="*80)

    # ========================================
    # 1. 生成數據
    # ========================================
    print("\n[1/6] 生成電商數據...")

    df = generate_ecommerce_data(
        n_users=500,
        n_products=100,
        n_interactions=5000
    )

    print(f"  ✓ 用戶數量: {df['user_id'].nunique():,}")
    print(f"  ✓ 商品數量: {df['product_id'].nunique():,}")
    print(f"  ✓ 互動記錄: {len(df):,}")
    print(f"  ✓ 購買記錄: {df[df['purchase_count'] > 0].shape[0]:,}")
    print(f"  ✓ 總交易額: ${df['purchase_amount'].sum():,.2f}")

    # 數據驗證
    validator = DataValidator(df)
    missing_check = validator.check_missing_values()
    duplicate_check = validator.check_duplicates()
    print(f"  ✓ 數據驗證: 缺失值={missing_check['total_missing_cells']}, 重複記錄={duplicate_check['duplicate_count']}")

    # ========================================
    # 2. 用戶行為聚類
    # ========================================
    print("\n[2/6] 用戶行為聚類分析...")

    behavior_analyzer = UserBehaviorAnalyzer(df)
    user_features = behavior_analyzer.create_user_features()
    user_features = behavior_analyzer.cluster_users(n_clusters=5)

    print(f"  ✓ 創建用戶特徵向量: {user_features.shape[0]} 用戶")
    print(f"  ✓ 識別 {user_features['cluster'].nunique()} 個用戶群組")

    cluster_summary = behavior_analyzer.describe_clusters()
    print("\n  用戶群組特徵:")
    print(f"{'群組':<8} {'用戶數':<8} {'購買率':<10} {'平均消費':<12} {'評分':<8}")
    print("-" * 55)
    for cluster_id, row in cluster_summary.iterrows():
        print(f"{cluster_id:<8} {int(row['user_count']):<8} "
              f"{row['purchase_rate']:<10.2%} ${row['avg_purchase_amount']:<11,.2f} "
              f"{row['avg_rating']:<8.2f}")

    # 為每個群組命名
    cluster_names = {}
    for cluster_id, row in cluster_summary.iterrows():
        if row['purchase_rate'] > 0.5 and row['avg_purchase_amount'] > cluster_summary['avg_purchase_amount'].median():
            cluster_names[cluster_id] = "高價值客戶"
        elif row['purchase_rate'] > 0.5:
            cluster_names[cluster_id] = "活躍買家"
        elif row['avg_browsing_time'] > cluster_summary.iloc[:, 0].median() and row['purchase_rate'] < 0.3:
            cluster_names[cluster_id] = "猶豫型用戶"
        elif row['avg_return_rate'] > cluster_summary['avg_return_rate'].median():
            cluster_names[cluster_id] = "高退貨用戶"
        else:
            cluster_names[cluster_id] = "一般用戶"

    print("\n  群組命名:")
    for cluster_id, name in cluster_names.items():
        print(f"    群組 {cluster_id}: {name}")

    # ========================================
    # 3. 商品親和度分析
    # ========================================
    print("\n[3/6] 商品親和度分析 (關聯規則挖掘)...")

    affinity_analyzer = ProductAffinityAnalyzer(df)
    affinity_rules = affinity_analyzer.calculate_affinity(min_support=0.01)

    if not affinity_rules.empty:
        print(f"  ✓ 發現 {len(affinity_rules)} 條關聯規則")
        print(f"\n  最強關聯規則 (Top 5):")
        print(f"{'商品A':<10} {'商品B':<10} {'Lift':<8} {'置信度':<10} {'共同購買':<10}")
        print("-" * 60)
        for _, rule in affinity_rules.head(5).iterrows():
            print(f"{rule['product_a']:<10} {rule['product_b']:<10} "
                  f"{rule['lift']:<8.2f} {rule['confidence_a_to_b']:<10.2%} "
                  f"{rule['co_purchases']:<10}")

        # 測試推薦
        test_product = affinity_rules.iloc[0]['product_a']
        recommendations = affinity_analyzer.get_recommendations(test_product, top_n=5)
        if recommendations:
            print(f"\n  示例: 購買 {test_product} 的用戶也購買了:")
            for prod_id, score in recommendations:
                print(f"    - {prod_id} (關聯分數: {score:.2f})")
    else:
        print("  ⚠️  未發現顯著的商品關聯規則 (可能需要更多數據)")

    # ========================================
    # 4. 協同過濾推薦
    # ========================================
    print("\n[4/6] 協同過濾推薦...")

    cf_recommender = CollaborativeFilteringRecommender(df)
    user_item_matrix = cf_recommender.create_user_item_matrix()

    print(f"  ✓ 用戶-商品矩陣: {user_item_matrix.shape[0]} 用戶 × {user_item_matrix.shape[1]} 商品")

    # 計算相似度
    user_similarity = cf_recommender.calculate_user_similarity()
    item_similarity = cf_recommender.calculate_item_similarity()

    print(f"  ✓ 計算用戶相似度矩陣")
    print(f"  ✓ 計算商品相似度矩陣")

    # User-Based CF 示例
    test_user = user_item_matrix.index[0]
    user_recommendations = cf_recommender.recommend_for_user(test_user, top_n=5)

    if user_recommendations:
        print(f"\n  User-Based CF 示例 (用戶 {test_user}):")
        print("  推薦商品:")
        for prod_id, score in user_recommendations:
            print(f"    - {prod_id} (預測評分: {score:.2f})")

    # Item-Based CF 示例
    if not user_item_matrix.empty:
        test_item = user_item_matrix.columns[0]
        item_recommendations = cf_recommender.recommend_similar_items(test_item, top_n=5)

        if item_recommendations:
            print(f"\n  Item-Based CF 示例 (商品 {test_item}):")
            print("  相似商品:")
            for prod_id, similarity in item_recommendations:
                print(f"    - {prod_id} (相似度: {similarity:.3f})")

    # ========================================
    # 5. 基於客戶分群的推薦
    # ========================================
    print("\n[5/6] 客戶分群推薦策略...")

    segment_recommender = SegmentBasedRecommender(df, user_features)
    segment_preferences = segment_recommender.get_segment_preferences()

    print("\n  各群組偏好類別:")
    for cluster_id, prefs in segment_preferences.items():
        cluster_name = cluster_names.get(cluster_id, f"群組{cluster_id}")
        print(f"\n  {cluster_name} (群組 {cluster_id}):")
        if not prefs.empty:
            top_category = prefs.head(3)
            for category, row in top_category.iterrows():
                print(f"    - {category}: ${row['total_revenue']:,.2f} "
                      f"(購買率: {row['purchase_rate']:.1%}, 評分: {row['avg_rating']:.1f})")

    # 為每個群組生成推薦
    print("\n  各群組推薦商品 (Top 3):")
    for cluster_id in user_features['cluster'].unique():
        cluster_name = cluster_names.get(cluster_id, f"群組{cluster_id}")
        recommendations = segment_recommender.recommend_for_segment(int(cluster_id), top_n=3)

        if not recommendations.empty:
            print(f"\n  {cluster_name}:")
            for _, rec in recommendations.iterrows():
                print(f"    - {rec['product_id']} ({rec['category']}): "
                      f"分數 {rec['recommendation_score']:.3f}, "
                      f"評分 {rec['avg_rating']:.1f}")

    # ========================================
    # 6. 綜合推薦策略
    # ========================================
    print("\n[6/6] 綜合推薦策略建議...")

    print("\n  推薦系統實施建議:")
    print("  " + "="*60)
    print("""
  1. 首頁推薦:
     - 使用協同過濾為登入用戶推薦個性化商品
     - 未登入用戶顯示熱門商品和新品

  2. 商品詳情頁:
     - 使用商品親和度分析推薦 "購買了A的用戶也購買了B"
     - 使用Item-Based CF推薦相似商品

  3. 購物車頁面:
     - 基於關聯規則推薦搭配商品
     - 顯示優惠組合提升客單價

  4. 郵件營銷:
     - 根據客戶分群發送不同的商品推薦
     - 高價值客戶推送新品和高端商品
     - 猶豫型用戶發送促銷優惠

  5. App推送:
     - 根據用戶瀏覽歷史推送相關商品
     - 結合用戶群組特徵推送個性化內容
    """)

    # ========================================
    # 性能統計
    # ========================================
    print("\n" + "="*80)
    print(" "*28 + "分析摘要")
    print("="*80)

    total_users = df['user_id'].nunique()
    total_purchases = df[df['purchase_count'] > 0].shape[0]
    total_revenue = df['purchase_amount'].sum()
    avg_rating = df[df['rating'] > 0]['rating'].mean()

    print(f"""
  📊 數據規模:
     - 用戶數: {total_users:,}
     - 商品數: {df['product_id'].nunique():,}
     - 購買記錄: {total_purchases:,}
     - 總營收: ${total_revenue:,.2f}

  🎯 推薦能力:
     - 用戶群組: {user_features['cluster'].nunique()} 個
     - 關聯規則: {len(affinity_rules) if not affinity_rules.empty else 0} 條
     - 協同過濾覆蓋: {user_item_matrix.shape[0]} 用戶
     - 平均評分: {avg_rating:.2f}/5.0

  💡 業務洞察:
     - 購買轉化率: {(total_purchases / len(df)):.1%}
     - 加購率: {df['add_to_cart'].mean():.1%}
     - 平均退貨率: {df[df['purchase_count'] > 0]['return_rate'].mean():.1%}
    """)

    # 保存結果
    try:
        user_features.to_csv('data/outputs/user_segments.csv')
        if not affinity_rules.empty:
            affinity_rules.to_csv('data/outputs/product_affinity_rules.csv', index=False)
        print("  📁 分析結果已保存至 data/outputs/")
    except Exception as e:
        print(f"  ⚠️  保存結果時發生錯誤: {e}")

    return {
        'df': df,
        'user_features': user_features,
        'affinity_rules': affinity_rules,
        'cf_recommender': cf_recommender,
        'segment_recommender': segment_recommender
    }


if __name__ == "__main__":
    results = main()
