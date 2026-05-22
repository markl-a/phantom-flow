"""
生成專案統計報告

這個腳本會統計所有Kaggle解決方案的數量、分布和質量指標
"""

from pathlib import Path
from collections import defaultdict
import json


def count_solutions():
    """統計所有解決方案"""
    base_dir = Path('/home/user/Data-Analysis-with-Chatbots/kaggle_solutions')

    stats = {
        'total': 0,
        'by_category': {},
        'files': {
            'solution_files': 0,
            'readme_files': 0
        }
    }

    # 統計每個類別
    for category_dir in sorted(base_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue

        if category_dir.name in ['__pycache__', '.git']:
            continue

        solutions = [d for d in category_dir.iterdir()
                    if d.is_dir() and not d.name.startswith('.')]

        count = len(solutions)
        stats['by_category'][category_dir.name] = count
        stats['total'] += count

        # 統計文件
        for solution_dir in solutions:
            if (solution_dir / 'solution.py').exists():
                stats['files']['solution_files'] += 1
            if (solution_dir / 'README.md').exists():
                stats['files']['readme_files'] += 1

    return stats


def generate_report():
    """生成統計報告"""
    stats = count_solutions()

    print("=" * 80)
    print("Kaggle 解決方案統計報告".center(80))
    print("=" * 80)
    print()

    print(f"📊 總解決方案數: {stats['total']}")
    print(f"📄 Solution 文件數: {stats['files']['solution_files']}")
    print(f"📖 README 文件數: {stats['files']['readme_files']}")
    print(f"✅ 文檔完整度: {stats['files']['readme_files'] / stats['total'] * 100:.1f}%")
    print()

    print("各類別統計:")
    print("-" * 80)

    # 中文類別名稱映射
    category_names = {
        '01_structured_data': '結構化數據',
        '02_time_series': '時間序列',
        '03_nlp': '自然語言處理',
        '04_recommendation': '推薦系統',
        '05_computer_vision': '計算機視覺',
        '06_clustering': '聚類算法',
        '07_special_domains': '特殊領域',
        '08_deep_learning': '深度學習',
        '09_audio_signal': '音訊信號',
        '10_anomaly_detection': '異常檢測',
        '11_graph_networks': '圖神經網絡',
        '12_geospatial': '地理空間',
        '13_feature_engineering': '特徵工程',
        '14_ensemble_methods': '集成學習',
        '15_bayesian_methods': '貝葉斯方法',
        '16_optimization': '優化算法',
        '17_multimodal': '多模態學習'
    }

    for category, count in sorted(stats['by_category'].items()):
        chinese_name = category_names.get(category, category)
        percentage = count / stats['total'] * 100
        bar = '█' * int(percentage / 2)
        print(f"{category:30} {chinese_name:15} {count:4} ({percentage:5.1f}%) {bar}")

    print()
    print("=" * 80)

    # 生成JSON報告
    report_file = Path('/home/user/Data-Analysis-with-Chatbots/scripts/solution_stats.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"✅ 詳細統計已保存至: {report_file}")

    return stats


def generate_markdown_summary():
    """生成Markdown格式的統計摘要"""
    stats = count_solutions()

    markdown = f"""# Kaggle 解決方案統計摘要

## 總覽

- **總解決方案數**: {stats['total']}
- **Solution 文件**: {stats['files']['solution_files']}
- **README 文件**: {stats['files']['readme_files']}
- **文檔完整度**: {stats['files']['readme_files'] / stats['total'] * 100:.1f}%

## 分類統計

| 類別 | 中文名稱 | 數量 | 百分比 |
|------|---------|------|--------|
"""

    category_names = {
        '01_structured_data': '結構化數據',
        '02_time_series': '時間序列',
        '03_nlp': '自然語言處理',
        '04_recommendation': '推薦系統',
        '05_computer_vision': '計算機視覺',
        '06_clustering': '聚類算法',
        '07_special_domains': '特殊領域',
        '08_deep_learning': '深度學習',
        '09_audio_signal': '音訊信號',
        '10_anomaly_detection': '異常檢測',
        '11_graph_networks': '圖神經網絡',
        '12_geospatial': '地理空間',
        '13_feature_engineering': '特徵工程',
        '14_ensemble_methods': '集成學習',
        '15_bayesian_methods': '貝葉斯方法',
        '16_optimization': '優化算法',
        '17_multimodal': '多模態學習'
    }

    for category, count in sorted(stats['by_category'].items()):
        chinese_name = category_names.get(category, category)
        percentage = count / stats['total'] * 100
        markdown += f"| {category} | {chinese_name} | {count} | {percentage:.1f}% |\n"

    # 保存Markdown
    summary_file = Path('/home/user/Data-Analysis-with-Chatbots/SOLUTIONS_SUMMARY.md')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"📝 Markdown摘要已保存至: {summary_file}")


if __name__ == "__main__":
    stats = generate_report()
    generate_markdown_summary()
