"""
教育學生績效分析範例

這個範例展示如何分析學生學習數據，包含：
- 學業成績分析
- 學習進度追蹤
- 風險學生識別
- 教學效果評估

真實應用場景:
- 學校學生成績管理
- 線上教育平台學習分析
- 教育政策制定
- 個人化學習推薦
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


class StudentAnalyzer:
    """
    學生績效分析器

    提供完整的學生數據分析功能:
    - 成績分析
    - 學習行為分析
    - 風險學生識別
    - 教學效果評估
    """

    def __init__(self, students_df: pd.DataFrame,
                 grades_df: Optional[pd.DataFrame] = None,
                 activities_df: Optional[pd.DataFrame] = None):
        """
        初始化分析器

        Args:
            students_df: 學生主檔DataFrame
            grades_df: 成績記錄DataFrame (可選)
            activities_df: 學習活動記錄DataFrame (可選)
        """
        self.students = students_df.copy()
        self.grades = grades_df
        self.activities = activities_df
        self._prepare_data()

    def _prepare_data(self):
        """準備數據"""
        if self.grades is not None and 'exam_date' in self.grades.columns:
            self.grades['exam_date'] = pd.to_datetime(self.grades['exam_date'])

    def analyze_academic_performance(self) -> Dict[str, any]:
        """分析學業成績"""
        if self.grades is None:
            return {}

        df = self.grades
        results = {}

        # 整體成績統計
        results['overall'] = {
            'mean': df['score'].mean(),
            'median': df['score'].median(),
            'std': df['score'].std(),
            'pass_rate': (df['score'] >= 60).mean() * 100,
            'excellent_rate': (df['score'] >= 90).mean() * 100
        }

        # 按科目分析
        if 'subject' in df.columns:
            subject_stats = df.groupby('subject').agg({
                'score': ['mean', 'median', 'std', 'min', 'max', 'count']
            }).round(2)
            subject_stats.columns = ['mean', 'median', 'std', 'min', 'max', 'count']
            subject_stats['pass_rate'] = df.groupby('subject').apply(
                lambda x: (x['score'] >= 60).mean() * 100
            ).round(1)
            results['by_subject'] = subject_stats.to_dict('index')

        # 按班級分析
        if 'class_id' in df.columns:
            class_stats = df.groupby('class_id').agg({
                'score': ['mean', 'std', 'count']
            }).round(2)
            class_stats.columns = ['mean', 'std', 'student_count']
            class_stats['pass_rate'] = df.groupby('class_id').apply(
                lambda x: (x['score'] >= 60).mean() * 100
            ).round(1)
            results['by_class'] = class_stats.sort_values('mean', ascending=False).to_dict('index')

        # 成績分佈
        grade_brackets = pd.cut(
            df['score'],
            bins=[0, 60, 70, 80, 90, 100],
            labels=['不及格(<60)', '及格(60-70)', '良好(70-80)', '優秀(80-90)', '傑出(90-100)']
        )
        results['grade_distribution'] = grade_brackets.value_counts().to_dict()

        return results

    def track_student_progress(self, student_id: str = None) -> pd.DataFrame:
        """追蹤學生學習進度"""
        if self.grades is None:
            return pd.DataFrame()

        df = self.grades.copy()

        if student_id:
            df = df[df['student_id'] == student_id]

        # 按學期/考試計算趨勢
        if 'exam_type' in df.columns:
            progress = df.groupby(['student_id', 'exam_type']).agg({
                'score': 'mean'
            }).round(2).reset_index()

            # 計算成績變化
            progress = progress.sort_values(['student_id', 'exam_type'])
            progress['score_change'] = progress.groupby('student_id')['score'].diff()
            progress['improvement'] = progress['score_change'] > 0

        else:
            progress = df.groupby('student_id').agg({
                'score': ['mean', 'std', 'min', 'max', 'count']
            }).round(2)
            progress.columns = ['avg_score', 'std_score', 'min_score', 'max_score', 'exam_count']

        return progress

    def identify_at_risk_students(self) -> pd.DataFrame:
        """識別風險學生"""
        if self.grades is None:
            return pd.DataFrame()

        # 計算學生級別統計
        student_stats = self.grades.groupby('student_id').agg({
            'score': ['mean', 'std', 'min', 'count']
        }).round(2)
        student_stats.columns = ['avg_score', 'std_score', 'min_score', 'exam_count']

        # 計算不及格次數
        fail_counts = self.grades[self.grades['score'] < 60].groupby('student_id').size()
        student_stats['fail_count'] = fail_counts.reindex(student_stats.index).fillna(0).astype(int)

        # 計算風險分數
        risk_score = pd.Series(0.0, index=student_stats.index)

        # 平均分低
        risk_score += np.where(student_stats['avg_score'] < 60, 40,
                               np.where(student_stats['avg_score'] < 70, 20, 0))

        # 不及格次數多
        risk_score += student_stats['fail_count'] * 10

        # 成績波動大
        risk_score += np.where(student_stats['std_score'] > 15, 15, 0)

        # 最低分很低
        risk_score += np.where(student_stats['min_score'] < 40, 20,
                               np.where(student_stats['min_score'] < 50, 10, 0))

        student_stats['risk_score'] = risk_score.clip(0, 100).round(1)
        student_stats['risk_level'] = pd.cut(
            student_stats['risk_score'],
            bins=[-1, 20, 40, 60, 100],
            labels=['Low', 'Medium', 'High', 'Critical']
        )

        # 合併學生資訊
        if 'name' in self.students.columns:
            student_stats = student_stats.merge(
                self.students[['student_id', 'name', 'class_id']],
                left_index=True, right_on='student_id', how='left'
            ).set_index('student_id')

        return student_stats.sort_values('risk_score', ascending=False)

    def analyze_learning_patterns(self) -> Dict[str, any]:
        """分析學習模式"""
        if self.activities is None:
            return {}

        df = self.activities
        results = {}

        # 學習時間分佈
        if 'activity_time' in df.columns:
            df['activity_time'] = pd.to_datetime(df['activity_time'])
            df['hour'] = df['activity_time'].dt.hour
            df['day_of_week'] = df['activity_time'].dt.dayofweek

            hourly_dist = df.groupby('hour').size()
            results['hourly_distribution'] = hourly_dist.to_dict()

            day_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
            daily_dist = df.groupby('day_of_week').size()
            daily_dist.index = [day_names[i] for i in daily_dist.index]
            results['daily_distribution'] = daily_dist.to_dict()

        # 活動類型分析
        if 'activity_type' in df.columns:
            activity_stats = df.groupby('activity_type').agg({
                'duration_minutes': ['sum', 'mean', 'count'] if 'duration_minutes' in df.columns else ['count']
            })
            if 'duration_minutes' in df.columns:
                activity_stats.columns = ['total_minutes', 'avg_minutes', 'count']
            else:
                activity_stats.columns = ['count']
            results['by_activity_type'] = activity_stats.to_dict('index')

        # 學習時長統計
        if 'duration_minutes' in df.columns:
            student_engagement = df.groupby('student_id').agg({
                'duration_minutes': ['sum', 'mean', 'count']
            })
            student_engagement.columns = ['total_minutes', 'avg_session', 'session_count']
            results['engagement_stats'] = {
                'avg_total_minutes': student_engagement['total_minutes'].mean(),
                'avg_session_length': student_engagement['avg_session'].mean(),
                'avg_session_count': student_engagement['session_count'].mean()
            }

        return results

    def evaluate_teaching_effectiveness(self) -> pd.DataFrame:
        """評估教學效果"""
        if self.grades is None or 'teacher_id' not in self.grades.columns:
            return pd.DataFrame()

        df = self.grades

        teacher_stats = df.groupby('teacher_id').agg({
            'score': ['mean', 'std', 'count'],
            'student_id': 'nunique'
        }).round(2)
        teacher_stats.columns = ['avg_score', 'std_score', 'exam_count', 'student_count']

        # 及格率
        teacher_stats['pass_rate'] = df.groupby('teacher_id').apply(
            lambda x: (x['score'] >= 60).mean() * 100
        ).round(1)

        # 優秀率
        teacher_stats['excellent_rate'] = df.groupby('teacher_id').apply(
            lambda x: (x['score'] >= 90).mean() * 100
        ).round(1)

        # 計算教學效果分數
        teacher_stats['effectiveness_score'] = (
            teacher_stats['avg_score'] * 0.4 +
            teacher_stats['pass_rate'] * 0.3 +
            teacher_stats['excellent_rate'] * 0.2 +
            (100 - teacher_stats['std_score']) * 0.1
        ).round(1)

        return teacher_stats.sort_values('effectiveness_score', ascending=False)

    def generate_intervention_recommendations(self) -> List[Dict]:
        """生成干預建議"""
        at_risk = self.identify_at_risk_students()
        high_risk = at_risk[at_risk['risk_level'].isin(['High', 'Critical'])]

        recommendations = []

        for student_id, row in high_risk.head(20).iterrows():
            actions = []

            # 根據風險因素制定干預措施
            if row['avg_score'] < 60:
                actions.append("安排課後補習，加強基礎知識")

            if row['fail_count'] >= 3:
                actions.append("與家長溝通，了解學習困難原因")

            if row['std_score'] > 15:
                actions.append("分析成績波動原因，穩定學習狀態")

            if row['min_score'] < 40:
                actions.append("針對薄弱科目進行專項輔導")

            # 通用建議
            actions.append("建立學習計劃，定期追蹤進度")
            actions.append("提供心理輔導支持")

            recommendations.append({
                'student_id': student_id,
                'name': row.get('name', 'Unknown'),
                'class_id': row.get('class_id', 'Unknown'),
                'avg_score': row['avg_score'],
                'risk_score': row['risk_score'],
                'risk_level': row['risk_level'],
                'recommended_actions': actions,
                'priority': 'URGENT' if row['risk_level'] == 'Critical' else 'HIGH'
            })

        return recommendations

    def generate_report(self) -> str:
        """生成完整的學生分析報告"""
        academic = self.analyze_academic_performance()
        at_risk = self.identify_at_risk_students()
        patterns = self.analyze_learning_patterns()
        recommendations = self.generate_intervention_recommendations()

        report = f"""
{'='*80}
                    學生績效分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

