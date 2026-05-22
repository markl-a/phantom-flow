#!/usr/bin/env python3
"""
導入相容性測試腳本
測試各個模組的實際導入情況
"""
import sys
import importlib
from typing import Dict, List, Tuple

def test_import(module_name: str) -> Tuple[bool, str]:
    """測試模組導入"""
    try:
        importlib.import_module(module_name)
        return True, "Success"
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def check_standard_library() -> Dict:
    """檢查 Python 標準庫模組"""
    print("=" * 80)
    print("  Python 標準庫檢查")
    print("=" * 80)

    stdlib_modules = [
        'os', 'sys', 'json', 'csv', 'email', 'hashlib', 'hmac',
        'imaplib', 'smtplib', 'sqlite3', 'statistics', 'subprocess',
        'threading', 'cProfile', 'pstats', 'concurrent.futures',
        're', 'pathlib', 'datetime', 'time', 'logging',
        'collections', 'functools', 'itertools', 'asyncio',
        'abc', 'enum', 'dataclasses', 'typing', 'io', 'base64'
    ]

    results = {'passed': [], 'failed': []}

    for module in sorted(stdlib_modules):
        success, error = test_import(module)
        if success:
            print(f"  ✅ {module}")
            results['passed'].append(module)
        else:
            print(f"  ❌ {module} - {error}")
            results['failed'].append((module, error))

    print(f"\n  總計: {len(stdlib_modules)} | 通過: {len(results['passed'])} | 失敗: {len(results['failed'])}")
    return results

def check_third_party_dependencies() -> Dict:
    """檢查第三方依賴"""
    print("\n" + "=" * 80)
    print("  第三方依賴實際導入測試")
    print("=" * 80)

    # 從 requirements.txt 提取的主要依賴
    dependencies = {
        'Core LLM': [
            ('openai', 'OpenAI API'),
            ('anthropic', 'Anthropic/Claude API'),
            ('langchain', 'LangChain'),
            ('langchain_community', 'LangChain Community'),
            ('langchain_openai', 'LangChain OpenAI'),
            ('langchain_anthropic', 'LangChain Anthropic'),
        ],
        'Vector & RAG': [
            ('chromadb', 'ChromaDB'),
            ('sentence_transformers', 'Sentence Transformers'),
            ('pypdf', 'PyPDF'),
            ('tiktoken', 'TikToken'),
        ],
        'Data Processing': [
            ('numpy', 'NumPy'),
            ('pandas', 'Pandas'),
            ('scipy', 'SciPy'),
        ],
        'Web & Automation': [
            ('requests', 'Requests'),
            ('aiohttp', 'AIOHTTP'),
            ('httpx', 'HTTPX'),
            ('bs4', 'BeautifulSoup4'),
            ('selenium', 'Selenium'),
        ],
        'Utilities': [
            ('dotenv', 'Python-dotenv'),
            ('pydantic', 'Pydantic'),
            ('rich', 'Rich'),
            ('loguru', 'Loguru'),
        ],
        'Cloud Services': [
            ('boto3', 'AWS SDK'),
            ('azure.storage.blob', 'Azure Storage'),
            ('google.cloud.storage', 'Google Cloud Storage'),
            ('oss2', 'Aliyun OSS'),
        ],
        'Workflow Orchestration': [
            ('temporalio', 'Temporal'),
            ('prefect', 'Prefect'),
            ('celery', 'Celery'),
        ],
        'Media Processing': [
            ('PIL', 'Pillow'),
            ('cv2', 'OpenCV'),
            ('moviepy.editor', 'MoviePy'),
        ],
        'APIs & Services': [
            ('flask', 'Flask'),
            ('fastapi', 'FastAPI'),
            ('graphene', 'Graphene'),
            ('websockets', 'WebSockets'),
        ],
    }

    results = {
        'by_category': {},
        'all_passed': [],
        'all_failed': []
    }

    for category, deps in dependencies.items():
        print(f"\n{'─' * 80}")
        print(f"📦 {category}")
        print('─' * 80)

        cat_results = {'passed': [], 'failed': []}

        for module, description in deps:
            success, error = test_import(module)
            if success:
                print(f"  ✅ {module:30} - {description}")
                cat_results['passed'].append(module)
                results['all_passed'].append(module)
            else:
                # 簡化錯誤信息
                error_msg = error.split('\n')[0][:50]
                print(f"  ❌ {module:30} - {description} [{error_msg}]")
                cat_results['failed'].append((module, description, error))
                results['all_failed'].append((module, description, error))

        results['by_category'][category] = cat_results
        print(f"  小計: 通過 {len(cat_results['passed'])}/{len(deps)}")

    return results

