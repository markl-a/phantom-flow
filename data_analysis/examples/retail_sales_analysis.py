"""
零售銷售分析範例

這個範例展示如何分析真實的零售銷售數據，
包含銷售趨勢、產品分析、季節性分析等。

真實應用場景:
- 零售店鋪銷售績效分析
- 產品組合優化
- 庫存管理決策支援
- 促銷效果評估
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import DataLoader, setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
    from data_analysis_chatbots.visualization import Plotter
except ImportError:
    import sys
    sys.path.insert(0, '..')


class RetailSalesAnalyzer:
    """
    零售銷售分析器

    提供完整的銷售數據分析功能:
    - 銷售趨勢分析
    - 產品表現分析
    - 門店績效比較
    - 季節性分析
    - 購物籃分析
    """

    def __init__(self, sales_df: pd.DataFrame):
        """
        初始化分析器

        Args:
            sales_df: 銷售數據DataFrame，需包含:
                - transaction_date: 交易日期
                - store_id: 門店ID
                - product_id: 產品ID
                - product_category: 產品類別
                - quantity: 數量
                - unit_price: 單價
                - total_amount: 總金額
        """
        self.df = sales_df.copy()
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'transaction_date' in self.df.columns:
            self.df['transaction_date'] = pd.to_datetime(self.df['transaction_date'])
            self.df['year'] = self.df['transaction_date'].dt.year
            self.df['month'] = self.df['transaction_date'].dt.month
            self.df['week'] = self.df['transaction_date'].dt.isocalendar().week
            self.df['day_of_week'] = self.df['transaction_date'].dt.dayofweek
            self.df['hour'] = self.df['transaction_date'].dt.hour
            self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6])

    def analyze_sales_trend(self, period: str = 'daily') -> pd.DataFrame:
        """
        分析銷售趨勢

        Args:
            period: 'daily', 'weekly', 'monthly'

        Returns:
            銷售趨勢DataFrame
        """
        if period == 'daily':
            group_col = self.df['transaction_date'].dt.date
        elif period == 'weekly':
            group_col = self.df['transaction_date'].dt.to_period('W')
        else:  # monthly
            group_col = self.df['transaction_date'].dt.to_period('M')

        trend = self.df.groupby(group_col).agg({
            'total_amount': ['sum', 'mean', 'count'],
            'quantity': 'sum',
            'transaction_id': 'nunique'
        }).round(2)

        trend.columns = ['revenue', 'avg_order_value', 'items_sold', 'total_quantity', 'transactions']
        trend['revenue_growth'] = trend['revenue'].pct_change() * 100

        return trend

    def analyze_product_performance(self, top_n: int = 20) -> Dict[str, pd.DataFrame]:
        """
        分析產品表現

        Returns:
            包含多個產品分析結果的字典
        """
        results = {}

        # 暢銷產品
        product_sales = self.df.groupby('product_id').agg({
            'quantity': 'sum',
            'total_amount': 'sum',
            'transaction_id': 'nunique'
        }).rename(columns={
            'quantity': 'units_sold',
            'total_amount': 'revenue',
            'transaction_id': 'transactions'
        })

        product_sales['avg_price'] = product_sales['revenue'] / product_sales['units_sold']
        product_sales = product_sales.sort_values('revenue', ascending=False)
        results['top_products'] = product_sales.head(top_n)

        # 類別分析
        category_sales = self.df.groupby('product_category').agg({
            'quantity': 'sum',
            'total_amount': 'sum',
            'transaction_id': 'nunique',
            'product_id': 'nunique'
        }).rename(columns={
            'quantity': 'units_sold',
            'total_amount': 'revenue',
            'transaction_id': 'transactions',
            'product_id': 'unique_products'
        })

        category_sales['revenue_share'] = (category_sales['revenue'] /
                                           category_sales['revenue'].sum() * 100).round(1)
        results['category_analysis'] = category_sales.sort_values('revenue', ascending=False)

        # ABC分析 (帕累托分析)
        product_sales_sorted = product_sales.sort_values('revenue', ascending=False)
        product_sales_sorted['cumulative_revenue'] = product_sales_sorted['revenue'].cumsum()
        product_sales_sorted['cumulative_pct'] = (product_sales_sorted['cumulative_revenue'] /
                                                  product_sales_sorted['revenue'].sum() * 100)

        product_sales_sorted['abc_class'] = pd.cut(
            product_sales_sorted['cumulative_pct'],
            bins=[0, 80, 95, 100],
            labels=['A', 'B', 'C']
        )
        results['abc_analysis'] = product_sales_sorted

        return results

    def analyze_store_performance(self) -> pd.DataFrame:
        """分析門店績效"""
        store_perf = self.df.groupby('store_id').agg({
            'total_amount': ['sum', 'mean'],
            'quantity': 'sum',
            'transaction_id': 'nunique',
            'customer_id': 'nunique'
        })

        store_perf.columns = ['revenue', 'avg_order_value', 'units_sold',
                              'transactions', 'unique_customers']

        store_perf['revenue_per_customer'] = (store_perf['revenue'] /
                                               store_perf['unique_customers']).round(2)
        store_perf['items_per_transaction'] = (store_perf['units_sold'] /
                                                store_perf['transactions']).round(2)

        # 排名
        store_perf['revenue_rank'] = store_perf['revenue'].rank(ascending=False).astype(int)

        return store_perf.sort_values('revenue', ascending=False)

    def analyze_seasonality(self) -> Dict[str, pd.DataFrame]:
        """分析季節性"""
        results = {}

        # 月度季節性
        monthly = self.df.groupby('month').agg({
            'total_amount': ['sum', 'mean'],
            'transaction_id': 'nunique'
        })
        monthly.columns = ['revenue', 'avg_order_value', 'transactions']
        monthly['seasonality_index'] = (monthly['revenue'] /
                                         monthly['revenue'].mean() * 100).round(1)
        results['monthly'] = monthly

        # 星期幾分析
        daily = self.df.groupby('day_of_week').agg({
            'total_amount': ['sum', 'mean'],
            'transaction_id': 'nunique'
        })
        daily.columns = ['revenue', 'avg_order_value', 'transactions']
        daily.index = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        results['day_of_week'] = daily

        # 小時分析 (如果有)
        if 'hour' in self.df.columns:
            hourly = self.df.groupby('hour').agg({
                'total_amount': ['sum', 'mean'],
                'transaction_id': 'nunique'
            })
            hourly.columns = ['revenue', 'avg_order_value', 'transactions']
            results['hourly'] = hourly

        # 週末 vs 平日
        weekend_analysis = self.df.groupby('is_weekend').agg({
            'total_amount': ['sum', 'mean'],
            'transaction_id': 'nunique'
        })
        weekend_analysis.columns = ['revenue', 'avg_order_value', 'transactions']
        weekend_analysis.index = ['平日', '週末']
        results['weekend_vs_weekday'] = weekend_analysis

        return results

    def analyze_basket(self) -> Dict[str, any]:
        """購物籃分析"""
        # 每筆交易的產品數
        basket_size = self.df.groupby('transaction_id').agg({
            'quantity': 'sum',
            'total_amount': 'sum',
            'product_id': 'nunique'
        }).rename(columns={
            'quantity': 'items',
            'total_amount': 'basket_value',
            'product_id': 'unique_products'
        })

        results = {
            'avg_basket_size': basket_size['items'].mean(),
            'avg_basket_value': basket_size['basket_value'].mean(),
            'avg_unique_products': basket_size['unique_products'].mean(),
            'basket_distribution': basket_size.describe(),
            'value_segments': pd.cut(
                basket_size['basket_value'],
                bins=[0, 50, 100, 200, 500, float('inf')],
                labels=['$0-50', '$50-100', '$100-200', '$200-500', '$500+']
            ).value_counts()
        }

        return results

    def generate_insights(self) -> List[str]:
        """生成洞察"""
        insights = []

        # 趨勢洞察
        trend = self.analyze_sales_trend('monthly')
        if len(trend) >= 2:
            latest_growth = trend['revenue_growth'].iloc[-1]
            if pd.notna(latest_growth):
                if latest_growth > 10:
                    insights.append(f"📈 銷售增長強勁: 上月營收成長 {latest_growth:.1f}%")
                elif latest_growth < -10:
                    insights.append(f"📉 銷售下滑警報: 上月營收下降 {abs(latest_growth):.1f}%")

        # 產品洞察
        product_perf = self.analyze_product_performance()
        abc = product_perf['abc_analysis']
        a_class_pct = len(abc[abc['abc_class'] == 'A']) / len(abc) * 100
        insights.append(f"🎯 {a_class_pct:.1f}% 的產品貢獻了 80% 的營收 (A類產品)")

        # 類別洞察
        top_category = product_perf['category_analysis'].index[0]
        top_share = product_perf['category_analysis']['revenue_share'].iloc[0]
        insights.append(f"🏆 最暢銷類別: {top_category} (佔營收 {top_share}%)")

        # 季節性洞察
        seasonality = self.analyze_seasonality()
        best_day = seasonality['day_of_week']['revenue'].idxmax()
        worst_day = seasonality['day_of_week']['revenue'].idxmin()
        insights.append(f"📅 最佳銷售日: {best_day}，最差銷售日: {worst_day}")

        # 購物籃洞察
        basket = self.analyze_basket()
        insights.append(f"🛒 平均購物籃: {basket['avg_basket_size']:.1f} 件商品, ${basket['avg_basket_value']:.2f}")

        return insights

    def generate_report(self) -> str:
        """生成完整報告"""
        report = f"""
{'='*80}
                    零售銷售分析報告
                    {datetime.now().strftime('%Y-%m-%d')}
{'='*80}