一、整體概覽
{'='*40}
  學生總數: {len(self.students):,}
  考試記錄: {len(self.grades):,}
  平均分數: {academic['overall']['mean']:.1f}
  及格率: {academic['overall']['pass_rate']:.1f}%
  優秀率: {academic['overall']['excellent_rate']:.1f}%

二、成績分佈
{'='*40}
"""
        for grade_level, count in academic.get('grade_distribution', {}).items():
            pct = count / len(self.grades) * 100
            bar = '█' * int(pct)
            report += f"  {grade_level}: {count:4} ({pct:5.1f}%) {bar}\n"

        report += f"""
三、各科目表現
{'='*40}
"""
        if 'by_subject' in academic:
            for subject, stats in academic['by_subject'].items():
                report += f"  {subject}:\n"
                report += f"    平均: {stats['mean']:.1f}, 及格率: {stats['pass_rate']:.1f}%\n"

        report += f"""
四、風險學生識別
{'='*40}
"""
        risk_dist = at_risk['risk_level'].value_counts()
        for level in ['Critical', 'High', 'Medium', 'Low']:
            count = risk_dist.get(level, 0)
            pct = count / len(at_risk) * 100
            icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}[level]
            report += f"  {icon} {level}: {count} ({pct:.1f}%)\n"

        report += f"""
  需重點關注的學生 (Top 10):
