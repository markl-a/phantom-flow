## 🏗️ 系統架構設計

本文檔詳細說明 **Data Analysis with Chatbots** 專案的架構設計、模塊組織和設計決策。

---

## 📐 總體架構

### 架構模式

專案採用 **分層架構** (Layered Architecture) + **模塊化設計** (Modular Design):

```
┌─────────────────────────────────────────────────────────────┐
│                    應用層 (Application Layer)                │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐    │
│  │  CLI工具   │  │ Streamlit  │  │  REST API (未來)   │    │
│  │  (cli.py)  │  │  (app.py)  │  │                     │    │
│  └────────────┘  └────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    業務邏輯層 (Business Logic)               │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ 聚類分析模塊   │  │  營銷分析模塊  │  │ 可視化模塊    │  │
│  │  clustering/   │  │  marketing/    │  │visualization/ │  │
│  └───────────────┘  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   數據處理層 (Data Processing)               │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │ 數據加載器     │  │  數據驗證器    │  │ 文本清洗器    │  │
│  │ data_loader.py │  │data_validator  │  │text_cleaner   │  │
│  └───────────────┘  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   基礎設施層 (Infrastructure)                │
│  ┌────────────┐  ┌───────────┐  ┌────────────┐            │
│  │ 配置管理   │  │ 日誌系統  │  │ 異常處理   │            │
│  │config_loader│  │utils.py   │  │exceptions  │            │
│  └────────────┘  └───────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 模塊設計

### 1. 核心模塊 (`src/data_analysis_chatbots/`)

#### 1.1 配置管理 (`config_loader.py`)

**職責**: 統一管理專案配置

```python
class ConfigLoader:
    """
    設計模式: 單例模式
    優勢:
    - 全局配置統一管理
    - 支持環境變量覆蓋
    - 配置文件熱重載
    """
```

**配置層次**:
1. 默認配置 (代碼中)
2. YAML配置文件 (`config/config.yaml`)
3. 環境變量 (最高優先級)

#### 1.2 數據加載 (`data_loader.py`)

**職責**: 數據集加載和管理

```python
class DataLoader:
    """
    設計模式: 工廠模式
    支持格式: CSV, Excel, Parquet
    特性:
    - 自動類型推斷
    - 緩存機制
    - 錯誤恢復
    """
```

**數據流**:
```
原始數據 → 驗證 → 清洗 → 緩存 → 返回DataFrame
```

#### 1.3 初始化工具 (`init.py`)

**職責**: 專案目錄結構初始化

**創建的目錄結構**:
```
data/
├── raw/           # 原始數據
├── processed/     # 處理後數據
└── outputs/       # 分析結果
models/            # 保存的模型
logs/              # 日誌文件
outputs/
├── plots/         # 圖表
└── reports/       # 報告
```

### 2. 聚類分析模塊 (`clustering/`)

#### 2.1 算法選擇決策樹

```
開始
  │
  ├─ 是否知道聚類數量K?
  │   ├─ 是 ──────────────┐
  │   └─ 否 ──┐            │
  │           │            │
  │           ▼            ▼
  │      DBSCAN/        K-Means
  │    Hierarchical       GMM
  │                        │
  ├─ 是否需要概率性結果?  │
  │   ├─ 是 ───────────► GMM
  │   └─ 否 ───────────► K-Means
  │
  ├─ 數據形狀是否規則?
  │   ├─ 是 (球形) ───► K-Means
  │   └─ 否 (任意) ───► DBSCAN
  │
  └─ 是否需要層次結構?
      ├─ 是 ──────────► Hierarchical
      └─ 否 ──────────► 其他算法
```

#### 2.2 聚類器類圖

```
┌─────────────────────────────────┐
│    <<interface>>                │
│   BaseClusterer                 │
│                                 │
│ + fit(df, features)             │
│ + predict(df, features)         │
│ + fit_predict(df, features)     │
│ + evaluate_clustering()         │
│ + get_cluster_summary()         │
└─────────────────────────────────┘
            △
            │ 繼承
    ┌───────┼────────────────┬────────┬─────────────┐
    │       │                │        │             │
