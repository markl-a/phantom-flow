# 🚀 快速啟動指南

本指南幫助您在5分鐘內開始使用本專案的核心功能。

## 📋 前置需求

- Python 3.8+
- pip 包管理器
- (可選) Kaggle API憑證

## ⚡ 快速開始

### 1. 安裝依賴

```bash
# 安裝核心依賴
pip install -r requirements.txt

# 或使用開發模式安裝
pip install -e .
```

### 2. 運行快速測試

確保所有功能正常：

```bash
python scripts/quick_test.py
```

✅ 如果看到"所有測試通過"，說明環境配置成功！

### 3. 查看專案統計

```bash
python scripts/generate_statistics.py
```

這會生成完整的專案統計報告，包括：
- 1504個Kaggle解決方案的分布
- 各類別數量統計
- 文檔完整度

## 🎯 使用場景

### 場景 1: 探索Kaggle解決方案

```bash
# 瀏覽所有解決方案
python scripts/browse_solutions.py

# 按類別搜索
python scripts/browse_solutions.py --category 01_structured_data

# 按關鍵詞搜索
python scripts/browse_solutions.py --search "time series"
```

### 場景 2: 下載Kaggle數據集

```python
from data_analysis_chatbots import quick_download

# 快速下載流行數據集
data_path = quick_download('titanic')
print(f"數據已下載到: {data_path}")

# 支持的數據集包括:
# titanic, house-prices, digit-recognizer, credit-fraud等50+
```

### 場景 3: 使用聚類算法

```python
from data_analysis_chatbots import KMeansClusterer
import pandas as pd

# 加載數據
df = pd.read_csv('data/your_data.csv')

# 創建聚類器
clusterer = KMeansClusterer(n_clusters=3, random_state=42)

# 訓練模型
labels = clusterer.fit_predict(df[['feature1', 'feature2']])

# 可視化結果
clusterer.visualize()
```

### 場景 4: 運行具體的Kaggle解決方案

```bash
# 運行結構化數據解決方案
cd kaggle_solutions/01_structured_data/01_customer_churn_prediction
python solution.py

# 查看解決方案說明
cat README.md
```

## 📊 2000個Kaggle解決方案一覽

本專案包含2000個完整的Kaggle解決方案，分為17個類別：

| 類別 | 數量 | 主要內容 |
|------|------|----------|
| 結構化數據 | 112 | 客戶滿意度預測、員工生產力、定價策略、品牌價值等 |
| 時間序列 | 128 | 多分辨率分析、Transformer變體、N-BEATS、TimesNet等 |
| NLP | 112 | 事實核查、論證挖掘、推理任務、實體鏈接等 |
| 推薦系統 | 116 | 視頻推薦、技能推薦、引用推薦、投資推薦等 |
| 計算機視覺 | 110 | 3D重建、神經渲染、醫學圖像分割、變化檢測等 |
| 聚類分析 | 120 | 張量分解聚類、深度聚類、自監督聚類、元聚類等 |
| 特殊領域 | 125 | 衍生品定價、算法交易、市場微觀結構、量化策略等 |
| 深度學習 | 125 | 神經架構搜索、聯邦學習、模型壓縮、邊緣智能等 |
| 音訊信號 | 120 | 音頻降噪、語音反欺騙、空間音頻、音頻質量評估等 |
| 異常檢測 | 119 | 對抗異常、概念漂移、分佈外檢測、離群因子等 |
| 圖神經網絡 | 119 | 圖Transformer、圖BERT、圖自編碼器、圖聯邦學習等 |
| 地理空間 | 118 | 衛星圖像分析、災害評估、環境監測、交通流分析等 |
| 特徵工程 | 123 | 自動特徵工程、特徵組合、小波特徵、嵌入特徵等 |
| 集成學習 | 123 | 梯度提升變體、學習排序、深度集成、在線集成等 |
| 貝葉斯方法 | 118 | 貝葉斯優化、變分推斷、層次模型、貝葉斯非參數等 |
| 優化算法 | 118 | 進化算法、群體智能、約束優化、在線優化等 |
| 多模態學習 | 111 | 跨模態檢索、視覺問答、多模態生成、模態對齊等 |

## 🛠️ 實用工具

### 驗證解決方案質量

```bash
python scripts/validate_solutions.py
```

這會檢查：
- Python語法正確性
- 文件完整性
- 代碼風格
- 文檔質量

### 生成缺失的README

```bash
python scripts/generate_missing_readmes.py
```

### 配置Kaggle API

```python
from data_analysis_chatbots import setup_kaggle_credentials

# 交互式設置Kaggle憑證
setup_kaggle_credentials()
```

## 📚 更多資源

- [完整文檔](README.md) - 詳細的專案說明
- [架構設計](ARCHITECTURE.md) - 系統架構文檔
- [FAQ](FAQ.md) - 常見問題解答
- [教程](TUTORIAL.md) - 詳細教程
- [Kaggle快速入門](docs/KAGGLE_QUICKSTART.md) - Kaggle數據集使用指南

## 🤝 需要幫助？

1. 查看 [FAQ.md](FAQ.md) 常見問題
2. 閱讀 [TUTORIAL.md](TUTORIAL.md) 詳細教程
3. 運行 `python scripts/quick_test.py` 診斷問題
4. 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何貢獻

## 🎉 開始您的數據分析之旅！

選擇一個Kaggle解決方案開始：

```bash
# 推薦新手從這些開始
cd kaggle_solutions/01_structured_data/01_customer_churn_prediction
python solution.py
```

祝您使用愉快！ 🚀
