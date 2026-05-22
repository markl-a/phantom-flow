"""
醫療保健患者分析範例

這個範例展示如何分析醫療數據，包含：
- 患者風險評估
- 再入院預測
- 治療效果分析
- 醫療資源利用分析

真實應用場景:
- 醫院患者管理
- 保險公司風險評估
- 公共衛生政策制定
- 臨床決策支援系統

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
    from data_analysis_chatbots.clustering import KMeansClusterer
except ImportError:
    import sys
    sys.path.insert(0, '..')


class HealthcareAnalyzer:
    """
    醫療保健分析器

    提供完整的患者數據分析功能:
    - 患者風險分層
    - 再入院風險預測
    - 治療效果評估
    - 資源利用分析
    """

    def __init__(self, patients_df: pd.DataFrame,
                 admissions_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            patients_df: 患者主檔DataFrame
            admissions_df: 入院記錄DataFrame (可選)
        """
        self.patients = patients_df.copy()
        self.admissions = admissions_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'birth_date' in self.patients.columns:
            self.patients['birth_date'] = pd.to_datetime(self.patients['birth_date'])
            self.patients['age'] = (
                datetime.now() - self.patients['birth_date']
            ).dt.days / 365

    def calculate_patient_risk_score(self) -> pd.DataFrame:
        """
        計算患者風險分數

        考慮因素:
        - 年齡
        - 慢性病數量
        - BMI
        - 吸煙/飲酒習慣
        - 過去入院次數
        """
        df = self.patients.copy()
        risk_score = pd.Series(0.0, index=df.index)

        # 年齡風險
        if 'age' in df.columns:
            age_risk = np.where(df['age'] >= 75, 30,
                               np.where(df['age'] >= 65, 20,
                                       np.where(df['age'] >= 50, 10, 5)))
            risk_score += age_risk

        # 慢性病風險
        if 'chronic_conditions' in df.columns:
            chronic_risk = df['chronic_conditions'] * 10
            risk_score += chronic_risk.clip(upper=40)

        # BMI 風險
        if 'bmi' in df.columns:
            bmi_risk = np.where(df['bmi'] >= 35, 20,
                               np.where(df['bmi'] >= 30, 15,
                                       np.where((df['bmi'] < 18.5), 10, 5)))
            risk_score += bmi_risk

        # 吸煙風險
        if 'smoker' in df.columns:
            smoke_risk = np.where(df['smoker'], 15, 0)
            risk_score += smoke_risk

        # 過去入院次數
        if 'prev_admissions_year' in df.columns:
            admit_risk = df['prev_admissions_year'] * 8
            risk_score += admit_risk.clip(upper=25)

        # 標準化到0-100
        risk_score = (risk_score / risk_score.max() * 100).clip(0, 100)

        df['risk_score'] = risk_score.round(1)
        df['risk_category'] = pd.cut(
            df['risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['Low', 'Moderate', 'High', 'Very High']
        )

        return df

    def predict_readmission_risk(self) -> pd.DataFrame:
        """
        預測30天再入院風險

        基於LACE指標:
        - Length of stay (住院天數)
        - Acuity of admission (急性入院)
        - Comorbidities (共病指數)
        - Emergency visits (急診次數)
        """
        if self.admissions is None:
            return pd.DataFrame()

        df = self.admissions.copy()

        # 計算LACE分數
        lace_score = pd.Series(0, index=df.index)

        # L: Length of stay
        if 'length_of_stay' in df.columns:
            los = df['length_of_stay']
            l_score = np.where(los >= 14, 7,
                              np.where(los >= 7, 5,
                                      np.where(los >= 4, 4,
                                              np.where(los >= 3, 3,
                                                      np.where(los >= 2, 2,
                                                              np.where(los >= 1, 1, 0))))))
            lace_score += l_score

        # A: Acuity (急性入院)
        if 'admission_type' in df.columns:
            a_score = np.where(df['admission_type'] == 'Emergency', 3, 0)
            lace_score += a_score

        # C: Comorbidity (Charlson指數)
        if 'charlson_index' in df.columns:
            c_score = df['charlson_index'].clip(upper=5)
            lace_score += c_score

        # E: Emergency visits
        if 'ed_visits_6months' in df.columns:
            e_score = np.where(df['ed_visits_6months'] >= 4, 4,
                              np.where(df['ed_visits_6months'] >= 3, 3,
                                      np.where(df['ed_visits_6months'] >= 2, 2,
                                              np.where(df['ed_visits_6months'] >= 1, 1, 0))))
            lace_score += e_score

        df['lace_score'] = lace_score
        df['readmission_risk'] = pd.cut(
            lace_score,
            bins=[-1, 4, 9, float('inf')],
            labels=['Low (<5)', 'Moderate (5-9)', 'High (10+)']
        )

        # 轉換為百分比風險
        df['readmission_probability'] = (lace_score / 19 * 100).round(1).clip(upper=95)

        return df

    def analyze_treatment_outcomes(self) -> Dict[str, pd.DataFrame]:
        """分析治療效果"""
        if self.admissions is None:
            return {}

        results = {}

        # 按診斷分析
        if 'primary_diagnosis' in self.admissions.columns:
            diag_outcomes = self.admissions.groupby('primary_diagnosis').agg({
                'length_of_stay': ['mean', 'median', 'std'],
                'total_cost': ['mean', 'sum'],
                'patient_id': 'count',
                'readmitted_30d': 'mean' if 'readmitted_30d' in self.admissions.columns else 'count'
            }).round(2)
            diag_outcomes.columns = ['avg_los', 'median_los', 'std_los',
                                     'avg_cost', 'total_cost', 'cases',
                                     'readmission_rate']
            if 'readmitted_30d' in self.admissions.columns:
                diag_outcomes['readmission_rate'] = (diag_outcomes['readmission_rate'] * 100).round(1)
            results['by_diagnosis'] = diag_outcomes.sort_values('cases', ascending=False)

        # 按治療方式分析
        if 'treatment_type' in self.admissions.columns:
            treatment_outcomes = self.admissions.groupby('treatment_type').agg({
                'length_of_stay': 'mean',
                'total_cost': 'mean',
                'patient_id': 'count',
                'satisfaction_score': 'mean' if 'satisfaction_score' in self.admissions.columns else 'count'
            }).round(2)
            treatment_outcomes.columns = ['avg_los', 'avg_cost', 'cases', 'satisfaction']
            results['by_treatment'] = treatment_outcomes.sort_values('cases', ascending=False)

        # 按醫師分析
        if 'attending_physician' in self.admissions.columns:
            physician_outcomes = self.admissions.groupby('attending_physician').agg({
                'length_of_stay': 'mean',
                'patient_id': 'count',
                'satisfaction_score': 'mean' if 'satisfaction_score' in self.admissions.columns else 'count'
            }).round(2)
            physician_outcomes.columns = ['avg_los', 'cases', 'satisfaction']
            results['by_physician'] = physician_outcomes.sort_values('cases', ascending=False)

        return results

    def analyze_resource_utilization(self) -> Dict[str, any]:
        """分析醫療資源利用"""
        results = {}

        if self.admissions is None:
            return results

        df = self.admissions

        # 床位利用
        if 'admission_date' in df.columns and 'discharge_date' in df.columns:
            df['admission_date'] = pd.to_datetime(df['admission_date'])
            df['discharge_date'] = pd.to_datetime(df['discharge_date'])

            # 按月份統計入院
            monthly_admissions = df.groupby(df['admission_date'].dt.to_period('M')).size()
            results['monthly_admissions'] = monthly_admissions

        # 住院天數分佈
        if 'length_of_stay' in df.columns:
            los_stats = {
                'mean': df['length_of_stay'].mean(),
                'median': df['length_of_stay'].median(),
                'max': df['length_of_stay'].max(),
                'pct_long_stay': (df['length_of_stay'] > 14).mean() * 100
            }
            results['length_of_stay_stats'] = los_stats

            # 長住院患者分析
            long_stay = df[df['length_of_stay'] > 14]
            if 'primary_diagnosis' in df.columns:
                results['long_stay_diagnoses'] = long_stay['primary_diagnosis'].value_counts().head(5)

        # 費用分析
        if 'total_cost' in df.columns:
            cost_stats = {
                'mean': df['total_cost'].mean(),
                'median': df['total_cost'].median(),
                'total': df['total_cost'].sum(),
                'pct_high_cost': (df['total_cost'] > df['total_cost'].quantile(0.9)).mean() * 100
            }
            results['cost_stats'] = cost_stats

            # 高費用患者
            high_cost_threshold = df['total_cost'].quantile(0.9)
            high_cost = df[df['total_cost'] > high_cost_threshold]
            results['high_cost_count'] = len(high_cost)
            results['high_cost_total'] = high_cost['total_cost'].sum()
            results['high_cost_pct_of_total'] = (
                high_cost['total_cost'].sum() / df['total_cost'].sum() * 100
            )

        # 急診vs預約入院
        if 'admission_type' in df.columns:
            admission_types = df['admission_type'].value_counts(normalize=True) * 100
            results['admission_type_distribution'] = admission_types.round(1).to_dict()

        return results

    def identify_high_risk_patients(self) -> pd.DataFrame:
        """識別需要特別關注的高風險患者"""
        risk_df = self.calculate_patient_risk_score()

        high_risk = risk_df[risk_df['risk_category'].isin(['High', 'Very High'])].copy()

        # 添加建議的干預措施
        interventions = []
        for _, patient in high_risk.iterrows():
            actions = []

            if patient.get('chronic_conditions', 0) >= 3:
                actions.append("安排慢性病管理計劃")

            if patient.get('smoker', False):
                actions.append("轉介戒煙計劃")

            if patient.get('bmi', 0) >= 30:
                actions.append("營養諮詢和運動計劃")

            if patient.get('prev_admissions_year', 0) >= 2:
                actions.append("加強出院後追蹤")

            if patient.get('age', 0) >= 75:
                actions.append("安排老年醫學評估")

            if not actions:
                actions.append("定期健康追蹤")

            interventions.append('; '.join(actions))

        high_risk['recommended_interventions'] = interventions

        return high_risk.sort_values('risk_score', ascending=False)

    def generate_report(self) -> str:
        """生成完整的醫療分析報告"""
        risk_df = self.calculate_patient_risk_score()
        resources = self.analyze_resource_utilization()

        report = f"""
{'='*80}
                    醫療保健分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、患者群體概覽
{'='*40}
  總患者數: {len(self.patients):,}
  平均年齡: {self.patients['age'].mean():.1f} 歲
  男性比例: {(self.patients['gender'] == 'M').mean() * 100:.1f}%
  平均慢性病數量: {self.patients['chronic_conditions'].mean():.1f}

二、風險分層
{'='*40}
"""
        risk_dist = risk_df['risk_category'].value_counts()
        for category in ['Very High', 'High', 'Moderate', 'Low']:
            count = risk_dist.get(category, 0)
            pct = count / len(risk_df) * 100
            bar = '█' * int(pct / 2)
            icon = {'Very High': '🔴', 'High': '🟠', 'Moderate': '🟡', 'Low': '🟢'}[category]
            report += f"  {icon} {category:12}: {count:5} ({pct:5.1f}%) {bar}\n"

        # 高風險患者
        high_risk = self.identify_high_risk_patients()
        report += f"""
  需特別關注的高風險患者 (Top 10):
"""
        for _, p in high_risk.head(10).iterrows():
            report += f"    - {p['patient_id']}: 風險分數 {p['risk_score']}, 年齡 {p['age']:.0f}\n"
            report += f"      建議: {p['recommended_interventions']}\n"

        # 再入院風險
        if self.admissions is not None:
            readmission = self.predict_readmission_risk()
            report += f"""
三、再入院風險分析
{'='*40}
  分析入院記錄數: {len(readmission):,}
  平均LACE分數: {readmission['lace_score'].mean():.1f}

  風險分佈:
"""
            readmit_dist = readmission['readmission_risk'].value_counts()
            for risk_level in ['High (10+)', 'Moderate (5-9)', 'Low (<5)']:
                count = readmit_dist.get(risk_level, 0)
                pct = count / len(readmission) * 100
                report += f"    {risk_level}: {count} ({pct:.1f}%)\n"

        # 資源利用
        if resources:
            report += f"""
四、資源利用分析
{'='*40}
"""
            if 'length_of_stay_stats' in resources:
                los = resources['length_of_stay_stats']
                report += f"""
  住院天數:
    平均: {los['mean']:.1f} 天
    中位數: {los['median']:.1f} 天
    最長: {los['max']:.0f} 天
    長住院率(>14天): {los['pct_long_stay']:.1f}%
"""

            if 'cost_stats' in resources:
                cost = resources['cost_stats']
                report += f"""
  費用分析:
    平均費用: ${cost['mean']:,.0f}
    中位數費用: ${cost['median']:,.0f}
    總費用: ${cost['total']:,.0f}

  高費用患者 (前10%):
    人數: {resources.get('high_cost_count', 0)}
    佔總費用: {resources.get('high_cost_pct_of_total', 0):.1f}%
"""

            if 'admission_type_distribution' in resources:
                report += f"""
  入院類型分佈:
"""
                for atype, pct in resources['admission_type_distribution'].items():
                    report += f"    {atype}: {pct:.1f}%\n"

        # 治療效果
        if self.admissions is not None:
            outcomes = self.analyze_treatment_outcomes()
            if 'by_diagnosis' in outcomes:
                report += f"""
五、治療效果分析
{'='*40}

  主要診斷分析 (按病例數):
"""
                for diag, row in outcomes['by_diagnosis'].head(5).iterrows():
                    report += f"    {diag}:\n"
                    report += f"      病例數: {row['cases']}, 平均住院: {row['avg_los']:.1f}天\n"
                    report += f"      平均費用: ${row['avg_cost']:,.0f}\n"

        # 建議
        report += f"""
六、行動建議
{'='*40}

1. 高風險患者管理:
   - 對 {len(high_risk)} 位高風險患者建立個人化照護計劃
   - 加強慢性病管理，減少急性發作

2. 再入院預防:
   - 強化出院計劃和過渡期照護
   - 建立48小時內電話追蹤機制

3. 資源優化:
   - 分析長住院病例，縮短不必要的住院天數
   - 關注高費用病例的成本效益

4. 預防保健:
   - 推廣戒煙計劃和體重管理
   - 加強高齡患者的定期健康檢查

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_patient_data(n_patients: int = 1000,
                          n_admissions: int = 2000,
                          seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """生成模擬醫療數據"""
    np.random.seed(seed)
    today = datetime.now()

    # ========================================
    # 患者主檔
    # ========================================
    patients = []
    for i in range(1, n_patients + 1):
        age = np.clip(np.random.normal(55, 18), 18, 95)
        gender = np.random.choice(['M', 'F'], p=[0.48, 0.52])

        # 慢性病數量 (與年齡相關)
        chronic_base = max(0, (age - 40) / 20)
        chronic_conditions = int(np.clip(np.random.poisson(chronic_base), 0, 8))

        # BMI (正態分佈)
        bmi = np.clip(np.random.normal(27, 5), 16, 50)

        # 吸煙者比例
        smoker = np.random.choice([True, False], p=[0.15, 0.85])

        # 過去一年入院次數
        admit_rate = 0.3 + chronic_conditions * 0.1
        prev_admissions = np.random.poisson(admit_rate)

        patients.append({
            'patient_id': f'PAT{i:06d}',
            'birth_date': today - timedelta(days=int(age * 365)),
            'gender': gender,
            'blood_type': np.random.choice(['A', 'B', 'AB', 'O'], p=[0.4, 0.1, 0.05, 0.45]),
            'chronic_conditions': chronic_conditions,
            'bmi': round(bmi, 1),
            'smoker': smoker,
            'prev_admissions_year': prev_admissions,
            'insurance_type': np.random.choice(
                ['Public', 'Private', 'Self-Pay'],
                p=[0.55, 0.35, 0.10]
            )
        })

    patients_df = pd.DataFrame(patients)

    # ========================================
    # 入院記錄
    # ========================================
    diagnoses = [
        'Heart Failure', 'Pneumonia', 'COPD', 'Diabetes Complications',
        'Hip Fracture', 'Stroke', 'Chest Pain', 'GI Bleeding',
        'Sepsis', 'Kidney Disease', 'Surgery - Elective', 'Surgery - Emergency'
    ]
    diag_weights = [0.15, 0.12, 0.10, 0.10, 0.08, 0.08, 0.10, 0.07, 0.05, 0.05, 0.05, 0.05]

    treatments = ['Medical', 'Surgical', 'Interventional', 'Supportive']
    treatment_weights = [0.50, 0.25, 0.15, 0.10]

    physicians = [f'Dr. {name}' for name in ['Smith', 'Johnson', 'Williams', 'Brown',
                                              'Jones', 'Garcia', 'Miller', 'Davis', 'Chen', 'Wang']]

    admissions = []
    for i in range(1, n_admissions + 1):
        patient = patients_df.sample(1).iloc[0]

        # 入院日期 (過去2年)
        days_ago = np.random.randint(0, 730)
        admission_date = today - timedelta(days=days_ago)

        # 住院天數 (對數正態分佈)
        base_los = np.random.lognormal(1.5, 0.7)
        # 高齡和多病患者住院更長
        age = (today - pd.to_datetime(patient['birth_date'])).days / 365
        los_modifier = 1 + (age - 50) / 100 + patient['chronic_conditions'] * 0.1
        length_of_stay = int(np.clip(base_los * los_modifier, 1, 60))

        discharge_date = admission_date + timedelta(days=length_of_stay)

        diagnosis = np.random.choice(diagnoses, p=diag_weights)
        treatment = np.random.choice(treatments, p=treatment_weights)

        # 入院類型
        admission_type = np.random.choice(['Emergency', 'Elective', 'Urgent'],
                                          p=[0.50, 0.30, 0.20])

        # 費用 (基於住院天數和治療類型)
        base_cost = 1500 * length_of_stay
        if treatment == 'Surgical':
            base_cost *= 2.5
        elif treatment == 'Interventional':
            base_cost *= 1.8
        total_cost = base_cost * np.random.uniform(0.8, 1.3)

        # Charlson共病指數
        charlson = min(patient['chronic_conditions'] + np.random.randint(0, 3), 10)

        # 急診次數
        ed_visits = np.random.poisson(patient['prev_admissions_year'] * 0.5)

        # 30天再入院
        readmission_prob = 0.05 + charlson * 0.02 + (length_of_stay > 7) * 0.05
        readmitted = np.random.random() < readmission_prob

        # 滿意度
        satisfaction = np.clip(np.random.normal(4.0, 0.8), 1, 5)

        admissions.append({
            'admission_id': f'ADM{i:07d}',
            'patient_id': patient['patient_id'],
            'admission_date': admission_date,
            'discharge_date': discharge_date,
            'length_of_stay': length_of_stay,
            'admission_type': admission_type,
            'primary_diagnosis': diagnosis,
            'treatment_type': treatment,
            'attending_physician': np.random.choice(physicians),
            'charlson_index': charlson,
            'ed_visits_6months': ed_visits,
            'total_cost': round(total_cost, 2),
            'readmitted_30d': readmitted,
            'satisfaction_score': round(satisfaction, 1)
        })

    admissions_df = pd.DataFrame(admissions)

    return patients_df, admissions_df


def main():
    """執行醫療保健分析範例"""
    print("="*80)
    print(" "*20 + "醫療保健患者分析")
    print("="*80)

    # ========================================
    # 1. 準備數據
    # ========================================
    print("\n[1/5] 準備醫療數據...")

    patients, admissions = generate_patient_data(n_patients=1000, n_admissions=2500)

    print(f"  ✓ 患者數: {len(patients):,}")
    print(f"  ✓ 入院記錄: {len(admissions):,}")
    print(f"  ✓ 平均年齡: {patients['age'].mean():.1f} 歲")
    print(f"  ✓ 平均慢性病數: {patients['chronic_conditions'].mean():.1f}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/5] 初始化醫療分析器...")
    analyzer = HealthcareAnalyzer(patients, admissions)
    print("  ✓ 分析器初始化完成")

    # ========================================
    # 3. 患者風險分層
    # ========================================
    print("\n[3/5] 計算患者風險分數...")

    risk_df = analyzer.calculate_patient_risk_score()
    risk_dist = risk_df['risk_category'].value_counts()

    print("\n  📊 風險分層分佈:")
    for category in ['Very High', 'High', 'Moderate', 'Low']:
        count = risk_dist.get(category, 0)
        pct = count / len(risk_df) * 100
        icon = {'Very High': '🔴', 'High': '🟠', 'Moderate': '🟡', 'Low': '🟢'}[category]
        print(f"     {icon} {category}: {count} ({pct:.1f}%)")

    # ========================================
    # 4. 再入院風險預測
    # ========================================
    print("\n[4/5] 預測再入院風險...")

    readmission = analyzer.predict_readmission_risk()
    print(f"  平均LACE分數: {readmission['lace_score'].mean():.1f}")

    readmit_dist = readmission['readmission_risk'].value_counts()
    print("\n  再入院風險分佈:")
    for risk in ['High (10+)', 'Moderate (5-9)', 'Low (<5)']:
        count = readmit_dist.get(risk, 0)
        print(f"     {risk}: {count}")

    # ========================================
    # 5. 資源利用分析
    # ========================================
    print("\n[5/5] 分析資源利用...")

    resources = analyzer.analyze_resource_utilization()

    if 'length_of_stay_stats' in resources:
        los = resources['length_of_stay_stats']
        print(f"\n  住院天數統計:")
        print(f"     平均: {los['mean']:.1f} 天")
        print(f"     中位數: {los['median']:.1f} 天")
        print(f"     長住院率: {los['pct_long_stay']:.1f}%")

    if 'cost_stats' in resources:
        cost = resources['cost_stats']
        print(f"\n  費用統計:")
        print(f"     平均: ${cost['mean']:,.0f}")
        print(f"     總計: ${cost['total']:,.0f}")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存報告
    try:
        with open('data/outputs/healthcare_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/healthcare_analysis_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
