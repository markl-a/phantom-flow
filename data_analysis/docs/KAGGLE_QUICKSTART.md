# Kaggle 數據集快速入門

本指南教您如何使用 Kaggle API 直接下載數據集並訓練模型。

## 🚀 快速開始

### 1. 安裝 Kaggle CLI

```bash
pip install kaggle
```

### 2. 配置 Kaggle API 憑證

#### 方法 A: 自動設置指南

```python
from data_analysis_chatbots import setup_kaggle_credentials

setup_kaggle_credentials()  # 顯示詳細的設置步驟
```

#### 方法 B: 手動設置

1. 登錄 [Kaggle](https://www.kaggle.com)
2. 進入 [Account Settings](https://www.kaggle.com/settings)
3. 滾動到 **API** 部分
4. 點擊 **Create New API Token**
5. 下載 `kaggle.json` 文件
6. 將文件移動到正確位置：

```bash
# Linux / Mac
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
mkdir %USERPROFILE%\.kaggle
move %USERPROFILE%\Downloads\kaggle.json %USERPROFILE%\.kaggle\
```

7. 驗證安裝：

```bash
kaggle datasets list
```

## 📦 下載數據集

### 使用 Python API

#### 方式 1: 快速下載（推薦）

```python
from data_analysis_chatbots import quick_download

# 下載 Titanic 數據集
data_path = quick_download('titanic')
print(f"數據路徑: {data_path}")
```

#### 方式 2: 使用下載器類

```python
from data_analysis_chatbots import KaggleDatasetDownloader

# 創建下載器
downloader = KaggleDatasetDownloader()

# 下載數據集
data_path = downloader.download_dataset('titanic')
```

### 常用數據集列表

```python
from data_analysis_chatbots import KaggleDatasetDownloader

downloader = KaggleDatasetDownloader()
downloader.list_popular_datasets()
```

### 支持的數據集簡稱

#### 結構化數據
- `titanic` - Titanic 生存預測
- `house-prices` - 房價預測
- `credit-fraud` - 信用卡欺詐檢測
- `customer-churn` - 客戶流失預測
- `bank-marketing` - 銀行營銷
- `wine-quality` - 葡萄酒質量
- `adult-income` - 成人收入預測

#### 時間序列
- `bitcoin` - 比特幣價格
- `stock-market` - 股票市場數據
- `sales` - 商店銷售數據
- `energy` - 能源消耗
- `covid19` - COVID-19 數據

#### NLP
- `sentiment` - 情感分析
- `spam` - 垃圾郵件檢測
- `news` - 新聞分類
- `toxic-comments` - 有毒評論

#### 推薦系統
- `movies` - 電影推薦 (MovieLens)
- `books` - 圖書推薦
- `music` - 音樂推薦

#### 計算機視覺
- `mnist` - 手寫數字
- `fashion-mnist` - 時尚物品分類
- `cifar10` - CIFAR-10 圖像
- `cats-dogs` - 貓狗分類
- `plant-disease` - 植物病害

## 🔍 搜索數據集

### 使用 Python

```python
downloader = KaggleDatasetDownloader()
downloader.search_datasets('time series', max_results=10)
```

### 使用命令行

```bash
kaggle datasets list -s "time series"
```

## 💻 完整示例

### Titanic 生存預測

```python
from data_analysis_chatbots import quick_download
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. 下載數據
data_path = quick_download('titanic')

# 2. 加載數據
df = pd.read_csv(data_path / 'train.csv')

# 3. 特徵工程
df['Age'].fillna(df['Age'].median(), inplace=True)
df['Fare'].fillna(df['Fare'].median(), inplace=True)
df['Sex'] = df['Sex'].map({'male': 0, 'female': 1})

# 4. 準備特徵和目標
features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare']
X = df[features]
y = df['Survived']

# 5. 訓練模型
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. 評估
y_pred = model.predict(X_test)
print(f"準確率: {accuracy_score(y_test, y_pred):.4f}")
```

### 運行完整示例

```bash
# 運行示例腳本
python examples/kaggle_dataset_example.py --example 1  # Titanic
python examples/kaggle_dataset_example.py --example 2  # 房價
python examples/kaggle_dataset_example.py --all         # 所有示例
```

## 🏆 下載競賽數據

```python
downloader = KaggleDatasetDownloader()

# 下載競賽數據（需要先接受競賽規則）
comp_path = downloader.download_competition_data('titanic')
```

## 🛠️ 高級用法

### 自定義下載目錄

```python
from pathlib import Path

downloader = KaggleDatasetDownloader(
    data_dir=Path('/custom/data/directory')
)

data_path = downloader.download_dataset('titanic')
```

### 強制重新下載

```python
data_path = downloader.download_dataset('titanic', force=True)
```

### 下載但不解壓

```python
data_path = downloader.download_dataset('titanic', unzip=False)
```

### 使用完整數據集路徑

```python
# 使用簡稱
data_path = downloader.download_dataset('titanic')

# 使用完整路徑
data_path = downloader.download_dataset('username/dataset-name')
```

## 📁 數據存儲結構

下載的數據會存儲在：

```
project_root/
└── data/
    ├── raw/                    # 原始數據集
    │   ├── titanic/
    │   ├── house-prices-.../
    │   └── ...
    ├── processed/              # 處理後的數據
    └── competitions/           # 競賽數據
```

## 🔧 故障排除

### 問題 1: 找不到 Kaggle 命令

```bash
# 確認安裝
pip install kaggle

# 檢查版本
kaggle --version
```

### 問題 2: 憑證錯誤

```
401 - Unauthorized
```

**解決方案**:
1. 檢查 `~/.kaggle/kaggle.json` 是否存在
2. 確認文件權限: `chmod 600 ~/.kaggle/kaggle.json`
3. 重新下載 API token

### 問題 3: 數據集未找到

```
404 - Not Found
```

**解決方案**:
1. 確認數據集名稱正確
2. 檢查數據集是否為私有
3. 使用 `kaggle datasets list -s "keyword"` 搜索

### 問題 4: 下載速度慢

**解決方案**:
- 使用更快的網絡連接
- 考慮使用代理
- 選擇較小的數據集

## 📚 更多資源

- [Kaggle API 官方文檔](https://github.com/Kaggle/kaggle-api)
- [Kaggle 數據集瀏覽](https://www.kaggle.com/datasets)
- [Kaggle 競賽](https://www.kaggle.com/competitions)
- [專案示例](../examples/kaggle_dataset_example.py)

## 💡 最佳實踐

1. **版本控制**: 不要將下載的數據提交到 Git
   ```gitignore
   # .gitignore
   data/raw/*
   data/processed/*
   !data/raw/.gitkeep
   ```

2. **數據管理**: 定期清理不用的數據集
   ```bash
   # 查看數據大小
   du -sh data/raw/*

   # 刪除特定數據集
   rm -rf data/raw/dataset-name
   ```

3. **自動化**: 在腳本中自動下載所需數據
   ```python
   def ensure_data(dataset_name):
       """確保數據已下載"""
       try:
           return quick_download(dataset_name)
       except Exception as e:
           print(f"下載失敗: {e}")
           raise
   ```

4. **緩存**: 避免重復下載
   ```python
   # 默認行為：如果已存在則跳過
   data_path = quick_download('titanic')  # 不會重複下載

   # 強制重新下載
   data_path = quick_download('titanic', force=True)
   ```

## 🎯 下一步

1. 嘗試下載並訓練一個模型
2. 探索不同的數據集
3. 參與 Kaggle 競賽
4. 分享您的解決方案

---

**作者**: Data Analysis with Chatbots Team
**更新**: 2025-01-19
