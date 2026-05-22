"""
增強版 Kaggle 解決方案驗證工具

提供更深入的代碼質量檢查和詳細報告
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
import re


class EnhancedValidator:
    """增強版驗證器"""

    def __init__(self, base_dir: str = "/home/user/Data-Analysis-with-Chatbots/kaggle_solutions"):
        self.base_dir = Path(base_dir)
        self.results = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'failed': 0,
            'details': []
        }

    def validate_all(self):
        """驗證所有解決方案"""
        print("=" * 80)
        print("增強版 Kaggle 解決方案質量驗證".center(80))
        print("=" * 80)
        print()

        for category_dir in sorted(self.base_dir.iterdir()):
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                self._validate_category(category_dir)

        self._print_summary()
        self._generate_detailed_report()

    def _validate_category(self, category_dir: Path):
        """驗證單個類別"""
        category_name = category_dir.name
        print(f"\n📁 驗證類別: {category_name}")
        print("-" * 80)

        for solution_dir in sorted(category_dir.iterdir()):
            if solution_dir.is_dir():
                self._validate_solution(category_name, solution_dir)

    def _validate_solution(self, category: str, solution_dir: Path):
        """驗證單個解決方案"""
        solution_id = solution_dir.name
        self.results['total'] += 1

        # 檢查項目
        checks = {
            'files_exist': self._check_files_exist(solution_dir),
            'syntax_valid': self._check_syntax(solution_dir),
            'class_structure': self._check_class_structure(solution_dir),
            'methods_complete': self._check_methods_completeness(solution_dir),
            'documentation': self._check_documentation(solution_dir),
            'code_quality': self._check_code_quality(solution_dir),
            'readme_quality': self._check_readme_quality(solution_dir)
        }

        # 計算得分
        score = sum(checks.values()) / len(checks) * 100

        # 判定結果
        if all(checks.values()):
            status = "✅"
            self.results['passed'] += 1
        elif score >= 80:
            status = "⚠️"
            self.results['warnings'] += 1
        else:
            status = "❌"
            self.results['failed'] += 1

        print(f"  {status} {solution_id:45s} 得分: {score:.1f}")

        # 記錄詳情
        self.results['details'].append({
            'category': category,
            'solution': solution_id,
            'score': score,
            'checks': checks,
            'status': status
        })

    def _check_files_exist(self, solution_dir: Path) -> bool:
        """檢查必要文件是否存在"""
        solution_py = solution_dir / 'solution.py'
        readme_md = solution_dir / 'README.md'
        return solution_py.exists() and readme_md.exists()

    def _check_syntax(self, solution_dir: Path) -> bool:
        """檢查Python語法"""
        solution_py = solution_dir / 'solution.py'
        if not solution_py.exists():
            return False

        try:
            with open(solution_py, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True
        except SyntaxError:
            return False

    def _check_class_structure(self, solution_dir: Path) -> bool:
        """檢查類結構"""
        solution_py = solution_dir / 'solution.py'
        if not solution_py.exists():
            return False

        try:
            with open(solution_py, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            # 檢查是否有類定義
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                return False

            # 檢查主類是否有__init__方法
            main_class = classes[0]
            methods = [node.name for node in main_class.body if isinstance(node, ast.FunctionDef)]
            return '__init__' in methods

        except Exception:
            return False

    def _check_methods_completeness(self, solution_dir: Path) -> bool:
        """檢查方法完整性"""
        solution_py = solution_dir / 'solution.py'
        if not solution_py.exists():
            return False

        try:
            with open(solution_py, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if not classes:
                return False

            main_class = classes[0]
            methods = [node.name for node in main_class.body if isinstance(node, ast.FunctionDef)]

            # 檢查必要方法
            required_methods = ['__init__', 'load_data', 'preprocess', 'train', 'evaluate']
            return all(method in methods for method in required_methods)

        except Exception:
            return False

    def _check_documentation(self, solution_dir: Path) -> bool:
        """檢查文檔質量"""
        solution_py = solution_dir / 'solution.py'
        if not solution_py.exists():
            return False

        try:
            with open(solution_py, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查是否有docstring
            has_module_docstring = '"""' in content and content.count('"""') >= 2

            # 檢查類和方法的docstring
            tree = ast.parse(content)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            if not classes:
                return False

            main_class = classes[0]
            has_class_docstring = ast.get_docstring(main_class) is not None

            # 檢查至少50%的方法有docstring
            methods = [node for node in main_class.body if isinstance(node, ast.FunctionDef)]
            if not methods:
                return False

            documented_methods = sum(1 for m in methods if ast.get_docstring(m) is not None)
            docstring_ratio = documented_methods / len(methods)

            return has_module_docstring and has_class_docstring and docstring_ratio >= 0.5

        except Exception:
            return False

    def _check_code_quality(self, solution_dir: Path) -> bool:
        """檢查代碼質量"""
        solution_py = solution_dir / 'solution.py'
        if not solution_py.exists():
            return False

        try:
            with open(solution_py, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查導入語句
            has_imports = 'import ' in content

            # 檢查是否使用標準庫
            has_pandas = 'pandas' in content or 'pd' in content
            has_numpy = 'numpy' in content or 'np' in content

            # 檢查代碼長度（不應太短）
            lines = content.split('\n')
            meaningful_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            has_sufficient_code = len(meaningful_lines) >= 50

            # 檢查是否有main函數
            has_main = 'def main(' in content or 'if __name__' in content

            return has_imports and (has_pandas or has_numpy) and has_sufficient_code and has_main

        except Exception:
            return False

    def _check_readme_quality(self, solution_dir: Path) -> bool:
        """檢查README質量"""
        readme_md = solution_dir / 'README.md'
        if not readme_md.exists():
            return False

        try:
            with open(readme_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # 檢查必要章節
            required_sections = ['問題描述', '解決方案概述', '技術棧', '使用方法']
            has_sections = all(section in content for section in required_sections)

            # 檢查長度
            has_sufficient_content = len(content) >= 500

            # 檢查是否有代碼示例
            has_code_examples = '```' in content

            return has_sections and has_sufficient_content and has_code_examples

        except Exception:
            return False

    def _print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 80)
        print("驗證摘要".center(80))
        print("=" * 80)
        print()
        print(f"總解決方案數: {self.results['total']}")
        print(f"✅ 完全通過: {self.results['passed']} ({self.results['passed']/self.results['total']*100:.1f}%)")
        print(f"⚠️  有警告: {self.results['warnings']} ({self.results['warnings']/self.results['total']*100:.1f}%)")
        print(f"❌ 失敗: {self.results['failed']} ({self.results['failed']/self.results['total']*100:.1f}%)")

        # 計算平均得分
        avg_score = sum(d['score'] for d in self.results['details']) / len(self.results['details'])
        print(f"\n平均質量得分: {avg_score:.1f}/100")

    def _generate_detailed_report(self):
        """生成詳細報告"""
        report_path = Path('/home/user/Data-Analysis-with-Chatbots/scripts/enhanced_validation_report.txt')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Kaggle 解決方案增強驗證詳細報告\n")
            f.write("=" * 80 + "\n\n")

            # 按類別組織
            by_category = {}
            for detail in self.results['details']:
                cat = detail['category']
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(detail)

            for category in sorted(by_category.keys()):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"類別: {category}\n")
                f.write(f"{'=' * 80}\n\n")

                for detail in by_category[category]:
                    f.write(f"{detail['status']} {detail['solution']}\n")
                    f.write(f"   得分: {detail['score']:.1f}/100\n")
                    f.write(f"   檢查項目:\n")
                    for check, passed in detail['checks'].items():
                        status = "✅" if passed else "❌"
                        f.write(f"     {status} {check}\n")
                    f.write("\n")

        print(f"\n✅ 詳細報告已保存至: {report_path}")


def main():
    """主函數"""
    validator = EnhancedValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