一、數據概覽
{'='*40}
  分析期間: {self.df['transaction_date'].min().date()} ~ {self.df['transaction_date'].max().date()}
  總交易數: {self.df['transaction_id'].nunique():,}
  總營收: ${self.df['total_amount'].sum():,.2f}
  總銷售件數: {self.df['quantity'].sum():,}
  獨立客戶數: {self.df['customer_id'].nunique():,}

二、關鍵洞察
{'='*40}
"""
        insights = self.generate_insights()
        for insight in insights:
            report += f"  {insight}\n"

        # 產品表現
        product_perf = self.analyze_product_performance(top_n=10)
        report += f"""
三、產品表現
{'='*40}

Top 10 暢銷產品:
"""
        for i, (prod_id, row) in enumerate(product_perf['top_products'].head(10).iterrows(), 1):
            report += f"  {i}. {prod_id}: ${row['revenue']:,.2f} ({row['units_sold']:,} 件)\n"

        report += "\n類別銷售分析:\n"
        for cat, row in product_perf['category_analysis'].head(5).iterrows():
            report += f"  {cat}: ${row['revenue']:,.2f} ({row['revenue_share']}%)\n"

        # 季節性
        seasonality = self.analyze_seasonality()
        report += f"""
四、季節性分析
{'='*40}

