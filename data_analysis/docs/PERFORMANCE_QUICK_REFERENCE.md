# 性能監控快速參考

## 快速開始

```python
from data_analysis_chatbots.utils import timer, memory_profiler, retry
from data_analysis_chatbots.utils.performance import monitor
```

## 裝飾器速查表

### @timer - 執行時間監控

```python
@timer
def my_function():
    # 你的代碼
    pass

# 輸出: "my_function executed in 0.1234 seconds"
```

### @memory_profiler - 內存監控

```python
@memory_profiler
def memory_intensive_task():
    # 你的代碼
    pass

# 輸出: "memory_intensive_task memory usage: Before=100.00 MB, After=150.00 MB, Diff=+50.00 MB"
```

### @retry - 重試機制

```python
# 基本用法
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def api_call():
    # 你的代碼
    pass

# 指定異常類型
@retry(
    max_attempts=5,
    delay=0.5,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError)
)
def network_operation():
    pass

# 使用回調
def on_retry_callback(attempt: int, error: Exception):
    print(f"Retry {attempt}: {error}")

@retry(max_attempts=3, on_retry=on_retry_callback)
def flaky_function():
    pass
```

### @monitor - 組合監控

```python
# 只監控時間
@monitor(time_it=True)
def func1():
    pass

# 時間 + 內存
@monitor(time_it=True, profile_memory=True)
def func2():
    pass

# 完整監控
@monitor(
    time_it=True,
    profile_memory=True,
    retry_config={"max_attempts": 3, "delay": 1.0}
)
def func3():
    pass
```

## 常見使用場景

### 場景 1: 數據處理管道

```python
@timer
def extract_data(source):
    return pd.read_csv(source)

@timer
@memory_profiler
def transform_data(df):
    # 轉換邏輯
    return transformed_df

@timer
@retry(max_attempts=3)
def load_data(df, destination):
    df.to_csv(destination)
```

### 場景 2: API 調用

```python
@timer
@retry(
    max_attempts=5,
    delay=1.0,
    backoff=2.0,
    exceptions=(requests.RequestException, ConnectionError)
)
def fetch_api_data(endpoint):
    response = requests.get(endpoint, timeout=10)
    response.raise_for_status()
    return response.json()
```

### 場景 3: 機器學習

```python
@monitor(time_it=True, profile_memory=True)
def train_model(X_train, y_train):
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    return model
```

## 裝飾器順序

```python
@timer                    # 最外層
@memory_profiler          # 中間層
@retry(max_attempts=3)    # 最內層
def my_function():
    pass
```

等價於:

```python
@monitor(
    time_it=True,
    profile_memory=True,
    retry_config={"max_attempts": 3}
)
def my_function():
    pass
```

## 參數說明

### @retry 參數

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `max_attempts` | int | 3 | 最大嘗試次數 |
| `delay` | float | 1.0 | 初始延遲（秒） |
| `backoff` | float | 2.0 | 延遲倍增因子 |
| `exceptions` | tuple | (Exception,) | 要捕獲的異常類型 |
| `on_retry` | callable | None | 重試回調函數 |

### @monitor 參數

| 參數 | 類型 | 默認值 | 說明 |
|------|------|--------|------|
| `time_it` | bool | True | 是否監控時間 |
| `profile_memory` | bool | False | 是否監控內存 |
| `retry_config` | dict | None | 重試配置字典 |

## 完整示例

```python
from data_analysis_chatbots.utils import timer, memory_profiler, retry
import pandas as pd
import requests

class DataProcessor:
    @timer
    @retry(max_attempts=3, delay=2.0)
    def fetch_data(self, url: str) -> dict:
        """從 API 獲取數據。"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    @timer
    @memory_profiler
    def process_data(self, data: dict) -> pd.DataFrame:
        """處理數據。"""
        df = pd.DataFrame(data)
        # 數據處理邏輯
        df['processed'] = df['value'] * 2
        return df

    @timer
    @retry(max_attempts=3)
    def save_results(self, df: pd.DataFrame, path: str):
        """保存結果。"""
        df.to_csv(path, index=False)

    def run(self, url: str, output_path: str):
        """運行完整流程。"""
        data = self.fetch_data(url)
        df = self.process_data(data)
        self.save_results(df, output_path)

# 使用
processor = DataProcessor()
processor.run('https://api.example.com/data', 'output.csv')
```

## 日誌輸出示例

```
2024-01-15 10:30:45.123 | INFO     | __main__:fetch_data - Fetching data...
2024-01-15 10:30:45.456 | INFO     | __main__:fetch_data - fetch_data executed in 0.3330 seconds
2024-01-15 10:30:45.457 | INFO     | __main__:process_data - Processing data...
2024-01-15 10:30:45.789 | INFO     | __main__:process_data - process_data memory usage: Before=150.25 MB, After=165.42 MB, Diff=+15.17 MB
2024-01-15 10:30:45.790 | INFO     | __main__:process_data - process_data executed in 0.3330 seconds
2024-01-15 10:30:45.791 | INFO     | __main__:save_results - Saving results...
2024-01-15 10:30:45.892 | INFO     | __main__:save_results - save_results executed in 0.1010 seconds
```

## 注意事項

1. **內存監控需要 psutil**: `pip install psutil`
2. **裝飾器順序很重要**: 遵循外層到內層的順序
3. **重試只捕獲指定異常**: 使用 `exceptions` 參數限制
4. **日誌配置**: 確保 loguru 已正確配置
5. **性能開銷**: 內存監控有一定開銷，僅在需要時使用

## 更多信息

詳細文檔請參考: `/home/user/Data-Analysis-with-Chatbots/docs/PERFORMANCE_MONITORING.md`
