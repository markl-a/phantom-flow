"""
IoT 感測器數據分析範例

這個範例展示如何分析 IoT 感測器數據，包含：
- 設備健康監控
- 異常檢測
- 預測性維護
- 數據品質分析

真實應用場景:
- 工業設備監控
- 智慧城市管理
- 農業環境監測
- 建築物管理系統
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

try:
    from data_analysis_chatbots import setup_logging
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class IoTSensorAnalyzer:
    """
    IoT 感測器分析器

    提供完整的感測器數據分析功能:
    - 設備健康評估
    - 異常檢測
    - 預測性維護
    - 數據品質監控
    """

    def __init__(self, sensor_data_df: pd.DataFrame,
                 devices_df: Optional[pd.DataFrame] = None,
                 maintenance_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            sensor_data_df: 感測器數據DataFrame
            devices_df: 設備資訊DataFrame (可選)
            maintenance_df: 維護記錄DataFrame (可選)
        """
        self.sensor_data = sensor_data_df.copy()
        self.devices = devices_df
        self.maintenance = maintenance_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'timestamp' in self.sensor_data.columns:
            self.sensor_data['timestamp'] = pd.to_datetime(self.sensor_data['timestamp'])
            self.sensor_data['hour'] = self.sensor_data['timestamp'].dt.hour
            self.sensor_data['date'] = self.sensor_data['timestamp'].dt.date

    def assess_device_health(self) -> pd.DataFrame:
        """評估設備健康狀態"""
        df = self.sensor_data

        # 按設備計算統計
        device_stats = df.groupby('device_id').agg({
            'value': ['mean', 'std', 'min', 'max', 'count'],
            'timestamp': ['min', 'max']
        })
        device_stats.columns = ['avg_value', 'std_value', 'min_value', 'max_value',
                                'reading_count', 'first_reading', 'last_reading']

        # 計算數據完整性
        expected_readings = (
            (device_stats['last_reading'] - device_stats['first_reading']).dt.total_seconds() / 300
        ).clip(lower=1)  # 假設5分鐘一次讀數
        device_stats['data_completeness'] = (
            device_stats['reading_count'] / expected_readings * 100
        ).clip(0, 100).round(1)

        # 計算異常率
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id]
            mean_val = device_data['value'].mean()
            std_val = device_data['value'].std()

            if std_val > 0:
                z_scores = (device_data['value'] - mean_val) / std_val
                anomaly_rate = (z_scores.abs() > 3).mean() * 100
            else:
                anomaly_rate = 0

            device_stats.loc[device_id, 'anomaly_rate'] = round(anomaly_rate, 2)

        # 計算健康分數
        device_stats['health_score'] = (
            device_stats['data_completeness'] * 0.4 +
            (100 - device_stats['anomaly_rate'] * 10).clip(0, 100) * 0.4 +
            (100 - device_stats['std_value'] / device_stats['avg_value'].abs().replace(0, 1) * 10).clip(0, 100) * 0.2
        ).round(1)

        device_stats['health_status'] = pd.cut(
            device_stats['health_score'],
            bins=[-1, 40, 60, 80, 100],
            labels=['Critical', 'Poor', 'Fair', 'Good']
        )

        return device_stats

    def detect_anomalies(self, method: str = 'zscore') -> pd.DataFrame:
        """檢測異常讀數"""
        df = self.sensor_data.copy()

        if method == 'zscore':
            # 按設備計算 Z-Score
            device_stats = df.groupby('device_id')['value'].agg(['mean', 'std'])
            df = df.merge(device_stats, left_on='device_id', right_index=True)
            df['z_score'] = (df['value'] - df['mean']) / df['std'].replace(0, 1)
            df['is_anomaly'] = df['z_score'].abs() > 3

        elif method == 'iqr':
            # IQR 方法
            device_stats = df.groupby('device_id')['value'].agg(
                lambda x: pd.Series({
                    'q1': x.quantile(0.25),
                    'q3': x.quantile(0.75)
                })
            ).unstack()
            device_stats['iqr'] = device_stats['q3'] - device_stats['q1']
            device_stats['lower'] = device_stats['q1'] - 1.5 * device_stats['iqr']
            device_stats['upper'] = device_stats['q3'] + 1.5 * device_stats['iqr']

            df = df.merge(device_stats[['lower', 'upper']], left_on='device_id', right_index=True)
            df['is_anomaly'] = (df['value'] < df['lower']) | (df['value'] > df['upper'])
            df['z_score'] = 0  # Placeholder

        # 分類異常類型
        df['anomaly_type'] = np.where(
            ~df['is_anomaly'], 'Normal',
            np.where(df['value'] > df['mean'] if method == 'zscore' else df['value'] > df['upper'],
                    'High', 'Low')
        )

        anomalies = df[df['is_anomaly']][
            ['device_id', 'timestamp', 'value', 'z_score', 'anomaly_type']
        ].sort_values('timestamp', ascending=False)

        return anomalies

    def predict_maintenance_needs(self) -> pd.DataFrame:
        """預測維護需求"""
        df = self.sensor_data
        health = self.assess_device_health()

        predictions = []

        for device_id, device_health in health.iterrows():
            device_data = df[df['device_id'] == device_id].sort_values('timestamp')

            # 趨勢分析
            if len(device_data) > 100:
                recent = device_data.tail(100)
                older = device_data.head(100)

                recent_avg = recent['value'].mean()
                older_avg = older['value'].mean()
                trend = (recent_avg - older_avg) / older_avg * 100 if older_avg != 0 else 0

                recent_std = recent['value'].std()
                older_std = older['value'].std()
                variability_change = (recent_std - older_std) / older_std * 100 if older_std != 0 else 0
            else:
                trend = 0
                variability_change = 0

            # 計算故障風險
            risk_score = 0

            # 健康分數低
            if device_health['health_score'] < 60:
                risk_score += 30

            # 異常率高
            if device_health['anomaly_rate'] > 5:
                risk_score += 25

            # 趨勢異常
            if abs(trend) > 20:
                risk_score += 20

            # 波動增加
            if variability_change > 50:
                risk_score += 15

            # 數據不完整
            if device_health['data_completeness'] < 90:
                risk_score += 10

            # 預測維護時間
            if risk_score >= 70:
                maintenance_urgency = 'Immediate'
                days_to_maintenance = 0
            elif risk_score >= 50:
                maintenance_urgency = 'Within 7 days'
                days_to_maintenance = 7
            elif risk_score >= 30:
                maintenance_urgency = 'Within 30 days'
                days_to_maintenance = 30
            else:
                maintenance_urgency = 'Scheduled'
                days_to_maintenance = 90

            predictions.append({
                'device_id': device_id,
                'health_score': device_health['health_score'],
                'risk_score': min(risk_score, 100),
                'trend_pct': round(trend, 1),
                'variability_change_pct': round(variability_change, 1),
                'maintenance_urgency': maintenance_urgency,
                'days_to_maintenance': days_to_maintenance,
                'recommended_action': self._get_maintenance_action(risk_score, trend, device_health)
            })

        return pd.DataFrame(predictions).sort_values('risk_score', ascending=False)

    def _get_maintenance_action(self, risk_score: float, trend: float, health: pd.Series) -> str:
        """根據設備狀態生成維護建議"""
        if risk_score >= 70:
            return "立即檢查設備，可能需要更換或維修"
        elif risk_score >= 50:
            if trend > 20:
                return "讀數持續上升，檢查校準和連接"
            elif trend < -20:
                return "讀數持續下降，檢查感測器靈敏度"
            else:
                return "安排預防性維護檢查"
        elif risk_score >= 30:
            return "列入下次定期維護計劃"
        else:
            return "正常運作，持續監控"

    def analyze_data_quality(self) -> Dict[str, any]:
        """分析數據品質"""
        df = self.sensor_data
        results = {}

        # 整體統計
        results['total_readings'] = len(df)
        results['total_devices'] = df['device_id'].nunique()
        results['date_range'] = {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat()
        }

        # 缺失值分析
        results['missing_values'] = {
            col: df[col].isna().sum() for col in df.columns
        }

        # 數據連續性檢查
        continuity_issues = []
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id].sort_values('timestamp')
            if len(device_data) > 1:
                time_diffs = device_data['timestamp'].diff().dropna()
                expected_interval = time_diffs.median()

                gaps = time_diffs[time_diffs > expected_interval * 2]
                if len(gaps) > 0:
                    continuity_issues.append({
                        'device_id': device_id,
                        'gap_count': len(gaps),
                        'max_gap_minutes': gaps.max().total_seconds() / 60
                    })

        results['continuity_issues'] = continuity_issues

        # 數據範圍檢查
        out_of_range = []
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id]
            sensor_type = device_data['sensor_type'].iloc[0] if 'sensor_type' in device_data.columns else 'unknown'

            # 根據感測器類型定義合理範圍
            ranges = {
                'temperature': (-40, 100),
                'humidity': (0, 100),
                'pressure': (800, 1200),
                'vibration': (0, 100),
                'voltage': (0, 500)
            }

            if sensor_type in ranges:
                min_val, max_val = ranges[sensor_type]
                invalid = device_data[(device_data['value'] < min_val) | (device_data['value'] > max_val)]
                if len(invalid) > 0:
                    out_of_range.append({
                        'device_id': device_id,
                        'sensor_type': sensor_type,
                        'invalid_count': len(invalid),
                        'invalid_pct': len(invalid) / len(device_data) * 100
                    })

        results['out_of_range_data'] = out_of_range

        # 重複數據檢查
        duplicates = df.duplicated(subset=['device_id', 'timestamp']).sum()
        results['duplicate_readings'] = duplicates

        # 數據品質分數
        quality_score = 100
        quality_score -= min(20, len(continuity_issues) * 2)  # 連續性問題
        quality_score -= min(20, len(out_of_range) * 3)  # 超範圍問題
        quality_score -= min(10, duplicates / len(df) * 100)  # 重複問題
        quality_score -= min(10, sum(results['missing_values'].values()) / len(df) * 100)  # 缺失值

        results['quality_score'] = max(0, round(quality_score, 1))
        results['quality_grade'] = (
            'Excellent' if quality_score >= 90 else
            ('Good' if quality_score >= 75 else
             ('Fair' if quality_score >= 60 else 'Poor'))
        )

        return results

    def get_real_time_alerts(self) -> List[Dict]:
        """生成即時警報"""
        health = self.assess_device_health()
        anomalies = self.detect_anomalies()
        maintenance = self.predict_maintenance_needs()

        alerts = []

        # 設備健康警報
        critical_devices = health[health['health_status'] == 'Critical']
        for device_id, device in critical_devices.iterrows():
            alerts.append({
                'type': 'CRITICAL',
                'device_id': device_id,
                'message': f"設備 {device_id} 健康狀態嚴重異常",
                'details': f"健康分數: {device['health_score']}, 異常率: {device['anomaly_rate']}%",
                'timestamp': datetime.now().isoformat(),
                'action': 'Immediate inspection required'
            })

        # 最近異常警報
        recent_anomalies = anomalies.head(10)
        for _, anom in recent_anomalies.iterrows():
            alerts.append({
                'type': 'WARNING',
                'device_id': anom['device_id'],
                'message': f"設備 {anom['device_id']} 檢測到異常讀數",
                'details': f"值: {anom['value']}, Z-Score: {anom['z_score']:.2f}",
                'timestamp': anom['timestamp'].isoformat(),
                'action': 'Monitor and investigate'
            })

        # 維護警報
        urgent_maintenance = maintenance[maintenance['maintenance_urgency'] == 'Immediate']
        for _, maint in urgent_maintenance.iterrows():
            alerts.append({
                'type': 'MAINTENANCE',
                'device_id': maint['device_id'],
                'message': f"設備 {maint['device_id']} 需要立即維護",
                'details': f"風險分數: {maint['risk_score']}, 建議: {maint['recommended_action']}",
                'timestamp': datetime.now().isoformat(),
                'action': maint['recommended_action']
            })

        # 按嚴重性排序
        priority = {'CRITICAL': 0, 'WARNING': 1, 'MAINTENANCE': 2}
        alerts.sort(key=lambda x: priority.get(x['type'], 3))

        return alerts

    def generate_report(self) -> str:
        """生成完整的 IoT 分析報告"""
        health = self.assess_device_health()
        quality = self.analyze_data_quality()
        maintenance = self.predict_maintenance_needs()
        alerts = self.get_real_time_alerts()

        report = f"""
{'='*80}
                    IoT 感測器分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、系統概覽
{'='*40}
  設備總數: {quality['total_devices']}
  數據讀數: {quality['total_readings']:,}
  數據品質: {quality['quality_grade']} ({quality['quality_score']}/100)
  活躍警報: {len(alerts)}

二、設備健康狀態
{'='*40}
"""
        health_dist = health['health_status'].value_counts()
        for status in ['Good', 'Fair', 'Poor', 'Critical']:
            count = health_dist.get(status, 0)
            pct = count / len(health) * 100
            icon = {'Good': '🟢', 'Fair': '🟡', 'Poor': '🟠', 'Critical': '🔴'}[status]
            bar = '█' * int(pct / 2)
            report += f"  {icon} {status:10}: {count:3} ({pct:5.1f}%) {bar}\n"

        report += f"""
  需關注的設備:
"""
        for device_id, device in health[health['health_status'].isin(['Poor', 'Critical'])].head(5).iterrows():
            report += f"    - {device_id}: 健康分數 {device['health_score']}, "
            report += f"異常率 {device['anomaly_rate']}%\n"

        report += f"""
三、數據品質分析
{'='*40}
  品質分數: {quality['quality_score']}/100 ({quality['quality_grade']})
  重複數據: {quality['duplicate_readings']}
  連續性問題: {len(quality['continuity_issues'])} 個設備
  超範圍數據: {len(quality['out_of_range_data'])} 個設備

四、預測性維護
{'='*40}
"""
        urgency_counts = maintenance['maintenance_urgency'].value_counts()
        for urgency in ['Immediate', 'Within 7 days', 'Within 30 days', 'Scheduled']:
            count = urgency_counts.get(urgency, 0)
            icon = {'Immediate': '🔴', 'Within 7 days': '🟠',
                   'Within 30 days': '🟡', 'Scheduled': '🟢'}[urgency]
            report += f"  {icon} {urgency}: {count} 個設備\n"

        report += f"""
  高風險設備:
"""
        for _, maint in maintenance[maintenance['risk_score'] >= 50].head(5).iterrows():
            report += f"    - {maint['device_id']}: 風險 {maint['risk_score']}, "
            report += f"趨勢 {maint['trend_pct']:+.1f}%\n"
            report += f"      建議: {maint['recommended_action']}\n"

        report += f"""
五、即時警報 (Top 10)
{'='*40}
"""
        for alert in alerts[:10]:
            icon = {'CRITICAL': '🔴', 'WARNING': '🟡', 'MAINTENANCE': '🔧'}[alert['type']]
            report += f"  {icon} [{alert['type']}] {alert['device_id']}\n"
            report += f"     {alert['message']}\n"
            report += f"     行動: {alert['action']}\n"

        report += f"""
六、建議行動
{'='*40}

1. 立即行動:
   - 檢查 {len(health[health['health_status'] == 'Critical'])} 個嚴重異常設備
   - 處理 {len(maintenance[maintenance['maintenance_urgency'] == 'Immediate'])} 個緊急維護需求
   - 調查最新的異常讀數

2. 短期計劃 (1週內):
   - 安排預防性維護
   - 修復數據連續性問題
   - 校準異常感測器

3. 長期改進:
   - 升級老舊設備
   - 優化數據收集頻率
   - 建立更完善的監控系統

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_iot_data(n_devices: int = 50,
                      n_days: int = 30,
                      seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """生成模擬 IoT 數據"""
    np.random.seed(seed)
    today = datetime.now().replace(minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=n_days)

    # 設備資訊
    sensor_types = ['temperature', 'humidity', 'pressure', 'vibration', 'voltage']
    locations = ['Factory A', 'Factory B', 'Warehouse', 'Office', 'Outdoor']

    devices = []
    for i in range(1, n_devices + 1):
        sensor_type = np.random.choice(sensor_types)
        devices.append({
            'device_id': f'DEV{i:04d}',
            'sensor_type': sensor_type,
            'location': np.random.choice(locations),
            'install_date': today - timedelta(days=np.random.randint(30, 1000)),
            'manufacturer': np.random.choice(['SensorCo', 'IoTech', 'SmartSense', 'DataNode'])
        })
    devices_df = pd.DataFrame(devices)

    # 感測器讀數 (每5分鐘)
    sensor_data = []

    # 各類感測器的基準值和標準差
    sensor_params = {
        'temperature': {'mean': 25, 'std': 5, 'drift': 0.1},
        'humidity': {'mean': 60, 'std': 10, 'drift': 0.05},
        'pressure': {'mean': 1013, 'std': 10, 'drift': 0.02},
        'vibration': {'mean': 20, 'std': 8, 'drift': 0.15},
        'voltage': {'mean': 220, 'std': 5, 'drift': 0.03}
    }

    for device in devices:
        device_id = device['device_id']
        sensor_type = device['sensor_type']
        params = sensor_params[sensor_type]

        # 設備的個體差異
        device_offset = np.random.normal(0, params['std'] * 0.3)
        device_health = np.random.uniform(0.7, 1.0)  # 設備健康度影響穩定性

        current_time = start_date
        while current_time < today:
            # 基礎值
            base_value = params['mean'] + device_offset

            # 時間變化 (模擬日變化)
            hour = current_time.hour
            if sensor_type == 'temperature':
                time_effect = 5 * np.sin((hour - 6) * np.pi / 12)  # 白天較高
            else:
                time_effect = 0

            # 隨機波動
            noise = np.random.normal(0, params['std'] * (2 - device_health))

            # 計算值
            value = base_value + time_effect + noise

            # 偶爾添加異常
            if np.random.random() < 0.01:  # 1% 異常率
                value += np.random.choice([-1, 1]) * params['std'] * 5

            # 模擬數據缺失 (1% 機率)
            if np.random.random() > 0.01:
                sensor_data.append({
                    'reading_id': f'R{len(sensor_data)+1:08d}',
                    'device_id': device_id,
                    'sensor_type': sensor_type,
                    'timestamp': current_time,
                    'value': round(value, 2),
                    'unit': {'temperature': '°C', 'humidity': '%', 'pressure': 'hPa',
                            'vibration': 'mm/s', 'voltage': 'V'}[sensor_type],
                    'quality': np.random.choice(['good', 'acceptable', 'poor'],
                                               p=[0.9, 0.08, 0.02])
                })

            current_time += timedelta(minutes=5)

    sensor_data_df = pd.DataFrame(sensor_data)

    # 維護記錄
    maintenance = []
    for device in devices:
        n_maintenance = np.random.randint(0, 5)
        for _ in range(n_maintenance):
            maintenance.append({
                'maintenance_id': f'M{len(maintenance)+1:05d}',
                'device_id': device['device_id'],
                'maintenance_date': start_date + timedelta(days=np.random.randint(0, n_days)),
                'maintenance_type': np.random.choice(['Calibration', 'Repair', 'Replacement', 'Inspection']),
                'duration_hours': np.random.uniform(0.5, 8),
                'cost': np.random.uniform(100, 2000)
            })

    maintenance_df = pd.DataFrame(maintenance)

    return sensor_data_df, devices_df, maintenance_df


def main():
    """執行 IoT 感測器分析範例"""
    print("="*80)
    print(" "*20 + "IoT 感測器分析")
    print("="*80)

    # 準備數據
    print("\n[1/4] 準備 IoT 數據...")
    sensor_data, devices, maintenance = generate_iot_data(n_devices=50, n_days=30)

    print(f"  ✓ 設備數: {len(devices)}")
    print(f"  ✓ 數據讀數: {len(sensor_data):,}")
    print(f"  ✓ 維護記錄: {len(maintenance)}")

    # 初始化分析器
    print("\n[2/4] 初始化分析器...")
    analyzer = IoTSensorAnalyzer(sensor_data, devices, maintenance)
    print("  ✓ 分析器初始化完成")

    # 健康評估
    print("\n[3/4] 評估設備健康...")
    health = analyzer.assess_device_health()
    health_dist = health['health_status'].value_counts()
    print(f"\n  📊 設備健康分佈:")
    for status in ['Good', 'Fair', 'Poor', 'Critical']:
        count = health_dist.get(status, 0)
        print(f"     {status}: {count}")

    # 預測維護
    print("\n[4/4] 預測維護需求...")
    predictions = analyzer.predict_maintenance_needs()
    urgent = len(predictions[predictions['maintenance_urgency'] == 'Immediate'])
    print(f"\n  🔧 需立即維護: {urgent} 個設備")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/iot_sensor_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/iot_sensor_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
