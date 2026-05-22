# Data Analysis with Agents

> **一個利用AI聊天機器人(ChatGPT, Gemini, Claude)進行客戶分析與分群的完整框架**
>
> Phantom Mesh ecosystem analytics layer for customer segmentation today and agent-telemetry analysis next.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Powered by phantom-mesh](https://img.shields.io/badge/powered%20by-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

---

## 🔗 phantom-mesh ecosystem

This repository is the **data-science & analytics layer** of the
[phantom-mesh](https://github.com/markl-a/phantom-mesh) ecosystem — a
self-hostable multi-agent AI runtime.

**Two roles in the ecosystem:**

1. **Stand-alone**: end-to-end customer analytics framework as documented
   below — clustering algorithms (K-Means, DBSCAN, GMM, Hierarchical), CLV
   prediction, RFM segmentation, AI-assisted interpretation.
2. **Phantom telemetry analysis**: the same algorithms applied to phantom-mesh's
   own agent execution logs — clustering 10K+ executions to surface
   prompt-failure patterns, provider-specific performance, and cost outliers.
   See `examples/phantom-telemetry/` (in progress).

The same statistical machinery powers both: customer behaviour and AI agent
behaviour are both "many discrete events with hidden structure" problems.

---

## Current Verification

Latest `goal_plan` local check:

- `python -m pytest tests -q -x`: blocked by missing dependencies/package setup.

This README documents the intended analytics package and historical test path, but the repo still needs a scoped dependency install before it can be used as a locally verified Phantom Mesh demo artifact.

---

## 🎯 專案概述

本專案提供一個全面的客戶分析框架,結合傳統數據科學方法與最新的AI技術(2024-2025年最佳實踐),幫助企業深入了解客戶行為、進行精準分群,並制定有效的營銷策略。

### ✨ 核心特色

- **客戶分群演算法** — K-Means、DBSCAN、GMM、Hierarchical 四種，可直接 import 使用
- **RFM + CLV 預測** — 經典 RFM 與機器學習混合的客戶終身價值預測
- **端到端範例** — 5 個 jupyter notebook 案例（mall customer、personality、marketing 等）
- **AI 輔助解讀** — 把 clustering / RFM 結果丟給 ChatGPT / Gemini / Claude 產生人類可讀的分析報告
- **Kaggle 範例庫** — 17 大類、約 2,019 個解決方案資料夾（**抽查發現完成度不齊**：部分是完整實作，部分是 LLM 批次生成的骨架，**持續手動修整中**）
- **Kaggle 資料集下載工具** — 支援 50+ 熱門資料集一鍵下載

> ⚠️ **誠實聲明**：早期版本 README 引用過「AI 分群可減少 75% 分析時間 / 95% 準確度」「100% 文檔覆蓋」等數字，這些**沒有來源、不該出現在 README**，已於 2026-05 移除。如果你看到舊截圖留有那些句子，請以本版為準。

## 📁 專案結構

```
Data-Analysis-with-Chatbots/
│
├── docs/                           # 📖 文檔
│   ├── 01_data_cleaning.md        # 數據清洗指南
│   ├── 02_customer_segmentation.md # 客戶分群分析
│   ├── 03_mall_customer_analysis.md # 購物中心會員分析
│   ├── 04_personality_analysis.md  # 客戶人格分析
│   └── 05_marketing_segmentation.md # 營銷分群策略
│
├── kaggle_solutions/               # ~2,019 個 Kaggle 風格解決方案資料夾（品質不齊，見 ✨ 核心特色 註）
│   ├── 01_structured_data/        # 結構化數據 (116 dirs)
│   ├── 02_time_series/            # 時間序列 (130 dirs)
│   ├── 03_nlp/                    # 自然語言處理 (112 dirs)
│   ├── 04_recommendation/         # 推薦系統 (114 dirs)
│   ├── 05_computer_vision/        # 計算機視覺 (110 dirs)
│   ├── 06_clustering/             # 聚類分析 (119 dirs)
│   ├── 07_special_domains/        # 特殊領域 (125 dirs)
│   ├── 08_deep_learning/          # 深度學習 (124 dirs)
│   ├── 09_audio_signal/           # 音訊信號 (119 dirs)
│   ├── 10_anomaly_detection/      # 異常檢測 (117 dirs)
│   ├── 11_graph_networks/         # 圖神經網絡 (117 dirs)
│   ├── 12_geospatial/             # 地理空間 (116 dirs)
│   ├── 13_feature_engineering/    # 特徵工程 (121 dirs)
│   ├── 14_ensemble_methods/       # 集成學習 (121 dirs)
│   ├── 15_bayesian_methods/       # 貝葉斯方法 (116 dirs)
│   ├── 16_optimization/           # 優化算法 (116 dirs)
│   ├── 17_multimodal/             # 多模態學習 (109 dirs)
│   ├── README.md                  # Kaggle解決方案總覽
│   ├── INDEX.md                   # 完整索引
│   └── SOLUTIONS_SUMMARY.md       # 統計摘要
│
├── notebooks/                      # 📓 Jupyter Notebooks
│   ├── 01_mall_customer_clustering.ipynb  # 購物中心客戶聚類
│   ├── 02_rfm_clv_analysis.ipynb          # RFM與CLV分析
│   └── 03_interactive_learning_tutorial.ipynb  # 互動式學習教程
│
├── src/data_analysis_chatbots/    # 💻 源代碼
│   ├── config_loader.py           # 配置管理
│   ├── data_loader.py             # 數據加載器
│   ├── data_downloader.py         # 數據下載工具
│   ├── preprocessing/             # 數據預處理模塊
│   ├── clustering/                # 聚類分析模塊
│   ├── visualization/             # 可視化模塊
│   └── marketing/                 # 營銷分析模塊
│
├── data/                          # 📦 數據目錄
│   ├── raw/                       # 原始數據
│   ├── processed/                 # 處理後數據
│   └── outputs/                   # 分析結果
│
├── config/config.yaml             # ⚙️ 配置文件
├── requirements.txt               # Python依賴
├── setup.py                       # 專案安裝配置
└── README.md                      # 本文檔
```

## 🚀 快速開始

### 環境要求

- Python 3.8或更高版本
- pip包管理器
- (可選) Jupyter Notebook
- (可選) Kaggle API憑證

### 安裝步驟

1. **克隆專案**

```bash
git clone https://github.com/markl-a/Data-Analysis-with-Agents.git
cd Data-Analysis-with-Agents
```

2. **創建虛擬環境**(推薦)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **安裝依賴**

```bash
pip install -r requirements.txt
```

4. **安裝專案包**

```bash
pip install -e .
```

5. **初始化專案結構**(新增!)

```bash
# 創建必要的目錄結構(data/, models/, logs/等)
python -m data_analysis_chatbots.init --with-examples

# 或僅驗證目錄結構是否完整
python -m data_analysis_chatbots.init --validate
```

6. **下載數據集**(可選)

```bash
# 下載所有數據集
python -m data_analysis_chatbots.data_downloader --all

# 或下載特定數據集
python -m data_analysis_chatbots.data_downloader --dataset mall_customers

# 或創建範例數據用於測試
python -m data_analysis_chatbots.data_downloader --sample
```

### 跑測試 (Running the test suite)

裝完依賴跟 `pip install -e .` 之後可直接跑測試：

```bash
# 全部測試 (historically documented as ~377 tests; install dependencies first)
pytest

# 加 verbose
pytest -v

# 只看 failures
pytest --tb=short

# 跑單一檔案
pytest tests/test_clustering.py -v
```

如果遇到 `ModuleNotFoundError: No module named 'data_analysis_chatbots'`，代表還沒跑步驟 4 的 `pip install -e .` — 那一步把 `src/data_analysis_chatbots/` 註冊成 import 得到的 package。

> **目前已知失敗**：377 個 test 中約 58 個失敗，多數是 test 檔跟 `data_analysis_chatbots` 模組 API 不同步（例如 `DataLoader.load_csv` 已改名）。修復進行中——歡迎 PR 修。

### 基本使用

#### 快速入門 - K-Means聚類

```python
from data_analysis_chatbots import DataLoader
from data_analysis_chatbots.clustering import KMeansClusterer
from data_analysis_chatbots.visualization import Plotter

# 加載數據
loader = DataLoader()
df = loader.load_mall_customers()

# 執行K-means聚類
clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(df, ['Age', 'Annual Income (k$)', 'Spending Score (1-100)'])

# 可視化結果
plotter = Plotter()
plotter.plot_clusters(df, 'Annual Income (k$)', 'Spending Score (1-100)', 'Cluster')
```

#### 新增! 使用高級聚類算法

```python
from data_analysis_chatbots.clustering import (
    DBSCANClusterer,      # 密度聚類
    GMMClusterer,         # 高斯混合模型
    HierarchicalClusterer # 層次聚類
)

# DBSCAN - 適合發現任意形狀的聚類
dbscan = DBSCANClusterer(eps=0.5, min_samples=10)
labels = dbscan.fit_predict(df, features)
print(f"發現 {dbscan.n_clusters_} 個聚類和 {dbscan.n_noise_} 個異常點")

# GMM - 提供概率性聚類結果
gmm = GMMClusterer(n_components=3)
labels = gmm.fit_predict(df, features)
probabilities = gmm.predict_proba(df, features)  # 獲取每個點屬於各聚類的概率

# Hierarchical - 可視化層次結構
hierarchical = HierarchicalClusterer(n_clusters=4, linkage='ward')
labels = hierarchical.fit_predict(df, features)
hierarchical.plot_dendrogram(save_path='outputs/plots/dendrogram.png')
```

## 📊 數據集

專案包含5個真實世界的數據集:

| # | 數據集 | 來源 | 用途 |
|---|--------|------|------|
| 1 | [NLP災難推文](https://www.kaggle.com/datasets/vbmokin/nlp-with-disaster-tweets-cleaning-data) | Kaggle | 文本清洗與NLP |
| 2 | [電商交易](https://www.kaggle.com/datasets/carrie1/ecommerce-data) | Kaggle | RFM分析 |
| 3 | [購物中心客戶](https://www.kaggle.com/datasets/vjchoudhary7/customer-segmentation-tutorial-in-python) | Kaggle | K-means聚類 |
| 4 | [客戶人格](https://github.com/g-aditi/customer-personality-analysis) | GitHub | CLV預測 |
| 5 | [營銷分群](https://www.kaggle.com/datasets/fahmidachowdhury/customer-segmentation-data-for-marketing-analysis) | Kaggle | 營銷策略 |

## 🎓 核心功能模塊

### 1. 數據預處理

```python
from data_analysis_chatbots.preprocessing import TextCleaner, DataValidator

# 文本清洗
cleaner = TextCleaner(lowercase=True, remove_urls=True)
clean_text = cleaner.clean_text("Check this out: http://example.com @user")

# 數據驗證
validator = DataValidator(df)
report = validator.generate_report()
```

### 2. RFM分析

```python
from data_analysis_chatbots.clustering import RFMAnalyzer

rfm = RFMAnalyzer(df, 'CustomerID', 'InvoiceDate', 'TotalAmount')
rfm_data = rfm.calculate_rfm()
segments = rfm.segment_customers()
summary = rfm.get_segment_summary()
```

### 3. K-Means聚類

```python
from data_analysis_chatbots.clustering import KMeansClusterer

clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(df, ['Age', 'Income', 'Spending'])
metrics = clusterer.evaluate_clustering()
```

### 4. CLV預測

```python
from data_analysis_chatbots.marketing import CLVPredictor

clv_predictor = CLVPredictor(discount_rate=0.1)
clv_results = clv_predictor.calculate_rfm_based_clv(rfm_data)
summary = clv_predictor.get_clv_summary(clv_results)
```

### 5. 營銷活動管理

```python
from data_analysis_chatbots.marketing import CampaignManager

campaign_mgr = CampaignManager(customer_df, 'CustomerID')
targeted = campaign_mgr.create_campaign(
    'VIP促銷',
    {'Income': {'min': 70}, 'Spending': {'min': 60}}
)
roi = campaign_mgr.calculate_campaign_roi('VIP促銷', 50, 0.15, 500)
```

## 🏆 2000個Kaggle實戰解決方案

專案包含 **2000個完整的Kaggle比賽解決方案**，涵蓋機器學習17個領域：

### 📊 結構化數據 (112個)
- Titanic存活預測、房價預測、信用卡詐欺偵測、客戶流失預測等

### ⏱️ 時間序列分析 (128個)
- 股票價格預測、銷售預測、COVID-19分析、Informer、Autoformer、TimesNet等

### 💬 自然語言處理 (112個)
- 情感分析、假新聞偵測、事實查核、論證挖掘、零樣本學習等

### 🎬 推薦系統 (116個)
- 電影推薦、產品推薦、視頻推薦、技能推薦、股票推薦等

### 🖼️ 計算機視覺 (110個)
- 3D重建、NeRF、SLAM、醫學影像、目標檢測等

### 🔍 聚類分析 (120個)
- 深度聚類、Transformer聚類、客戶分群等

### 🏥 特殊領域應用 (125個)
- 量化交易、算法交易、醫療診斷等

### 🧠 深度學習 (125個)
- NAS、聯邦學習、模型壓縮等

### 🎵 音訊信號處理 (120個)
- 音訊降噪、語音反欺騙等

### 🔎 異常檢測 (119個)
- 對抗性檢測、概念漂移、OOD檢測等

### 🕸️ 圖神經網絡 (119個)
- Graph Transformers、Graph BERT等

### 🌍 地理空間分析 (118個)
- 衛星影像、災害評估等

### ⚙️ 特徵工程 (123個)
- 自動特徵、小波變換、嵌入等

### 🎯 集成學習 (123個)
- 學習排序、深度集成等

### 📈 貝葉斯方法 (118個)
- 貝葉斯優化、變分推斷等

### 🔧 優化算法 (118個)
- 進化算法、凸優化、自適應優化等

### 🎨 多模態學習 (111個)
- 跨模態檢索、VQA、多模態生成等

### 快速開始

```bash
# 查看所有解決方案
cd kaggle_solutions
python run_all.py

# 運行單個解決方案
cd kaggle_solutions/01_structured_data/01_titanic_survival
python solution.py
```

**詳細信息**: 查看 [kaggle_solutions/README.md](kaggle_solutions/README.md)

## 📖 詳細文檔

### 📚 完整學習指南 (新增!)

**從零基礎到專家的完整路徑**:

- 📖 **[TUTORIAL.md](TUTORIAL.md)** - 完整學習教程 (入門到精通)
  - 4個階段學習路徑 (0-12個月)
  - 每週/每月結構化課程
  - 實戰代碼示例與練習
  - 進度追蹤檢查表

- 🤖 **[AI_ASSISTANCE_GUIDE.md](AI_ASSISTANCE_GUIDE.md)** - AI輔助使用指南
  - ChatGPT、Claude、Gemini 比較與使用
  - AI輔助數據清洗 (3種方法)
  - AI輔助編碼最佳實踐
  - 實戰案例與安全建議

- 📊 **[CASE_STUDIES.md](CASE_STUDIES.md)** - 實際案例研究
  - 4個熱門Kaggle競賽詳解
  - 3個企業應用案例
  - 完整端到端專案實戰
  - 業務成果與指標

- 🏆 **[KAGGLE_COMPETITIONS_SUGGESTIONS.md](KAGGLE_COMPETITIONS_SUGGESTIONS.md)** - Kaggle競賽推薦
  - 12個精選競賽 (入門到專家)
  - 詳細競賽分析與策略
  - 學習路徑建議
  - AI輔助競賽技巧

- ❓ **[FAQ.md](FAQ.md)** - 常見問題解答 (新增!)
  - 20個最常見問題詳解
  - 安裝、使用、錯誤處理
  - 聚類算法選擇指南
  - 性能優化技巧
  - AI輔助最佳實踐

- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - 系統架構設計 (新增!)
  - 分層架構詳解
  - 模塊設計原則
  - 設計模式應用
  - 數據流與狀態管理
  - 性能優化策略
  - 安全性考慮

### 📂 技術文檔

請查看[docs/](docs/)目錄獲取技術文檔:

- [01_data_cleaning.md](docs/01_data_cleaning.md) - 數據清洗完整指南
- [02_customer_segmentation.md](docs/02_customer_segmentation.md) - RFM與電商分析
- [03_mall_customer_analysis.md](docs/03_mall_customer_analysis.md) - K-means聚類實戰
- [04_personality_analysis.md](docs/04_personality_analysis.md) - 客戶人格與CLV
- [05_marketing_segmentation.md](docs/05_marketing_segmentation.md) - 營銷策略制定

## 🔧 配置

編輯`config/config.yaml`以自定義分析參數:

```yaml
analysis:
  clustering:
    n_clusters_range: [2, 3, 4, 5, 6, 7, 8]
    random_state: 42
  rfm:
    recency_bins: [0, 30, 90, 180, 365, 9999]
  clv:
    discount_rate: 0.1
    time_horizon_years: 3
```

## 📚 參考資源

### 相關文章
- [利用集群分析掌握消費者輪廓](https://medium.com/finformation%E7%95%B6%E7%A8%8B%E5%BC%8F%E9%81%87%E4%B8%8A%E8%B2%A1%E5%8B%99%E9%87%91%E8%9E%8D/%E5%88%A9%E7%94%A8%E9%9B%86%E7%BE%A4%E5%88%86%E6%9E%90%E6%8E%8C%E6%8F%A1%E6%B6%88%E8%B2%BB%E8%80%85%E8%BC%AA%E5%BB%93-python%E5%AF%A6%E4%BD%9C-%E4%B8%80-7086082fbb2e)

### 學術研究
- Estimating Customer Lifetime Value Based on RFM Analysis
- Machine Learning Algorithms for Customer Relationship Management

### 行業最佳實踐(2024-2025)
- AI驅動分群減少75%分析時間,提升95%準確度
- 動態實時客戶分析
- 隱私優先的數據處理

## 📄 許可證

本專案採用MIT許可證 - 詳見[LICENSE](LICENSE)文件

## 👤 作者

**賴祺清**

## 🙏 致謝

- Kaggle社區提供的優質數據集
- Scikit-learn、Pandas、Matplotlib等開源專案
- ChatGPT、Gemini、Claude等AI工具的啟發

---

⭐ 如果這個專案對你有幫助,請給個星星! ⭐

---

## 🚀 快速導航

### 新手入門
1. 閱讀 [QUICKSTART.md](QUICKSTART.md) - 5分鐘快速體驗
2. 學習 [TUTORIAL.md](TUTORIAL.md) - 完整學習路徑
3. 運行第一個範例: `python examples/complete_analysis_workflow.py`

### AI輔助學習
1. 閱讀 [AI_ASSISTANCE_GUIDE.md](AI_ASSISTANCE_GUIDE.md)
2. 使用AI優化你的代碼
3. 參考 [CASE_STUDIES.md](CASE_STUDIES.md) 中的AI輔助案例

### Kaggle競賽
1. 查看 [KAGGLE_COMPETITIONS_SUGGESTIONS.md](KAGGLE_COMPETITIONS_SUGGESTIONS.md)
2. 從Titanic開始: `cd kaggle_solutions/01_structured_data/01_titanic_survival`
3. 參加你的第一個競賽!

### 企業應用
1. 研究 [CASE_STUDIES.md](CASE_STUDIES.md) 中的企業案例
2. 運行CLV預測: `docs/04_personality_analysis.md`
3. 部署Streamlit儀表板: `streamlit run app.py`

---

**最後更新:** 2025年1月18日