def test_framework_modules() -> Dict:
    """測試框架內部模組"""
    print("\n" + "=" * 80)
    print("  AI Automation Framework 模組導入測試")
    print("=" * 80)

    modules = [
        ('ai_automation_framework', '主模組'),
        ('ai_automation_framework.core', '核心模組'),
        ('ai_automation_framework.core.config', '配置模組'),
        ('ai_automation_framework.core.logger', '日誌模組'),
        ('ai_automation_framework.llm', 'LLM 模組'),
        ('ai_automation_framework.llm.base_client', 'LLM 基礎客戶端'),
        ('ai_automation_framework.rag', 'RAG 模組'),
        ('ai_automation_framework.agents', 'Agents 模組'),
        ('ai_automation_framework.tools', 'Tools 模組'),
        ('ai_automation_framework.workflows', 'Workflows 模組'),
    ]

    results = {'passed': [], 'failed': []}

    for module, description in modules:
        success, error = test_import(module)
        if success:
            print(f"  ✅ {module:50} - {description}")
            results['passed'].append(module)
        else:
            # 找出根本原因
            error_lines = error.split('\n')
            root_cause = error_lines[-1] if error_lines else error
            print(f"  ❌ {module:50} - {description}")
            print(f"     原因: {root_cause}")
            results['failed'].append((module, description, error))

    print(f"\n  總計: {len(modules)} | 通過: {len(results['passed'])} | 失敗: {len(results['failed'])}")
    return results

def main():
    print("\n" + "=" * 80)
    print("  導入相容性完整測試報告")
    print("=" * 80)
    print(f"  Python 版本: {sys.version}")
    print("=" * 80)

    # 1. 檢查標準庫
    stdlib_results = check_standard_library()

    # 2. 檢查第三方依賴
    third_party_results = check_third_party_dependencies()

    # 3. 測試框架模組
    framework_results = test_framework_modules()

    # 總結
    print("\n" + "=" * 80)
    print("  最終總結")
    print("=" * 80)

    total_stdlib = len(stdlib_results['passed']) + len(stdlib_results['failed'])
    total_third_party = len(third_party_results['all_passed']) + len(third_party_results['all_failed'])
    total_framework = len(framework_results['passed']) + len(framework_results['failed'])

    print(f"\n  📊 統計:")
    print(f"     標準庫: {len(stdlib_results['passed'])}/{total_stdlib} 通過")
    print(f"     第三方依賴: {len(third_party_results['all_passed'])}/{total_third_party} 通過")
    print(f"     框架模組: {len(framework_results['passed'])}/{total_framework} 通過")

    # 嚴重性評估
    critical_missing = []
    for module, desc, error in third_party_results['all_failed']:
        # 核心依賴標記為 critical
        if module in ['openai', 'anthropic', 'pydantic', 'dotenv', 'loguru']:
            critical_missing.append(module)

    print(f"\n  🔴 Critical 問題數量: {len(critical_missing)}")
    print(f"  🟡 Warning 問題數量: {len(third_party_results['all_failed']) - len(critical_missing)}")
    print(f"  ℹ️  Info: 標準庫全部正常" if not stdlib_results['failed'] else f"  ⚠️  標準庫有 {len(stdlib_results['failed'])} 個問題")

    # 具體建議
    if critical_missing:
        print(f"\n  ⚠️  Critical 缺失依賴 (必須安裝):")
        for module in critical_missing:
            print(f"     - {module}")

    if framework_results['failed']:
        print(f"\n  ⚠️  框架模組導入失敗:")
        for module, desc, error in framework_results['failed']:
            error_line = error.split('\n')[-1]
            print(f"     - {module}")
            print(f"       原因: {error_line}")

    # 修復建議
    print("\n" + "=" * 80)
    print("  修復建議")
    print("=" * 80)

    if third_party_results['all_failed']:
        missing_packages = [m for m, _, _ in third_party_results['all_failed']]
        # 映射到 requirements.txt 中的包名
        package_map = {
            'dotenv': 'python-dotenv',
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'bs4': 'beautifulsoup4',
        }

        install_packages = []
        for pkg in missing_packages:
            install_packages.append(package_map.get(pkg, pkg))

        print(f"\n  建議執行:")
        print(f"  pip install {' '.join(install_packages[:10])}")
        if len(install_packages) > 10:
            print(f"  # ... 以及其他 {len(install_packages) - 10} 個包")
        print(f"\n  或直接安裝所有依賴:")
        print(f"  pip install -r requirements.txt")

    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
