#!/usr/bin/env python3
"""Kaggle 解決方案質量驗證工具

此腳本批量檢查所有 500 個解決方案的質量，包括：
- 文件完整性檢查
- Python 語法檢查
- 導入依賴檢查
- 代碼風格檢查
- 文檔質量檢查

使用方法:
    python scripts/validate_solutions.py
    python scripts/validate_solutions.py --category 02_time_series
    python scripts/validate_solutions.py --check syntax
    python scripts/validate_solutions.py --report
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict


class SolutionValidator:
    """解決方案驗證器"""

    def __init__(self, kaggle_dir: Path = None, verbose: bool = False):
        """初始化驗證器

        Args:
            kaggle_dir: Kaggle 解決方案根目錄
            verbose: 是否顯示詳細信息
        """
        if kaggle_dir is None:
            kaggle_dir = Path(__file__).parent.parent / 'kaggle_solutions'

        self.kaggle_dir = kaggle_dir
        self.verbose = verbose
        self.results = defaultdict(list)

    def check_file_completeness(self, solution_path: Path) -> Dict:
        """檢查文件完整性

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            檢查結果字典
        """
        result = {
            'has_solution': (solution_path / 'solution.py').exists(),
            'has_readme': (solution_path / 'README.md').exists(),
            'has_init': (solution_path / '__init__.py').exists(),
            'has_requirements': (solution_path / 'requirements.txt').exists(),
        }

        # 計算完整度得分
        score = sum([
            result['has_solution'] * 50,  # solution.py 最重要
            result['has_readme'] * 40,     # README 很重要
            result['has_init'] * 5,        # __init__.py 可選
            result['has_requirements'] * 5, # requirements.txt 可選
        ])

        result['completeness_score'] = score
        result['status'] = 'pass' if score >= 90 else ('warning' if score >= 50 else 'fail')

        return result

    def check_python_syntax(self, solution_path: Path) -> Dict:
        """檢查 Python 語法

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            檢查結果字典
        """
        solution_file = solution_path / 'solution.py'

        if not solution_file.exists():
            return {'status': 'skip', 'message': 'solution.py 不存在'}

        try:
            code = solution_file.read_text(encoding='utf-8')
            ast.parse(code)
            return {'status': 'pass', 'message': '語法正確'}
        except SyntaxError as e:
            return {
                'status': 'fail',
                'message': f'語法錯誤: {e.msg} (第 {e.lineno} 行)',
                'lineno': e.lineno,
            }
        except Exception as e:
            return {'status': 'error', 'message': f'無法解析: {str(e)}'}

    def check_imports(self, solution_path: Path) -> Dict:
        """檢查導入依賴

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            檢查結果字典
        """
        solution_file = solution_path / 'solution.py'

        if not solution_file.exists():
            return {'status': 'skip', 'imports': []}

        try:
            code = solution_file.read_text(encoding='utf-8')
            tree = ast.parse(code)

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])

            # 常見的機器學習庫
            common_libs = {
                'sklearn', 'tensorflow', 'keras', 'torch', 'xgboost',
                'lightgbm', 'pandas', 'numpy', 'scipy', 'matplotlib',
                'seaborn', 'plotly', 'cv2', 'transformers', 'nltk', 'spacy'
            }

            detected_libs = set(imports) & common_libs

            return {
                'status': 'pass',
                'imports': list(set(imports)),
                'ml_libraries': list(detected_libs),
                'total_imports': len(set(imports)),
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def check_code_style(self, solution_path: Path) -> Dict:
        """檢查代碼風格

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            檢查結果字典
        """
        solution_file = solution_path / 'solution.py'

        if not solution_file.exists():
            return {'status': 'skip'}

        try:
            code = solution_file.read_text(encoding='utf-8')

            issues = []

            # 檢查文件是否有 docstring
            if not code.strip().startswith('"""') and not code.strip().startswith("'''"):
                issues.append('缺少文件級 docstring')

            # 檢查是否有函數定義
            tree = ast.parse(code)
            has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))

            if has_functions:
                # 檢查函數是否有 docstring
                funcs_without_docs = 0
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not ast.get_docstring(node):
                            funcs_without_docs += 1

                if funcs_without_docs > 0:
                    issues.append(f'{funcs_without_docs} 個函數缺少 docstring')

            # 檢查行長度
            long_lines = [i+1 for i, line in enumerate(code.split('\n')) if len(line) > 120]
            if long_lines:
                issues.append(f'{len(long_lines)} 行超過 120 字符')

            # 計算代碼行數
            lines = code.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            comment_lines = [l for l in lines if l.strip().startswith('#')]

            result = {
                'status': 'warning' if issues else 'pass',
                'issues': issues,
                'total_lines': len(lines),
                'code_lines': len(code_lines),
                'comment_lines': len(comment_lines),
                'comment_ratio': len(comment_lines) / max(len(code_lines), 1),
            }

            return result

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def check_readme_quality(self, solution_path: Path) -> Dict:
        """檢查 README 質量

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            檢查結果字典
        """
        readme_file = solution_path / 'README.md'

        if not readme_file.exists():
            return {'status': 'fail', 'message': 'README.md 不存在'}

        try:
            content = readme_file.read_text(encoding='utf-8')

            # 檢查必要章節
            required_sections = ['描述', '目標', '使用', '方法']
            missing_sections = [s for s in required_sections if s not in content]

            # 檢查字數
            word_count = len(content)

            # 檢查是否有代碼塊
            has_code_blocks = '```' in content

            issues = []
            if missing_sections:
                issues.append(f'缺少章節: {", ".join(missing_sections)}')
            if word_count < 500:
                issues.append(f'內容過短 ({word_count} 字符)')
            if not has_code_blocks:
                issues.append('缺少代碼示例')

            return {
                'status': 'warning' if issues else 'pass',
                'issues': issues,
                'word_count': word_count,
                'has_code_blocks': has_code_blocks,
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def validate_solution(self, solution_path: Path) -> Dict:
        """驗證單個解決方案

        Args:
            solution_path: 解決方案目錄路徑

        Returns:
            完整的驗證結果
        """
        result = {
            'name': solution_path.name,
            'path': str(solution_path.relative_to(self.kaggle_dir.parent)),
            'category': solution_path.parent.name,
        }

        # 執行各項檢查
        result['completeness'] = self.check_file_completeness(solution_path)
        result['syntax'] = self.check_python_syntax(solution_path)
        result['imports'] = self.check_imports(solution_path)
        result['style'] = self.check_code_style(solution_path)
        result['readme'] = self.check_readme_quality(solution_path)

        # 計算總體得分
        scores = []
        if result['completeness']['status'] == 'pass':
            scores.append(result['completeness']['completeness_score'])
        if result['syntax']['status'] == 'pass':
            scores.append(100)
        elif result['syntax']['status'] == 'fail':
            scores.append(0)

        result['overall_score'] = sum(scores) / len(scores) if scores else 0
        result['overall_status'] = 'pass' if result['overall_score'] >= 80 else ('warning' if result['overall_score'] >= 50 else 'fail')

        return result

    def validate_category(self, category: str) -> List[Dict]:
        """驗證特定類別的所有解決方案

        Args:
            category: 類別 ID

        Returns:
            驗證結果列表
        """
        category_path = self.kaggle_dir / category
        if not category_path.exists():
            print(f"❌ 類別 '{category}' 不存在")
            return []

        results = []
        solutions = sorted([d for d in category_path.iterdir() if d.is_dir() and not d.name.startswith('.')])

        print(f"\n驗證 {category} ({len(solutions)} 個解決方案)...")

        for solution_dir in solutions:
            if self.verbose:
                print(f"  檢查 {solution_dir.name}...")

            result = self.validate_solution(solution_dir)
            results.append(result)

            # 顯示簡要狀態
            status_icon = {
                'pass': '✅',
                'warning': '⚠️',
                'fail': '❌',
                'skip': '⏭️',
                'error': '💥',
            }.get(result['overall_status'], '❓')

            print(f"    {status_icon} {solution_dir.name:50s} 得分: {result['overall_score']:.0f}")

        return results

    def validate_all(self) -> Dict[str, List[Dict]]:
        """驗證所有解決方案

        Returns:
            按類別組織的驗證結果
        """
        all_results = {}

        categories = sorted([d for d in self.kaggle_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

        for category_dir in categories:
            category_results = self.validate_category(category_dir.name)
            all_results[category_dir.name] = category_results

        return all_results

    def generate_report(self, results: Dict[str, List[Dict]], output_file: Optional[Path] = None):
        """生成驗證報告

        Args:
            results: 驗證結果
            output_file: 輸出文件路徑
        """
        # 統計信息
        total_solutions = sum(len(r) for r in results.values())
        passed = sum(1 for r in results.values() for sol in r if sol['overall_status'] == 'pass')
        warnings = sum(1 for r in results.values() for sol in r if sol['overall_status'] == 'warning')
        failed = sum(1 for r in results.values() for sol in r if sol['overall_status'] == 'fail')

        # 生成報告
        report = []
        report.append("=" * 80)
        report.append("Kaggle 解決方案質量驗證報告")
        report.append("=" * 80)
        report.append("")
        report.append(f"總解決方案數: {total_solutions}")
        report.append(f"通過: {passed} ({passed/total_solutions*100:.1f}%)")
        report.append(f"警告: {warnings} ({warnings/total_solutions*100:.1f}%)")
        report.append(f"失敗: {failed} ({failed/total_solutions*100:.1f}%)")
        report.append("")

        # 各類別統計
        report.append("各類別統計:")
        report.append("-" * 80)

        for category, category_results in sorted(results.items()):
            cat_passed = sum(1 for sol in category_results if sol['overall_status'] == 'pass')
            cat_total = len(category_results)
            cat_avg_score = sum(sol['overall_score'] for sol in category_results) / cat_total if cat_total > 0 else 0

            report.append(f"{category:30s} {cat_passed:3d}/{cat_total:3d} 通過  平均得分: {cat_avg_score:.1f}")

        report.append("")

        # 常見問題
        report.append("常見問題:")
        report.append("-" * 80)

        # 語法錯誤
        syntax_errors = [(sol['name'], sol['syntax']) for r in results.values() for sol in r if sol['syntax']['status'] == 'fail']
        if syntax_errors:
            report.append(f"\n語法錯誤 ({len(syntax_errors)} 個):")
            for name, error in syntax_errors[:10]:  # 只顯示前 10 個
                report.append(f"  - {name}: {error['message']}")

        # 缺少文件
        missing_files = [(sol['name'], sol['completeness']) for r in results.values() for sol in r if sol['completeness']['status'] == 'fail']
        if missing_files:
            report.append(f"\n文件不完整 ({len(missing_files)} 個):")
            for name, comp in missing_files[:10]:
                issues = []
                if not comp['has_solution']:
                    issues.append('solution.py')
                if not comp['has_readme']:
                    issues.append('README.md')
                report.append(f"  - {name}: 缺少 {', '.join(issues)}")

        report.append("")
        report.append("=" * 80)
        report.append("報告生成完成")
        report.append("=" * 80)

        # 輸出報告
        report_text = '\n'.join(report)
        print(report_text)

        # 保存到文件
        if output_file:
            output_file.write_text(report_text, encoding='utf-8')
            print(f"\n報告已保存到: {output_file}")

        # 保存 JSON 格式的詳細結果
        if output_file:
            json_file = output_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"詳細結果已保存到: {json_file}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Kaggle 解決方案質量驗證工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 驗證所有解決方案
  python scripts/validate_solutions.py

  # 驗證特定類別
  python scripts/validate_solutions.py --category 02_time_series

  # 生成詳細報告
  python scripts/validate_solutions.py --report

  # 只檢查語法
  python scripts/validate_solutions.py --check syntax

  # 詳細模式
  python scripts/validate_solutions.py --verbose
        """
    )

    parser.add_argument('--category', type=str,
                       help='只驗證特定類別')
    parser.add_argument('--check', type=str,
                       choices=['syntax', 'imports', 'style', 'readme', 'all'],
                       default='all',
                       help='指定檢查類型')
    parser.add_argument('--report', action='store_true',
                       help='生成詳細報告')
    parser.add_argument('--output', type=str,
                       help='報告輸出文件路徑')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='顯示詳細信息')

    args = parser.parse_args()

    validator = SolutionValidator(verbose=args.verbose)

    # 執行驗證
    if args.category:
        results = {args.category: validator.validate_category(args.category)}
    else:
        results = validator.validate_all()

    # 生成報告
    output_file = Path(args.output) if args.output else Path('validation_report.txt')
    validator.generate_report(results, output_file if args.report else None)


if __name__ == '__main__':
    main()