"""
        for _, row in at_risk.head(10).iterrows():
            report += f"    [{row['risk_level']}] {row.get('name', row.name)}: "
            report += f"平均 {row['avg_score']:.1f}, 風險分數 {row['risk_score']:.1f}\n"

        # 學習模式
        if patterns:
            report += f"""
五、學習模式分析
{'='*40}
"""
            if 'engagement_stats' in patterns:
                eng = patterns['engagement_stats']
                report += f"  平均學習時長: {eng['avg_total_minutes']:.0f} 分鐘\n"
                report += f"  平均每次學習: {eng['avg_session_length']:.0f} 分鐘\n"
                report += f"  平均學習次數: {eng['avg_session_count']:.1f} 次\n"

            if 'daily_distribution' in patterns:
                report += "\n  每日學習分佈:\n"
                for day, count in patterns['daily_distribution'].items():
                    bar = '█' * int(count / max(patterns['daily_distribution'].values()) * 20)
                    report += f"    {day}: {count:4} {bar}\n"

        # 教學效果
        teaching = self.evaluate_teaching_effectiveness()
        if not teaching.empty:
            report += f"""
六、教學效果評估
{'='*40}
  教師排名 (按效果分數):
"""
            for i, (teacher, row) in enumerate(teaching.head(5).iterrows(), 1):
                report += f"    {i}. {teacher}: 效果分數 {row['effectiveness_score']:.1f}\n"
                report += f"       平均分: {row['avg_score']:.1f}, 及格率: {row['pass_rate']:.1f}%\n"

        # 干預建議
        report += f"""
