#!/usr/bin/env python3
"""
導入分析腳本 - 檢查所有模組的導入依賴和循環導入問題
"""
import ast
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_imports(file_path: str) -> Tuple[List[str], List[str]]:
    """提取文件中的導入語句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        return [], []

    imports = []
    from_imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_imports.append(node.module)

    return imports, from_imports

def analyze_project_imports(root_dir: str) -> Dict:
    """分析專案中所有 Python 文件的導入"""
    project_path = Path(root_dir)
    results = {
        'files': {},
        'third_party_deps': set(),
        'internal_deps': defaultdict(set),
        'errors': []
    }

    for py_file in project_path.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue

        rel_path = py_file.relative_to(project_path)
        imports, from_imports = extract_imports(str(py_file))

        all_imports = imports + from_imports
        results['files'][str(rel_path)] = {
            'imports': imports,
            'from_imports': from_imports
        }

        # 區分第三方依賴和內部依賴
        for imp in all_imports:
            if imp.startswith('ai_automation_framework'):
                results['internal_deps'][str(rel_path)].add(imp)
            else:
                # 只取頂層包名
                top_level = imp.split('.')[0]
                if top_level not in ['os', 'sys', 'json', 'typing', 're',
                                     'pathlib', 'datetime', 'time', 'logging',
                                     'collections', 'functools', 'itertools',
                                     'asyncio', 'abc', 'enum', 'dataclasses']:
                    results['third_party_deps'].add(top_level)

    return results

def detect_circular_imports(internal_deps: Dict[str, Set[str]]) -> List[Tuple]:
    """檢測循環導入"""
    circular = []

    def has_cycle(file, target, visited, path):
        if file in visited:
            if file == target:
                return path
            return None

        visited.add(file)
        path.append(file)

        if file in internal_deps:
            for dep in internal_deps[file]:
                # 轉換模組名為文件路徑
                dep_file = dep.replace('.', '/') + '.py'
                result = has_cycle(dep_file, target, visited.copy(), path.copy())
                if result:
                    return result

        return None

    for file in internal_deps:
        for dep in internal_deps[file]:
            dep_file = dep.replace('.', '/') + '.py'
            cycle = has_cycle(dep_file, file, set(), [])
            if cycle:
                circular.append(tuple(cycle))

    return circular

def check_installed_packages() -> Set[str]:
    """檢查已安裝的包"""
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        return installed
    except ImportError:
        return set()

def main():
    print("=" * 80)
    print("  導入依賴分析報告")
    print("=" * 80)

    root_dir = '/home/user/Automation_with_AI/ai_automation_framework'
    results = analyze_project_imports(root_dir)

    print("\n" + "─" * 80)
    print("📦 第三方依賴分析")
    print("─" * 80)

    # 檢查已安裝的包
    installed = check_installed_packages()

    third_party = sorted(results['third_party_deps'])
    missing_deps = []
    installed_deps = []

    for dep in third_party:
        # 特殊處理一些包名差異
        package_name_map = {
            'dotenv': 'python-dotenv',
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'yaml': 'PyYAML'
        }

        check_name = package_name_map.get(dep, dep)
        normalized_name = check_name.lower().replace('-', '_').replace('.', '_')

        is_installed = any(
            normalized_name in pkg.lower().replace('-', '_').replace('.', '_')
            for pkg in installed
        )

        if is_installed:
            print(f"  ✅ {dep:30} - 已安裝")
            installed_deps.append(dep)
        else:
            print(f"  ❌ {dep:30} - 未安裝 (CRITICAL)")
            missing_deps.append(dep)

    print(f"\n  總計: {len(third_party)} 個第三方依賴")
    print(f"  已安裝: {len(installed_deps)}")
    print(f"  未安裝: {len(missing_deps)}")

    if missing_deps:
        print(f"\n  ⚠️  缺失的依賴:")
        for dep in missing_deps:
            print(f"    - {dep}")

    # 內部依賴分析
    print("\n" + "─" * 80)
    print("🔗 內部模組依賴關係")
    print("─" * 80)

    for file, deps in sorted(results['internal_deps'].items()):
        if deps:
            print(f"\n  {file}")
            for dep in sorted(deps):
                print(f"    → {dep}")

    # 循環導入檢測
    print("\n" + "─" * 80)
    print("🔄 循環導入檢測")
    print("─" * 80)

    circular = detect_circular_imports(results['internal_deps'])
    if circular:
        print(f"\n  ⚠️  發現 {len(circular)} 個循環導入:")
        for i, cycle in enumerate(circular, 1):
            print(f"\n  循環 {i}:")
            for file in cycle:
                print(f"    → {file}")
    else:
        print("\n  ✅ 未發現循環導入")

    # 詳細文件導入列表
    print("\n" + "─" * 80)
    print("📄 詳細文件導入列表")
    print("─" * 80)

    for file, data in sorted(results['files'].items()):
        if data['imports'] or data['from_imports']:
            print(f"\n  {file}")
            if data['imports']:
                print(f"    import: {', '.join(sorted(data['imports']))}")
            if data['from_imports']:
                print(f"    from: {', '.join(sorted(data['from_imports']))}")

    print("\n" + "=" * 80)
    print("  總結")
    print("=" * 80)

    critical_issues = len(missing_deps)
    warnings = len(circular)

    print(f"\n  🔴 Critical 問題: {critical_issues}")
    print(f"  🟡 Warning 問題: {warnings}")
    print(f"  ℹ️  Info: 分析了 {len(results['files'])} 個文件")

    if critical_issues == 0 and warnings == 0:
        print("\n  ✅ 所有檢查通過！")
    else:
        print("\n  ⚠️  發現問題需要修復")

    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