每週銷售分佈:
"""
        for day, row in seasonality['day_of_week'].iterrows():
            bar = '█' * int(row['revenue'] / seasonality['day_of_week']['revenue'].max() * 20)
            report += f"  {day}: ${row['revenue']:,.0f} {bar}\n"

        # 建議
        report += f"""
五、行動建議
{'='*40}

1. 庫存管理:
   - 增加 A 類產品庫存深度
   - 考慮淘汰銷售較差的 C 類產品

2. 促銷策略:
   - 在銷售較差的日子安排促銷活動
   - 針對高價值客戶提供專屬優惠

3. 產品組合:
   - 考慮捆綁銷售暢銷產品
   - 開發新的暢銷類別產品

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_retail_data(n_transactions: int = 10000,
                         n_stores: int = 5,
                         n_products: int = 100) -> pd.DataFrame:
    """生成真實的零售銷售數據"""
    np.random.seed(42)
    today = datetime.now()
    start_date = today - timedelta(days=365)

    # 產品主檔
    categories = ['電子產品', '服飾', '食品', '家居', '美妝', '運動', '玩具']
    category_prices = {
        '電子產品': (100, 2000), '服飾': (30, 300), '食品': (5, 50),
        '家居': (20, 500), '美妝': (15, 200), '運動': (20, 400), '玩具': (10, 100)
    }

    products = []
    for i in range(1, n_products + 1):
        category = np.random.choice(categories)
        price_range = category_prices[category]
        products.append({
            'product_id': f'PROD{i:04d}',
            'product_category': category,
            'unit_price': round(np.random.uniform(*price_range), 2)
        })
    products_df = pd.DataFrame(products)

    # 門店列表
    stores = [f'STORE{i:02d}' for i in range(1, n_stores + 1)]
    store_weights = np.random.dirichlet(np.ones(n_stores))  # 不同門店銷售權重

    # 生成交易
    transactions = []
    for tx_id in range(1, n_transactions + 1):
        # 隨機選擇門店
        store = np.random.choice(stores, p=store_weights)

        # 隨機日期 (考慮季節性和週末效應)
        days_ago = np.random.randint(0, 365)
        tx_date = start_date + timedelta(days=days_ago)

        # 週末銷售較多
        if tx_date.weekday() >= 5:
            if np.random.random() > 0.3:  # 70%機率週末有更多交易
                days_ago = np.random.randint(0, 365)
                tx_date = start_date + timedelta(days=days_ago)

        # 添加時間
        hour = np.random.choice(range(9, 22), p=np.array([
            0.02, 0.04, 0.06, 0.10, 0.12, 0.10, 0.10, 0.12, 0.12, 0.10, 0.06, 0.04, 0.02
        ]))
        tx_date = tx_date.replace(hour=hour, minute=np.random.randint(0, 60))

        customer_id = f'CUST{np.random.randint(1, 2000):05d}'

        # 每筆交易1-5個產品
        n_items = np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.15, 0.1, 0.05])
        selected_products = products_df.sample(n=n_items)

        for _, prod in selected_products.iterrows():
            quantity = np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])
            transactions.append({
                'transaction_id': f'TXN{tx_id:08d}',
                'transaction_date': tx_date,
                'store_id': store,
                'customer_id': customer_id,
                'product_id': prod['product_id'],
                'product_category': prod['product_category'],
                'quantity': quantity,
                'unit_price': prod['unit_price'],
                'total_amount': round(prod['unit_price'] * quantity, 2)
            })

    return pd.DataFrame(transactions)