七、干預建議
{'='*40}
  需立即干預的學生: {len([r for r in recommendations if r['priority'] == 'URGENT'])}
  需重點關注的學生: {len([r for r in recommendations if r['priority'] == 'HIGH'])}
"""
        for rec in recommendations[:5]:
            report += f"""
  [{rec['priority']}] {rec['name']} ({rec['student_id']}):
    平均分: {rec['avg_score']:.1f}, 風險分數: {rec['risk_score']:.1f}
    建議措施:
"""
            for action in rec['recommended_actions'][:3]:
                report += f"      - {action}\n"

        report += f"""
八、行動計劃
{'='*40}

1. 短期行動 (1-2週):
   - 與高風險學生進行個別談話
   - 通知家長並建立溝通機制
   - 安排補習和課後輔導

2. 中期計劃 (1-2月):
   - 實施個性化學習計劃
   - 定期追蹤進度
   - 調整教學策略

3. 長期策略 (學期):
   - 建立預警系統
   - 優化課程設計
   - 培訓教師差異化教學能力

{'='*80}
                        報告結束
{'='*80}
"""
        return report


def generate_education_data(n_students: int = 500,
                            n_teachers: int = 30,
                            seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """生成模擬教育數據"""
    np.random.seed(seed)
    today = datetime.now()

    # 科目
    subjects = ['數學', '國文', '英文', '物理', '化學', '歷史', '地理']

    # 班級
    classes = [f'{grade}{section}班' for grade in [1, 2, 3] for section in ['A', 'B', 'C', 'D']]

    # 教師
    teachers = []
    for i in range(1, n_teachers + 1):
        teachers.append({
            'teacher_id': f'T{i:03d}',
            'name': f'Teacher_{i}',
            'subject': np.random.choice(subjects),
            'experience_years': np.random.randint(1, 30)
        })
    teachers_df = pd.DataFrame(teachers)

    # 學生
    students = []
    for i in range(1, n_students + 1):
        class_id = np.random.choice(classes)
        students.append({
            'student_id': f'S{i:05d}',
            'name': f'Student_{i}',
            'class_id': class_id,
            'grade': int(class_id[0]),
            'gender': np.random.choice(['M', 'F']),
            'enrollment_date': today - timedelta(days=np.random.randint(365, 1095)),
            'base_ability': np.random.normal(70, 15)  # 基礎能力
        })
    students_df = pd.DataFrame(students)

    # 成績記錄
    exam_types = ['期中考', '期末考', '平時測驗']
    grades = []

    for _, student in students_df.iterrows():
        student_id = student['student_id']
        base_ability = student['base_ability']

        for subject in subjects:
            # 學生在不同科目的表現差異
            subject_aptitude = np.random.normal(0, 10)

            for exam_type in exam_types:
                # 考試難度
                exam_difficulty = np.random.normal(0, 5)

                # 計算分數
                score = base_ability + subject_aptitude - exam_difficulty + np.random.normal(0, 8)
                score = np.clip(score, 0, 100)

                # 隨機選擇教師
                subject_teachers = teachers_df[teachers_df['subject'] == subject]
                if len(subject_teachers) > 0:
                    teacher_id = subject_teachers.sample(1).iloc[0]['teacher_id']
                else:
                    teacher_id = teachers_df.sample(1).iloc[0]['teacher_id']

                grades.append({
                    'record_id': f'G{len(grades)+1:07d}',
                    'student_id': student_id,
                    'subject': subject,
                    'exam_type': exam_type,
                    'score': round(score, 1),
                    'teacher_id': teacher_id,
                    'class_id': student['class_id'],
                    'exam_date': today - timedelta(days=np.random.randint(0, 180))
                })

    grades_df = pd.DataFrame(grades)

    # 學習活動記錄
    activity_types = ['視頻學習', '作業練習', '線上測驗', '討論參與', '資料閱讀']
    activities = []

    for _, student in students_df.iterrows():
        student_id = student['student_id']
        # 學習活躍度與基礎能力相關
        activity_level = max(1, int(student['base_ability'] / 10))

        for _ in range(activity_level * 5):
            activity_time = today - timedelta(
                days=np.random.randint(0, 90),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )

            activities.append({
                'activity_id': f'A{len(activities)+1:08d}',
                'student_id': student_id,
                'activity_type': np.random.choice(activity_types),
                'activity_time': activity_time,
                'duration_minutes': np.random.randint(5, 120),
                'subject': np.random.choice(subjects),
                'completed': np.random.random() > 0.1
            })

    activities_df = pd.DataFrame(activities)

    return students_df, grades_df, activities_df


def main():
    """執行學生績效分析範例"""
    print("="*80)
    print(" "*20 + "學生績效分析")
    print("="*80)

    # 準備數據
    print("\n[1/4] 準備教育數據...")
    students, grades, activities = generate_education_data(n_students=500, n_teachers=30)

    print(f"  ✓ 學生數: {len(students):,}")
    print(f"  ✓ 成績記錄: {len(grades):,}")
    print(f"  ✓ 學習活動: {len(activities):,}")
    print(f"  ✓ 平均分數: {grades['score'].mean():.1f}")

    # 初始化分析器
    print("\n[2/4] 初始化分析器...")
    analyzer = StudentAnalyzer(students, grades, activities)
    print("  ✓ 分析器初始化完成")

    # 學業分析
    print("\n[3/4] 分析學業成績...")
    academic = analyzer.analyze_academic_performance()
    print(f"\n  📊 成績概覽:")
    print(f"     平均分: {academic['overall']['mean']:.1f}")
    print(f"     及格率: {academic['overall']['pass_rate']:.1f}%")
    print(f"     優秀率: {academic['overall']['excellent_rate']:.1f}%")

    # 風險學生
    print("\n[4/4] 識別風險學生...")
    at_risk = analyzer.identify_at_risk_students()
    high_risk_count = len(at_risk[at_risk['risk_level'].isin(['High', 'Critical'])])
    print(f"\n  ⚠️ 高風險學生: {high_risk_count} ({high_risk_count/len(at_risk)*100:.1f}%)")

    # 生成報告
    print("\n" + "="*80)
    report = analyzer.generate_report()
    print(report)

    # 保存
    try:
        with open('data/outputs/education_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 報告已保存至: data/outputs/education_analysis_report.txt")
    except Exception as e:
        print(f"\n⚠️ 無法保存報告: {e}")

    return analyzer


if __name__ == "__main__":
    analyzer = main()
