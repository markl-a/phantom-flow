"""
快速測試腳本

測試所有核心功能是否正常工作
"""

import sys
from pathlib import Path

# 添加src目錄到路徑
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


def test_imports():
    """測試核心模塊導入"""
    print("=" * 80)
    print("測試核心模塊導入".center(80))
    print("=" * 80)

    tests = []

    try:
        from data_analysis_chatbots.data_loader import DataLoader
        print("✅ DataLoader 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ DataLoader 導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.clustering import KMeansClusterer
        print("✅ KMeansClusterer 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ KMeansClusterer 導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.clustering import DBSCANClusterer
        print("✅ DBSCANClusterer 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ DBSCANClusterer 導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.clustering import GMMClusterer
        print("✅ GMMClusterer 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ GMMClusterer 導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.clustering import HierarchicalClusterer
        print("✅ HierarchicalClusterer 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ HierarchicalClusterer 導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.exceptions import DataLoadError
        print("✅ 自定義異常系統導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ 自定義異常系統導入失敗: {e}")
        tests.append(False)

    try:
        from data_analysis_chatbots.kaggle_downloader import KaggleDatasetDownloader
        print("✅ KaggleDatasetDownloader 導入成功")
        tests.append(True)
    except Exception as e:
        print(f"❌ KaggleDatasetDownloader 導入失敗: {e}")
        tests.append(False)

    print()
    success_rate = sum(tests) / len(tests) * 100
    print(f"導入測試通過率: {success_rate:.1f}% ({sum(tests)}/{len(tests)})")
    print()

    return all(tests)


def test_kaggle_solutions():
    """測試Kaggle解決方案"""
    print("=" * 80)
    print("測試Kaggle解決方案".center(80))
    print("=" * 80)

    solutions_dir = Path(__file__).parent.parent / 'kaggle_solutions'

    categories = sorted([d for d in solutions_dir.iterdir()
                        if d.is_dir() and not d.name.startswith('.')])

    total_solutions = 0
    total_files = 0

    for category in categories:
        solutions = sorted([d for d in category.iterdir()
                          if d.is_dir() and not d.name.startswith('.')])
        total_solutions += len(solutions)

        for solution in solutions:
            if (solution / 'solution.py').exists():
                total_files += 1
            if (solution / 'README.md').exists():
                total_files += 1

    print(f"📊 發現 {len(categories)} 個類別")
    print(f"📊 發現 {total_solutions} 個解決方案")
    print(f"📄 發現 {total_files} 個文件")
    print()

    expected_files = total_solutions * 2  # solution.py + README.md
    completeness = total_files / expected_files * 100
    print(f"文件完整度: {completeness:.1f}%")
    print()

    return completeness == 100


def test_data_processing():
    """測試數據處理功能"""
    print("=" * 80)
    print("測試數據處理功能".center(80))
    print("=" * 80)

    try:
        import pandas as pd
        import numpy as np
        from sklearn.cluster import KMeans

        # 創建測試數據
        np.random.seed(42)
        data = np.random.randn(100, 2)
        df = pd.DataFrame(data, columns=['feature1', 'feature2'])

        # 測試聚類
        kmeans = KMeans(n_clusters=3, random_state=42)
        labels = kmeans.fit_predict(data)

        print(f"✅ 成功創建測試數據: {df.shape}")
        print(f"✅ 成功執行K-Means聚類: {len(set(labels))} 個群集")
        print()

        return True
    except Exception as e:
        print(f"❌ 數據處理測試失敗: {e}")
        print()
        return False


def main():
    """主測試函數"""
    print("\n" + "🔍 開始快速測試\n")

    tests = {
        '核心模塊導入': test_imports(),
        'Kaggle解決方案': test_kaggle_solutions(),
        '數據處理功能': test_data_processing()
    }

    print("=" * 80)
    print("測試摘要".center(80))
    print("=" * 80)

    for test_name, result in tests.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:20} {status}")

    print()
    passed = sum(tests.values())
    total = len(tests)
    success_rate = passed / total * 100

    print(f"總體通過率: {success_rate:.1f}% ({passed}/{total})")
    print()

    if success_rate == 100:
        print("🎉 所有測試通過！專案配置正確。")
    else:
        print("⚠️  部分測試失敗，請檢查配置。")

    return success_rate == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
