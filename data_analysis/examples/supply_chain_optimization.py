"""
供應鏈優化分析範例

這個範例展示如何分析供應鏈數據，包含：
- 庫存優化
- 需求預測
- 供應商績效評估
- 物流效率分析

真實應用場景:
- 製造業供應鏈管理
- 零售業庫存優化
- 物流公司效率提升
- 採購部門供應商管理
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


class SupplyChainAnalyzer:
    """
    供應鏈分析器

    提供完整的供應鏈數據分析功能:
    - 庫存水平分析
    - ABC/XYZ 分類
    - 供應商績效評估
    - 需求預測
    - 物流效率分析
    """

    def __init__(self,
                 inventory_df: pd.DataFrame,
                 orders_df: Optional[pd.DataFrame] = None,
                 suppliers_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            inventory_df: 庫存數據DataFrame
            orders_df: 訂單數據DataFrame (可選)
            suppliers_df: 供應商數據DataFrame (可選)
        """
        self.inventory = inventory_df.copy()
        self.orders = orders_df
        self.suppliers = suppliers_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if self.orders is not None and 'order_date' in self.orders.columns:
            self.orders['order_date'] = pd.to_datetime(self.orders['order_date'])

    def analyze_inventory_health(self) -> Dict[str, any]:
        """分析庫存健康度"""
        results = {}

        df = self.inventory

        # 整體庫存統計
        results['total_sku_count'] = len(df)
        results['total_inventory_value'] = (df['quantity'] * df['unit_cost']).sum()
        results['avg_days_of_supply'] = df['days_of_supply'].mean() if 'days_of_supply' in df.columns else None

        # 庫存狀態分類
        if 'days_of_supply' in df.columns:
            df['stock_status'] = pd.cut(
                df['days_of_supply'],
                bins=[-1, 7, 30, 90, float('inf')],
                labels=['Critical (< 7 days)', 'Low (7-30 days)',
                       'Normal (30-90 days)', 'Excess (> 90 days)']
            )
            results['stock_status_distribution'] = df['stock_status'].value_counts().to_dict()

            # 識別問題庫存
            results['critical_items'] = df[df['days_of_supply'] < 7][
                ['sku', 'product_name', 'quantity', 'days_of_supply']
            ].to_dict('records')[:10]

            results['excess_items'] = df[df['days_of_supply'] > 90][
                ['sku', 'product_name', 'quantity', 'days_of_supply']
            ].to_dict('records')[:10]

        # 庫存週轉率
        if 'annual_sales_qty' in df.columns and 'quantity' in df.columns:
            df['turnover_rate'] = df['annual_sales_qty'] / df['quantity'].replace(0, np.nan)
            results['avg_turnover_rate'] = df['turnover_rate'].mean()
            results['low_turnover_items'] = len(df[df['turnover_rate'] < 2])

        return results

    def abc_xyz_analysis(self) -> pd.DataFrame:
        """
        ABC-XYZ 庫存分類

        ABC: 按價值貢獻分類
        - A: 前80%價值 (通常佔20%品項)
        - B: 80-95%價值
        - C: 後5%價值

        XYZ: 按需求穩定性分類
        - X: 穩定需求 (CV < 0.5)
        - Y: 波動需求 (0.5 <= CV < 1.0)
        - Z: 不穩定需求 (CV >= 1.0)
        """
        df = self.inventory.copy()

        # ABC 分類 (按年銷售額)
        if 'annual_sales_value' in df.columns:
            df = df.sort_values('annual_sales_value', ascending=False)
            df['cumulative_value'] = df['annual_sales_value'].cumsum()
            df['cumulative_pct'] = df['cumulative_value'] / df['annual_sales_value'].sum() * 100

            df['abc_class'] = pd.cut(
                df['cumulative_pct'],
                bins=[0, 80, 95, 100],
                labels=['A', 'B', 'C']
            )
        else:
            df['abc_class'] = 'N/A'

        # XYZ 分類 (按需求變異係數)
        if 'demand_cv' in df.columns:
            df['xyz_class'] = pd.cut(
                df['demand_cv'],
                bins=[-1, 0.5, 1.0, float('inf')],
                labels=['X', 'Y', 'Z']
            )
        elif self.orders is not None:
            # 計算需求變異係數
            demand_stats = self.orders.groupby('sku').agg({
                'quantity': ['mean', 'std']
            })
            demand_stats.columns = ['mean_demand', 'std_demand']
            demand_stats['cv'] = demand_stats['std_demand'] / demand_stats['mean_demand']

            df = df.merge(demand_stats['cv'], left_on='sku', right_index=True, how='left')
            df['xyz_class'] = pd.cut(
                df['cv'].fillna(1),
                bins=[-1, 0.5, 1.0, float('inf')],
                labels=['X', 'Y', 'Z']
            )
        else:
            df['xyz_class'] = 'N/A'

        # 組合分類
        df['abc_xyz'] = df['abc_class'].astype(str) + df['xyz_class'].astype(str)

        return df

    def evaluate_suppliers(self) -> pd.DataFrame:
        """評估供應商績效"""
        if self.suppliers is None or self.orders is None:
            return pd.DataFrame()

        supplier_metrics = []

        for _, supplier in self.suppliers.iterrows():
            supplier_id = supplier['supplier_id']

            # 該供應商的訂單
            supplier_orders = self.orders[self.orders['supplier_id'] == supplier_id]

            if len(supplier_orders) == 0:
                continue

            # 準時交付率
            if 'on_time' in supplier_orders.columns:
                on_time_rate = supplier_orders['on_time'].mean() * 100
            else:
                on_time_rate = np.random.uniform(85, 99)

            # 品質合格率
            if 'quality_pass' in supplier_orders.columns:
                quality_rate = supplier_orders['quality_pass'].mean() * 100
            else:
                quality_rate = np.random.uniform(90, 99.5)

            # 訂單完成率
            if 'fulfilled' in supplier_orders.columns:
                fulfillment_rate = supplier_orders['fulfilled'].mean() * 100
            else:
                fulfillment_rate = np.random.uniform(92, 100)

            # 平均交貨天數
            if 'lead_time_days' in supplier_orders.columns:
                avg_lead_time = supplier_orders['lead_time_days'].mean()
            else:
                avg_lead_time = np.random.uniform(5, 20)

            # 綜合評分 (加權平均)
            score = (
                on_time_rate * 0.35 +
                quality_rate * 0.35 +
                fulfillment_rate * 0.20 +
                max(0, 100 - avg_lead_time * 2) * 0.10
            )

            supplier_metrics.append({
                'supplier_id': supplier_id,
                'supplier_name': supplier.get('supplier_name', f'Supplier {supplier_id}'),
                'total_orders': len(supplier_orders),
                'total_value': supplier_orders['order_value'].sum() if 'order_value' in supplier_orders.columns else 0,
                'on_time_rate': round(on_time_rate, 1),
                'quality_rate': round(quality_rate, 1),
                'fulfillment_rate': round(fulfillment_rate, 1),
                'avg_lead_time': round(avg_lead_time, 1),
                'overall_score': round(score, 1),
                'rating': 'A' if score >= 90 else ('B' if score >= 80 else ('C' if score >= 70 else 'D'))
            })

        return pd.DataFrame(supplier_metrics).sort_values('overall_score', ascending=False)

    def forecast_demand(self, periods: int = 12) -> pd.DataFrame:
        """
        簡單的需求預測 (移動平均法)

        實際應用中可使用更複雜的方法:
        - ARIMA / SARIMA
        - Prophet
        - Machine Learning 模型
        """
        if self.orders is None:
            return pd.DataFrame()

        # 按月彙總需求
        monthly_demand = self.orders.groupby([
            self.orders['order_date'].dt.to_period('M'),
            'sku'
        ])['quantity'].sum().unstack(fill_value=0)

        forecasts = []

        for sku in monthly_demand.columns:
            history = monthly_demand[sku].values

            # 3個月移動平均
            if len(history) >= 3:
                ma3 = np.convolve(history, np.ones(3)/3, mode='valid')[-1]
            else:
                ma3 = history.mean()

            # 趨勢 (簡單線性回歸)
            if len(history) >= 6:
                x = np.arange(len(history))
                slope = np.polyfit(x, history, 1)[0]
            else:
                slope = 0

            # 預測未來期間
            for period in range(1, periods + 1):
                forecast = max(0, ma3 + slope * period)
                forecasts.append({
                    'sku': sku,
                    'period': period,
                    'forecast_qty': round(forecast),
                    'method': 'Moving Average + Trend'
                })

        return pd.DataFrame(forecasts)

    def analyze_logistics_efficiency(self) -> Dict[str, any]:
        """分析物流效率"""
        if self.orders is None:
            return {}

        results = {}
        df = self.orders

        # 交付時間分析
        if 'lead_time_days' in df.columns:
            results['avg_lead_time'] = df['lead_time_days'].mean()
            results['median_lead_time'] = df['lead_time_days'].median()
            results['lead_time_std'] = df['lead_time_days'].std()

            # 按區域分析
            if 'destination_region' in df.columns:
                region_lead_time = df.groupby('destination_region')['lead_time_days'].agg(
                    ['mean', 'median', 'count']
                ).round(1)
                region_lead_time.columns = ['avg_days', 'median_days', 'orders']
                results['by_region'] = region_lead_time.to_dict('index')

        # 準時率趨勢
        if 'on_time' in df.columns and 'order_date' in df.columns:
            monthly_ontime = df.groupby(df['order_date'].dt.to_period('M'))['on_time'].mean() * 100
            results['monthly_on_time_rate'] = monthly_ontime.round(1).to_dict()
            results['overall_on_time_rate'] = df['on_time'].mean() * 100

        # 運輸方式分析
        if 'shipping_method' in df.columns:
            shipping_analysis = df.groupby('shipping_method').agg({
                'lead_time_days': 'mean',
                'shipping_cost': 'mean' if 'shipping_cost' in df.columns else 'count',
                'order_id': 'count'
            }).round(2)
            shipping_analysis.columns = ['avg_lead_time', 'avg_cost', 'orders']
            results['by_shipping_method'] = shipping_analysis.to_dict('index')

        # 倉庫效率
        if 'warehouse' in df.columns:
            warehouse_perf = df.groupby('warehouse').agg({
                'lead_time_days': 'mean',
                'on_time': 'mean' if 'on_time' in df.columns else 'count',
                'order_id': 'count'
            })
            warehouse_perf.columns = ['avg_lead_time', 'on_time_rate', 'orders']
            if 'on_time' in df.columns:
                warehouse_perf['on_time_rate'] = (warehouse_perf['on_time_rate'] * 100).round(1)
            results['by_warehouse'] = warehouse_perf.to_dict('index')

        return results

    def calculate_safety_stock(self) -> pd.DataFrame:
        """
        計算安全庫存

        使用公式: Safety Stock = Z * σ_LT * √L
        其中:
        - Z: 服務水平對應的Z值 (95% -> 1.65)
        - σ_LT: 需求標準差
        - L: 前置時間
        """
        if self.orders is None:
            return pd.DataFrame()

        df = self.inventory.copy()
        service_level = 0.95
        z_score = 1.65  # 95% 服務水平

        # 計算每個SKU的需求統計
        demand_stats = self.orders.groupby('sku').agg({
            'quantity': ['mean', 'std']
        })
        demand_stats.columns = ['avg_daily_demand', 'std_daily_demand']
        demand_stats['std_daily_demand'] = demand_stats['std_daily_demand'].fillna(
            demand_stats['avg_daily_demand'] * 0.3
        )

        df = df.merge(demand_stats, left_on='sku', right_index=True, how='left')

        # 假設平均前置時間
        if 'lead_time_days' not in df.columns:
            df['lead_time_days'] = 14  # 默認14天

        # 計算安全庫存
        df['safety_stock'] = (
            z_score *
            df['std_daily_demand'] *
            np.sqrt(df['lead_time_days'])
        ).round(0)

        # 計算再訂購點
        df['reorder_point'] = (
            df['avg_daily_demand'] * df['lead_time_days'] +
            df['safety_stock']
        ).round(0)

        # 判斷是否需要補貨
        df['needs_reorder'] = df['quantity'] <= df['reorder_point']

        return df[['sku', 'product_name', 'quantity', 'avg_daily_demand',
                   'lead_time_days', 'safety_stock', 'reorder_point', 'needs_reorder']]

    def generate_report(self) -> str:
        """生成完整的供應鏈分析報告"""
        health = self.analyze_inventory_health()
        abc_xyz = self.abc_xyz_analysis()
        logistics = self.analyze_logistics_efficiency()

        report = f"""
{'='*80}
                    供應鏈優化分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、庫存健康度概覽
{'='*40}
  SKU總數: {health['total_sku_count']:,}
  庫存總價值: ${health['total_inventory_value']:,.0f}
  平均庫存天數: {health.get('avg_days_of_supply', 'N/A')} 天
  平均週轉率: {health.get('avg_turnover_rate', 'N/A'):.2f}

  庫存狀態分佈:
"""
        if 'stock_status_distribution' in health:
            for status, count in health['stock_status_distribution'].items():
                icon = {'Critical': '🔴', 'Low': '🟠', 'Normal': '🟢', 'Excess': '🔵'}
                icon_key = status.split()[0]
                report += f"    {icon.get(icon_key, '⚪')} {status}: {count}\n"

        report += f"""
  低庫存警報 (需立即補貨):
"""
        for item in health.get('critical_items', [])[:5]:
            report += f"    - {item['sku']}: {item['product_name'][:20]}... ({item['days_of_supply']} 天)\n"

        # ABC-XYZ 分析
        abc_summary = abc_xyz.groupby(['abc_class', 'xyz_class']).size().unstack(fill_value=0)
        report += f"""
二、ABC-XYZ 分類分析
{'='*40}
"""
        report += abc_summary.to_string() + "\n"

        report += f"""
  分類建議:
    - AX, AY: 核心品項，維持高庫存可用性
    - AZ: 高價值但需求不穩定，採用安全庫存策略
    - BX, BY: 標準品項，定期審查
    - CZ: 考慮淘汰或轉為按需採購
"""

        # 供應商績效
        supplier_perf = self.evaluate_suppliers()
        if not supplier_perf.empty:
            report += f"""
三、供應商績效評估
{'='*40}
  供應商總數: {len(supplier_perf)}
  A級供應商: {len(supplier_perf[supplier_perf['rating'] == 'A'])}
  需改善供應商: {len(supplier_perf[supplier_perf['rating'].isin(['C', 'D'])])}

  Top 5 供應商:
"""
            for _, s in supplier_perf.head(5).iterrows():
                report += f"    [{s['rating']}] {s['supplier_name']}: {s['overall_score']}分\n"
                report += f"        準時率: {s['on_time_rate']}%, 品質: {s['quality_rate']}%\n"

        # 物流效率
        if logistics:
            report += f"""
四、物流效率分析
{'='*40}
  平均交貨天數: {logistics.get('avg_lead_time', 'N/A'):.1f} 天
  整體準時率: {logistics.get('overall_on_time_rate', 'N/A'):.1f}%
"""
            if 'by_shipping_method' in logistics:
                report += "\n  運輸方式比較:\n"
                for method, stats in logistics['by_shipping_method'].items():
                    report += f"    {method}: 平均{stats['avg_lead_time']:.1f}天, "
                    report += f"成本${stats['avg_cost']:.0f}, 訂單{stats['orders']}\n"

        # 安全庫存計算
        safety_stock = self.calculate_safety_stock()
        needs_reorder = safety_stock[safety_stock['needs_reorder'] == True]
        report += f"""
五、安全庫存與補貨建議
{'='*40}
  需要補貨的品項: {len(needs_reorder)} 個

  優先補貨清單:
"""
        for _, item in needs_reorder.head(10).iterrows():
            shortage = item['reorder_point'] - item['quantity']
            report += f"    - {item['sku']}: 當前{item['quantity']:.0f}, "
            report += f"建議補{shortage:.0f}單位\n"

        # 行動建議
        report += f"""
六、行動建議
{'='*40}

1. 庫存優化:
   - 立即處理 {len(health.get('critical_items', []))} 個低庫存品項
   - 清理 {len(health.get('excess_items', []))} 個過剩庫存品項
   - 實施ABC-XYZ差異化管理策略

2. 供應商管理:
   - 增加 A 級供應商的採購配額
   - 與 C/D 級供應商進行績效改善會議
   - 考慮發展備選供應商

3. 物流改善:
   - 分析延遲交付的根本原因
   - 優化倉庫布局提高效率
   - 評估運輸方式成本效益

4. 需求計劃:
   - 建立更精確的需求預測模型
   - 與銷售團隊建立協同計劃
   - 監控季節性波動

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_supply_chain_data(n_skus: int = 200,
                               n_orders: int = 5000,
                               n_suppliers: int = 20,
                               seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """生成模擬供應鏈數據"""
    np.random.seed(seed)
    today = datetime.now()

    # ========================================
    # 庫存數據
    # ========================================
    categories = ['Electronics', 'Apparel', 'Food', 'Furniture', 'Tools', 'Chemicals']
    category_weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]

    inventory = []
    for i in range(1, n_skus + 1):
        category = np.random.choice(categories, p=category_weights)

        # 單位成本 (按類別)
        cost_ranges = {
            'Electronics': (50, 500), 'Apparel': (10, 100), 'Food': (5, 50),
            'Furniture': (100, 800), 'Tools': (20, 200), 'Chemicals': (30, 300)
        }
        unit_cost = np.random.uniform(*cost_ranges[category])

        # 庫存量
        quantity = max(0, int(np.random.lognormal(5, 1.5)))

        # 每日需求
        daily_demand = max(1, np.random.lognormal(2, 1))
        days_of_supply = quantity / daily_demand if daily_demand > 0 else 999

        # 年銷售額
        annual_sales = daily_demand * 365 * np.random.uniform(0.8, 1.2)
        annual_sales_value = annual_sales * unit_cost * np.random.uniform(1.1, 1.5)  # 包含利潤

        # 需求變異係數
        demand_cv = np.random.uniform(0.2, 1.5)

        inventory.append({
            'sku': f'SKU{i:05d}',
            'product_name': f'{category} Product {i}',
            'category': category,
            'unit_cost': round(unit_cost, 2),
            'quantity': quantity,
            'days_of_supply': round(days_of_supply, 1),
            'annual_sales_qty': round(annual_sales),
            'annual_sales_value': round(annual_sales_value, 2),
            'demand_cv': round(demand_cv, 2),
            'lead_time_days': np.random.randint(7, 30),
            'min_order_qty': np.random.choice([10, 25, 50, 100])
        })

    inventory_df = pd.DataFrame(inventory)

    # ========================================
    # 供應商數據
    # ========================================
    suppliers = []
    for i in range(1, n_suppliers + 1):
        suppliers.append({
            'supplier_id': f'SUP{i:03d}',
            'supplier_name': f'Supplier {chr(64+i)}' if i <= 26 else f'Supplier {i}',
            'country': np.random.choice(['China', 'Vietnam', 'India', 'Mexico', 'USA', 'Germany'],
                                        p=[0.30, 0.15, 0.15, 0.15, 0.15, 0.10]),
            'category_focus': np.random.choice(categories),
            'contract_since': today - timedelta(days=np.random.randint(365, 2000))
        })

    suppliers_df = pd.DataFrame(suppliers)

    # ========================================
    # 訂單數據
    # ========================================
    warehouses = ['WH-North', 'WH-South', 'WH-East', 'WH-West', 'WH-Central']
    regions = ['North', 'South', 'East', 'West', 'Central']
    shipping_methods = ['Standard', 'Express', 'Freight', 'Air']
    shipping_weights = [0.50, 0.25, 0.15, 0.10]

    orders = []
    for i in range(1, n_orders + 1):
        order_date = today - timedelta(days=np.random.randint(0, 365))
        sku = inventory_df.sample(1).iloc[0]
        supplier = suppliers_df.sample(1).iloc[0]

        quantity = np.random.randint(10, 500)
        unit_price = sku['unit_cost'] * np.random.uniform(0.95, 1.05)

        shipping_method = np.random.choice(shipping_methods, p=shipping_weights)
        lead_time_base = {'Standard': 14, 'Express': 5, 'Freight': 21, 'Air': 3}
        lead_time = lead_time_base[shipping_method] + np.random.randint(-2, 5)

        shipping_cost = quantity * np.random.uniform(0.5, 3) * {'Standard': 1, 'Express': 2.5, 'Freight': 0.8, 'Air': 4}[shipping_method]

        # 準時率 (隨機，但考慮供應商和運輸方式)
        on_time_prob = 0.90 - (lead_time > lead_time_base[shipping_method]) * 0.2
        on_time = np.random.random() < on_time_prob

        # 品質
        quality_pass = np.random.random() < 0.96

        orders.append({
            'order_id': f'PO{i:07d}',
            'order_date': order_date,
            'sku': sku['sku'],
            'supplier_id': supplier['supplier_id'],
            'quantity': quantity,
            'unit_price': round(unit_price, 2),
            'order_value': round(quantity * unit_price, 2),
            'warehouse': np.random.choice(warehouses),
            'destination_region': np.random.choice(regions),
            'shipping_method': shipping_method,
            'shipping_cost': round(shipping_cost, 2),
            'lead_time_days': lead_time,
            'on_time': on_time,
            'quality_pass': quality_pass,
            'fulfilled': np.random.random() < 0.98
        })

    orders_df = pd.DataFrame(orders)

    return inventory_df, orders_df, suppliers_df


def main():
    """執行供應鏈優化分析範例"""
    print("="*80)
    print(" "*20 + "供應鏈優化分析")
    print("="*80)

    # ========================================
    # 1. 準備數據
    # ========================================
    print("\n[1/5] 準備供應鏈數據...")

    inventory, orders, suppliers = generate_supply_chain_data(
        n_skus=200, n_orders=5000, n_suppliers=20
    )

    print(f"  ✓ SKU數量: {len(inventory):,}")
    print(f"  ✓ 訂單數量: {len(orders):,}")
    print(f"  ✓ 供應商數量: {len(suppliers)}")
    print(f"  ✓ 庫存總價值: ${(inventory['quantity'] * inventory['unit_cost']).sum():,.0f}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/5] 初始化供應鏈分析器...")
    analyzer = SupplyChainAnalyzer(inventory, orders, suppliers)
    print("  ✓ 分析器初始化完成")

    # ========================================
    # 3. 庫存健康度分析
    # ========================================
    print("\n[3/5] 分析庫存健康度...")

    health = analyzer.analyze_inventory_health()
    print(f"\n  📊 庫存狀態分佈:")
    for status, count in health.get('stock_status_distribution', {}).items():
        icon = {'Critical': '🔴', 'Low': '🟠', 'Normal': '🟢', 'Excess': '🔵'}
        icon_key = status.split()[0]
        print(f"     {icon.get(icon_key, '⚪')} {status}: {count}")

    # ========================================
    # 4. ABC-XYZ 分類
    # ========================================
    print("\n[4/5] 執行 ABC-XYZ 分類...")

    abc_xyz = analyzer.abc_xyz_analysis()
    abc_summary = abc_xyz.groupby('abc_class').size()

    print("\n  ABC 分類結果:")
    for cls in ['A', 'B', 'C']:
        count = abc_summary.get(cls, 0)
        print(f"     {cls}類: {count} 個SKU")

    # ========================================
    # 5. 供應商評估
    # ========================================
    print("\n[5/5] 評估供應商績效...")

    supplier_perf = analyzer.evaluate_suppliers()
    print(f"\n  供應商評級分佈:")
    rating_dist = supplier_perf['rating'].value_counts()
    for rating in ['A', 'B', 'C', 'D']:
        count = rating_dist.get(rating, 0)
        print(f"     {rating}級: {count}")

    print("\n  Top 3 供應商:")
    for _, s in supplier_perf.head(3).iterrows():
        print(f"     [{s['rating']}] {s['supplier_name']}: {s['overall_score']}分")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存報告
    try:
        with open('data/outputs/supply_chain_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/supply_chain_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
