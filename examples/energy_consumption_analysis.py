"""
能源消耗分析範例

這個範例展示如何分析能源消耗數據，包含：
- 用電量分析
- 尖峰負載識別
- 能效評估
- 節能建議

真實應用場景:
- 電力公司負載管理
- 企業能源成本優化
- 建築能效評估
- 碳排放計算
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


class EnergyAnalyzer:
    """
    能源消耗分析器

    提供完整的能源數據分析功能:
    - 消耗模式分析
    - 尖峰時段識別
    - 異常檢測
    - 節能建議
    """

    def __init__(self, consumption_df: pd.DataFrame,
                 buildings_df: Optional[pd.DataFrame] = None,
                 weather_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            consumption_df: 能源消耗數據DataFrame
            buildings_df: 建築資訊DataFrame (可選)
            weather_df: 天氣數據DataFrame (可選)
        """
        self.consumption = consumption_df.copy()
        self.buildings = buildings_df
        self.weather = weather_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'timestamp' in self.consumption.columns:
            self.consumption['timestamp'] = pd.to_datetime(self.consumption['timestamp'])
            self.consumption['hour'] = self.consumption['timestamp'].dt.hour
            self.consumption['day_of_week'] = self.consumption['timestamp'].dt.dayofweek
            self.consumption['month'] = self.consumption['timestamp'].dt.month
            self.consumption['is_weekend'] = self.consumption['day_of_week'].isin([5, 6])

            # 時段分類
            self.consumption['time_period'] = pd.cut(
                self.consumption['hour'],
                bins=[-1, 6, 12, 18, 24],
                labels=['夜間(0-6)', '上午(6-12)', '下午(12-18)', '晚間(18-24)']
            )

    def analyze_consumption_patterns(self) -> Dict[str, any]:
        """分析消耗模式"""
        df = self.consumption
        results = {}

        # 整體統計
        results['overall'] = {
            'total_consumption': df['consumption_kwh'].sum(),
            'avg_hourly': df['consumption_kwh'].mean(),
            'max_hourly': df['consumption_kwh'].max(),
            'min_hourly': df['consumption_kwh'].min(),
            'std': df['consumption_kwh'].std()
        }

        # 按小時分析
        hourly_pattern = df.groupby('hour')['consumption_kwh'].agg(['mean', 'std', 'max']).round(2)
        hourly_pattern.columns = ['avg', 'std', 'max']
        results['hourly_pattern'] = hourly_pattern.to_dict('index')

        # 按星期幾分析
        day_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        daily_pattern = df.groupby('day_of_week')['consumption_kwh'].agg(['mean', 'sum']).round(2)
        daily_pattern.index = [day_names[i] for i in daily_pattern.index]
        daily_pattern.columns = ['avg', 'total']
        results['daily_pattern'] = daily_pattern.to_dict('index')

        # 按月分析
        monthly_pattern = df.groupby('month')['consumption_kwh'].agg(['mean', 'sum']).round(2)
        monthly_pattern.columns = ['avg', 'total']
        results['monthly_pattern'] = monthly_pattern.to_dict('index')

        # 平日 vs 週末
        weekday_weekend = df.groupby('is_weekend')['consumption_kwh'].agg(['mean', 'sum']).round(2)
        weekday_weekend.index = ['平日', '週末']
        weekday_weekend.columns = ['avg', 'total']
        results['weekday_vs_weekend'] = weekday_weekend.to_dict('index')

        # 時段分析
        if 'time_period' in df.columns:
            period_pattern = df.groupby('time_period')['consumption_kwh'].agg(['mean', 'sum']).round(2)
            period_pattern.columns = ['avg', 'total']
            results['time_period_pattern'] = period_pattern.to_dict('index')

        return results

    def identify_peak_hours(self, top_n: int = 10) -> pd.DataFrame:
        """識別尖峰時段"""
        df = self.consumption

        # 按小時找出最高消耗
        peak_hours = df.nlargest(top_n, 'consumption_kwh')[
            ['timestamp', 'consumption_kwh', 'hour', 'day_of_week']
        ].copy()

        peak_hours['day_name'] = peak_hours['day_of_week'].map({
            0: '週一', 1: '週二', 2: '週三', 3: '週四',
            4: '週五', 5: '週六', 6: '週日'
        })

        # 計算相對於平均的倍數
        avg_consumption = df['consumption_kwh'].mean()
        peak_hours['vs_avg_ratio'] = (peak_hours['consumption_kwh'] / avg_consumption).round(2)

        return peak_hours

    def calculate_efficiency_metrics(self) -> Dict[str, any]:
        """計算能效指標"""
        df = self.consumption
        results = {}

        # 基礎效率指標
        total = df['consumption_kwh'].sum()
        avg = df['consumption_kwh'].mean()
        peak = df['consumption_kwh'].max()

        # 負載因子 (平均/尖峰)
        results['load_factor'] = round(avg / peak * 100, 1) if peak > 0 else 0

        # 尖峰/離峰比
        peak_hours = df[(df['hour'] >= 10) & (df['hour'] <= 18)]
        off_peak_hours = df[(df['hour'] < 10) | (df['hour'] > 18)]
        if len(off_peak_hours) > 0:
            results['peak_to_offpeak_ratio'] = round(
                peak_hours['consumption_kwh'].mean() / off_peak_hours['consumption_kwh'].mean(), 2
            )

        # 變異係數
        results['coefficient_of_variation'] = round(df['consumption_kwh'].std() / avg * 100, 1) if avg > 0 else 0

        # 如果有建築資訊，計算 EUI (Energy Use Intensity)
        if self.buildings is not None and 'area_sqm' in self.buildings.columns:
            total_area = self.buildings['area_sqm'].sum()
            results['eui'] = round(total / total_area, 2) if total_area > 0 else 0

        # 碳排放估算 (假設電力碳排放係數 0.5 kg CO2/kWh)
        carbon_factor = 0.5
        results['estimated_carbon_emissions'] = round(total * carbon_factor, 0)

        return results

    def detect_anomalies(self) -> pd.DataFrame:
        """檢測異常消耗"""
        df = self.consumption.copy()

        # 計算每個小時段的統計
        hour_stats = df.groupby('hour')['consumption_kwh'].agg(['mean', 'std']).reset_index()
        hour_stats.columns = ['hour', 'hour_mean', 'hour_std']

        df = df.merge(hour_stats, on='hour')

        # Z-Score
        df['z_score'] = (df['consumption_kwh'] - df['hour_mean']) / df['hour_std'].replace(0, 1)
        df['is_anomaly'] = df['z_score'].abs() > 2.5

        # 異常記錄
        anomalies = df[df['is_anomaly']][
            ['timestamp', 'consumption_kwh', 'hour', 'z_score', 'hour_mean']
        ].copy()

        anomalies['anomaly_type'] = np.where(
            anomalies['consumption_kwh'] > anomalies['hour_mean'],
            'High Consumption',
            'Low Consumption'
        )

        return anomalies.sort_values('z_score', key=abs, ascending=False)

    def analyze_weather_correlation(self) -> Dict[str, any]:
        """分析天氣與能耗的相關性"""
        if self.weather is None:
            return {}

        df = self.consumption.copy()
        weather = self.weather.copy()

        # 合併數據
        df['date'] = df['timestamp'].dt.date
        weather['date'] = pd.to_datetime(weather['date']).dt.date

        merged = df.merge(weather, on='date', how='left')

        results = {}

        # 溫度與用電相關性
        if 'temperature' in merged.columns:
            correlation = merged['consumption_kwh'].corr(merged['temperature'])
            results['temperature_correlation'] = round(correlation, 3)

            # 按溫度區間分析
            merged['temp_bracket'] = pd.cut(
                merged['temperature'],
                bins=[-float('inf'), 15, 20, 25, 30, float('inf')],
                labels=['<15°C', '15-20°C', '20-25°C', '25-30°C', '>30°C']
            )
            temp_consumption = merged.groupby('temp_bracket')['consumption_kwh'].mean().round(2)
            results['by_temperature'] = temp_consumption.to_dict()

        # 濕度相關性
        if 'humidity' in merged.columns:
            results['humidity_correlation'] = round(
                merged['consumption_kwh'].corr(merged['humidity']), 3
            )

        return results

    def generate_savings_recommendations(self) -> List[Dict]:
        """生成節能建議"""
        patterns = self.analyze_consumption_patterns()
        efficiency = self.calculate_efficiency_metrics()
        anomalies = self.detect_anomalies()

        recommendations = []

        # 基於負載因子的建議
        if efficiency['load_factor'] < 50:
            recommendations.append({
                'category': 'Load Management',
                'recommendation': '負載因子偏低，建議平滑用電負載',
                'details': f"當前負載因子: {efficiency['load_factor']}%，建議目標: >60%",
                'potential_savings': '10-15%',
                'priority': 'HIGH'
            })

        # 基於尖峰/離峰比的建議
        if 'peak_to_offpeak_ratio' in efficiency and efficiency['peak_to_offpeak_ratio'] > 2:
            recommendations.append({
                'category': 'Peak Shifting',
                'recommendation': '尖峰用電過高，建議將負載轉移到離峰時段',
                'details': f"尖峰/離峰比: {efficiency['peak_to_offpeak_ratio']}，建議目標: <1.5",
                'potential_savings': '15-20%',
                'priority': 'HIGH'
            })

        # 基於時段模式的建議
        if 'time_period_pattern' in patterns:
            night_avg = patterns['time_period_pattern'].get('夜間(0-6)', {}).get('avg', 0)
            day_avg = patterns['time_period_pattern'].get('下午(12-18)', {}).get('avg', 0)
            if night_avg > day_avg * 0.3:
                recommendations.append({
                    'category': 'Night Operations',
                    'recommendation': '夜間用電偏高，檢查是否有不必要的設備運行',
                    'details': f"夜間平均: {night_avg:.1f} kWh，日間平均: {day_avg:.1f} kWh",
                    'potential_savings': '5-10%',
                    'priority': 'MEDIUM'
                })

        # 基於異常的建議
        high_anomalies = len(anomalies[anomalies['anomaly_type'] == 'High Consumption'])
        if high_anomalies > 10:
            recommendations.append({
                'category': 'Anomaly Resolution',
                'recommendation': f'發現 {high_anomalies} 次異常高消耗事件，建議調查原因',
                'details': '可能存在設備故障或能源浪費',
                'potential_savings': '5-8%',
                'priority': 'MEDIUM'
            })

        # 通用建議
        recommendations.append({
            'category': 'General Efficiency',
            'recommendation': '安裝智能電表和能源管理系統',
            'details': '即時監控和自動調節可有效降低能耗',
            'potential_savings': '8-12%',
            'priority': 'LOW'
        })

        recommendations.append({
            'category': 'Equipment Upgrade',
            'recommendation': '評估老舊設備更換為高效設備',
            'details': '特別是空調、照明和馬達等高耗能設備',
            'potential_savings': '15-25%',
            'priority': 'LOW'
        })

        return recommendations

    def generate_report(self) -> str:
        """生成完整的能源分析報告"""
        patterns = self.analyze_consumption_patterns()
        peaks = self.identify_peak_hours()
        efficiency = self.calculate_efficiency_metrics()
        anomalies = self.detect_anomalies()
        recommendations = self.generate_savings_recommendations()

        report = f"""
{'='*80}
                    能源消耗分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、消耗概覽
{'='*40}
  分析期間: {self.consumption['timestamp'].min().strftime('%Y-%m-%d')} ~ {self.consumption['timestamp'].max().strftime('%Y-%m-%d')}
  總消耗量: {patterns['overall']['total_consumption']:,.0f} kWh
  平均每小時: {patterns['overall']['avg_hourly']:.1f} kWh
  尖峰消耗: {patterns['overall']['max_hourly']:.1f} kWh
  預估碳排放: {efficiency['estimated_carbon_emissions']:,.0f} kg CO2

二、時段消耗模式
{'='*40}
"""
        if 'time_period_pattern' in patterns:
            for period, stats in patterns['time_period_pattern'].items():
                avg = stats['avg']
                total = stats['total']
                pct = total / patterns['overall']['total_consumption'] * 100
                bar = '█' * int(pct / 2)
                report += f"  {period}: {avg:.1f} kWh/hr ({pct:.1f}%) {bar}\n"

        report += f"""
三、每日消耗模式
{'='*40}
"""
        for day, stats in patterns['daily_pattern'].items():
            avg = stats['avg']
            pct = stats['total'] / patterns['overall']['total_consumption'] * 100
            bar = '█' * int(avg / max(s['avg'] for s in patterns['daily_pattern'].values()) * 20)
            report += f"  {day}: {avg:.1f} kWh/hr ({pct:.1f}%) {bar}\n"

        report += f"""
四、尖峰時段分析
{'='*40}
  Top 10 尖峰時段:
"""
        for _, peak in peaks.head(10).iterrows():
            report += f"    {peak['timestamp'].strftime('%m/%d %H:00')} ({peak['day_name']}): "
            report += f"{peak['consumption_kwh']:.1f} kWh (平均的 {peak['vs_avg_ratio']}倍)\n"

        report += f"""
五、能效指標
{'='*40}
  負載因子: {efficiency['load_factor']:.1f}%
  尖峰/離峰比: {efficiency.get('peak_to_offpeak_ratio', 'N/A')}
  變異係數: {efficiency['coefficient_of_variation']:.1f}%
"""
        if 'eui' in efficiency:
            report += f"  能源使用強度 (EUI): {efficiency['eui']:.2f} kWh/m²\n"

        report += f"""
六、異常檢測
{'='*40}
  檢測到的異常事件: {len(anomalies)}
  高消耗異常: {len(anomalies[anomalies['anomaly_type'] == 'High Consumption'])}
  低消耗異常: {len(anomalies[anomalies['anomaly_type'] == 'Low Consumption'])}

  最顯著的異常:
"""
        for _, anom in anomalies.head(5).iterrows():
            report += f"    {anom['timestamp'].strftime('%m/%d %H:00')}: "
            report += f"{anom['consumption_kwh']:.1f} kWh "
            report += f"(Z-Score: {anom['z_score']:.2f}, {anom['anomaly_type']})\n"

        # 天氣相關性
        weather_corr = self.analyze_weather_correlation()
        if weather_corr:
            report += f"""
七、天氣相關性分析
{'='*40}
  溫度相關係數: {weather_corr.get('temperature_correlation', 'N/A')}
  濕度相關係數: {weather_corr.get('humidity_correlation', 'N/A')}
"""
            if 'by_temperature' in weather_corr:
                report += "\n  按溫度區間消耗:\n"
                for temp, consumption in weather_corr['by_temperature'].items():
                    report += f"    {temp}: {consumption:.1f} kWh\n"

        # 節能建議
        report += f"""
八、節能建議
{'='*40}
"""
        for i, rec in enumerate(recommendations, 1):
            icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[rec['priority']]
            report += f"""
  {i}. {icon} [{rec['category']}]
     建議: {rec['recommendation']}
     說明: {rec['details']}
     預估節省: {rec['potential_savings']}
"""

        # 總結
        total_potential = sum(
            int(r['potential_savings'].split('-')[0].replace('%', ''))
            for r in recommendations
        )
        report += f"""
九、總結與行動計劃
{'='*40}

  綜合節能潛力: {total_potential}%+
  預估可節省電費: ${patterns['overall']['total_consumption'] * 0.15 * total_potential / 100:,.0f}
  預估可減少碳排放: {efficiency['estimated_carbon_emissions'] * total_potential / 100:,.0f} kg CO2

  優先行動:
  1. 處理尖峰負載問題
  2. 調查異常消耗事件
  3. 實施負載轉移策略
  4. 評估設備更新計劃

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_energy_data(n_days: int = 365,
                         n_buildings: int = 5,
                         seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """生成模擬能源數據"""
    np.random.seed(seed)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=n_days)

    # 建築資訊
    buildings = []
    building_types = ['Office', 'Factory', 'Retail', 'Warehouse', 'Data Center']
    for i in range(1, n_buildings + 1):
        buildings.append({
            'building_id': f'BLD{i:03d}',
            'building_type': np.random.choice(building_types),
            'area_sqm': np.random.uniform(1000, 10000),
            'floors': np.random.randint(1, 20),
            'year_built': np.random.randint(1980, 2020)
        })
    buildings_df = pd.DataFrame(buildings)

    # 消耗記錄 (每小時)
    consumption = []

    # 每小時的基準消耗模式 (工作時間較高)
    hourly_base = [
        0.3, 0.3, 0.3, 0.3, 0.3, 0.4,  # 0-5
        0.5, 0.7, 0.9, 1.0, 1.0, 0.9,  # 6-11
        0.8, 1.0, 1.0, 0.9, 0.8, 0.7,  # 12-17
        0.6, 0.6, 0.5, 0.4, 0.4, 0.3   # 18-23
    ]

    # 月份調整 (夏冬較高 - 空調)
    monthly_factor = {
        1: 1.2, 2: 1.1, 3: 0.9, 4: 0.8, 5: 0.9, 6: 1.1,
        7: 1.3, 8: 1.3, 9: 1.1, 10: 0.9, 11: 1.0, 12: 1.2
    }

    for building in buildings:
        building_id = building['building_id']
        base_consumption = building['area_sqm'] / 100  # 基礎消耗與面積相關

        current_date = start_date
        while current_date < today:
            month = current_date.month
            day_of_week = current_date.weekday()
            is_weekend = day_of_week >= 5

            # 週末消耗較低
            weekend_factor = 0.5 if is_weekend else 1.0

            for hour in range(24):
                # 計算該小時消耗
                hourly_factor = hourly_base[hour]
                seasonal_factor = monthly_factor[month]

                consumption_kwh = (
                    base_consumption *
                    hourly_factor *
                    seasonal_factor *
                    weekend_factor *
                    np.random.uniform(0.85, 1.15)  # 隨機波動
                )

                # 偶爾添加異常值
                if np.random.random() < 0.005:
                    consumption_kwh *= np.random.uniform(1.5, 3.0)

                consumption.append({
                    'record_id': f'E{len(consumption)+1:08d}',
                    'building_id': building_id,
                    'timestamp': current_date.replace(hour=hour),
                    'consumption_kwh': round(consumption_kwh, 2),
                    'power_factor': round(np.random.uniform(0.85, 0.98), 2)
                })

            current_date += timedelta(days=1)

    consumption_df = pd.DataFrame(consumption)

    # 天氣數據
    weather = []
    current_date = start_date
    while current_date < today:
        month = current_date.month

        # 月份基準溫度
        base_temps = {
            1: 15, 2: 16, 3: 20, 4: 24, 5: 27, 6: 30,
            7: 32, 8: 32, 9: 29, 10: 25, 11: 20, 12: 16
        }

        weather.append({
            'date': current_date.date(),
            'temperature': round(base_temps[month] + np.random.normal(0, 3), 1),
            'humidity': round(np.random.uniform(40, 90), 1),
            'precipitation': round(max(0, np.random.exponential(5)), 1)
        })

        current_date += timedelta(days=1)

    weather_df = pd.DataFrame(weather)

    return consumption_df, buildings_df, weather_df


def main():
    """執行能源消耗分析範例"""
    print("="*80)
    print(" "*20 + "能源消耗分析")
    print("="*80)

    # 準備數據
    print("\n[1/4] 準備能源數據...")
    consumption, buildings, weather = generate_energy_data(n_days=365, n_buildings=5)

    print(f"  ✓ 消耗記錄: {len(consumption):,}")
    print(f"  ✓ 建築數: {len(buildings)}")
    print(f"  ✓ 總消耗: {consumption['consumption_kwh'].sum():,.0f} kWh")

    # 初始化分析器
    print("\n[2/4] 初始化分析器...")
    analyzer = EnergyAnalyzer(consumption, buildings, weather)
    print("  ✓ 分析器初始化完成")

    # 消耗分析
    print("\n[3/4] 分析消耗模式...")
    patterns = analyzer.analyze_consumption_patterns()
    print(f"\n  📊 消耗概覽:")
    print(f"     總消耗: {patterns['overall']['total_consumption']:,.0f} kWh")
    print(f"     平均每小時: {patterns['overall']['avg_hourly']:.1f} kWh")
    print(f"     尖峰: {patterns['overall']['max_hourly']:.1f} kWh")

    # 能效分析
    print("\n[4/4] 計算能效指標...")
    efficiency = analyzer.calculate_efficiency_metrics()
    print(f"\n  ⚡ 能效指標:")
    print(f"     負載因子: {efficiency['load_factor']:.1f}%")
    print(f"     碳排放: {efficiency['estimated_carbon_emissions']:,.0f} kg CO2")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/energy_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/energy_analysis_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
