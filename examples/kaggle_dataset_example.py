#!/usr/bin/env python3
"""
Kaggle 數據集使用示例

演示如何使用 Kaggle 下載器自動下載數據並訓練模型

作者: Data Analysis with Chatbots Team
日期: 2025-01-19
"""

import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from data_analysis_chatbots.kaggle_downloader import (
    KaggleDatasetDownloader,
    setup_kaggle_credentials,
    quick_download
)
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


def example_1_titanic():
    """示例 1: Titanic 生存預測"""
    print("\n" + "=" * 80)
    print("示例 1: Titanic 生存預測")
    print("=" * 80 + "\n")

    # 1. 下載數據集
    print("步驟 1: 下載 Titanic 數據集")
    try:
        downloader = KaggleDatasetDownloader()
        data_path = downloader.download_dataset('titanic')
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        print("\n💡 請先配置 Kaggle API:")
        setup_kaggle_credentials()
        return

    # 2. 加載數據
    print("\n步驟 2: 加載訓練數據")
    train_file = data_path / 'train.csv'

    if not train_file.exists():
        print(f"❌ 找不到訓練數據: {train_file}")
        return

    df = pd.read_csv(train_file)
    print(f"✓ 數據形狀: {df.shape}")
    print(f"\n前5行數據:")
    print(df.head())

    # 3. 簡單的特徵工程
    print("\n步驟 3: 特徵工程")

    # 選擇特徵
    features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare']

    # 處理缺失值
    df['Age'].fillna(df['Age'].median(), inplace=True)
    df['Fare'].fillna(df['Fare'].median(), inplace=True)

    # 編碼性別
    df['Sex'] = df['Sex'].map({'male': 0, 'female': 1})

    # 準備特徵和目標
    X = df[features]
    y = df['Survived']

    print(f"✓ 特徵數量: {len(features)}")
    print(f"✓ 樣本數量: {len(X)}")

    # 4. 訓練模型
    print("\n步驟 4: 訓練隨機森林模型")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. 評估模型
    print("\n步驟 5: 評估模型")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"✓ 準確率: {accuracy:.4f}")
    print(f"\n分類報告:")
    print(classification_report(y_test, y_pred,
                               target_names=['Not Survived', 'Survived']))

    # 6. 特徵重要性
    print("\n步驟 6: 特徵重要性")
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(feature_importance)

    print("\n" + "=" * 80)
    print("✅ Titanic 示例完成！")
    print("=" * 80 + "\n")


def example_2_house_prices():
    """示例 2: 房價預測"""
    print("\n" + "=" * 80)
    print("示例 2: 房價預測")
    print("=" * 80 + "\n")

    print("步驟 1: 下載房價數據集")
    try:
        data_path = quick_download('house-prices')
        print(f"✓ 數據路徑: {data_path}")

        train_file = data_path / 'train.csv'
        if train_file.exists():
            df = pd.read_csv(train_file)
            print(f"\n數據概覽:")
            print(f"  - 樣本數: {len(df)}")
            print(f"  - 特徵數: {len(df.columns)}")
            print(f"  - 目標變量: SalePrice")
            print(f"\n價格統計:")
            print(df['SalePrice'].describe())
        else:
            print(f"⚠️  找不到 train.csv")

    except Exception as e:
        print(f"❌ 下載失敗: {e}")

    print("\n" + "=" * 80 + "\n")


def example_3_list_datasets():
    """示例 3: 列出常用數據集"""
    print("\n" + "=" * 80)
    print("示例 3: 常用數據集列表")
    print("=" * 80 + "\n")

    downloader = KaggleDatasetDownloader()
    downloader.list_popular_datasets()


def example_4_search():
    """示例 4: 搜索數據集"""
    print("\n" + "=" * 80)
    print("示例 4: 搜索數據集")
    print("=" * 80 + "\n")

    downloader = KaggleDatasetDownloader()

    keywords = ['nlp', 'time series', 'image classification']

    for keyword in keywords:
        print(f"\n搜索關鍵詞: {keyword}")
        print("-" * 80)
        downloader.search_datasets(keyword, max_results=5)


def main():
    """主函數"""
    print("\n" + "=" * 80)
    print("🎯 Kaggle 數據集使用示例")
    print("=" * 80)

    import argparse
    parser = argparse.ArgumentParser(description='Kaggle 數據集使用示例')
    parser.add_argument(
        '--example',
        type=int,
        choices=[1, 2, 3, 4],
        help='選擇示例 (1: Titanic, 2: 房價, 3: 列表, 4: 搜索)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='運行所有示例'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='顯示 Kaggle API 設置指南'
    )

    args = parser.parse_args()

    if args.setup:
        setup_kaggle_credentials()
        return

    if args.all:
        example_1_titanic()
        example_2_house_prices()
        example_3_list_datasets()
        example_4_search()
    elif args.example == 1:
        example_1_titanic()
    elif args.example == 2:
        example_2_house_prices()
    elif args.example == 3:
        example_3_list_datasets()
    elif args.example == 4:
        example_4_search()
    else:
        # 默認運行示例 1
        print("\n提示: 使用 --example N 選擇特定示例")
        print("      使用 --all 運行所有示例")
        print("      使用 --setup 查看 API 設置指南\n")
        example_1_titanic()


if __name__ == '__main__':
    main()