┌───▼───┐ ┌─▼──────┐ ┌──────▼──┐ ┌──▼────────┐ ┌─▼────────┐
│KMeans │ │DBSCAN  │ │  GMM    │ │Hierarchical│ │RFMAnalyzer│
│Clusterer│ │Clusterer│ │Clusterer│ │Clusterer   │ │           │
└────────┘ └─────────┘ └─────────┘ └────────────┘ └──────────┘
```

**設計原則**:
- **單一職責**: 每個聚類器專注一種算法
- **開閉原則**: 易於擴展新算法
- **依賴倒置**: 依賴抽象接口,不依賴具體實現

#### 2.3 聚類算法對比

| 算法 | 時間複雜度 | 空間複雜度 | 適用數據規模 | 主要用途 |
|------|-----------|-----------|-------------|---------|
| K-Means | O(n·k·i·d) | O(n·d) | <100萬 | 通用聚類 |
| DBSCAN | O(n·log n) | O(n) | <50萬 | 異常檢測 |
| GMM | O(n·k²·d) | O(k·d²) | <10萬 | 概率聚類 |
| Hierarchical | O(n²·log n) | O(n²) | <5萬 | 探索性分析 |

*註: n=樣本數, k=聚類數, i=迭代次數, d=特徵維度*

### 3. 營銷分析模塊 (`marketing/`)

#### 3.1 CLV預測流程

```
客戶交易數據
      ↓
 ┌────────────┐
 │ RFM分析    │ ← 計算Recency, Frequency, Monetary
 └────────────┘
      ↓
 ┌────────────┐
 │ RFM分群    │ ← 11種標準分群
 └────────────┘
      ↓
 ┌────────────┐
 │ CLV計算    │ ← 歷史CLV + 預測CLV
 └────────────┘
      ↓
 ┌────────────┐
 │ 營銷策略   │ ← 針對性活動設計
 └────────────┘
```

#### 3.2 CLV計算公式

```python
# 歷史CLV
Historical_CLV = Σ(過去交易金額)

# 預測CLV (NPV方法)
Predicted_CLV = Σ(t=1到T) [
    (購買概率_t × 平均訂單值 × 毛利率) / (1 + 折現率)^t
]

# RFM基礎CLV
RFM_CLV = (R分數 × 0.3 + F分數 × 0.4 + M分數 × 0.3) × 基準值
```

### 4. 可視化模塊 (`visualization/`)

#### 4.1 圖表類型與用途

| 圖表類型 | 用途 | 函數 |
|---------|------|------|
| 散點圖 | 聚類分佈 | `plot_clusters()` |
| 肘部圖 | K值選擇 | `plot_elbow()` |
| 輪廓圖 | 聚類質量 | `plot_silhouette()` |
| 樹狀圖 | 層次結構 | `plot_dendrogram()` |
| 熱力圖 | 特徵相關性 | `plot_heatmap()` |
| 箱線圖 | 異常值檢測 | `plot_boxplot()` |

#### 4.2 Streamlit Dashboard架構

```
app.py
  │
  ├─ 側邊欄 (配置)
  │   ├─ 數據集選擇
  │   ├─ 算法選擇
  │   └─ 參數調整
  │
  ├─ 主頁面
  │   ├─ 數據預覽
  │   ├─ 聚類執行
  │   ├─ 結果展示
  │   └─ 可視化圖表
  │
  └─ 下載區
      ├─ CSV導出
      ├─ 圖表保存
      └─ 報告生成
```

### 5. 預處理模塊 (`preprocessing/`)

#### 5.1 數據清洗流水線

```
原始數據
    ↓
┌─────────────────┐
│  缺失值處理     │ ← 刪除/填充/插值
└─────────────────┘
    ↓
┌─────────────────┐
│  異常值處理     │ ← IQR/Z-score
└─────────────────┘
    ↓
┌─────────────────┐
│  文本清洗       │ ← URL/表情/停用詞
└─────────────────┘
    ↓
┌─────────────────┐
│  特徵標準化     │ ← StandardScaler
└─────────────────┘
    ↓
┌─────────────────┐
│  數據驗證       │ ← 完整性檢查
└─────────────────┘
    ↓
