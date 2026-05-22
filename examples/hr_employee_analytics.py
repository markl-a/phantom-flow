"""
人力資源員工分析範例

這個範例展示如何分析員工數據，包含：
- 員工流失預測
- 績效分析與人才識別
- 薪資公平性分析
- 組織健康度評估

真實應用場景:
- 人力資源部門人才管理
- 企業組織發展規劃
- 員工滿意度調查分析
- 薪酬福利優化
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


class HRAnalyzer:
    """
    人力資源分析器

    提供完整的員工數據分析功能:
    - 員工流失風險評估
    - 績效分析
    - 薪資公平性檢測
    - 組織健康度指標
    """

    def __init__(self, employees_df: pd.DataFrame,
                 performance_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            employees_df: 員工主檔DataFrame
            performance_df: 績效記錄DataFrame (可選)
        """
        self.employees = employees_df.copy()
        self.performance = performance_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if 'hire_date' in self.employees.columns:
            self.employees['hire_date'] = pd.to_datetime(self.employees['hire_date'])
            self.employees['tenure_years'] = (
                datetime.now() - self.employees['hire_date']
            ).dt.days / 365

        if 'birth_date' in self.employees.columns:
            self.employees['birth_date'] = pd.to_datetime(self.employees['birth_date'])
            self.employees['age'] = (
                datetime.now() - self.employees['birth_date']
            ).dt.days / 365

    def analyze_attrition_risk(self) -> pd.DataFrame:
        """
        分析員工流失風險

        風險因素:
        - 工作年資 (過短或過長)
        - 薪資水平相對市場
        - 績效評分
        - 晉升歷史
        - 工作滿意度
        """
        df = self.employees.copy()

        risk_score = pd.Series(0.0, index=df.index)

        # 年資風險 (1-2年流失率最高)
        if 'tenure_years' in df.columns:
            tenure_risk = np.where(
                (df['tenure_years'] >= 1) & (df['tenure_years'] <= 2), 20,
                np.where(df['tenure_years'] < 1, 10, 5)
            )
            risk_score += tenure_risk

        # 薪資風險 (低於部門平均)
        if 'salary' in df.columns and 'department' in df.columns:
            dept_avg = df.groupby('department')['salary'].transform('mean')
            salary_ratio = df['salary'] / dept_avg
            salary_risk = np.where(salary_ratio < 0.9, 25, np.where(salary_ratio < 1.0, 15, 5))
            risk_score += salary_risk

        # 績效風險 (高績效可能被挖角)
        if 'performance_score' in df.columns:
            perf_risk = np.where(
                df['performance_score'] >= 4.5, 15,  # 高績效有被挖角風險
                np.where(df['performance_score'] <= 2.5, 20, 5)  # 低績效可能主動離職
            )
            risk_score += perf_risk

        # 晉升風險 (長期未晉升)
        if 'years_since_promotion' in df.columns:
            promo_risk = np.where(df['years_since_promotion'] > 3, 20,
                                  np.where(df['years_since_promotion'] > 2, 10, 5))
            risk_score += promo_risk

        # 滿意度風險
        if 'satisfaction_score' in df.columns:
            sat_risk = (5 - df['satisfaction_score']) / 5 * 30
            risk_score += sat_risk

        # 標準化到0-100
        risk_score = (risk_score / risk_score.max() * 100).clip(0, 100)

        df['attrition_risk_score'] = risk_score.round(1)
        df['attrition_risk_level'] = pd.cut(
            df['attrition_risk_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Critical']
        )

        return df[['employee_id', 'name', 'department', 'attrition_risk_score',
                   'attrition_risk_level']].sort_values('attrition_risk_score', ascending=False)

    def analyze_performance(self) -> Dict[str, pd.DataFrame]:
        """分析員工績效分佈"""
        results = {}

        if 'performance_score' not in self.employees.columns:
            return results

        # 整體績效分佈
        perf_dist = self.employees['performance_score'].value_counts().sort_index()
        results['distribution'] = perf_dist

        # 部門績效比較
        if 'department' in self.employees.columns:
            dept_perf = self.employees.groupby('department').agg({
                'performance_score': ['mean', 'std', 'min', 'max', 'count']
            }).round(2)
            dept_perf.columns = ['avg_score', 'std_dev', 'min_score', 'max_score', 'count']
            results['by_department'] = dept_perf.sort_values('avg_score', ascending=False)

        # 識別高潛力人才 (High Potential)
        if all(col in self.employees.columns for col in ['performance_score', 'tenure_years']):
            hipot = self.employees[
                (self.employees['performance_score'] >= 4.0) &
                (self.employees['tenure_years'] <= 3)
            ].copy()
            hipot['potential_score'] = (
                hipot['performance_score'] * 0.6 +
                (5 - hipot['tenure_years']) * 0.4
            ).round(2)
            results['high_potential'] = hipot.nlargest(20, 'potential_score')

        # 績效改善候選人
        if 'performance_score' in self.employees.columns:
            needs_improvement = self.employees[
                self.employees['performance_score'] <= 2.5
            ].copy()
            results['needs_improvement'] = needs_improvement

        return results

    def analyze_compensation(self) -> Dict[str, any]:
        """薪資公平性分析"""
        if 'salary' not in self.employees.columns:
            return {}

        results = {}

        # 整體薪資統計
        results['overall'] = {
            'mean': self.employees['salary'].mean(),
            'median': self.employees['salary'].median(),
            'std': self.employees['salary'].std(),
            'min': self.employees['salary'].min(),
            'max': self.employees['salary'].max()
        }

        # 部門薪資比較
        if 'department' in self.employees.columns:
            dept_salary = self.employees.groupby('department')['salary'].agg(
                ['mean', 'median', 'std', 'min', 'max', 'count']
            ).round(0)
            results['by_department'] = dept_salary

        # 性別薪資差異 (Pay Gap Analysis)
        if 'gender' in self.employees.columns:
            gender_salary = self.employees.groupby('gender')['salary'].agg(['mean', 'median'])

            if len(gender_salary) >= 2:
                gap = gender_salary.loc['F', 'mean'] / gender_salary.loc['M', 'mean'] - 1
                results['gender_pay_gap'] = {
                    'by_gender': gender_salary,
                    'gap_percentage': gap * 100,
                    'analysis': '需關注' if abs(gap) > 0.05 else '正常範圍'
                }

        # 薪資與績效關聯
        if 'performance_score' in self.employees.columns:
            correlation = self.employees['salary'].corr(self.employees['performance_score'])
            results['performance_correlation'] = {
                'correlation': correlation,
                'analysis': '高度正相關' if correlation > 0.5 else
                           ('中度正相關' if correlation > 0.3 else '相關性較弱')
            }

        # 薪資公平性指標 (Compa-Ratio)
        if 'job_level' in self.employees.columns:
            level_midpoint = self.employees.groupby('job_level')['salary'].median()
            self.employees['compa_ratio'] = self.employees.apply(
                lambda x: x['salary'] / level_midpoint.get(x['job_level'], x['salary']),
                axis=1
            )
            underpaid = self.employees[self.employees['compa_ratio'] < 0.9]
            overpaid = self.employees[self.employees['compa_ratio'] > 1.1]
            results['compa_ratio_analysis'] = {
                'underpaid_count': len(underpaid),
                'overpaid_count': len(overpaid),
                'fair_pay_count': len(self.employees) - len(underpaid) - len(overpaid)
            }

        return results

    def calculate_organization_health(self) -> Dict[str, any]:
        """計算組織健康度指標"""
        health_metrics = {}

        total_employees = len(self.employees)

        # 人員結構
        if 'job_level' in self.employees.columns:
            level_dist = self.employees['job_level'].value_counts(normalize=True) * 100
            health_metrics['level_distribution'] = level_dist.round(1).to_dict()

            # 理想的金字塔結構：基層60%, 中層30%, 高層10%
            ideal = {'Junior': 60, 'Mid': 30, 'Senior': 10}
            # 計算結構健康度

        # 年資分佈
        if 'tenure_years' in self.employees.columns:
            tenure_brackets = pd.cut(
                self.employees['tenure_years'],
                bins=[0, 1, 3, 5, 10, float('inf')],
                labels=['<1年', '1-3年', '3-5年', '5-10年', '>10年']
            )
            health_metrics['tenure_distribution'] = tenure_brackets.value_counts().to_dict()

        # 年齡分佈
        if 'age' in self.employees.columns:
            age_brackets = pd.cut(
                self.employees['age'],
                bins=[0, 25, 35, 45, 55, 100],
                labels=['<25', '25-35', '35-45', '45-55', '>55']
            )
            health_metrics['age_distribution'] = age_brackets.value_counts().to_dict()

        # 多元化指標
        if 'gender' in self.employees.columns:
            gender_dist = self.employees['gender'].value_counts(normalize=True) * 100
            health_metrics['gender_diversity'] = {
                'distribution': gender_dist.round(1).to_dict(),
                'balance_score': 100 - abs(50 - gender_dist.get('F', 50)) * 2
            }

        # 流失風險分佈
        attrition = self.analyze_attrition_risk()
        risk_dist = attrition['attrition_risk_level'].value_counts()
        health_metrics['attrition_risk_distribution'] = risk_dist.to_dict()
        health_metrics['high_risk_percentage'] = (
            (risk_dist.get('High', 0) + risk_dist.get('Critical', 0)) / total_employees * 100
        )

        # 績效分佈
        if 'performance_score' in self.employees.columns:
            avg_perf = self.employees['performance_score'].mean()
            health_metrics['avg_performance'] = round(avg_perf, 2)
            health_metrics['performance_health'] = (
                'Excellent' if avg_perf >= 4.0 else
                ('Good' if avg_perf >= 3.5 else
                 ('Needs Attention' if avg_perf >= 3.0 else 'Critical'))
            )

        # 計算整體健康度分數
        health_score = 50  # 基礎分
        if health_metrics.get('high_risk_percentage', 0) < 20:
            health_score += 15
        if health_metrics.get('avg_performance', 0) >= 3.5:
            health_score += 15
        if health_metrics.get('gender_diversity', {}).get('balance_score', 0) >= 80:
            health_score += 10
        health_metrics['overall_health_score'] = min(health_score, 100)

        return health_metrics

    def generate_retention_strategies(self) -> List[Dict]:
        """為高風險員工生成挽留策略"""
        attrition = self.analyze_attrition_risk()
        high_risk = attrition[attrition['attrition_risk_level'].isin(['High', 'Critical'])]

        strategies = []

        for _, emp in high_risk.head(10).iterrows():
            emp_data = self.employees[self.employees['employee_id'] == emp['employee_id']].iloc[0]

            actions = []

            # 根據風險因素制定策略
            if 'salary' in emp_data.index:
                dept_avg = self.employees[
                    self.employees['department'] == emp_data['department']
                ]['salary'].mean()
                if emp_data['salary'] < dept_avg * 0.95:
                    actions.append(f"調薪建議: 調整至部門平均水平 (${dept_avg:,.0f})")

            if 'years_since_promotion' in emp_data.index:
                if emp_data['years_since_promotion'] > 2:
                    actions.append("晉升評估: 考慮晉升或橫向調動機會")

            if 'performance_score' in emp_data.index:
                if emp_data['performance_score'] >= 4.0:
                    actions.append("高績效人才: 安排職涯發展談話，提供更多挑戰")
                elif emp_data['performance_score'] <= 2.5:
                    actions.append("績效輔導: 安排1對1輔導計劃")

            actions.append("安排與主管進行留任面談")
            actions.append("評估是否需要工作內容調整")

            strategies.append({
                'employee_id': emp['employee_id'],
                'name': emp['name'],
                'department': emp['department'],
                'risk_score': emp['attrition_risk_score'],
                'risk_level': emp['attrition_risk_level'],
                'recommended_actions': actions,
                'priority': 'URGENT' if emp['attrition_risk_level'] == 'Critical' else 'HIGH'
            })

        return strategies

    def generate_report(self) -> str:
        """生成完整的HR分析報告"""
        health = self.calculate_organization_health()
        attrition = self.analyze_attrition_risk()
        performance = self.analyze_performance()
        compensation = self.analyze_compensation()

        report = f"""
{'='*80}
                    人力資源分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、組織概覽
{'='*40}
  員工總數: {len(self.employees):,}
  部門數量: {self.employees['department'].nunique() if 'department' in self.employees.columns else 'N/A'}
  平均年資: {self.employees['tenure_years'].mean():.1f} 年
  整體健康度: {health['overall_health_score']}/100

二、流失風險分析
{'='*40}
"""
        risk_dist = attrition['attrition_risk_level'].value_counts()
        for level in ['Critical', 'High', 'Medium', 'Low']:
            count = risk_dist.get(level, 0)
            pct = count / len(attrition) * 100
            bar = '█' * int(pct / 2)
            icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[level]
            report += f"  {icon} {level:10}: {count:4} ({pct:5.1f}%) {bar}\n"

        report += f"""
  高風險員工 (需立即關注):
"""
        for _, emp in attrition[attrition['attrition_risk_level'] == 'Critical'].head(5).iterrows():
            report += f"    - {emp['name']} ({emp['department']}): 風險分數 {emp['attrition_risk_score']}\n"

        report += f"""
三、績效分析
{'='*40}
  平均績效分數: {self.employees['performance_score'].mean():.2f}
  績效健康度: {health.get('performance_health', 'N/A')}

  部門績效排名:
"""
        if 'by_department' in performance:
            for dept, row in performance['by_department'].head(5).iterrows():
                report += f"    {dept}: {row['avg_score']:.2f} ({row['count']} 人)\n"

        if 'high_potential' in performance:
            report += f"""
  高潛力人才 (Top 5):
"""
            for _, emp in performance['high_potential'].head(5).iterrows():
                report += f"    - {emp['name']}: 績效 {emp['performance_score']}, 年資 {emp['tenure_years']:.1f}年\n"

        report += f"""
四、薪資分析
{'='*40}
  平均薪資: ${compensation['overall']['mean']:,.0f}
  中位數薪資: ${compensation['overall']['median']:,.0f}
  薪資標準差: ${compensation['overall']['std']:,.0f}
"""

        if 'gender_pay_gap' in compensation:
            gap = compensation['gender_pay_gap']
            report += f"""
  性別薪資差異:
    差距: {gap['gap_percentage']:.1f}%
    分析: {gap['analysis']}
"""

        if 'compa_ratio_analysis' in compensation:
            compa = compensation['compa_ratio_analysis']
            report += f"""
  薪資公平性:
    薪資偏低: {compa['underpaid_count']} 人
    薪資適中: {compa['fair_pay_count']} 人
    薪資偏高: {compa['overpaid_count']} 人
"""

        report += f"""
五、組織健康度
{'='*40}
  整體健康分數: {health['overall_health_score']}/100

  年齡分佈:
"""
        for age_group, count in health.get('age_distribution', {}).items():
            report += f"    {age_group}: {count} 人\n"

        report += f"""
  年資分佈:
"""
        for tenure_group, count in health.get('tenure_distribution', {}).items():
            report += f"    {tenure_group}: {count} 人\n"

        if 'gender_diversity' in health:
            report += f"""
  性別多元化:
    平衡分數: {health['gender_diversity']['balance_score']:.0f}/100
"""

        # 策略建議
        strategies = self.generate_retention_strategies()
        report += f"""
六、行動建議
{'='*40}

1. 高風險員工挽留:
"""
        for s in strategies[:5]:
            report += f"   [{s['priority']}] {s['name']} ({s['department']})\n"
            for action in s['recommended_actions'][:2]:
                report += f"      → {action}\n"

        report += f"""
2. 整體建議:
   - 定期進行滿意度調查，及早發現問題
   - 建立透明的晉升機制和時間表
   - 確保薪資具有市場競爭力
   - 強化主管的人才管理能力培訓

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_employee_data(n_employees: int = 500, seed: int = 42) -> pd.DataFrame:
    """生成模擬員工數據"""
    np.random.seed(seed)

    departments = ['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Product']
    dept_weights = [0.30, 0.20, 0.15, 0.10, 0.08, 0.10, 0.07]

    job_levels = ['Junior', 'Mid', 'Senior', 'Lead', 'Manager', 'Director']
    level_weights = [0.35, 0.30, 0.20, 0.08, 0.05, 0.02]

    # 部門薪資基準
    dept_salary_base = {
        'Engineering': 80000, 'Sales': 70000, 'Marketing': 65000,
        'Finance': 75000, 'HR': 60000, 'Operations': 55000, 'Product': 78000
    }

    # 職級薪資乘數
    level_multiplier = {
        'Junior': 0.8, 'Mid': 1.0, 'Senior': 1.3,
        'Lead': 1.6, 'Manager': 2.0, 'Director': 2.8
    }

    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
                   'William', 'Elizabeth', 'David', 'Barbara', 'Wei', 'Mei', 'Hiroshi', 'Yuki']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Chen', 'Wang', 'Li', 'Zhang', 'Tanaka', 'Yamamoto', 'Kim', 'Park']

    employees = []
    today = datetime.now()

    for i in range(1, n_employees + 1):
        department = np.random.choice(departments, p=dept_weights)
        job_level = np.random.choice(job_levels, p=level_weights)
        gender = np.random.choice(['M', 'F'], p=[0.55, 0.45])

        # 計算薪資 (考慮部門和職級)
        base = dept_salary_base[department]
        multiplier = level_multiplier[job_level]
        salary = base * multiplier * np.random.uniform(0.9, 1.1)

        # 年資影響薪資
        tenure_years = np.random.exponential(3)
        tenure_years = np.clip(tenure_years, 0.1, 25)
        salary *= (1 + tenure_years * 0.02)  # 每年2%增長

        # 績效分數 (正態分佈，均值3.5)
        performance = np.clip(np.random.normal(3.5, 0.8), 1, 5)

        # 滿意度 (與績效和薪資相關)
        satisfaction = np.clip(performance * 0.5 + np.random.normal(2, 0.5), 1, 5)

        # 晉升年數
        years_since_promo = np.random.exponential(2)
        years_since_promo = min(years_since_promo, tenure_years)

        employees.append({
            'employee_id': f'EMP{i:05d}',
            'name': f"{np.random.choice(first_names)} {np.random.choice(last_names)}",
            'gender': gender,
            'birth_date': today - timedelta(days=int(np.random.uniform(22, 60) * 365)),
            'hire_date': today - timedelta(days=int(tenure_years * 365)),
            'department': department,
            'job_level': job_level,
            'salary': round(salary, 0),
            'performance_score': round(performance, 1),
            'satisfaction_score': round(satisfaction, 1),
            'years_since_promotion': round(years_since_promo, 1),
            'email': f"emp{i}@company.com",
            'is_remote': np.random.choice([True, False], p=[0.3, 0.7])
        })

    return pd.DataFrame(employees)


def main():
    """執行HR員工分析範例"""
    print("="*80)
    print(" "*20 + "人力資源員工分析")
    print("="*80)

    # ========================================
    # 1. 準備數據
    # ========================================
    print("\n[1/5] 準備員工數據...")

    employees = generate_employee_data(n_employees=500)

    print(f"  ✓ 員工總數: {len(employees):,}")
    print(f"  ✓ 部門數量: {employees['department'].nunique()}")
    print(f"  ✓ 平均年資: {employees['tenure_years'].mean():.1f} 年")
    print(f"  ✓ 平均薪資: ${employees['salary'].mean():,.0f}")

    # ========================================
    # 2. 初始化分析器
    # ========================================
    print("\n[2/5] 初始化HR分析器...")
    analyzer = HRAnalyzer(employees)
    print("  ✓ 分析器初始化完成")

    # ========================================
    # 3. 流失風險分析
    # ========================================
    print("\n[3/5] 分析員工流失風險...")

    attrition = analyzer.analyze_attrition_risk()
    risk_dist = attrition['attrition_risk_level'].value_counts()

    print("\n  📊 流失風險分佈:")
    for level in ['Critical', 'High', 'Medium', 'Low']:
        count = risk_dist.get(level, 0)
        pct = count / len(attrition) * 100
        icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[level]
        print(f"     {icon} {level}: {count} ({pct:.1f}%)")

    # ========================================
    # 4. 績效分析
    # ========================================
    print("\n[4/5] 分析員工績效...")

    performance = analyzer.analyze_performance()
    print(f"  平均績效分數: {employees['performance_score'].mean():.2f}")

    if 'high_potential' in performance:
        print(f"\n  🌟 高潛力人才 (Top 5):")
        for _, emp in performance['high_potential'].head(5).iterrows():
            print(f"     {emp['name']} ({emp['department']}): 績效 {emp['performance_score']}")

    # ========================================
    # 5. 薪資分析
    # ========================================
    print("\n[5/5] 分析薪資公平性...")

    compensation = analyzer.analyze_compensation()
    print(f"  平均薪資: ${compensation['overall']['mean']:,.0f}")
    print(f"  薪資中位數: ${compensation['overall']['median']:,.0f}")

    if 'gender_pay_gap' in compensation:
        gap = compensation['gender_pay_gap']['gap_percentage']
        print(f"  性別薪資差距: {gap:+.1f}%")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存報告
    try:
        with open('data/outputs/hr_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/hr_analysis_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