def main():
    """執行零售銷售分析範例"""
    print("="*80)
    print(" "*25 + "零售銷售分析")
    print("="*80)

    # 生成數據
    print("\n生成銷售數據...")
    sales_data = generate_retail_data(n_transactions=10000, n_stores=5, n_products=100)
    print(f"✓ 生成 {len(sales_data):,} 筆銷售記錄")
    print(f"  交易數: {sales_data['transaction_id'].nunique():,}")
    print(f"  門店數: {sales_data['store_id'].nunique()}")
    print(f"  產品數: {sales_data['product_id'].nunique()}")

    # 初始化分析器
    analyzer = RetailSalesAnalyzer(sales_data)

    # 銷售趨勢
    print("\n[1/5] 分析銷售趨勢...")
    trend = analyzer.analyze_sales_trend('monthly')
    print(f"  月平均營收: ${trend['revenue'].mean():,.2f}")
    print(f"  月平均交易數: {trend['transactions'].mean():,.0f}")

    # 產品表現
    print("\n[2/5] 分析產品表現...")
    product_perf = analyzer.analyze_product_performance()
    print(f"  暢銷產品數 (A類): {len(product_perf['abc_analysis'][product_perf['abc_analysis']['abc_class'] == 'A'])}")
    print(f"  類別數: {len(product_perf['category_analysis'])}")

    # 門店績效
    print("\n[3/5] 分析門店績效...")
    store_perf = analyzer.analyze_store_performance()
    best_store = store_perf.index[0]
    print(f"  最佳門店: {best_store} (${store_perf.loc[best_store, 'revenue']:,.2f})")

    # 季節性
    print("\n[4/5] 分析季節性...")
    seasonality = analyzer.analyze_seasonality()
    print(f"  最佳銷售月份: {seasonality['monthly']['revenue'].idxmax()}月")
    print(f"  週末佔比: {seasonality['weekend_vs_weekday'].loc['週末', 'revenue'] / seasonality['weekend_vs_weekday']['revenue'].sum() * 100:.1f}%")

    # 購物籃分析
    print("\n[5/5] 購物籃分析...")
    basket = analyzer.analyze_basket()
    print(f"  平均購物籃金額: ${basket['avg_basket_value']:.2f}")
    print(f"  平均商品數量: {basket['avg_basket_size']:.1f}")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/retail_sales_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n📄 報告已保存至: data/outputs/retail_sales_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