乾淨數據
```

---

## 🔧 設計模式與最佳實踐

### 1. 使用的設計模式

#### 1.1 工廠模式 (Factory Pattern)
```python
class DataLoader:
    def load_dataset(self, dataset_name: str):
        """根據名稱創建不同的數據加載器"""
        loaders = {
            'mall_customers': self.load_mall_customers,
            'ecommerce': self.load_ecommerce,
            'personality': self.load_personality,
        }
        return loaders[dataset_name]()
```

#### 1.2 策略模式 (Strategy Pattern)
```python
class Plotter:
    def plot(self, plot_type: str, data, **kwargs):
        """根據策略選擇繪圖方法"""
        strategies = {
            'scatter': self._plot_scatter,
            'heatmap': self._plot_heatmap,
            'dendrogram': self._plot_dendrogram,
        }
        return strategies[plot_type](data, **kwargs)
```

#### 1.3 單例模式 (Singleton Pattern)
```python
class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. SOLID原則應用

#### S - 單一職責原則
- ✅ `DataLoader`: 只負責數據加載
- ✅ `DataValidator`: 只負責數據驗證
- ✅ `TextCleaner`: 只負責文本清洗

#### O - 開閉原則
- ✅ 易於添加新的聚類算法而不修改現有代碼
- ✅ 插件式設計,支持自定義擴展

#### L - 里氏替換原則
- ✅ 所有聚類器可互換使用
- ✅ 一致的接口設計

#### I - 接口隔離原則
- ✅ 最小化接口,只暴露必要方法
- ✅ `__all__`明確定義公共API

#### D - 依賴倒置原則
- ✅ 依賴抽象(異常類)而非具體實現
- ✅ 使用type hints增強抽象性

### 3. 錯誤處理策略

#### 3.1 異常層次結構

```
Exception (Python內置)
    │
    └─ DataAnalysisError (基礎異常)
        ├─ DataLoadError (數據加載)
        ├─ ValidationError (數據驗證)
        ├─ ClusteringError (聚類)
        ├─ ConfigurationError (配置)
        ├─ VisualizationError (可視化)
        └─ ... (其他領域異常)
```

#### 3.2 錯誤處理最佳實踐

```python
# ✅ 好的做法
try:
    clusterer.fit(df, features)
except ValidationError as e:
    logger.error(f"數據驗證失敗: {e}")
    # 提供恢復建議
    raise
except ClusteringError as e:
    logger.error(f"聚類失敗: {e}")
    # 降級處理
    return default_result

# ❌ 避免
try:
    clusterer.fit(df, features)
except Exception:  # 太寬泛
    pass  # 吞掉錯誤
```

### 4. 日誌記錄策略

#### 4.1 日誌級別使用

| 級別 | 用途 | 示例 |
|------|------|------|
| DEBUG | 開發調試 | 中間變量值,循環計數 |
| INFO | 正常流程 | "開始聚類", "加載數據" |
| SUCCESS | 成功完成 | "聚類完成", "模型已保存" |
| WARNING | 潛在問題 | "未收斂", "性能下降" |
| ERROR | 錯誤但可恢復 | "文件未找到", "參數無效" |
| CRITICAL | 致命錯誤 | "系統崩潰", "數據損壞" |

#### 4.2 日誌配置

```python
# utils.py
def setup_logging(level="INFO"):
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=level
    )
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        level="DEBUG"
    )
```

---

## 📊 數據流與狀態管理

### 1. 典型分析流程

```
1. 初始化
   └─ python -m data_analysis_chatbots.init

2. 數據獲取
   └─ DataDownloader.download_dataset()

3. 數據加載
   └─ DataLoader.load_xxx()

4. 數據驗證
   └─ DataValidator.validate()

5. 數據清洗
   └─ TextCleaner.clean() / 手動處理

6. 特徵工程
   └─ 標準化 / PCA / 特徵選擇

7. 聚類分析
   ├─ 選擇算法
   ├─ 參數調優
   ├─ fit_predict()
   └─ evaluate_clustering()

8. 結果解釋
   ├─ get_cluster_summary()
   ├─ 可視化
   └─ 生成報告

9. 模型保存
   └─ joblib.dump()

10. 部署上線
    └─ Streamlit / API / Docker
```

### 2. 狀態管理

