# 性能監控功能使用指南

本文檔介紹如何使用 `data_analysis_chatbots.utils.performance` 模塊中的性能監控裝飾器。

## 目錄

1. [安裝依賴](#安裝依賴)
2. [裝飾器概覽](#裝飾器概覽)
3. [詳細使用說明](#詳細使用說明)
4. [實際應用示例](#實際應用示例)
5. [最佳實踐](#最佳實踐)

## 安裝依賴

### 必需依賴

```bash
pip install loguru
```

### 可選依賴（用於內存分析）

```bash
pip install psutil
```

如果未安裝 `psutil`，`@memory_profiler` 裝飾器會優雅降級，只執行函數而不進行內存分析。

## 裝飾器概覽

### 1. `@timer` - 執行時間監控

記錄函數執行時間，適用於性能優化和瓶頸識別。

**特點：**
- 自動記錄函數執行時間（精確到 0.0001 秒）
- 成功和失敗都會記錄
- 使用 loguru 進行日誌輸出

### 2. `@memory_profiler` - 內存使用監控

監控函數執行前後的內存使用情況。

**特點：**
- 記錄執行前後的內存使用量（MB）
- 計算內存差異
- 可選依賴（需要 psutil）
- 無 psutil 時自動降級

### 3. `@retry` - 重試機制

為函數添加帶指數退避的重試邏輯。

**特點：**
- 可配置最大重試次數
- 指數退避延遲
- 可指定捕獲的異常類型
- 支持自定義重試回調
- 詳細的重試日誌

### 4. `@monitor` - 組合監控

便利裝飾器，可同時應用多個監控功能。

**特點：**
- 可選擇性啟用 timer、memory_profiler、retry
- 一次性配置所有監控功能
- 簡化代碼

## 詳細使用說明

### 1. Timer 裝飾器

#### 基本用法

```python
from data_analysis_chatbots.utils import timer

@timer
def process_data(df):
    """處理數據框。"""
    # 數據處理邏輯
    result = df.groupby('category').agg({'value': 'sum'})
    return result

# 使用
result = process_data(my_dataframe)
# 日誌輸出: "process_data executed in 0.1234 seconds"
```

#### 用於類方法

```python
class DataProcessor:
    @timer
    def load_data(self, filepath):
        """加載數據。"""
        return pd.read_csv(filepath)

    @timer
    def transform(self, df):
        """轉換數據。"""
        return df.apply(some_transformation)
```

### 2. Memory Profiler 裝飾器

#### 基本用法

```python
from data_analysis_chatbots.utils import memory_profiler

@memory_profiler
def create_large_dataset():
    """創建大型數據集。"""
    data = pd.DataFrame({
        'col1': range(1000000),
        'col2': range(1000000)
    })
    return data

# 使用
df = create_large_dataset()
# 日誌輸出: "create_large_dataset memory usage: Before=150.25 MB, After=182.45 MB, Diff=+32.20 MB"
```

#### 監控內存泄漏

```python
@memory_profiler
def potentially_leaky_function():
    """可能存在內存泄漏的函數。"""
    results = []
    for i in range(1000):
        # 某些可能導致內存累積的操作
        results.append(heavy_computation(i))
    return results
```

### 3. Retry 裝飾器

#### 基本用法

```python
from data_analysis_chatbots.utils import retry

@retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_data_from_api():
    """從 API 獲取數據。"""
    response = requests.get('https://api.example.com/data')
    response.raise_for_status()
    return response.json()

# 使用
data = fetch_data_from_api()
# 如果失敗，會自動重試：第1次延遲1秒，第2次延遲2秒，第3次延遲4秒
```

#### 指定異常類型

```python
@retry(
    max_attempts=5,
    delay=0.5,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError, requests.RequestException)
)
def unstable_network_operation():
    """不穩定的網絡操作。"""
    # 只捕獲指定的異常類型
    return download_file()
```

#### 使用自定義回調

```python
def custom_retry_handler(attempt: int, error: Exception):
    """自定義重試處理器。"""
    logger.warning(f"重試第 {attempt} 次: {error}")
    # 可以添加其他邏輯，如發送通知
    send_alert(f"Operation failed: {error}")

@retry(
    max_attempts=3,
    delay=1.0,
    on_retry=custom_retry_handler
)
def critical_operation():
    """關鍵操作。"""
    return perform_important_task()
```

### 4. Monitor 組合裝飾器

#### 只監控時間

```python
from data_analysis_chatbots.utils.performance import monitor

@monitor(time_it=True)
def simple_analysis(data):
    """簡單分析。"""
    return data.describe()
```

#### 時間 + 內存監控

```python
@monitor(time_it=True, profile_memory=True)
def complex_analysis(data):
    """複雜分析。"""
    result = perform_heavy_computation(data)
    return result
```

#### 完整監控（時間 + 內存 + 重試）

```python
@monitor(
    time_it=True,
    profile_memory=True,
    retry_config={
        "max_attempts": 3,
        "delay": 1.0,
        "backoff": 2.0,
        "exceptions": (ConnectionError, TimeoutError)
    }
)
def fetch_and_process():
    """獲取並處理數據。"""
    data = fetch_from_remote_api()
    processed = process_data(data)
    return processed
```

## 實際應用示例

### 示例 1: 數據 ETL 管道

```python
from data_analysis_chatbots.utils import timer, memory_profiler, retry
import pandas as pd

class DataPipeline:
    """數據 ETL 管道。"""

    @timer
    @retry(max_attempts=3, delay=2.0)
    def extract(self, source: str) -> pd.DataFrame:
        """從數據源提取數據。"""
        logger.info(f"Extracting from {source}")
        return pd.read_csv(source)

    @timer
    @memory_profiler
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """轉換數據。"""
        logger.info("Transforming data")
        df = df.copy()
        df['normalized_value'] = (df['value'] - df['value'].mean()) / df['value'].std()
        df['category_mean'] = df.groupby('category')['value'].transform('mean')
        return df

    @timer
    @retry(max_attempts=3, delay=1.0, exceptions=(IOError, ConnectionError))
    def load(self, df: pd.DataFrame, destination: str):
        """加載數據到目標位置。"""
        logger.info(f"Loading to {destination}")
        df.to_csv(destination, index=False)
        logger.info(f"Successfully loaded {len(df)} records")

    def run(self, source: str, destination: str):
        """運行完整管道。"""
        df = self.extract(source)
        df = self.transform(df)
        self.load(df, destination)

# 使用
pipeline = DataPipeline()
pipeline.run('input.csv', 'output.csv')
```

### 示例 2: 機器學習模型訓練

```python
from data_analysis_chatbots.utils.performance import monitor

class ModelTrainer:
    """機器學習模型訓練器。"""

    @monitor(time_it=True, profile_memory=True)
    def train_model(self, X_train, y_train):
        """訓練模型。"""
        logger.info("Training model...")
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X_train, y_train)
        return model

    @monitor(time_it=True)
    def evaluate_model(self, model, X_test, y_test):
        """評估模型。"""
        logger.info("Evaluating model...")
        predictions = model.predict(X_test)
        return {
            'accuracy': accuracy_score(y_test, predictions),
            'precision': precision_score(y_test, predictions),
            'recall': recall_score(y_test, predictions)
        }
```

### 示例 3: API 數據獲取

```python
import requests
from data_analysis_chatbots.utils import retry, timer

def retry_callback(attempt: int, error: Exception):
    """重試回調函數。"""
    logger.warning(f"API call failed (attempt {attempt}): {error}")

@timer
@retry(
    max_attempts=5,
    delay=1.0,
    backoff=2.0,
    exceptions=(requests.RequestException, ConnectionError, TimeoutError),
    on_retry=retry_callback
)
def fetch_api_data(endpoint: str, params: dict = None):
    """從 API 獲取數據。"""
    response = requests.get(endpoint, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# 使用
data = fetch_api_data('https://api.example.com/data', {'limit': 100})
```

### 示例 4: 批量數據處理

```python
from data_analysis_chatbots.utils import timer, memory_profiler
from typing import List
import pandas as pd

class BatchProcessor:
    """批量數據處理器。"""

    @timer
    def process_batch(self, files: List[str]) -> pd.DataFrame:
        """處理批量文件。"""
        results = []
        for file in files:
            df = self._process_single_file(file)
            results.append(df)
        return pd.concat(results, ignore_index=True)

    @timer
    @memory_profiler
    def _process_single_file(self, filepath: str) -> pd.DataFrame:
        """處理單個文件。"""
        df = pd.read_csv(filepath)
        df = self._clean_data(df)
        df = self._transform_data(df)
        return df

    @timer
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理數據。"""
        df = df.dropna()
        df = df.drop_duplicates()
        return df

    @timer
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """轉換數據。"""
        df['processed_at'] = pd.Timestamp.now()
        return df

# 使用
processor = BatchProcessor()
result = processor.process_batch(['file1.csv', 'file2.csv', 'file3.csv'])
```

## 最佳實踐

### 1. 選擇合適的裝飾器

- **@timer**: 用於所有需要性能監控的函數
- **@memory_profiler**: 用於處理大型數據集或可能出現內存問題的函數
- **@retry**: 用於網絡請求、數據庫操作等可能暫時失敗的操作
- **@monitor**: 用於需要多種監控的複雜操作

### 2. 裝飾器順序

裝飾器從下往上執行，建議順序：

```python
@timer                    # 最外層：記錄總時間
@memory_profiler          # 中間層：記錄內存使用
@retry(max_attempts=3)    # 最內層：處理重試邏輯
def my_function():
    pass
```

或使用 `@monitor` 簡化：

```python
@monitor(
    time_it=True,
    profile_memory=True,
    retry_config={"max_attempts": 3}
)
def my_function():
    pass
```

### 3. 日誌配置

確保在應用啟動時配置 loguru：

```python
from loguru import logger
import sys

# 配置日誌
logger.remove()  # 移除默認處理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 添加文件日誌
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)
```

### 4. 性能優化建議

- 僅在需要時使用 `@memory_profiler`，因為它會增加一些開銷
- 在生產環境中，考慮使用配置文件控制裝飾器的啟用
- 對於高頻調用的函數，謹慎使用內存分析
- 使用 `@retry` 時，設置合理的 `max_attempts` 和 `delay` 參數

### 5. 錯誤處理

```python
@retry(
    max_attempts=3,
    exceptions=(ValueError, TypeError),  # 只重試特定異常
)
def validate_and_process(data):
    """驗證並處理數據。"""
    if not isinstance(data, dict):
        raise TypeError("Expected dict")
    if 'required_field' not in data:
        raise ValueError("Missing required field")
    return process(data)
```

### 6. 測試建議

在單元測試中，可以臨時禁用裝飾器：

```python
# test_my_module.py
import pytest
from unittest.mock import patch

def test_my_function():
    """測試函數邏輯，不進行性能監控。"""
    # 方法 1: 直接調用被裝飾函數的 __wrapped__ 屬性
    result = my_function.__wrapped__(args)

    # 方法 2: 使用 mock
    with patch('data_analysis_chatbots.utils.performance.timer', lambda f: f):
        result = my_function(args)
```

## 運行示例

完整示例請參考：

- **模塊測試**: `/home/user/Data-Analysis-with-Chatbots/src/data_analysis_chatbots/utils/performance.py`

  運行內置示例：
  ```bash
  python src/data_analysis_chatbots/utils/performance.py
  ```

- **實際應用示例**: `/home/user/Data-Analysis-with-Chatbots/examples/performance_monitoring_demo.py`

  運行完整演示：
  ```bash
  python examples/performance_monitoring_demo.py
  ```

## 故障排除

### psutil 未安裝

**問題**: 使用 `@memory_profiler` 時出現警告

**解決方案**:
```bash
pip install psutil
```

### 日誌未顯示

**問題**: 沒有看到性能監控日誌

**解決方案**: 檢查 loguru 配置，確保日誌級別設置正確
```python
logger.add(sys.stderr, level="INFO")  # 確保級別不是 WARNING 或 ERROR
```

### 裝飾器不工作

**問題**: 裝飾器似乎沒有效果

**解決方案**:
1. 檢查導入是否正確
2. 確保裝飾器語法正確（使用 `@` 符號）
3. 檢查是否有其他裝飾器衝突

## 總結

性能監控裝飾器提供了：

- ✅ 簡單易用的 API
- ✅ 詳細的執行時間和內存使用信息
- ✅ 靈活的重試機制
- ✅ 可組合的監控功能
- ✅ 生產環境就緒

根據實際需求選擇合適的裝飾器，可以有效提升應用的可觀測性和可靠性。
