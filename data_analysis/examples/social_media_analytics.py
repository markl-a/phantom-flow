"""
社交媒體分析範例

這個範例展示如何分析社交媒體數據，包含：
- 互動率分析
- 情感分析
- 內容表現評估
- 受眾分析
- 最佳發布時間分析

真實應用場景:
- 社交媒體行銷優化
- 品牌聲譽監控
- 內容策略制定
- 競品分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter
import re
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class SocialMediaAnalyzer:
    """
    社交媒體分析器

    提供完整的社交媒體數據分析功能:
    - 互動指標計算
    - 內容表現分析
    - 情感分析
    - 受眾行為分析
    - 發布時間優化
    """

    def __init__(self, posts_df: pd.DataFrame,
                 comments_df: Optional[pd.DataFrame] = None,
                 followers_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            posts_df: 貼文數據DataFrame
            comments_df: 留言數據DataFrame (可選)
            followers_df: 粉絲數據DataFrame (可選)
        """
        self.posts = posts_df.copy()
        self.comments = comments_df
        self.followers = followers_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'post_date' in self.posts.columns:
            self.posts['post_date'] = pd.to_datetime(self.posts['post_date'])
            self.posts['day_of_week'] = self.posts['post_date'].dt.dayofweek
            self.posts['hour'] = self.posts['post_date'].dt.hour
            self.posts['month'] = self.posts['post_date'].dt.month

    def calculate_engagement_metrics(self) -> pd.DataFrame:
        """計算互動指標"""
        df = self.posts.copy()

        # 總互動數
        interaction_cols = ['likes', 'comments', 'shares', 'saves']
        existing_cols = [col for col in interaction_cols if col in df.columns]
        df['total_engagement'] = df[existing_cols].sum(axis=1)

        # 互動率 (以觸及率計算)
        if 'reach' in df.columns:
            df['engagement_rate'] = (df['total_engagement'] / df['reach'] * 100).round(2)
        elif 'impressions' in df.columns:
            df['engagement_rate'] = (df['total_engagement'] / df['impressions'] * 100).round(2)
        else:
            # 假設平均觸及
            df['engagement_rate'] = (df['total_engagement'] / 1000 * 100).round(2)

        # 各項互動佔比
        for col in existing_cols:
            df[f'{col}_rate'] = (df[col] / df['total_engagement'] * 100).round(1)

        # 病毒式傳播係數 (分享/按讚)
        if 'shares' in df.columns and 'likes' in df.columns:
            df['virality_score'] = (df['shares'] / df['likes'].replace(0, 1) * 100).round(1)

        return df

    def analyze_content_performance(self) -> Dict[str, pd.DataFrame]:
        """分析內容表現"""
        results = {}
        df = self.calculate_engagement_metrics()

        # 按內容類型分析
        if 'content_type' in df.columns:
            content_perf = df.groupby('content_type').agg({
                'total_engagement': ['mean', 'sum'],
                'engagement_rate': 'mean',
                'post_id': 'count',
                'likes': 'mean',
                'comments': 'mean' if 'comments' in df.columns else 'count',
                'shares': 'mean' if 'shares' in df.columns else 'count'
            }).round(2)
            content_perf.columns = ['avg_engagement', 'total_engagement', 'avg_eng_rate',
                                    'post_count', 'avg_likes', 'avg_comments', 'avg_shares']
            results['by_content_type'] = content_perf.sort_values('avg_engagement', ascending=False)

        # 按主題/標籤分析
        if 'hashtags' in df.columns:
            # 展開標籤
            hashtag_perf = []
            for _, row in df.iterrows():
                tags = row['hashtags'] if isinstance(row['hashtags'], list) else []
                for tag in tags:
                    hashtag_perf.append({
                        'hashtag': tag,
                        'engagement': row['total_engagement'],
                        'engagement_rate': row['engagement_rate']
                    })

            if hashtag_perf:
                hashtag_df = pd.DataFrame(hashtag_perf)
                hashtag_summary = hashtag_df.groupby('hashtag').agg({
                    'engagement': ['mean', 'sum', 'count'],
                    'engagement_rate': 'mean'
                }).round(2)
                hashtag_summary.columns = ['avg_engagement', 'total_engagement',
                                           'usage_count', 'avg_eng_rate']
                results['by_hashtag'] = hashtag_summary.sort_values(
                    'avg_engagement', ascending=False
                ).head(20)

        # 識別最佳表現貼文
        top_posts = df.nlargest(10, 'total_engagement')[
            ['post_id', 'content_type', 'post_date', 'total_engagement',
             'engagement_rate', 'likes', 'comments']
        ]
        results['top_posts'] = top_posts

        # 識別最差表現貼文
        bottom_posts = df.nsmallest(10, 'total_engagement')[
            ['post_id', 'content_type', 'post_date', 'total_engagement',
             'engagement_rate', 'likes', 'comments']
        ]
        results['bottom_posts'] = bottom_posts

        return results

    def analyze_sentiment(self) -> Dict[str, any]:
        """
        簡單情感分析

        注意：實際應用中應使用更專業的NLP模型
        此處僅作為示範
        """
        if self.comments is None:
            return {}

        # 簡單的情感詞典 (示範用)
        positive_words = {
            'love', 'great', 'amazing', 'awesome', 'excellent', 'fantastic',
            'wonderful', 'perfect', 'best', 'beautiful', 'good', 'nice',
            '讚', '喜歡', '太棒了', '很好', '超讚', '推推', '優秀'
        }
        negative_words = {
            'hate', 'bad', 'terrible', 'awful', 'horrible', 'worst',
            'poor', 'disappointing', 'fail', 'sucks', 'ugly',
            '爛', '差', '糟糕', '失望', '難用', '不推'
        }

        df = self.comments.copy()

        def analyze_text(text):
            if pd.isna(text):
                return 'neutral'
            text_lower = str(text).lower()
            words = set(re.findall(r'\w+', text_lower))

            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)

            if pos_count > neg_count:
                return 'positive'
            elif neg_count > pos_count:
                return 'negative'
            else:
                return 'neutral'

        df['sentiment'] = df['comment_text'].apply(analyze_text)

        results = {
            'sentiment_distribution': df['sentiment'].value_counts().to_dict(),
            'sentiment_percentages': (df['sentiment'].value_counts(normalize=True) * 100).round(1).to_dict(),
            'total_comments': len(df)
        }

        # 按貼文分析情感
        if 'post_id' in df.columns:
            post_sentiment = df.groupby('post_id')['sentiment'].value_counts().unstack(fill_value=0)
            post_sentiment['sentiment_score'] = (
                (post_sentiment.get('positive', 0) - post_sentiment.get('negative', 0)) /
                (post_sentiment.sum(axis=1).replace(0, 1))
            ).round(2)
            results['by_post'] = post_sentiment

        return results

    def find_best_posting_times(self) -> Dict[str, any]:
        """找出最佳發布時間"""
        df = self.calculate_engagement_metrics()
        results = {}

        # 按星期幾分析
        day_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        day_perf = df.groupby('day_of_week').agg({
            'total_engagement': 'mean',
            'engagement_rate': 'mean',
            'post_id': 'count'
        }).round(2)
        day_perf.index = [day_names[i] for i in day_perf.index]
        day_perf.columns = ['avg_engagement', 'avg_eng_rate', 'post_count']
        results['by_day_of_week'] = day_perf

        # 找出最佳發布日
        best_day = day_perf['avg_engagement'].idxmax()
        results['best_day'] = best_day

        # 按小時分析
        hour_perf = df.groupby('hour').agg({
            'total_engagement': 'mean',
            'engagement_rate': 'mean',
            'post_id': 'count'
        }).round(2)
        hour_perf.columns = ['avg_engagement', 'avg_eng_rate', 'post_count']
        results['by_hour'] = hour_perf

        # 找出最佳發布時段
        best_hours = hour_perf.nlargest(3, 'avg_engagement').index.tolist()
        results['best_hours'] = best_hours

        # 組合分析 (日 + 時)
        combined = df.groupby(['day_of_week', 'hour'])['total_engagement'].mean().round(0)
        best_combo = combined.idxmax()
        results['best_combination'] = {
            'day': day_names[best_combo[0]],
            'hour': best_combo[1],
            'avg_engagement': combined[best_combo]
        }

        return results

    def analyze_audience(self) -> Dict[str, any]:
        """分析受眾"""
        if self.followers is None:
            return {}

        df = self.followers
        results = {}

        # 地理分佈
        if 'location' in df.columns:
            location_dist = df['location'].value_counts().head(10)
            results['top_locations'] = location_dist.to_dict()

        # 年齡分佈
        if 'age_range' in df.columns:
            age_dist = df['age_range'].value_counts()
            results['age_distribution'] = age_dist.to_dict()

        # 性別分佈
        if 'gender' in df.columns:
            gender_dist = df['gender'].value_counts(normalize=True) * 100
            results['gender_distribution'] = gender_dist.round(1).to_dict()

        # 活躍度分佈
        if 'activity_score' in df.columns:
            activity_brackets = pd.cut(
                df['activity_score'],
                bins=[0, 25, 50, 75, 100],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            results['activity_distribution'] = activity_brackets.value_counts().to_dict()

        # 粉絲增長趨勢
        if 'follow_date' in df.columns:
            df['follow_date'] = pd.to_datetime(df['follow_date'])
            monthly_growth = df.groupby(df['follow_date'].dt.to_period('M')).size()
            results['monthly_growth'] = monthly_growth.to_dict()

        return results

    def generate_content_recommendations(self) -> List[Dict]:
        """生成內容建議"""
        content_perf = self.analyze_content_performance()
        timing = self.find_best_posting_times()
        sentiment = self.analyze_sentiment()

        recommendations = []

        # 基於內容類型的建議
        if 'by_content_type' in content_perf:
            top_type = content_perf['by_content_type']['avg_engagement'].idxmax()
            recommendations.append({
                'category': 'Content Type',
                'recommendation': f"增加 {top_type} 類型的內容",
                'reason': f"{top_type} 平均互動最高",
                'priority': 'HIGH'
            })

        # 基於發布時間的建議
        if 'best_combination' in timing:
            best = timing['best_combination']
            recommendations.append({
                'category': 'Posting Time',
                'recommendation': f"優先在 {best['day']} {best['hour']}:00 發布",
                'reason': "這個時段平均互動率最高",
                'priority': 'HIGH'
            })

        # 基於情感的建議
        if sentiment and sentiment.get('sentiment_percentages', {}).get('negative', 0) > 20:
            recommendations.append({
                'category': 'Sentiment',
                'recommendation': "關注負面評論並積極回應",
                'reason': f"負面評論佔比 {sentiment['sentiment_percentages']['negative']:.1f}%",
                'priority': 'MEDIUM'
            })

        # 基於標籤的建議
        if 'by_hashtag' in content_perf:
            top_tags = content_perf['by_hashtag'].head(3).index.tolist()
            if top_tags:
                recommendations.append({
                    'category': 'Hashtags',
                    'recommendation': f"多使用這些標籤: {', '.join(top_tags)}",
                    'reason': "這些標籤帶來最高互動",
                    'priority': 'MEDIUM'
                })

        return recommendations

    def generate_report(self) -> str:
        """生成完整的社交媒體分析報告"""
        metrics = self.calculate_engagement_metrics()
        content = self.analyze_content_performance()
        timing = self.find_best_posting_times()
        sentiment = self.analyze_sentiment()
        recommendations = self.generate_content_recommendations()

        report = f"""
{'='*80}
                    社交媒體分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、帳號概覽
{'='*40}
  分析期間: {self.posts['post_date'].min().strftime('%Y-%m-%d')} ~ {self.posts['post_date'].max().strftime('%Y-%m-%d')}
  貼文總數: {len(self.posts):,}
  總互動數: {metrics['total_engagement'].sum():,}
  平均互動率: {metrics['engagement_rate'].mean():.2f}%

二、互動指標
{'='*40}
  平均每則貼文:
    讚: {metrics['likes'].mean():.0f}
    留言: {metrics['comments'].mean():.0f}
    分享: {metrics.get('shares', pd.Series([0])).mean():.0f}
    收藏: {metrics.get('saves', pd.Series([0])).mean():.0f}

  互動率分佈:
    最高: {metrics['engagement_rate'].max():.2f}%
    最低: {metrics['engagement_rate'].min():.2f}%
    平均: {metrics['engagement_rate'].mean():.2f}%

三、內容表現
{'='*40}
"""
        if 'by_content_type' in content:
            report += "  按內容類型:\n"
            for ctype, row in content['by_content_type'].iterrows():
                report += f"    {ctype}: 平均 {row['avg_engagement']:.0f} 互動, "
                report += f"互動率 {row['avg_eng_rate']:.2f}%\n"

        report += f"""
  Top 5 貼文:
"""
        for _, post in content['top_posts'].head(5).iterrows():
            report += f"    - [{post['content_type']}] {post['total_engagement']:.0f} 互動 "
            report += f"({post['post_date'].strftime('%m/%d')})\n"

        # 最佳發布時間
        report += f"""
四、最佳發布時間
{'='*40}
  最佳發布日: {timing['best_day']}
  最佳發布時段: {', '.join(f"{h}:00" for h in timing['best_hours'])}

  每日表現:
"""
        for day, row in timing['by_day_of_week'].iterrows():
            bar = '█' * int(row['avg_engagement'] / timing['by_day_of_week']['avg_engagement'].max() * 20)
            report += f"    {day}: {row['avg_engagement']:.0f} {bar}\n"

        # 情感分析
        if sentiment:
            report += f"""
五、情感分析
{'='*40}
  分析留言數: {sentiment['total_comments']:,}

  情感分佈:
    😊 正面: {sentiment['sentiment_percentages'].get('positive', 0):.1f}%
    😐 中性: {sentiment['sentiment_percentages'].get('neutral', 0):.1f}%
    😞 負面: {sentiment['sentiment_percentages'].get('negative', 0):.1f}%
"""

        # 建議
        report += f"""
六、內容策略建議
{'='*40}
"""
        for i, rec in enumerate(recommendations, 1):
            priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
            icon = priority_icon.get(rec['priority'], '⚪')
            report += f"""
  {i}. {icon} [{rec['category']}] {rec['recommendation']}
     理由: {rec['reason']}
"""

        report += f"""
七、行動計劃
{'='*40}

1. 內容規劃:
   - 增加表現最佳的內容類型
   - 測試新的內容格式
   - 使用高互動標籤

2. 發布優化:
   - 在最佳時段發布重要內容
   - 保持穩定的發布頻率
   - 避免在低互動時段發布

3. 互動管理:
   - 及時回應留言，特別是前30分鐘
   - 關注負面評論並積極處理
   - 鼓勵用戶生成內容

4. 數據追蹤:
   - 每週檢視互動指標
   - 持續優化內容策略
   - A/B測試不同內容形式

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_social_media_data(n_posts: int = 300,
                               n_comments: int = 5000,
                               n_followers: int = 10000,
                               seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """生成模擬社交媒體數據"""
    np.random.seed(seed)
    today = datetime.now()

    # ========================================
    # 貼文數據
    # ========================================
    content_types = ['Image', 'Video', 'Carousel', 'Reel', 'Story', 'Text']
    content_weights = [0.30, 0.20, 0.20, 0.15, 0.10, 0.05]

    # 不同內容類型的基礎互動率
    type_engagement = {
        'Image': 1.0, 'Video': 1.5, 'Carousel': 1.3,
        'Reel': 2.0, 'Story': 0.8, 'Text': 0.5
    }

    hashtag_pool = [
        '#marketing', '#socialmedia', '#business', '#startup', '#entrepreneur',
        '#motivation', '#success', '#tips', '#growth', '#digital',
        '#content', '#strategy', '#branding', '#creative', '#innovation',
        '#數位行銷', '#社群經營', '#品牌經營', '#創業', '#商業洞察'
    ]

    posts = []
    for i in range(1, n_posts + 1):
        # 隨機發布時間 (過去180天)
        days_ago = np.random.randint(0, 180)
        post_date = today - timedelta(days=days_ago)

        # 根據時段調整 (早上和晚上發布較多)
        hour = np.random.choice(
            range(24),
            p=[0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05, 0.06, 0.05,
               0.04, 0.04, 0.05, 0.04, 0.04, 0.05, 0.05, 0.06, 0.07, 0.08,
               0.07, 0.05, 0.03, 0.02]
        )
        post_date = post_date.replace(hour=hour, minute=np.random.randint(0, 60))

        content_type = np.random.choice(content_types, p=content_weights)
        base_eng = type_engagement[content_type]

        # 基礎互動數 (對數正態分佈)
        base_likes = np.random.lognormal(6, 1) * base_eng

        # 週末效應
        if post_date.weekday() >= 5:
            base_likes *= 1.2

        # 時段效應 (晚上較高)
        if 19 <= hour <= 22:
            base_likes *= 1.3

        likes = int(np.clip(base_likes, 10, 50000))
        comments = int(likes * np.random.uniform(0.02, 0.08))
        shares = int(likes * np.random.uniform(0.01, 0.05))
        saves = int(likes * np.random.uniform(0.03, 0.1))

        # 曝光和觸及
        reach = int(likes * np.random.uniform(10, 30))
        impressions = int(reach * np.random.uniform(1.2, 2.0))

        # 隨機選擇標籤
        n_tags = np.random.randint(3, 10)
        hashtags = list(np.random.choice(hashtag_pool, n_tags, replace=False))

        posts.append({
            'post_id': f'POST{i:05d}',
            'post_date': post_date,
            'content_type': content_type,
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'saves': saves,
            'reach': reach,
            'impressions': impressions,
            'hashtags': hashtags,
            'caption_length': np.random.randint(50, 500)
        })

    posts_df = pd.DataFrame(posts)

    # ========================================
    # 留言數據
    # ========================================
    positive_templates = [
        "Love this!", "Amazing content!", "So helpful!", "Great post!",
        "This is exactly what I needed", "Awesome!", "Keep it up!",
        "太棒了！", "很喜歡！", "很有幫助！", "讚！", "推推"
    ]
    negative_templates = [
        "Not useful", "Disappointed", "Could be better",
        "失望", "不太好", "還好而已"
    ]
    neutral_templates = [
        "Interesting", "Thanks for sharing", "Noted",
        "謝謝分享", "了解", "好的"
    ]

    comments = []
    for i in range(1, n_comments + 1):
        post = posts_df.sample(1).iloc[0]

        # 根據貼文互動決定情感傾向
        if post['likes'] > posts_df['likes'].quantile(0.75):
            sentiment_weights = [0.7, 0.2, 0.1]  # 高互動貼文較多正面
        else:
            sentiment_weights = [0.5, 0.35, 0.15]

        sentiment_type = np.random.choice(['positive', 'neutral', 'negative'],
                                          p=sentiment_weights)

        if sentiment_type == 'positive':
            text = np.random.choice(positive_templates)
        elif sentiment_type == 'negative':
            text = np.random.choice(negative_templates)
        else:
            text = np.random.choice(neutral_templates)

        # 添加一些隨機文字
        if np.random.random() > 0.5:
            text += " " + "".join(np.random.choice(['👍', '❤️', '🔥', '👏', '💯', '😊', '🙏'],
                                                   size=np.random.randint(1, 4)))

        comment_date = post['post_date'] + timedelta(
            hours=np.random.randint(0, 72),
            minutes=np.random.randint(0, 60)
        )

        comments.append({
            'comment_id': f'CMT{i:07d}',
            'post_id': post['post_id'],
            'comment_date': comment_date,
            'comment_text': text,
            'likes': int(np.random.lognormal(1, 1.5)),
            'user_id': f'USER{np.random.randint(1, n_followers):06d}'
        })

    comments_df = pd.DataFrame(comments)

    # ========================================
    # 粉絲數據
    # ========================================
    locations = ['台北', '新北', '台中', '高雄', '桃園', '新竹', '台南', '其他']
    location_weights = [0.25, 0.15, 0.12, 0.10, 0.10, 0.08, 0.08, 0.12]

    age_ranges = ['13-17', '18-24', '25-34', '35-44', '45-54', '55+']
    age_weights = [0.05, 0.25, 0.35, 0.20, 0.10, 0.05]

    followers = []
    for i in range(1, n_followers + 1):
        follow_date = today - timedelta(days=np.random.randint(0, 730))

        followers.append({
            'user_id': f'USER{i:06d}',
            'follow_date': follow_date,
            'location': np.random.choice(locations, p=location_weights),
            'gender': np.random.choice(['M', 'F', 'Other'], p=[0.40, 0.55, 0.05]),
            'age_range': np.random.choice(age_ranges, p=age_weights),
            'activity_score': np.clip(np.random.normal(60, 25), 0, 100).round(0)
        })

    followers_df = pd.DataFrame(followers)

    return posts_df, comments_df, followers_df


def main():
    """執行社交媒體分析範例"""
    print("="*80)
    print(" "*20 + "社交媒體分析")
    print("="*80)

    # ========================================
    # 1. 準備數據
    # ========================================
    print("\n[1/5] 準備社交媒體數據...")

    posts, comments, followers = generate_social_media_data(
        n_posts=300, n_comments=5000, n_followers=10000
    )

    print(f"  ✓ 貼文數: {len(posts):,}")
    print(f"  ✓ 留言數: {len(comments):,}")
    print(f"  ✓ 粉絲數: {len(followers):,}")
    print(f"  ✓ 總互動: {posts['likes'].sum() + posts['comments'].sum():,}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/5] 初始化社交媒體分析器...")
    analyzer = SocialMediaAnalyzer(posts, comments, followers)
    print("  ✓ 分析器初始化完成")

    # ========================================
    # 3. 互動指標分析
    # ========================================
    print("\n[3/5] 計算互動指標...")

    metrics = analyzer.calculate_engagement_metrics()
    print(f"\n  📊 互動指標摘要:")
    print(f"     平均互動率: {metrics['engagement_rate'].mean():.2f}%")
    print(f"     平均讚數: {metrics['likes'].mean():.0f}")
    print(f"     平均留言: {metrics['comments'].mean():.0f}")

    # ========================================
    # 4. 內容表現分析
    # ========================================
    print("\n[4/5] 分析內容表現...")

    content = analyzer.analyze_content_performance()
    if 'by_content_type' in content:
        print("\n  內容類型表現:")
        for ctype, row in content['by_content_type'].head(3).iterrows():
            print(f"     {ctype}: 平均 {row['avg_engagement']:.0f} 互動")

    # ========================================
    # 5. 最佳發布時間
    # ========================================
    print("\n[5/5] 分析最佳發布時間...")

    timing = analyzer.find_best_posting_times()
    best = timing['best_combination']
    print(f"\n  🕐 最佳發布時間: {best['day']} {best['hour']}:00")
    print(f"     平均互動: {best['avg_engagement']:.0f}")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存報告
    try:
        with open('data/outputs/social_media_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/social_media_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
