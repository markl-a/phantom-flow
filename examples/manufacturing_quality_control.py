"""
製造業品質控制分析範例

這個範例展示如何使用數據分析技術進行製造業品質控制，包含：
- 缺陷模式聚類分析 (使用DBSCAN)
- 統計製程控制 (SPC) 分析
- 品質趨勢分析
- 根因分析視覺化

真實應用場景:
- 生產線品質監控
- 缺陷預測與預防
- 製程參數優化
- 供應商品質評估
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 導入專案模組
try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory, DBSCANClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator
except ImportError:
    import sys
    sys.path.insert(0, '..')
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import ClustererFactory, DBSCANClusterer
    from data_analysis_chatbots.visualization import Plotter
    from data_analysis_chatbots.preprocessing import DataValidator


def generate_manufacturing_data(n_products: int = 5000,
                                n_production_lines: int = 5,
                                n_days: int = 30) -> pd.DataFrame:
    """
    生成模擬製造業品質數據

    模擬真實的生產環境，包含：
    - 多條生產線
    - 三班制輪班
    - 環境參數 (溫度、壓力、濕度)
    - 產品尺寸測量 (dimension_x, dimension_y, weight)
    - 缺陷類型和數量
    - 品質分數

    Args:
        n_products: 產品數量
        n_production_lines: 生產線數量
        n_days: 生產天數

    Returns:
        製造品質數據DataFrame
    """
    np.random.seed(42)
    today = datetime.now()
    start_date = today - timedelta(days=n_days)

    # ========================================
    # 基本配置
    # ========================================
    shifts = ['早班', '中班', '晚班']
    shift_times = {
        '早班': (8, 16),   # 08:00-16:00
        '中班': (16, 24),  # 16:00-00:00
        '晚班': (0, 8)     # 00:00-08:00
    }

    defect_types = ['刮痕', '變形', '尺寸誤差', '顏色不均', '裂紋', '無缺陷']
    defect_weights = [0.15, 0.10, 0.20, 0.12, 0.08, 0.35]

    # ========================================
    # 生成產品數據
    # ========================================
    products = []

    for i in range(n_products):
        # 隨機選擇生產線和班次
        production_line = f'Line_{np.random.randint(1, n_production_lines + 1)}'
        shift = np.random.choice(shifts)

        # 生產時間
        days_ago = np.random.randint(0, n_days)
        production_date = start_date + timedelta(days=days_ago)

        # 班次時間
        shift_start, shift_end = shift_times[shift]
        if shift == '晚班':
            hour = np.random.randint(0, 8)
        else:
            hour = np.random.randint(shift_start, shift_end)

        production_datetime = production_date.replace(hour=hour, minute=np.random.randint(0, 60))

        # ========================================
        # 環境參數 (影響品質的關鍵因素)
        # ========================================
        # 溫度: 正常範圍 20-25°C
        base_temp = 22.5
        temp_variation = 2.0

        # 晚班溫度較不穩定
        if shift == '晚班':
            temp_variation *= 1.5

        temperature = np.clip(np.random.normal(base_temp, temp_variation), 18, 28)

        # 壓力: 正常範圍 95-105 psi
        base_pressure = 100
        pressure_variation = 3.0

        # 某些生產線壓力控制較差
        if production_line in ['Line_3', 'Line_5']:
            pressure_variation *= 1.3

        pressure = np.clip(np.random.normal(base_pressure, pressure_variation), 90, 110)

        # 濕度: 正常範圍 40-60%
        base_humidity = 50
        humidity_variation = 5.0
        humidity = np.clip(np.random.normal(base_humidity, humidity_variation), 30, 70)

        # ========================================
        # 產品尺寸 (受環境參數影響)
        # ========================================
        # 目標尺寸
        target_dimension_x = 100.0  # mm
        target_dimension_y = 50.0   # mm
        target_weight = 250.0       # g

        # 溫度和壓力影響尺寸
        temp_effect = (temperature - base_temp) * 0.1
        pressure_effect = (pressure - base_pressure) * 0.05

        dimension_x = target_dimension_x + temp_effect + pressure_effect + np.random.normal(0, 0.3)
        dimension_y = target_dimension_y + temp_effect * 0.5 + pressure_effect * 0.3 + np.random.normal(0, 0.2)
        weight = target_weight + temp_effect * 2 + pressure_effect + np.random.normal(0, 1.5)

        # ========================================
        # 缺陷判定
        # ========================================
        defect_type = np.random.choice(defect_types, p=defect_weights)

        # 計算缺陷數量 (基於環境參數和隨機因素)
        defect_probability = 0.0

        # 溫度過高或過低增加缺陷
        if temperature < 20 or temperature > 25:
            defect_probability += abs(temperature - 22.5) * 0.05

        # 壓力異常增加缺陷
        if pressure < 97 or pressure > 103:
            defect_probability += abs(pressure - 100) * 0.03

        # 濕度異常增加缺陷
        if humidity < 45 or humidity > 55:
            defect_probability += abs(humidity - 50) * 0.02

        # 尺寸偏差增加缺陷
        dimension_deviation = abs(dimension_x - target_dimension_x) + abs(dimension_y - target_dimension_y)
        if dimension_deviation > 1.0:
            defect_probability += dimension_deviation * 0.1

        # 晚班缺陷率較高
        if shift == '晚班':
            defect_probability *= 1.3

        # 決定缺陷數量
        if defect_type == '無缺陷':
            defect_count = 0
        else:
            defect_count = int(np.random.poisson(max(0, defect_probability)))

        # ========================================
        # 品質分數計算 (0-100)
        # ========================================
        quality_score = 100.0

        # 尺寸偏差扣分
        quality_score -= abs(dimension_x - target_dimension_x) * 2
        quality_score -= abs(dimension_y - target_dimension_y) * 2
        quality_score -= abs(weight - target_weight) * 0.2

        # 環境參數偏差扣分
        quality_score -= abs(temperature - base_temp) * 1.5
        quality_score -= abs(pressure - base_pressure) * 0.8
        quality_score -= abs(humidity - base_humidity) * 0.5

        # 缺陷扣分
        quality_score -= defect_count * 15

        # 確保分數在0-100之間
        quality_score = np.clip(quality_score, 0, 100)

        # ========================================
        # 記錄產品數據
        # ========================================
        products.append({
            'product_id': f'P{i+1:06d}',
            'production_line': production_line,
            'shift': shift,
            'production_datetime': production_datetime,
            'temperature': round(temperature, 2),
            'pressure': round(pressure, 2),
            'humidity': round(humidity, 2),
            'dimension_x': round(dimension_x, 3),
            'dimension_y': round(dimension_y, 3),
            'weight': round(weight, 2),
            'defect_type': defect_type,
            'defect_count': defect_count,
            'quality_score': round(quality_score, 2)
        })

    df = pd.DataFrame(products)
    df['production_date'] = pd.to_datetime(df['production_datetime']).dt.date
    df['production_hour'] = pd.to_datetime(df['production_datetime']).dt.hour

    return df


def perform_defect_clustering(df: pd.DataFrame) -> Tuple[pd.DataFrame, DBSCANClusterer]:
    """
    使用DBSCAN進行缺陷模式聚類分析

    目的：
    - 識別具有相似缺陷模式的產品群組
    - 發現隱藏的品質問題模式
    - 為根因分析提供線索

    Args:
        df: 製造品質數據

    Returns:
        (添加聚類標籤的DataFrame, 訓練好的聚類器)
    """
    print("\n" + "="*60)
    print("  缺陷模式聚類分析 (DBSCAN)")
    print("="*60)

    # 選擇聚類特徵 (環境參數 + 產品尺寸)
    feature_columns = [
        'temperature', 'pressure', 'humidity',
        'dimension_x', 'dimension_y', 'weight'
    ]

    # 只分析有缺陷的產品
    defective_df = df[df['defect_count'] > 0].copy()

    print(f"\n分析對象: {len(defective_df)} 個有缺陷的產品")
    print(f"特徵維度: {feature_columns}")

    # 使用ClustererFactory創建DBSCAN聚類器
    # eps: 鄰域半徑，影響聚類的密集程度
    # min_samples: 核心點最小鄰居數，通常設為特徵數+1
    # 注意: 對於標準化數據，eps值通常在1.0-3.0之間較合適
    clusterer = ClustererFactory.create(
        'dbscan',
        eps=1.2,
        min_samples=5,
        normalize=True
    )

    # 執行聚類
    labels = clusterer.fit_predict(defective_df, feature_columns)
    defective_df['cluster'] = labels

    # 統計聚類結果
    n_clusters = clusterer.n_clusters_
    n_noise = clusterer.n_noise_

    print(f"\n聚類結果:")
    print(f"  ✓ 發現聚類數: {n_clusters}")
    print(f"  ✓ 噪聲點數: {n_noise} ({n_noise/len(defective_df)*100:.1f}%)")

    # 分析每個聚類
    print(f"\n各聚類特徵分析:")

    for cluster_id in range(n_clusters):
        cluster_data = defective_df[defective_df['cluster'] == cluster_id]

        if len(cluster_data) == 0:
            continue

        print(f"\n  聚類 {cluster_id} ({len(cluster_data)} 個產品):")
        print(f"    主要缺陷類型: {cluster_data['defect_type'].mode().values[0]}")
        print(f"    平均品質分數: {cluster_data['quality_score'].mean():.2f}")
        print(f"    溫度範圍: {cluster_data['temperature'].min():.1f}-{cluster_data['temperature'].max():.1f}°C")
        print(f"    壓力範圍: {cluster_data['pressure'].min():.1f}-{cluster_data['pressure'].max():.1f} psi")
        print(f"    主要生產線: {cluster_data['production_line'].mode().values[0]}")
        print(f"    主要班次: {cluster_data['shift'].mode().values[0]}")

    # 將聚類結果合併回原始數據
    df_with_clusters = df.copy()
    df_with_clusters['cluster'] = -2  # 預設值：無缺陷產品
    df_with_clusters.loc[defective_df.index, 'cluster'] = defective_df['cluster']

    return df_with_clusters, clusterer


def statistical_process_control_analysis(df: pd.DataFrame) -> Dict[str, any]:
    """
    統計製程控制 (SPC) 分析

    使用控制圖監控製程穩定性：
    - 計算中心線 (CL)
    - 計算上下控制限 (UCL, LCL)
    - 識別異常點
    - 判斷製程能力

    Args:
        df: 製造品質數據

    Returns:
        SPC分析結果字典
    """
    print("\n" + "="*60)
    print("  統計製程控制 (SPC) 分析")
    print("="*60)

    results = {}

    # ========================================
    # 1. 品質分數控制圖
    # ========================================
    quality_scores = df['quality_score'].values

    # 計算控制限 (使用3-sigma規則)
    mean_quality = np.mean(quality_scores)
    std_quality = np.std(quality_scores)

    ucl_quality = mean_quality + 3 * std_quality
    lcl_quality = max(0, mean_quality - 3 * std_quality)

    # 識別異常點
    out_of_control = df[
        (df['quality_score'] > ucl_quality) |
        (df['quality_score'] < lcl_quality)
    ]

    results['quality_control'] = {
        'mean': round(mean_quality, 2),
        'std': round(std_quality, 2),
        'ucl': round(ucl_quality, 2),
        'lcl': round(lcl_quality, 2),
        'out_of_control_count': len(out_of_control),
        'out_of_control_pct': round(len(out_of_control) / len(df) * 100, 2)
    }

    print(f"\n品質分數控制圖:")
    print(f"  中心線 (CL):  {mean_quality:.2f}")
    print(f"  上控制限 (UCL): {ucl_quality:.2f}")
    print(f"  下控制限 (LCL): {lcl_quality:.2f}")
    print(f"  異常點數: {len(out_of_control)} ({len(out_of_control)/len(df)*100:.2f}%)")

    # ========================================
    # 2. 關鍵尺寸控制圖 (X-bar and R chart)
    # ========================================
    # X-bar chart (尺寸平均值)
    dim_x_mean = df['dimension_x'].mean()
    dim_x_std = df['dimension_x'].std()

    ucl_dim_x = dim_x_mean + 3 * dim_x_std
    lcl_dim_x = dim_x_mean - 3 * dim_x_std

    dim_x_out = df[
        (df['dimension_x'] > ucl_dim_x) |
        (df['dimension_x'] < lcl_dim_x)
    ]

    results['dimension_x_control'] = {
        'target': 100.0,
        'mean': round(dim_x_mean, 3),
        'std': round(dim_x_std, 3),
        'ucl': round(ucl_dim_x, 3),
        'lcl': round(lcl_dim_x, 3),
        'out_of_control_count': len(dim_x_out),
        'cpk': calculate_cpk(df['dimension_x'].values, 100.0, 99.0, 101.0)
    }

    print(f"\nDimension X 控制圖:")
    print(f"  目標值: 100.0 mm")
    print(f"  實際平均: {dim_x_mean:.3f} mm (偏差: {dim_x_mean - 100:.3f} mm)")
    print(f"  標準差: {dim_x_std:.3f} mm")
    print(f"  製程能力指數 (Cpk): {results['dimension_x_control']['cpk']:.3f}")

    # 製程能力判定
    cpk = results['dimension_x_control']['cpk']
    if cpk >= 1.33:
        capability = "優良 (Cpk ≥ 1.33)"
    elif cpk >= 1.0:
        capability = "尚可 (1.0 ≤ Cpk < 1.33)"
    else:
        capability = "需改善 (Cpk < 1.0)"

    print(f"  製程能力: {capability}")

    # ========================================
    # 3. 環境參數控制圖
    # ========================================
    for param in ['temperature', 'pressure', 'humidity']:
        param_mean = df[param].mean()
        param_std = df[param].std()

        ucl = param_mean + 3 * param_std
        lcl = param_mean - 3 * param_std

        out_of_control = df[(df[param] > ucl) | (df[param] < lcl)]

        results[f'{param}_control'] = {
            'mean': round(param_mean, 2),
            'std': round(param_std, 2),
            'ucl': round(ucl, 2),
            'lcl': round(lcl, 2),
            'out_of_control_count': len(out_of_control)
        }

    print(f"\n環境參數控制:")
    print(f"  溫度: {results['temperature_control']['mean']:.1f}°C ± {results['temperature_control']['std']:.1f}°C")
    print(f"  壓力: {results['pressure_control']['mean']:.1f} psi ± {results['pressure_control']['std']:.1f} psi")
    print(f"  濕度: {results['humidity_control']['mean']:.1f}% ± {results['humidity_control']['std']:.1f}%")

    return results


def calculate_cpk(data: np.ndarray, target: float, lsl: float, usl: float) -> float:
    """
    計算製程能力指數 (Cpk)

    Cpk 衡量製程產出是否符合規格要求:
    - Cpk ≥ 1.33: 優良
    - 1.0 ≤ Cpk < 1.33: 尚可
    - Cpk < 1.0: 需改善

    Args:
        data: 測量數據
        target: 目標值
        lsl: 規格下限
        usl: 規格上限

    Returns:
        Cpk值
    """
    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return float('inf')

    cpu = (usl - mean) / (3 * std)
    cpl = (mean - lsl) / (3 * std)

    cpk = min(cpu, cpl)
    return cpk


def quality_trend_analysis(df: pd.DataFrame) -> Dict[str, any]:
    """
    品質趨勢分析

    分析品質隨時間的變化趨勢:
    - 每日品質趨勢
    - 班次品質比較
    - 生產線品質比較
    - 缺陷率趨勢

    Args:
        df: 製造品質數據

    Returns:
        趨勢分析結果
    """
    print("\n" + "="*60)
    print("  品質趨勢分析")
    print("="*60)

    results = {}

    # ========================================
    # 1. 每日品質趨勢
    # ========================================
    daily_stats = df.groupby('production_date').agg({
        'quality_score': ['mean', 'std', 'min', 'max'],
        'defect_count': 'sum',
        'product_id': 'count'
    }).round(2)

    daily_stats.columns = ['avg_quality', 'std_quality', 'min_quality', 'max_quality',
                           'total_defects', 'total_products']

    daily_stats['defect_rate'] = (
        daily_stats['total_defects'] / daily_stats['total_products'] * 100
    ).round(2)

    # 計算趨勢 (線性回歸)
    dates_numeric = np.arange(len(daily_stats))
    quality_trend = np.polyfit(dates_numeric, daily_stats['avg_quality'], 1)[0]

    results['daily_trend'] = {
        'quality_slope': round(quality_trend, 4),
        'trend_direction': 'improving' if quality_trend > 0 else 'declining',
        'avg_quality': round(daily_stats['avg_quality'].mean(), 2),
        'avg_defect_rate': round(daily_stats['defect_rate'].mean(), 2)
    }

    print(f"\n每日品質趨勢:")
    print(f"  平均品質分數: {results['daily_trend']['avg_quality']:.2f}")
    print(f"  趨勢方向: {results['daily_trend']['trend_direction']}")
    print(f"  趨勢斜率: {quality_trend:+.4f} (每日)")
    print(f"  平均缺陷率: {results['daily_trend']['avg_defect_rate']:.2f}%")

    # ========================================
    # 2. 班次品質比較
    # ========================================
    shift_stats = df.groupby('shift').agg({
        'quality_score': 'mean',
        'defect_count': 'sum',
        'product_id': 'count'
    }).round(2)

    shift_stats['defect_rate'] = (
        shift_stats['defect_count'] / shift_stats['product_id'] * 100
    ).round(2)

    shift_stats = shift_stats.sort_values('quality_score', ascending=False)

    results['shift_comparison'] = shift_stats.to_dict('index')

    print(f"\n班次品質比較:")
    for shift, stats in shift_stats.iterrows():
        print(f"  {shift}:")
        print(f"    品質分數: {stats['quality_score']:.2f}")
        print(f"    缺陷率: {stats['defect_rate']:.2f}%")
        print(f"    產量: {int(stats['product_id'])}")

    # 識別問題班次
    worst_shift = shift_stats.index[-1]
    best_shift = shift_stats.index[0]
    quality_gap = shift_stats.loc[best_shift, 'quality_score'] - shift_stats.loc[worst_shift, 'quality_score']

    if quality_gap > 5:
        print(f"\n  ⚠️ 警告: {worst_shift} 品質顯著低於 {best_shift} ({quality_gap:.2f} 分)")

    # ========================================
    # 3. 生產線品質比較
    # ========================================
    line_stats = df.groupby('production_line').agg({
        'quality_score': 'mean',
        'defect_count': 'sum',
        'product_id': 'count'
    }).round(2)

    line_stats['defect_rate'] = (
        line_stats['defect_count'] / line_stats['product_id'] * 100
    ).round(2)

    line_stats = line_stats.sort_values('quality_score', ascending=False)

    results['line_comparison'] = line_stats.to_dict('index')

    print(f"\n生產線品質排名:")
    for i, (line, stats) in enumerate(line_stats.iterrows(), 1):
        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'  {i}.'
        print(f"  {medal} {line}: 品質 {stats['quality_score']:.2f}, 缺陷率 {stats['defect_rate']:.2f}%")

    # ========================================
    # 4. 缺陷類型分析
    # ========================================
    defect_analysis = df[df['defect_type'] != '無缺陷'].groupby('defect_type').agg({
        'product_id': 'count',
        'quality_score': 'mean'
    }).round(2)

    defect_analysis.columns = ['count', 'avg_quality']
    defect_analysis['percentage'] = (
        defect_analysis['count'] / defect_analysis['count'].sum() * 100
    ).round(2)

    defect_analysis = defect_analysis.sort_values('count', ascending=False)

    results['defect_types'] = defect_analysis.to_dict('index')

    print(f"\n主要缺陷類型 (柏拉圖分析):")
    cumulative = 0
    for defect, stats in defect_analysis.iterrows():
        cumulative += stats['percentage']
        bar = '█' * int(stats['percentage'] / 2)
        print(f"  {defect:12}: {int(stats['count']):4} ({stats['percentage']:5.1f}%) {bar} [累計: {cumulative:.1f}%]")

    return results


def root_cause_analysis(df: pd.DataFrame, spc_results: Dict) -> Dict[str, any]:
    """
    根因分析

    識別品質問題的根本原因:
    - 環境參數與品質的相關性
    - 高缺陷產品的共同特徵
    - 關鍵影響因素排名

    Args:
        df: 製造品質數據
        spc_results: SPC分析結果

    Returns:
        根因分析結果
    """
    print("\n" + "="*60)
    print("  根因分析 (Root Cause Analysis)")
    print("="*60)

    results = {}

    # ========================================
    # 1. 環境參數與品質相關性
    # ========================================
    environmental_params = ['temperature', 'pressure', 'humidity']

    correlations = {}
    for param in environmental_params:
        corr = df[param].corr(df['quality_score'])
        correlations[param] = round(corr, 3)

    results['correlations'] = correlations

    print(f"\n環境參數與品質分數相關性:")
    for param, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
        direction = "正相關" if corr > 0 else "負相關"
        strength = "強" if abs(corr) > 0.5 else ("中" if abs(corr) > 0.3 else "弱")
        print(f"  {param:12}: {corr:+.3f} ({strength}{direction})")

    # ========================================
    # 2. 低品質產品分析
    # ========================================
    # 定義低品質閾值 (低於平均 - 1個標準差)
    quality_threshold = df['quality_score'].mean() - df['quality_score'].std()
    low_quality = df[df['quality_score'] < quality_threshold]

    print(f"\n低品質產品分析 (品質分數 < {quality_threshold:.2f}):")
    print(f"  數量: {len(low_quality)} ({len(low_quality)/len(df)*100:.2f}%)")

    # 分析低品質產品的特徵
    print(f"\n  主要特徵:")

    # 生產線分布
    line_dist = low_quality['production_line'].value_counts()
    print(f"    問題生產線:")
    for line, count in line_dist.head(3).items():
        pct = count / len(low_quality) * 100
        print(f"      {line}: {count} ({pct:.1f}%)")

    # 班次分布
    shift_dist = low_quality['shift'].value_counts()
    print(f"    問題班次:")
    for shift, count in shift_dist.items():
        pct = count / len(low_quality) * 100
        print(f"      {shift}: {count} ({pct:.1f}%)")

    # 缺陷類型
    defect_dist = low_quality['defect_type'].value_counts()
    print(f"    主要缺陷:")
    for defect, count in defect_dist.head(3).items():
        pct = count / len(low_quality) * 100
        print(f"      {defect}: {count} ({pct:.1f}%)")

    # ========================================
    # 3. 環境參數異常分析
    # ========================================
    print(f"\n環境參數異常產品:")

    temp_abnormal = df[
        (df['temperature'] < 20) | (df['temperature'] > 25)
    ]
    print(f"  溫度異常: {len(temp_abnormal)} 產品")
    print(f"    平均品質: {temp_abnormal['quality_score'].mean():.2f}")

    pressure_abnormal = df[
        (df['pressure'] < 97) | (df['pressure'] > 103)
    ]
    print(f"  壓力異常: {len(pressure_abnormal)} 產品")
    print(f"    平均品質: {pressure_abnormal['quality_score'].mean():.2f}")

    humidity_abnormal = df[
        (df['humidity'] < 45) | (df['humidity'] > 55)
    ]
    print(f"  濕度異常: {len(humidity_abnormal)} 產品")
    print(f"    平均品質: {humidity_abnormal['quality_score'].mean():.2f}")

    results['environmental_impact'] = {
        'temperature': {
            'abnormal_count': len(temp_abnormal),
            'avg_quality': round(temp_abnormal['quality_score'].mean(), 2)
        },
        'pressure': {
            'abnormal_count': len(pressure_abnormal),
            'avg_quality': round(pressure_abnormal['quality_score'].mean(), 2)
        },
        'humidity': {
            'abnormal_count': len(humidity_abnormal),
            'avg_quality': round(humidity_abnormal['quality_score'].mean(), 2)
        }
    }

    # ========================================
    # 4. 關鍵影響因素排名
    # ========================================
    print(f"\n關鍵影響因素排名:")

    # 使用簡單的影響力評分
    impact_scores = {}

    # 相關性影響
    for param, corr in correlations.items():
        impact_scores[param] = abs(corr) * 100

    # 異常影響
    normal_quality = df['quality_score'].mean()

    temp_impact = abs(temp_abnormal['quality_score'].mean() - normal_quality) if len(temp_abnormal) > 0 else 0
    pressure_impact = abs(pressure_abnormal['quality_score'].mean() - normal_quality) if len(pressure_abnormal) > 0 else 0
    humidity_impact = abs(humidity_abnormal['quality_score'].mean() - normal_quality) if len(humidity_abnormal) > 0 else 0

    impact_scores['temperature_abnormality'] = temp_impact
    impact_scores['pressure_abnormality'] = pressure_impact
    impact_scores['humidity_abnormality'] = humidity_impact

    # 班次影響
    shift_quality_range = df.groupby('shift')['quality_score'].mean()
    shift_impact = shift_quality_range.max() - shift_quality_range.min()
    impact_scores['shift'] = shift_impact

    # 生產線影響
    line_quality_range = df.groupby('production_line')['quality_score'].mean()
    line_impact = line_quality_range.max() - line_quality_range.min()
    impact_scores['production_line'] = line_impact

    results['impact_ranking'] = impact_scores

    # 排序並顯示
    sorted_impacts = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)
    for i, (factor, score) in enumerate(sorted_impacts, 1):
        print(f"  {i}. {factor}: {score:.2f}")

    return results


def generate_improvement_recommendations(df: pd.DataFrame,
                                        spc_results: Dict,
                                        trend_results: Dict,
                                        rca_results: Dict) -> List[Dict]:
    """
    生成改善建議

    基於分析結果提供具體的改善建議

    Args:
        df: 製造品質數據
        spc_results: SPC分析結果
        trend_results: 趨勢分析結果
        rca_results: 根因分析結果

    Returns:
        改善建議列表
    """
    print("\n" + "="*60)
    print("  改善建議")
    print("="*60)

    recommendations = []

    # ========================================
    # 1. 基於SPC結果的建議
    # ========================================
    cpk = spc_results['dimension_x_control']['cpk']

    if cpk < 1.0:
        recommendations.append({
            'priority': 'HIGH',
            'category': '製程能力',
            'issue': f'Dimension X 的 Cpk ({cpk:.3f}) 低於 1.0',
            'recommendation': '立即調查並改善製程變異，考慮：\n'
                            '  - 校準生產設備\n'
                            '  - 檢查刀具磨損\n'
                            '  - 審查操作標準\n'
                            '  - 加強製程監控',
            'expected_impact': '提升 Cpk 至 1.33 以上，減少不良品 50%'
        })

    # ========================================
    # 2. 基於趨勢分析的建議
    # ========================================
    # 班次問題
    shift_stats = trend_results['shift_comparison']
    shift_quality = {k: v['quality_score'] for k, v in shift_stats.items()}
    worst_shift = min(shift_quality.keys(), key=lambda x: shift_quality[x])
    best_shift = max(shift_quality.keys(), key=lambda x: shift_quality[x])

    quality_gap = shift_quality[best_shift] - shift_quality[worst_shift]

    if quality_gap > 5:
        recommendations.append({
            'priority': 'HIGH',
            'category': '班次管理',
            'issue': f'{worst_shift} 品質顯著低於 {best_shift} (差距 {quality_gap:.2f} 分)',
            'recommendation': f'改善 {worst_shift} 的運作:\n'
                            f'  - 對比 {best_shift} 與 {worst_shift} 的作業差異\n'
                            '  - 加強培訓和監督\n'
                            '  - 檢查設備保養時間是否影響該班次\n'
                            '  - 考慮調整人員配置',
            'expected_impact': f'將 {worst_shift} 品質提升至接近 {best_shift} 水平'
        })

    # 生產線問題
    line_stats = trend_results['line_comparison']
    line_quality = {k: v['quality_score'] for k, v in line_stats.items()}
    worst_line = min(line_quality.keys(), key=lambda x: line_quality[x])
    best_line = max(line_quality.keys(), key=lambda x: line_quality[x])

    line_gap = line_quality[best_line] - line_quality[worst_line]

    if line_gap > 5:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '生產線優化',
            'issue': f'{worst_line} 品質低於 {best_line} (差距 {line_gap:.2f} 分)',
            'recommendation': f'優化 {worst_line}:\n'
                            '  - 進行設備健檢和校準\n'
                            f'  - 學習 {best_line} 的最佳實踐\n'
                            '  - 檢查原料批次是否有差異\n'
                            '  - 考慮設備升級或更換',
            'expected_impact': '減少生產線間的品質變異'
        })

    # ========================================
    # 3. 基於根因分析的建議
    # ========================================
    # 找出最大影響因素
    top_impact = max(rca_results['impact_ranking'].items(), key=lambda x: x[1])

    if top_impact[0] == 'temperature':
        recommendations.append({
            'priority': 'HIGH',
            'category': '環境控制',
            'issue': '溫度是品質的關鍵影響因素',
            'recommendation': '加強溫度控制:\n'
                            '  - 安裝更精確的溫控系統\n'
                            '  - 設定溫度警報 (20-25°C)\n'
                            '  - 定期校準溫度感測器\n'
                            '  - 檢查空調系統效能',
            'expected_impact': '減少溫度引起的品質變異 30%'
        })

    elif top_impact[0] == 'pressure':
        recommendations.append({
            'priority': 'HIGH',
            'category': '環境控制',
            'issue': '壓力是品質的關鍵影響因素',
            'recommendation': '改善壓力控制:\n'
                            '  - 升級壓力調節系統\n'
                            '  - 設定壓力警報 (97-103 psi)\n'
                            '  - 檢查壓縮機效能\n'
                            '  - 定期保養壓力設備',
            'expected_impact': '提升製程穩定性，減少壓力波動'
        })

    # ========================================
    # 4. 缺陷類型建議
    # ========================================
    top_defect = list(trend_results['defect_types'].keys())[0]
    defect_count = trend_results['defect_types'][top_defect]['count']

    defect_recommendations = {
        '刮痕': '改善處理流程，檢查傳送帶表面，培訓操作員小心處理',
        '變形': '檢查冷卻過程，調整模具設計，控制溫度均勻性',
        '尺寸誤差': '校準測量設備，檢查模具磨損，加強製程監控',
        '顏色不均': '檢查塗裝設備，控制塗料濃度，改善乾燥過程',
        '裂紋': '檢查材料品質，調整成型參數，改善冷卻速率'
    }

    if top_defect in defect_recommendations:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '缺陷預防',
            'issue': f'{top_defect} 是最常見的缺陷類型 ({int(defect_count)} 件)',
            'recommendation': defect_recommendations[top_defect],
            'expected_impact': f'減少 {top_defect} 發生率 40%'
        })

    # ========================================
    # 5. 一般改善建議
    # ========================================
    avg_quality = df['quality_score'].mean()

    if avg_quality < 85:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '整體品質',
            'issue': f'整體平均品質分數 ({avg_quality:.2f}) 低於目標 (85)',
            'recommendation': '全面品質改善計劃:\n'
                            '  - 建立品質管理系統 (QMS)\n'
                            '  - 實施全面品質管理 (TQM)\n'
                            '  - 定期品質審核\n'
                            '  - 員工品質意識培訓',
            'expected_impact': '整體品質提升 10-15%'
        })

    # 顯示建議
    recommendations.sort(key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])

    for i, rec in enumerate(recommendations, 1):
        priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[rec['priority']]
        print(f"\n建議 {i} {priority_icon} [{rec['priority']}] {rec['category']}")
        print(f"問題: {rec['issue']}")
        print(f"建議:\n{rec['recommendation']}")
        print(f"預期效果: {rec['expected_impact']}")

    return recommendations


def main():
    """執行完整的製造業品質控制分析"""
    print("="*80)
    print(" "*20 + "製造業品質控制分析")
    print("="*80)

    # ========================================
    # 1. 生成/載入數據
    # ========================================
    print("\n[1/6] 準備製造數據...")

    df = generate_manufacturing_data(
        n_products=5000,
        n_production_lines=5,
        n_days=30
    )

    print(f"  ✓ 產品數量: {len(df):,}")
    print(f"  ✓ 生產線數: {df['production_line'].nunique()}")
    print(f"  ✓ 生產天數: {df['production_date'].nunique()}")
    print(f"  ✓ 平均品質分數: {df['quality_score'].mean():.2f}")
    print(f"  ✓ 缺陷產品數: {len(df[df['defect_count'] > 0])} ({len(df[df['defect_count'] > 0])/len(df)*100:.1f}%)")

    # 數據驗證
    validator = DataValidator(df)
    missing_check = validator.check_missing_values()

    if missing_check['total_missing_cells'] > 0:
        print(f"\n  ⚠️ 警告: 發現 {missing_check['total_missing_cells']} 個缺失值")
    else:
        print(f"  ✓ 數據完整性檢查通過")

    # ========================================
    # 2. 缺陷模式聚類分析
    # ========================================
    print("\n[2/6] 執行缺陷模式聚類分析...")

    df_clustered, clusterer = perform_defect_clustering(df)

    # ========================================
    # 3. 統計製程控制分析
    # ========================================
    print("\n[3/6] 執行統計製程控制分析...")

    spc_results = statistical_process_control_analysis(df)

    # ========================================
    # 4. 品質趨勢分析
    # ========================================
    print("\n[4/6] 執行品質趨勢分析...")

    trend_results = quality_trend_analysis(df)

    # ========================================
    # 5. 根因分析
    # ========================================
    print("\n[5/6] 執行根因分析...")

    rca_results = root_cause_analysis(df, spc_results)

    # ========================================
    # 6. 生成改善建議
    # ========================================
    print("\n[6/6] 生成改善建議...")

    recommendations = generate_improvement_recommendations(
        df, spc_results, trend_results, rca_results
    )

    # ========================================
    # 總結報告
    # ========================================
    print("\n" + "="*80)
    print(" "*25 + "分析摘要")
    print("="*80)

    print(f"""
    📊 數據概覽:
       總產品數: {len(df):,}
       分析期間: {df['production_date'].min()} ~ {df['production_date'].max()}
       平均品質分數: {df['quality_score'].mean():.2f}

    🔍 關鍵發現:
       缺陷產品: {len(df[df['defect_count'] > 0]):,} ({len(df[df['defect_count'] > 0])/len(df)*100:.1f}%)
       識別缺陷群組: {clusterer.n_clusters_} 個
       製程能力 (Cpk): {spc_results['dimension_x_control']['cpk']:.3f}
       品質趨勢: {trend_results['daily_trend']['trend_direction']}

    ⚠️  需關注問題:
       SPC 異常點: {spc_results['quality_control']['out_of_control_count']} 個
       低品質產品: {len(df[df['quality_score'] < 70])} 個
       關鍵影響因素: {list(rca_results['impact_ranking'].keys())[0]}

    💡 改善建議: {len(recommendations)} 項
       高優先級: {len([r for r in recommendations if r['priority'] == 'HIGH'])} 項
       中優先級: {len([r for r in recommendations if r['priority'] == 'MEDIUM'])} 項
    """)

    # 保存結果
    output_dir = 'data/outputs'
    try:
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 保存數據
        df_clustered.to_csv(f'{output_dir}/manufacturing_quality_analysis.csv', index=False)
        print(f"\n  📁 分析結果已保存至: {output_dir}/manufacturing_quality_analysis.csv")

        # 保存報告
        report_path = f'{output_dir}/quality_control_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(" "*20 + "製造業品質控制分析報告\n")
            f.write(" "*25 + datetime.now().strftime('%Y-%m-%d %H:%M') + "\n")
            f.write("="*80 + "\n\n")

            f.write("一、SPC分析結果\n")
            f.write("-"*40 + "\n")
            for key, value in spc_results.items():
                f.write(f"{key}: {value}\n")

            f.write("\n二、趨勢分析結果\n")
            f.write("-"*40 + "\n")
            for key, value in trend_results.items():
                f.write(f"{key}: {value}\n")

            f.write("\n三、根因分析結果\n")
            f.write("-"*40 + "\n")
            for key, value in rca_results.items():
                f.write(f"{key}: {value}\n")

            f.write("\n四、改善建議\n")
            f.write("-"*40 + "\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"\n建議 {i} [{rec['priority']}] {rec['category']}\n")
                f.write(f"問題: {rec['issue']}\n")
                f.write(f"建議: {rec['recommendation']}\n")
                f.write(f"預期效果: {rec['expected_impact']}\n")

        print(f"  📁 分析報告已保存至: {report_path}")

    except Exception as e:
        print(f"\n  ⚠️ 保存結果時發生錯誤: {e}")

    print("\n" + "="*80)
    print(" "*30 + "分析完成")
    print("="*80)

    return {
        'data': df_clustered,
        'clusterer': clusterer,
        'spc_results': spc_results,
        'trend_results': trend_results,
        'rca_results': rca_results,
        'recommendations': recommendations
    }


if __name__ == "__main__":
    results = main()
