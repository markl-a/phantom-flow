"""
A/B 測試分析範例

這個範例展示如何分析營銷活動的A/B測試結果，
包含統計顯著性檢驗和商業決策建議。

真實應用場景:
- Email 行銷主題行測試
- 網站按鈕顏色/文案測試
- 優惠券金額測試
- 產品定價測試
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ABTestResult:
    """A/B測試結果"""
    test_name: str
    control_group: str
    treatment_group: str
    metric_name: str
    control_value: float
    treatment_value: float
    lift: float
    lift_percentage: float
    p_value: float
    confidence_level: float
    is_significant: bool
    sample_size_control: int
    sample_size_treatment: int
    recommendation: str


class ABTestAnalyzer:
    """
    A/B測試分析器

    支持多種測試指標:
    - 轉換率 (Conversion Rate)
    - 平均訂單金額 (Average Order Value)
    - 點擊率 (Click-Through Rate)
    - 留存率 (Retention Rate)
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        初始化分析器

        Args:
            confidence_level: 置信水平 (默認95%)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        self.results: List[ABTestResult] = []

    def analyze_conversion_rate(self,
                                control_conversions: int,
                                control_total: int,
                                treatment_conversions: int,
                                treatment_total: int,
                                test_name: str = "Conversion Rate Test") -> ABTestResult:
        """
        分析轉換率差異

        使用雙比例Z檢驗
        """
        # 計算轉換率
        p1 = control_conversions / control_total
        p2 = treatment_conversions / treatment_total

        # 合併比例
        p_pooled = (control_conversions + treatment_conversions) / (control_total + treatment_total)

        # 標準誤差
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))

        # Z統計量
        z_stat = (p2 - p1) / se if se > 0 else 0

        # P值 (雙尾檢驗)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        # 計算提升
        lift = p2 - p1
        lift_pct = ((p2 - p1) / p1 * 100) if p1 > 0 else 0

        is_significant = p_value < self.alpha

        # 生成建議
        recommendation = self._generate_recommendation(
            is_significant, lift_pct, 'conversion_rate'
        )

        result = ABTestResult(
            test_name=test_name,
            control_group="Control",
            treatment_group="Treatment",
            metric_name="Conversion Rate",
            control_value=p1,
            treatment_value=p2,
            lift=lift,
            lift_percentage=lift_pct,
            p_value=p_value,
            confidence_level=self.confidence_level,
            is_significant=is_significant,
            sample_size_control=control_total,
            sample_size_treatment=treatment_total,
            recommendation=recommendation
        )

        self.results.append(result)
        return result

    def analyze_continuous_metric(self,
                                  control_values: np.ndarray,
                                  treatment_values: np.ndarray,
                                  metric_name: str = "Average Order Value",
                                  test_name: str = "AOV Test") -> ABTestResult:
        """
        分析連續指標差異 (如訂單金額)

        使用獨立樣本t檢驗
        """
        # 計算統計量
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)

        # Welch's t-test (不假設等方差)
        t_stat, p_value = stats.ttest_ind(treatment_values, control_values, equal_var=False)

        # 計算提升
        lift = treatment_mean - control_mean
        lift_pct = ((treatment_mean - control_mean) / control_mean * 100) if control_mean > 0 else 0

        is_significant = p_value < self.alpha

        recommendation = self._generate_recommendation(
            is_significant, lift_pct, 'continuous'
        )

        result = ABTestResult(
            test_name=test_name,
            control_group="Control",
            treatment_group="Treatment",
            metric_name=metric_name,
            control_value=control_mean,
            treatment_value=treatment_mean,
            lift=lift,
            lift_percentage=lift_pct,
            p_value=p_value,
            confidence_level=self.confidence_level,
            is_significant=is_significant,
            sample_size_control=len(control_values),
            sample_size_treatment=len(treatment_values),
            recommendation=recommendation
        )

        self.results.append(result)
        return result

    def calculate_sample_size(self,
                              baseline_rate: float,
                              minimum_detectable_effect: float,
                              power: float = 0.8) -> int:
        """
        計算所需樣本大小

        Args:
            baseline_rate: 基準轉換率
            minimum_detectable_effect: 最小可檢測效應 (相對變化)
            power: 統計檢定力 (默認80%)

        Returns:
            每組所需樣本數
        """
        # 效應大小
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        # 使用正態近似計算
        z_alpha = stats.norm.ppf(1 - self.alpha/2)
        z_beta = stats.norm.ppf(power)

        # 合併標準差估計
        p_bar = (p1 + p2) / 2

        numerator = (z_alpha * np.sqrt(2 * p_bar * (1 - p_bar)) +
                    z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2

        n = numerator / denominator if denominator > 0 else float('inf')

        return int(np.ceil(n))

    def _generate_recommendation(self,
                                 is_significant: bool,
                                 lift_pct: float,
                                 metric_type: str) -> str:
        """生成商業建議"""
        if is_significant:
            if lift_pct > 10:
                return "強烈建議採用實驗組方案，效果顯著且提升明顯"
            elif lift_pct > 5:
                return "建議採用實驗組方案，統計顯著且有實質提升"
            elif lift_pct > 0:
                return "可考慮採用實驗組，但提升幅度較小，需評估實施成本"
            else:
                return "實驗組表現較差，建議維持原方案"
        else:
            if abs(lift_pct) < 2:
                return "差異不顯著，兩方案效果相當，可根據其他因素決定"
            else:
                return "差異不顯著，建議延長測試或增加樣本量"

    def generate_report(self) -> str:
        """生成分析報告"""
        if not self.results:
            return "尚無分析結果"

        report = f"""
{'='*80}
                    A/B 測試分析報告
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*80}

測試設定:
  置信水平: {self.confidence_level*100:.0f}%
  顯著性水準 (α): {self.alpha}

"""

        for i, result in enumerate(self.results, 1):
            status = "✅ 顯著" if result.is_significant else "❌ 不顯著"
            direction = "↑" if result.lift > 0 else "↓"

            report += f"""
{'='*40}
測試 {i}: {result.test_name}
{'='*40}

指標: {result.metric_name}

組別比較:
  對照組 ({result.control_group}):
    - 樣本數: {result.sample_size_control:,}
    - 數值: {result.control_value:.4f}

  實驗組 ({result.treatment_group}):
    - 樣本數: {result.sample_size_treatment:,}
    - 數值: {result.treatment_value:.4f}

效果評估:
  絕對提升: {result.lift:+.4f}
  相對提升: {result.lift_percentage:+.2f}% {direction}
  P值: {result.p_value:.4f}
  統計顯著性: {status}

建議: {result.recommendation}
"""

        # 摘要
        significant_count = sum(1 for r in self.results if r.is_significant)
        positive_count = sum(1 for r in self.results if r.lift > 0)

        report += f"""
{'='*80}
                        摘要
{'='*80}

總測試數: {len(self.results)}
顯著測試: {significant_count}
正向提升: {positive_count}

"""

        return report


def generate_email_campaign_data(n_recipients: int = 10000) -> pd.DataFrame:
    """
    生成Email行銷A/B測試數據

    測試場景: 比較兩種Email主題行的效果
    - A: "限時優惠！今日下單享8折"
    - B: "專屬好禮等你來！會員獨享優惠"
    """
    np.random.seed(42)

    # 分配到兩組
    group = np.random.choice(['A', 'B'], n_recipients)

    data = []
    for i, g in enumerate(group):
        customer_id = f'CUST{i+1:06d}'

        # A組基礎開信率 25%, B組 28%
        open_rate = 0.25 if g == 'A' else 0.28
        opened = np.random.random() < open_rate

        # 開信後點擊率: A組 15%, B組 18%
        click_rate = 0.15 if g == 'A' else 0.18
        clicked = opened and (np.random.random() < click_rate)

        # 點擊後轉換率: A組 8%, B組 10%
        conversion_rate = 0.08 if g == 'A' else 0.10
        converted = clicked and (np.random.random() < conversion_rate)

        # 訂單金額 (如果轉換)
        if converted:
            order_amount = np.random.lognormal(5, 0.8)  # 平均約 $150
        else:
            order_amount = 0

        data.append({
            'customer_id': customer_id,
            'group': g,
            'subject_line': '限時優惠！今日下單享8折' if g == 'A' else '專屬好禮等你來！會員獨享優惠',
            'opened': opened,
            'clicked': clicked,
            'converted': converted,
            'order_amount': round(order_amount, 2)
        })

    return pd.DataFrame(data)


def generate_pricing_test_data(n_visitors: int = 5000) -> pd.DataFrame:
    """
    生成定價A/B測試數據

    測試場景: 比較兩種定價策略
    - A: 原價 $99
    - B: 新價 $89
    """
    np.random.seed(123)

    group = np.random.choice(['A', 'B'], n_visitors)

    data = []
    for i, g in enumerate(group):
        visitor_id = f'VIS{i+1:06d}'

        # 定價影響轉換率
        # A組 (高價): 轉換率 3.2%
        # B組 (低價): 轉換率 4.5%
        conversion_rate = 0.032 if g == 'A' else 0.045
        converted = np.random.random() < conversion_rate

        price = 99 if g == 'A' else 89
        revenue = price if converted else 0

        # 額外購買 (加購)
        if converted:
            upsell_rate = 0.25 if g == 'A' else 0.20  # 高價客戶更願意加購
            if np.random.random() < upsell_rate:
                revenue += np.random.choice([29, 49, 79])

        data.append({
            'visitor_id': visitor_id,
            'group': g,
            'price': price,
            'converted': converted,
            'revenue': revenue
        })

    return pd.DataFrame(data)


def main():
    """執行A/B測試分析範例"""
    print("="*80)
    print(" "*25 + "A/B 測試分析範例")
    print("="*80)

    analyzer = ABTestAnalyzer(confidence_level=0.95)

    # ========================================
    # 測試1: Email行銷主題行測試
    # ========================================
    print("\n[測試1] Email行銷主題行A/B測試")
    print("-"*40)

    email_data = generate_email_campaign_data(n_recipients=10000)

    # 分組統計
    group_a = email_data[email_data['group'] == 'A']
    group_b = email_data[email_data['group'] == 'B']

    print(f"A組 (限時優惠): {len(group_a):,} 封")
    print(f"B組 (專屬好禮): {len(group_b):,} 封")

    # 開信率分析
    result_open = analyzer.analyze_conversion_rate(
        control_conversions=group_a['opened'].sum(),
        control_total=len(group_a),
        treatment_conversions=group_b['opened'].sum(),
        treatment_total=len(group_b),
        test_name="Email開信率測試"
    )

    print(f"\n開信率:")
    print(f"  A組: {result_open.control_value*100:.2f}%")
    print(f"  B組: {result_open.treatment_value*100:.2f}%")
    print(f"  提升: {result_open.lift_percentage:+.2f}%")
    print(f"  P值: {result_open.p_value:.4f}")
    print(f"  {'✅ 統計顯著' if result_open.is_significant else '❌ 不顯著'}")

    # 轉換率分析
    result_conv = analyzer.analyze_conversion_rate(
        control_conversions=group_a['converted'].sum(),
        control_total=len(group_a),
        treatment_conversions=group_b['converted'].sum(),
        treatment_total=len(group_b),
        test_name="Email轉換率測試"
    )

    print(f"\n轉換率:")
    print(f"  A組: {result_conv.control_value*100:.3f}%")
    print(f"  B組: {result_conv.treatment_value*100:.3f}%")
    print(f"  提升: {result_conv.lift_percentage:+.2f}%")
    print(f"  {'✅ 統計顯著' if result_conv.is_significant else '❌ 不顯著'}")

    # ========================================
    # 測試2: 定價策略測試
    # ========================================
    print("\n" + "="*80)
    print("[測試2] 產品定價A/B測試")
    print("-"*40)

    pricing_data = generate_pricing_test_data(n_visitors=5000)

    price_a = pricing_data[pricing_data['group'] == 'A']
    price_b = pricing_data[pricing_data['group'] == 'B']

    print(f"A組 ($99定價): {len(price_a):,} 訪客")
    print(f"B組 ($89定價): {len(price_b):,} 訪客")

    # 轉換率分析
    result_pricing_conv = analyzer.analyze_conversion_rate(
        control_conversions=price_a['converted'].sum(),
        control_total=len(price_a),
        treatment_conversions=price_b['converted'].sum(),
        treatment_total=len(price_b),
        test_name="定價轉換率測試"
    )

    print(f"\n轉換率:")
    print(f"  A組 ($99): {result_pricing_conv.control_value*100:.2f}%")
    print(f"  B組 ($89): {result_pricing_conv.treatment_value*100:.2f}%")
    print(f"  提升: {result_pricing_conv.lift_percentage:+.2f}%")

    # 收入分析 (只看有購買的)
    revenue_a = price_a[price_a['revenue'] > 0]['revenue'].values
    revenue_b = price_b[price_b['revenue'] > 0]['revenue'].values

    if len(revenue_a) > 0 and len(revenue_b) > 0:
        result_revenue = analyzer.analyze_continuous_metric(
            control_values=revenue_a,
            treatment_values=revenue_b,
            metric_name="客單價",
            test_name="定價客單價測試"
        )

        print(f"\n客單價 (轉換客戶):")
        print(f"  A組: ${result_revenue.control_value:.2f}")
        print(f"  B組: ${result_revenue.treatment_value:.2f}")
        print(f"  差異: {result_revenue.lift_percentage:+.2f}%")

    # 每訪客收入 (Revenue Per Visitor)
    rpv_a = price_a['revenue'].values
    rpv_b = price_b['revenue'].values

    result_rpv = analyzer.analyze_continuous_metric(
        control_values=rpv_a,
        treatment_values=rpv_b,
        metric_name="每訪客收入 (RPV)",
        test_name="定價RPV測試"
    )

    print(f"\n每訪客收入 (RPV):")
    print(f"  A組: ${result_rpv.control_value:.2f}")
    print(f"  B組: ${result_rpv.treatment_value:.2f}")
    print(f"  差異: {result_rpv.lift_percentage:+.2f}%")
    print(f"  {'✅ 統計顯著' if result_rpv.is_significant else '❌ 不顯著'}")

    # ========================================
    # 樣本量計算範例
    # ========================================
    print("\n" + "="*80)
    print("[附加] 樣本量計算")
    print("-"*40)

    baseline = 0.03  # 基準轉換率 3%
    mde = 0.15  # 希望檢測到 15% 的相對提升

    required_n = analyzer.calculate_sample_size(
        baseline_rate=baseline,
        minimum_detectable_effect=mde,
        power=0.8
    )

    print(f"場景: 基準轉換率 {baseline*100}%，希望檢測 {mde*100}% 相對提升")
    print(f"所需樣本量: 每組至少 {required_n:,} 個樣本")
    print(f"總樣本量: {required_n*2:,}")

    # ========================================
    # 生成完整報告
    # ========================================
    print("\n" + "="*80)
    print("生成完整分析報告...")

    report = analyzer.generate_report()

    # 保存報告
    try:
        with open('data/outputs/ab_test_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("📄 報告已保存至: data/outputs/ab_test_report.txt")
    except Exception as e:
        print(f"⚠️ 無法保存報告: {e}")

    print("\n" + "="*80)
    print("                    分析完成")
    print("="*80)

    return analyzer


if __name__ == "__main__":
    analyzer = main()