```python
class Clusterer:
    """狀態機設計"""

    STATES = ['INIT', 'FITTED', 'EVALUATED']

    def __init__(self):
        self.state = 'INIT'
        self.model = None
        self.labels_ = None

    def fit(self, X):
        assert self.state == 'INIT', "Already fitted"
        # ... 訓練邏輯
        self.state = 'FITTED'

    def predict(self, X):
        assert self.state in ['FITTED', 'EVALUATED'], "Not fitted"
        # ... 預測邏輯
        return labels

    def evaluate(self):
        assert self.state == 'FITTED', "Not fitted"
        # ... 評估邏輯
        self.state = 'EVALUATED'
```

---

## 🔐 安全性考慮

### 1. 數據隱私

```python
# 敏感數據處理
class DataLoader:
    def load_customer_data(self, anonymize=True):
        df = pd.read_csv(path)

        if anonymize:
            # 移除PII (個人可識別信息)
            df = df.drop(columns=['Name', 'Email', 'Phone'])
            # ID哈希化
            df['CustomerID'] = df['CustomerID'].apply(
                lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:16]
            )

        return df
```

### 2. 輸入驗證

```python
def validate_input(value, min_val, max_val, param_name):
    """驗證用戶輸入"""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{param_name}必須是數字")

    if not (min_val <= value <= max_val):
        raise ValidationError(
            f"{param_name}必須在[{min_val}, {max_val}]範圍內"
        )
```

### 3. 依賴安全

```bash
# 定期檢查安全漏洞
pip install safety
safety check -r requirements.txt

# 使用Bandit進行安全掃描
pip install bandit
bandit -r src/
```

---

## 🚀 性能優化

### 1. 計算優化

```python
# 使用向量化操作
# ❌ 慢
for i in range(len(df)):
    df.loc[i, 'normalized'] = (df.loc[i, 'value'] - mean) / std

# ✅ 快
df['normalized'] = (df['value'] - mean) / std

# 使用Numba加速
from numba import jit

@jit(nopython=True)
def fast_distance(X, Y):
    # 編譯為機器碼,速度提升10-100倍
    pass
```

### 2. 內存優化

```python
# 使用合適的數據類型
df['Category'] = df['Category'].astype('category')  # 節省內存
df['Count'] = df['Count'].astype('int32')  # 而非int64

# 分塊處理大文件
for chunk in pd.read_csv('large.csv', chunksize=10000):
    process(chunk)

# 使用Dask處理超大數據
import dask.dataframe as dd
ddf = dd.read_csv('huge.csv')
```

### 3. 緩存策略

```python
from functools import lru_cache

class DataLoader:
    @lru_cache(maxsize=5)
    def load_dataset(self, name):
        """緩存最近5個數據集"""
        return pd.read_csv(f'data/raw/{name}.csv')
```

---

## 📝 代碼質量保證

### 1. 測試策略

```
tests/
├── unit/              # 單元測試(70%)
│   ├── test_clustering.py
│   ├── test_preprocessing.py
│   └── ...
├── integration/       # 集成測試(20%)
│   ├── test_workflows.py
│   └── test_end_to_end.py
└── performance/       # 性能測試(10%)
    └── test_benchmarks.py

目標覆蓋率: 80%
```

### 2. 代碼質量工具

```yaml
# .pre-commit-config.yaml
- black (代碼格式化)
- isort (導入排序)
- flake8 (代碼檢查)
- mypy (類型檢查)
- bandit (安全檢查)
- pytest (測試)
```

### 3. 文檔規範

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    簡短描述(一句話)

    詳細描述(可選):
    - 功能說明
    - 使用場景
    - 注意事項

    Args:
        param1: 參數1說明
        param2: 參數2說明

    Returns:
        返回值說明

    Raises:
        ValueError: 何時拋出
        TypeError: 何時拋出

    Examples:
        >>> complex_function("test", 42)
        {'result': 'success'}

    Notes:
        - 性能考慮
        - 已知限制
    """
```

---

## 🔄 持續集成/部署 (CI/CD)

### GitHub Actions工作流

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src
      - name: Lint
        run: |
          black --check src/
          flake8 src/
          mypy src/
```

---

## 📚 延伸閱讀

- [系統設計文檔](docs/)
- [API參考](docs/api/)
- [貢獻指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

---

**架構設計**: 賴祺清
**最後更新**: 2025年1月18日
