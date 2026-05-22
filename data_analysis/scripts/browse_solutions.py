#!/usr/bin/env python3
"""Kaggle 解決方案瀏覽工具

此腳本提供互動式界面來瀏覽、搜索和查看 500 個 Kaggle 解決方案。

使用方法:
    python scripts/browse_solutions.py
    python scripts/browse_solutions.py --category 02_time_series
    python scripts/browse_solutions.py --search lstm
    python scripts/browse_solutions.py --list
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re


class SolutionBrowser:
    """解決方案瀏覽器"""

    CATEGORY_NAMES = {
        '01_structured_data': '結構化數據與分類',
        '02_time_series': '時間序列分析',
        '03_nlp': '自然語言處理',
        '04_recommendation': '推薦系統',
        '05_computer_vision': '計算機視覺',
        '06_clustering': '聚類與無監督學習',
        '07_special_domains': '特殊領域應用',
        '08_deep_learning': '深度學習',
        '09_audio_signal': '音訊與信號處理',
        '10_anomaly_detection': '異常檢測',
        '11_graph_networks': '圖神經網絡',
        '12_geospatial': '地理空間分析',
        '13_feature_engineering': '特徵工程',
        '14_ensemble_methods': '集成學習方法',
        '15_bayesian_methods': '貝葉斯方法',
        '16_optimization': '優化算法',
        '17_multimodal': '多模態學習',
    }

    def __init__(self, kaggle_dir: Path = None):
        """初始化瀏覽器

        Args:
            kaggle_dir: Kaggle 解決方案根目錄
        """
        if kaggle_dir is None:
            kaggle_dir = Path(__file__).parent.parent / 'kaggle_solutions'

        self.kaggle_dir = kaggle_dir
        self.solutions = self._scan_solutions()

    def _scan_solutions(self) -> Dict[str, List[Dict]]:
        """掃描所有解決方案

        Returns:
            按類別組織的解決方案字典
        """
        solutions = {}

        for category_dir in sorted(self.kaggle_dir.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue

            category_solutions = []
            for solution_dir in sorted(category_dir.iterdir()):
                if not solution_dir.is_dir() or solution_dir.name.startswith('.'):
                    continue

                solution_info = {
                    'name': solution_dir.name,
                    'path': str(solution_dir.relative_to(self.kaggle_dir.parent)),
                    'has_readme': (solution_dir / 'README.md').exists(),
                    'has_solution': (solution_dir / 'solution.py').exists(),
                    'category': category_dir.name,
                }

                # 嘗試從 solution.py 提取描述
                solution_file = solution_dir / 'solution.py'
                if solution_file.exists():
                    try:
                        content = solution_file.read_text(encoding='utf-8')
                        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                        if docstring_match:
                            solution_info['description'] = docstring_match.group(1).strip()[:100]
                    except Exception:
                        pass

                category_solutions.append(solution_info)

            solutions[category_dir.name] = category_solutions

        return solutions

    def list_categories(self):
        """列出所有類別"""
        print("\n" + "=" * 80)
        print("📚 Kaggle 解決方案類別列表")
        print("=" * 80 + "\n")

        for idx, (cat_id, cat_name) in enumerate(self.CATEGORY_NAMES.items(), 1):
            count = len(self.solutions.get(cat_id, []))
            print(f"{idx:2d}. {cat_id:25s} - {cat_name:25s} ({count:3d} 個解決方案)")

        total = sum(len(sols) for sols in self.solutions.values())
        print(f"\n{'=' * 80}")
        print(f"總計: {total} 個解決方案")
        print("=" * 80 + "\n")

    def list_category_solutions(self, category: str):
        """列出特定類別的所有解決方案

        Args:
            category: 類別 ID
        """
        if category not in self.solutions:
            print(f"❌ 類別 '{category}' 不存在")
            self.list_categories()
            return

        solutions = self.solutions[category]
        cat_name = self.CATEGORY_NAMES.get(category, category)

        print("\n" + "=" * 80)
        print(f"📂 {cat_name} ({category})")
        print("=" * 80 + "\n")

        for idx, sol in enumerate(solutions, 1):
            status = "✅" if sol['has_readme'] and sol['has_solution'] else "⚠️"
            name_display = sol['name'].replace('_', ' ').title()

            print(f"{idx:3d}. {status} {sol['name']:40s}")

            if 'description' in sol:
                print(f"       {sol['description'][:70]}...")
            print()

        print(f"{'=' * 80}")
        print(f"總計: {len(solutions)} 個解決方案")
        print("=" * 80 + "\n")

    def search_solutions(self, keyword: str):
        """搜索解決方案

        Args:
            keyword: 搜索關鍵詞
        """
        keyword_lower = keyword.lower()
        results = []

        for category, solutions in self.solutions.items():
            for sol in solutions:
                # 在名稱、描述和 solution.py 內容中搜索
                if keyword_lower in sol['name'].lower():
                    results.append(sol)
                    continue

                if 'description' in sol and keyword_lower in sol['description'].lower():
                    results.append(sol)
                    continue

                # 搜索 solution.py 內容
                solution_file = Path(sol['path']) / 'solution.py'
                if solution_file.exists():
                    try:
                        content = solution_file.read_text(encoding='utf-8').lower()
                        if keyword_lower in content:
                            results.append(sol)
                    except Exception:
                        pass

        print("\n" + "=" * 80)
        print(f"🔍 搜索結果: '{keyword}' (找到 {len(results)} 個)")
        print("=" * 80 + "\n")

        if not results:
            print("未找到匹配的解決方案")
        else:
            for idx, sol in enumerate(results, 1):
                cat_name = self.CATEGORY_NAMES.get(sol['category'], sol['category'])
                print(f"{idx:3d}. {sol['name']:40s} ({cat_name})")
                print(f"       路徑: {sol['path']}")
                if 'description' in sol:
                    print(f"       {sol['description'][:70]}...")
                print()

        print("=" * 80 + "\n")

    def show_statistics(self):
        """顯示統計信息"""
        total = sum(len(sols) for sols in self.solutions.values())
        with_readme = sum(1 for sols in self.solutions.values() for sol in sols if sol['has_readme'])
        with_solution = sum(1 for sols in self.solutions.values() for sol in sols if sol['has_solution'])

        print("\n" + "=" * 80)
        print("📊 統計信息")
        print("=" * 80 + "\n")

        print(f"總解決方案數:     {total}")
        print(f"包含 README:      {with_readme} ({with_readme/total*100:.1f}%)")
        print(f"包含 solution.py: {with_solution} ({with_solution/total*100:.1f}%)")
        print(f"類別數量:         {len(self.solutions)}")

        print("\n各類別解決方案數量:")
        for cat_id, cat_name in self.CATEGORY_NAMES.items():
            count = len(self.solutions.get(cat_id, []))
            bar = "█" * (count // 2)
            print(f"  {cat_name:30s} {count:3d} {bar}")

        print("\n" + "=" * 80 + "\n")

    def interactive_mode(self):
        """互動模式"""
        print("\n" + "=" * 80)
        print("🎯 Kaggle 解決方案瀏覽器 - 互動模式")
        print("=" * 80)
        print("\n可用命令:")
        print("  list              - 列出所有類別")
        print("  cat <類別ID>      - 查看特定類別的解決方案")
        print("  search <關鍵詞>   - 搜索解決方案")
        print("  stats             - 顯示統計信息")
        print("  help              - 顯示幫助")
        print("  quit/exit         - 退出")
        print("\n" + "=" * 80 + "\n")

        while True:
            try:
                command = input("瀏覽器> ").strip()

                if not command:
                    continue

                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else None

                if cmd in ['quit', 'exit', 'q']:
                    print("再見！")
                    break

                elif cmd == 'list':
                    self.list_categories()

                elif cmd == 'cat':
                    if arg:
                        self.list_category_solutions(arg)
                    else:
                        print("❌ 請指定類別 ID，例如: cat 02_time_series")

                elif cmd == 'search':
                    if arg:
                        self.search_solutions(arg)
                    else:
                        print("❌ 請指定搜索關鍵詞，例如: search lstm")

                elif cmd == 'stats':
                    self.show_statistics()

                elif cmd == 'help':
                    print("\n可用命令:")
                    print("  list              - 列出所有類別")
                    print("  cat <類別ID>      - 查看特定類別的解決方案")
                    print("  search <關鍵詞>   - 搜索解決方案")
                    print("  stats             - 顯示統計信息")
                    print("  help              - 顯示幫助")
                    print("  quit/exit         - 退出\n")

                else:
                    print(f"❌ 未知命令: {cmd}。輸入 'help' 查看可用命令。")

            except KeyboardInterrupt:
                print("\n\n再見！")
                break
            except EOFError:
                print("\n\n再見！")
                break
            except Exception as e:
                print(f"❌ 錯誤: {e}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Kaggle 解決方案瀏覽工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 互動模式
  python scripts/browse_solutions.py

  # 列出所有類別
  python scripts/browse_solutions.py --list

  # 查看特定類別
  python scripts/browse_solutions.py --category 02_time_series

  # 搜索解決方案
  python scripts/browse_solutions.py --search lstm

  # 顯示統計
  python scripts/browse_solutions.py --stats
        """
    )

    parser.add_argument('--list', action='store_true',
                       help='列出所有類別')
    parser.add_argument('--category', type=str,
                       help='查看特定類別的解決方案')
    parser.add_argument('--search', type=str,
                       help='搜索解決方案')
    parser.add_argument('--stats', action='store_true',
                       help='顯示統計信息')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='進入互動模式')

    args = parser.parse_args()

    browser = SolutionBrowser()

    # 如果沒有參數，進入互動模式
    if len(sys.argv) == 1:
        browser.interactive_mode()
        return

    if args.list:
        browser.list_categories()

    if args.category:
        browser.list_category_solutions(args.category)

    if args.search:
        browser.search_solutions(args.search)

    if args.stats:
        browser.show_statistics()

    if args.interactive:
        browser.interactive_mode()


if __name__ == '__main__':
    main()
