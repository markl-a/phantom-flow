"""
房地產市場分析範例

這個範例展示如何分析房地產數據，包含：
- 房價預測因素分析
- 區域市場比較
- 投資報酬率計算
- 市場趨勢分析

真實應用場景:
- 房地產開發商市場調研
- 投資者決策支援
- 銀行房貸風險評估
- 政府住房政策分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class RealEstateAnalyzer:
    """
    房地產分析器

    提供完整的房地產數據分析功能:
    - 房價因素分析
    - 區域市場分析
    - 投資回報計算
    - 市場趨勢預測
    """

    def __init__(self, properties_df: pd.DataFrame,
                 transactions_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            properties_df: 房產主檔DataFrame
            transactions_df: 交易記錄DataFrame (可選)
        """
        self.properties = properties_df.copy()
        self.transactions = transactions_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'list_date' in self.properties.columns:
            self.properties['list_date'] = pd.to_datetime(self.properties['list_date'])

        # 計算每坪單價
        if 'price' in self.properties.columns and 'area_ping' in self.properties.columns:
            self.properties['price_per_ping'] = (
                self.properties['price'] / self.properties['area_ping']
            ).round(2)

    def analyze_price_factors(self) -> Dict[str, any]:
        """分析影響房價的因素"""
        df = self.properties
        results = {}

        # 各因素與房價的相關性
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if 'price' in numeric_cols:
            correlations = df[numeric_cols].corr()['price'].drop('price').sort_values(ascending=False)
            results['correlations'] = correlations.to_dict()

            # 前5個正相關因素
            results['top_positive_factors'] = correlations.head(5).to_dict()
            # 前5個負相關因素
            results['top_negative_factors'] = correlations.tail(5).to_dict()

        # 按房型分析
        if 'property_type' in df.columns:
            type_stats = df.groupby('property_type').agg({
                'price': ['mean', 'median', 'std', 'count'],
                'price_per_ping': 'mean' if 'price_per_ping' in df.columns else 'count'
            }).round(0)
            type_stats.columns = ['avg_price', 'median_price', 'std_price', 'count', 'avg_price_per_ping']
            results['by_property_type'] = type_stats.to_dict('index')

        # 按屋齡分析
        if 'building_age' in df.columns:
            df['age_bracket'] = pd.cut(
                df['building_age'],
                bins=[0, 5, 10, 20, 30, float('inf')],
                labels=['0-5年', '5-10年', '10-20年', '20-30年', '30年以上']
            )
            age_stats = df.groupby('age_bracket').agg({
                'price_per_ping': ['mean', 'median']
            }).round(0)
            age_stats.columns = ['avg_price_per_ping', 'median_price_per_ping']
            results['by_building_age'] = age_stats.to_dict('index')

        return results

    def analyze_by_district(self) -> pd.DataFrame:
        """按區域分析市場"""
        df = self.properties

        if 'district' not in df.columns:
            return pd.DataFrame()

        district_stats = df.groupby('district').agg({
            'price': ['mean', 'median', 'min', 'max', 'count'],
            'price_per_ping': 'mean' if 'price_per_ping' in df.columns else 'count',
            'area_ping': 'mean' if 'area_ping' in df.columns else 'count'
        }).round(0)

        district_stats.columns = [
            'avg_price', 'median_price', 'min_price', 'max_price',
            'listing_count', 'avg_price_per_ping', 'avg_area'
        ]

        # 計算市場份額
        district_stats['market_share'] = (
            district_stats['listing_count'] / district_stats['listing_count'].sum() * 100
        ).round(1)

        # 價格排名
        district_stats['price_rank'] = district_stats['avg_price_per_ping'].rank(ascending=False).astype(int)

        return district_stats.sort_values('avg_price_per_ping', ascending=False)

    def calculate_investment_metrics(self) -> pd.DataFrame:
        """計算投資指標"""
        df = self.properties.copy()

        # 租金報酬率 (假設月租金約為房價的0.3-0.5%)
        if 'monthly_rent' not in df.columns:
            df['estimated_monthly_rent'] = df['price'] * np.random.uniform(0.003, 0.005, len(df))
        else:
            df['estimated_monthly_rent'] = df['monthly_rent']

        # 年租金收益率
        df['annual_yield'] = (df['estimated_monthly_rent'] * 12 / df['price'] * 100).round(2)

        # 本益比 (房價/年租金)
        df['price_to_rent_ratio'] = (df['price'] / (df['estimated_monthly_rent'] * 12)).round(1)

        # 預期增值 (基於區域和屋齡)
        base_appreciation = 0.02  # 基礎年增值2%
        if 'district' in df.columns:
            district_premium = df.groupby('district')['price_per_ping'].transform(
                lambda x: 0.01 if x.mean() > df['price_per_ping'].median() else -0.005
            )
        else:
            district_premium = 0

        if 'building_age' in df.columns:
            age_factor = np.where(df['building_age'] < 10, 0.01,
                                  np.where(df['building_age'] < 20, 0, -0.01))
        else:
            age_factor = 0

        df['expected_appreciation'] = ((base_appreciation + district_premium + age_factor) * 100).round(2)

        # 綜合投資評分
        df['investment_score'] = (
            df['annual_yield'] * 0.4 +
            df['expected_appreciation'] * 0.4 +
            (10 - df['price_to_rent_ratio'] / 10).clip(0, 10) * 0.2
        ).round(1)

        return df[['property_id', 'district', 'price', 'estimated_monthly_rent',
                   'annual_yield', 'price_to_rent_ratio', 'expected_appreciation',
                   'investment_score']].sort_values('investment_score', ascending=False)

    def analyze_market_trends(self) -> Dict[str, any]:
        """分析市場趨勢"""
        if self.transactions is None:
            return {}

        df = self.transactions.copy()
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        results = {}

        # 月度交易量與價格趨勢
        monthly = df.groupby(df['transaction_date'].dt.to_period('M')).agg({
            'price': ['mean', 'median', 'count'],
            'price_per_ping': 'mean' if 'price_per_ping' in df.columns else 'count'
        })
        monthly.columns = ['avg_price', 'median_price', 'transaction_count', 'avg_price_per_ping']

        # 計算月度變化
        monthly['price_change_pct'] = monthly['avg_price'].pct_change() * 100
        monthly['volume_change_pct'] = monthly['transaction_count'].pct_change() * 100

        results['monthly_trends'] = monthly.round(2).to_dict('index')

        # 年度統計
        yearly = df.groupby(df['transaction_date'].dt.year).agg({
            'price': ['mean', 'sum', 'count'],
            'price_per_ping': 'mean'
        })
        yearly.columns = ['avg_price', 'total_value', 'transaction_count', 'avg_price_per_ping']
        results['yearly_stats'] = yearly.round(0).to_dict('index')

        # 市場熱度指標
        recent_months = df[df['transaction_date'] >= df['transaction_date'].max() - timedelta(days=90)]
        prev_months = df[(df['transaction_date'] < df['transaction_date'].max() - timedelta(days=90)) &
                         (df['transaction_date'] >= df['transaction_date'].max() - timedelta(days=180))]

        if len(recent_months) > 0 and len(prev_months) > 0:
            results['market_heat'] = {
                'recent_avg_price': recent_months['price'].mean(),
                'previous_avg_price': prev_months['price'].mean(),
                'price_change': (recent_months['price'].mean() / prev_months['price'].mean() - 1) * 100,
                'volume_change': (len(recent_months) / len(prev_months) - 1) * 100,
                'market_status': 'Hot' if len(recent_months) > len(prev_months) * 1.1 else
                                ('Cold' if len(recent_months) < len(prev_months) * 0.9 else 'Stable')
            }

        return results

    def identify_opportunities(self) -> pd.DataFrame:
        """識別投資機會"""
        df = self.properties.copy()

        # 計算價值偏離度 (相對於區域平均)
        if 'district' in df.columns and 'price_per_ping' in df.columns:
            district_avg = df.groupby('district')['price_per_ping'].transform('mean')
            df['value_deviation'] = ((df['price_per_ping'] - district_avg) / district_avg * 100).round(1)
        else:
            df['value_deviation'] = 0

        # 識別低估房產 (低於區域平均10%以上)
        undervalued = df[df['value_deviation'] < -10].copy()

        # 計算機會評分
        undervalued['opportunity_score'] = (
            abs(undervalued['value_deviation']) * 0.5 +
            (30 - undervalued.get('building_age', 15)) * 0.3 +
            undervalued.get('area_ping', 30) / 10 * 0.2
        ).round(1)

        return undervalued.nlargest(20, 'opportunity_score')[
            ['property_id', 'district', 'property_type', 'price', 'price_per_ping',
             'value_deviation', 'opportunity_score']
        ]

    def generate_report(self) -> str:
        """生成完整的房地產分析報告"""
        factors = self.analyze_price_factors()
        district = self.analyze_by_district()
        investment = self.calculate_investment_metrics()
        opportunities = self.identify_opportunities()

        report = f"""
{'='*80}
                    房地產市場分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、市場概覽
{'='*40}
  房源總數: {len(self.properties):,}
  平均房價: ${self.properties['price'].mean():,.0f} 萬
  平均單價: ${self.properties['price_per_ping'].mean():,.0f} 萬/坪
  平均面積: {self.properties['area_ping'].mean():.1f} 坪

二、房價影響因素
{'='*40}
  正相關因素 (房價越高):
"""
        for factor, corr in list(factors.get('top_positive_factors', {}).items())[:5]:
            bar = '█' * int(abs(corr) * 20)
            report += f"    {factor}: {corr:.2f} {bar}\n"

        report += f"""
  負相關因素 (房價越低):
"""
        for factor, corr in list(factors.get('top_negative_factors', {}).items())[:3]:
            report += f"    {factor}: {corr:.2f}\n"

        # 區域分析
        report += f"""
三、區域市場分析
{'='*40}
"""
        if not district.empty:
            report += "  區域排名 (按每坪單價):\n"
            for i, (dist, row) in enumerate(district.head(10).iterrows(), 1):
                report += f"    {i:2}. {dist}: ${row['avg_price_per_ping']:,.0f}/坪, "
                report += f"{row['listing_count']:.0f} 筆 ({row['market_share']:.1f}%)\n"

        # 投資分析
        report += f"""
四、投資分析
{'='*40}
  平均租金報酬率: {investment['annual_yield'].mean():.2f}%
  平均本益比: {investment['price_to_rent_ratio'].mean():.1f}
  預期年增值: {investment['expected_appreciation'].mean():.2f}%

  Top 10 投資標的:
"""
        for _, prop in investment.head(10).iterrows():
            report += f"    [{prop['district']}] ${prop['price']:,.0f}萬 - "
            report += f"報酬率 {prop['annual_yield']:.1f}%, 評分 {prop['investment_score']:.1f}\n"

        # 投資機會
        report += f"""
五、潛在投資機會 (低估房產)
{'='*40}
  發現 {len(opportunities)} 個潛在機會:
"""
        for _, prop in opportunities.head(5).iterrows():
            report += f"    - [{prop['district']}] {prop['property_type']}\n"
            report += f"      價格: ${prop['price']:,.0f}萬, 單價: ${prop['price_per_ping']:,.0f}/坪\n"
            report += f"      低於區域 {abs(prop['value_deviation']):.1f}%\n"

        # 市場趨勢
        if self.transactions is not None:
            trends = self.analyze_market_trends()
            if 'market_heat' in trends:
                heat = trends['market_heat']
                report += f"""
六、市場趨勢
{'='*40}
  近期 vs 前期:
    價格變化: {heat['price_change']:+.1f}%
    交易量變化: {heat['volume_change']:+.1f}%
    市場狀態: {heat['market_status']}
"""

        report += f"""
七、投資建議
{'='*40}

1. 區域選擇:
   - 高端市場: 考慮房價穩定區域的保值投資
   - 成長型: 關注新興開發區域的增值潛力

2. 物件選擇:
   - 優先考慮屋齡10年內的物件
   - 關注低於區域均價的投資機會
   - 評估租金收益與增值潛力的平衡

3. 時機把握:
   - 持續監控市場熱度指標
   - 淡季進場可能有較好議價空間

4. 風險控制:
   - 分散投資區域降低風險
   - 保持適當現金流預備

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_real_estate_data(n_properties: int = 500,
                              n_transactions: int = 2000,
                              seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """生成模擬房地產數據"""
    np.random.seed(seed)
    today = datetime.now()

    # 區域設定
    districts = {
        '信義區': {'base_price': 120, 'std': 30},
        '大安區': {'base_price': 110, 'std': 25},
        '中山區': {'base_price': 95, 'std': 20},
        '松山區': {'base_price': 90, 'std': 18},
        '內湖區': {'base_price': 70, 'std': 15},
        '士林區': {'base_price': 65, 'std': 15},
        '北投區': {'base_price': 55, 'std': 12},
        '文山區': {'base_price': 50, 'std': 10},
        '萬華區': {'base_price': 45, 'std': 10},
        '南港區': {'base_price': 60, 'std': 12},
    }

    property_types = ['公寓', '電梯大樓', '華廈', '透天', '套房']
    type_weights = [0.25, 0.35, 0.20, 0.10, 0.10]

    # 房產資料
    properties = []
    for i in range(1, n_properties + 1):
        district = np.random.choice(list(districts.keys()))
        district_info = districts[district]

        property_type = np.random.choice(property_types, p=type_weights)

        # 面積 (坪)
        if property_type == '套房':
            area = np.random.uniform(8, 15)
        elif property_type == '透天':
            area = np.random.uniform(40, 100)
        else:
            area = np.random.uniform(20, 60)

        # 屋齡
        building_age = np.random.exponential(15)
        building_age = np.clip(building_age, 0, 50)

        # 樓層
        if property_type in ['電梯大樓', '華廈']:
            total_floors = np.random.randint(7, 25)
            floor = np.random.randint(1, total_floors + 1)
        else:
            total_floors = np.random.randint(4, 7)
            floor = np.random.randint(1, total_floors + 1)

        # 房間數
        if property_type == '套房':
            rooms = 1
            bathrooms = 1
        else:
            rooms = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
            bathrooms = np.random.choice([1, 2], p=[0.6, 0.4])

        # 每坪單價
        base_price = district_info['base_price']
        std_price = district_info['std']

        # 調整因素
        age_factor = max(0.7, 1 - building_age * 0.01)
        floor_factor = 1 + (floor - total_floors / 2) * 0.01
        type_factor = {'公寓': 0.85, '電梯大樓': 1.1, '華廈': 1.0, '透天': 1.2, '套房': 0.9}[property_type]

        price_per_ping = np.random.normal(base_price, std_price) * age_factor * floor_factor * type_factor
        price_per_ping = max(20, price_per_ping)

        # 總價
        total_price = price_per_ping * area

        # 上架日期
        list_date = today - timedelta(days=np.random.randint(1, 180))

        properties.append({
            'property_id': f'PROP{i:05d}',
            'district': district,
            'property_type': property_type,
            'area_ping': round(area, 1),
            'building_age': round(building_age, 0),
            'floor': floor,
            'total_floors': total_floors,
            'rooms': rooms,
            'bathrooms': bathrooms,
            'has_parking': np.random.choice([True, False], p=[0.6, 0.4]),
            'has_balcony': np.random.choice([True, False], p=[0.7, 0.3]),
            'price_per_ping': round(price_per_ping, 1),
            'price': round(total_price, 0),
            'list_date': list_date,
            'mrt_distance': np.random.uniform(100, 1500),
            'school_nearby': np.random.choice([True, False], p=[0.5, 0.5])
        })

    properties_df = pd.DataFrame(properties)

    # 交易記錄
    transactions = []
    for i in range(1, n_transactions + 1):
        prop = properties_df.sample(1).iloc[0]

        # 交易日期 (過去2年)
        tx_date = today - timedelta(days=np.random.randint(1, 730))

        # 成交價 (可能有議價)
        discount = np.random.uniform(0.92, 1.0)
        final_price = prop['price'] * discount

        transactions.append({
            'transaction_id': f'TX{i:06d}',
            'property_id': prop['property_id'],
            'district': prop['district'],
            'property_type': prop['property_type'],
            'area_ping': prop['area_ping'],
            'transaction_date': tx_date,
            'list_price': prop['price'],
            'price': round(final_price, 0),
            'price_per_ping': round(final_price / prop['area_ping'], 1),
            'days_on_market': np.random.randint(30, 180)
        })

    transactions_df = pd.DataFrame(transactions)

    return properties_df, transactions_df


def main():
    """執行房地產分析範例"""
    print("="*80)
    print(" "*20 + "房地產市場分析")
    print("="*80)

    # 準備數據
    print("\n[1/4] 準備房地產數據...")
    properties, transactions = generate_real_estate_data(n_properties=500, n_transactions=2000)

    print(f"  ✓ 房源數: {len(properties):,}")
    print(f"  ✓ 交易記錄: {len(transactions):,}")
    print(f"  ✓ 平均房價: ${properties['price'].mean():,.0f} 萬")

    # 初始化分析器
    print("\n[2/4] 初始化分析器...")
    analyzer = RealEstateAnalyzer(properties, transactions)
    print("  ✓ 分析器初始化完成")

    # 區域分析
    print("\n[3/4] 分析區域市場...")
    district_analysis = analyzer.analyze_by_district()
    print("\n  區域單價排名 (Top 5):")
    for i, (dist, row) in enumerate(district_analysis.head(5).iterrows(), 1):
        print(f"     {i}. {dist}: ${row['avg_price_per_ping']:,.0f}/坪")

    # 投資分析
    print("\n[4/4] 計算投資指標...")
    investment = analyzer.calculate_investment_metrics()
    print(f"\n  平均租金報酬率: {investment['annual_yield'].mean():.2f}%")
    print(f"  最佳投資標的: {investment.iloc[0]['district']}, 評分 {investment.iloc[0]['investment_score']:.1f}")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/real_estate_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/real_estate_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
