# 故障排除指南

> **完整的 Data Analysis with Chatbots 專案故障排除指南**
> 涵蓋常見錯誤、環境問題、數據問題、性能問題的診斷和解決方案

## 目錄

1. [常見錯誤](#常見錯誤)
2. [環境問題](#環境問題)
3. [數據問題](#數據問題)
4. [性能問題](#性能問題)
5. [聚類相關問題](#聚類相關問題)
6. [Docker 相關問題](#docker-相關問題)
7. [Streamlit 相關問題](#streamlit-相關問題)
8. [調試技巧](#調試技巧)
9. [獲取幫助](#獲取幫助)

---

## 常見錯誤

### ModuleNotFoundError

#### 錯誤 1: `ModuleNotFoundError: No module named 'data_analysis_chatbots'`

**原因**:
- 專案包未正確安裝
- Python 路徑配置不正確
- 虛擬環境未激活

**診斷**:
```bash
# 檢查包是否已安裝
pip list | grep data-analysis-chatbots

# 檢查 Python 路徑
python -c "import sys; print('\n'.join(sys.path))"

# 檢查虛擬環境
which python
```

**解決方案**:

方案 1 - 重新安裝包:
```bash
# 確保在專案根目錄
cd /path/to/Data-Analysis-with-Chatbots

# 激活虛擬環境（如果使用）
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 以可編輯模式安裝
pip install -e .

# 驗證安裝
python -c "import data_analysis_chatbots; print('Success!')"
```

方案 2 - 添加到 Python 路徑:
```python
# 在腳本頂部添加
import sys
from pathlib import Path

# 添加 src 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# 現在可以導入
import data_analysis_chatbots
```

方案 3 - 使用環境變量:
```bash
# Linux/macOS
export PYTHONPATH="${PYTHONPATH}:/path/to/Data-Analysis-with-Chatbots/src"

# Windows
set PYTHONPATH=%PYTHONPATH%;C:\path\to\Data-Analysis-with-Chatbots\src
```

#### 錯誤 2: `ModuleNotFoundError: No module named 'sklearn'`

**原因**: scikit-learn 未安裝或版本不兼容

**解決方案**:
```bash
# 安裝 scikit-learn
pip install scikit-learn>=1.3.0

# 或重新安裝所有依賴
pip install -r requirements.txt

# 驗證
python -c "import sklearn; print(sklearn.__version__)"
```

#### 錯誤 3: `ModuleNotFoundError: No module named 'streamlit'`

**解決方案**:
```bash
# 安裝 Streamlit
pip install streamlit>=1.28.0

# 驗證
streamlit --version
```

---

### FileNotFoundError

#### 錯誤 1: 數據文件未找到

**錯誤信息**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/Mall_Customers.csv'
```

**原因**:
- 數據文件未下載
- 文件路徑不正確
- 目錄結構未初始化

**診斷**:
```bash
# 檢查文件是否存在
ls -la data/raw/

# 檢查目錄結構
tree data/  # 或使用 find data/

# 檢查當前工作目錄
pwd
```

**解決方案**:

方案 1 - 初始化目錄結構:
```bash
# 創建必要的目錄
python -m data_analysis_chatbots.init --with-examples

# 驗證
ls -la data/raw/
```

方案 2 - 下載數據集:
```bash
# 下載所有數據集
python -m data_analysis_chatbots.data_downloader --all

# 或下載特定數據集
python -m data_analysis_chatbots.data_downloader --dataset mall_customers

# 或創建範例數據
python -m data_analysis_chatbots.data_downloader --sample
```

方案 3 - 手動下載:
```bash
# 從 Kaggle 手動下載數據集
# 1. 訪問 https://www.kaggle.com/datasets/vjchoudhary7/customer-segmentation-tutorial-in-python
# 2. 下載 CSV 文件
# 3. 將文件移動到 data/raw/ 目錄

mkdir -p data/raw
mv ~/Downloads/Mall_Customers.csv data/raw/
```

方案 4 - 使用絕對路徑:
```python
from pathlib import Path

# 獲取專案根目錄
project_root = Path(__file__).parent.absolute()
data_path = project_root / 'data' / 'raw' / 'Mall_Customers.csv'

# 使用絕對路徑
df = pd.read_csv(data_path)
```

#### 錯誤 2: 配置文件未找到

**錯誤信息**:
```
FileNotFoundError: 配置文件不存在: config/config.yaml
```

**解決方案**:
```bash
# 檢查配置文件
ls -la config/

# 如果不存在，從模板創建
cp config/config.yaml.example config/config.yaml

# 或從 GitHub 獲取
curl -o config/config.yaml https://raw.githubusercontent.com/markl-a/Data-Analysis-with-Chatbots/main/config/config.yaml
```

---

### MemoryError

#### 錯誤: 處理大數據集時內存不足

**錯誤信息**:
```
MemoryError: Unable to allocate array with shape (1000000, 100)
```

**原因**:
- 系統內存不足
- 嘗試一次性加載過大的數據
- 未使用批處理

**診斷**:
```bash
# 檢查系統內存
free -h  # Linux
# 或
vm_stat  # macOS

# 檢查 Python 進程內存使用
ps aux | grep python

# 在 Python 中檢查
import psutil
print(f"可用內存: {psutil.virtual_memory().available / 1024**3:.2f} GB")
```

**解決方案**:

方案 1 - 使用批處理（chunks）:
```python
import pandas as pd

# 使用 chunksize 參數
chunk_size = 10000
chunks = pd.read_csv('large_file.csv', chunksize=chunk_size)

results = []
for chunk in chunks:
    # 處理每個塊
    processed = process_chunk(chunk)
    results.append(processed)

# 合併結果
final_df = pd.concat(results, ignore_index=True)
```

方案 2 - 減少數據類型大小:
```python
# 優化數據類型以減少內存使用
df['age'] = df['age'].astype('int8')  # 而不是 int64
df['income'] = df['income'].astype('float32')  # 而不是 float64

# 或使用 category 類型
df['gender'] = df['gender'].astype('category')
```

方案 3 - 使用 Dask 處理大數據:
```bash
# 安裝 Dask
pip install dask[complete]
```

```python
import dask.dataframe as dd

# 使用 Dask 讀取大文件
df = dd.read_csv('large_file.csv')

# Dask 會延遲計算，只在需要時加載數據
result = df.groupby('customer_id').agg({'amount': 'sum'}).compute()
```

方案 4 - 增加交換空間（Linux）:
```bash
# 創建 4GB 交換文件
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 驗證
swapon --show
```

方案 5 - 配置 Docker 內存限制:
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 8G  # 增加到 8GB
        reservations:
          memory: 4G
```

方案 6 - 降採樣數據:
```python
# 如果可行，對數據進行採樣
df_sample = df.sample(frac=0.1, random_state=42)  # 使用 10% 的數據

# 或使用 stratified 採樣
from sklearn.model_selection import train_test_split
df_sample, _ = train_test_split(df, train_size=0.1, stratify=df['category'], random_state=42)
```

---

### ImportError

#### 錯誤: `ImportError: cannot import name 'XXX' from 'data_analysis_chatbots'`

**原因**:
- 模塊結構變更
- 循環導入
- 版本不兼容

**診斷**:
```python
# 檢查模塊內容
import data_analysis_chatbots
print(dir(data_analysis_chatbots))

# 檢查具體模塊
from data_analysis_chatbots import clustering
print(dir(clustering))
```

**解決方案**:
```bash
# 重新安裝包
pip uninstall data-analysis-chatbots
pip install -e .

# 清除 Python 緩存
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 重新導入
python -c "from data_analysis_chatbots import KMeansClusterer; print('OK')"
```

---

### ValueError

#### 錯誤 1: 數組形狀不匹配

**錯誤信息**:
```
ValueError: Found array with 0 sample(s) (shape=(0, 5)) while a minimum of 1 is required.
```

**原因**: DataFrame 為空或過濾後沒有數據

**解決方案**:
```python
# 添加數據驗證
if df.empty:
    raise ValueError("DataFrame 為空，請檢查數據源")

if len(df) < 10:
    raise ValueError(f"數據太少（{len(df)} 行），需要至少 10 行數據")

# 檢查過濾條件
print(f"過濾前: {len(df_original)} 行")
df_filtered = df_original[df_original['age'] > 18]
print(f"過濾後: {len(df_filtered)} 行")

if df_filtered.empty:
    print("警告: 過濾條件過於嚴格，導致沒有數據")
```

#### 錯誤 2: 列名不存在

**錯誤信息**:
```
ValueError: 列 'Annual Income (k$)' 不存在於 DataFrame
```

**解決方案**:
```python
# 檢查可用列名
print("可用列:", df.columns.tolist())

# 使用正確的列名
# 可能是大小寫或空格問題
df.columns = df.columns.str.strip()  # 去除空格
df.columns = df.columns.str.lower()  # 轉小寫

# 或使用映射
column_mapping = {
    'Annual Income (k$)': 'income',
    'Spending Score (1-100)': 'spending'
}
df = df.rename(columns=column_mapping)
```

---

### KeyError

#### 錯誤: 字典鍵不存在

**錯誤信息**:
```
KeyError: 'CustomerID'
```

**解決方案**:
```python
# 使用 .get() 方法提供默認值
customer_id = data.get('CustomerID', None)

# 或使用 try-except
try:
    customer_id = data['CustomerID']
except KeyError:
    print("警告: CustomerID 不存在，使用默認值")
    customer_id = None

# 檢查鍵是否存在
if 'CustomerID' in data:
    customer_id = data['CustomerID']
else:
    print("可用鍵:", list(data.keys()))
```

---

### AttributeError

#### 錯誤: 對象沒有該屬性

**錯誤信息**:
```
AttributeError: 'NoneType' object has no attribute 'fit'
```

**原因**: 對象未正確初始化或為 None

**解決方案**:
```python
# 添加 None 檢查
if clusterer is None:
    clusterer = KMeansClusterer(n_clusters=5)

# 或使用斷言
assert clusterer is not None, "聚類器未初始化"

# 檢查對象類型
print(f"對象類型: {type(clusterer)}")
print(f"可用方法: {dir(clusterer)}")
```

---

## 環境問題

### Kaggle API 配置

#### 問題 1: Kaggle API 憑證未找到

**錯誤信息**:
```
OSError: Could not find kaggle.json. Make sure it's located in ~/.kaggle/
```

**解決方案**:

步驟 1 - 創建 API Token:
1. 登錄 Kaggle: https://www.kaggle.com
2. 點擊右上角頭像 -> Account
3. 滾動到 "API" 部分
4. 點擊 "Create New API Token"
5. 下載 `kaggle.json` 文件

步驟 2 - 配置憑證:
```bash
# Linux/macOS
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows
# 創建目錄: C:\Users\<你的用戶名>\.kaggle\
# 將 kaggle.json 移動到該目錄
```

步驟 3 - 驗證:
```bash
# 測試 Kaggle API
kaggle datasets list

# 或在 Python 中測試
python -c "from kaggle.api.kaggle_api_extended import KaggleApi; api = KaggleApi(); api.authenticate(); print('OK')"
```

#### 問題 2: Kaggle API 權限錯誤

**錯誤信息**:
```
PermissionError: [Errno 13] Permission denied: '/root/.kaggle/kaggle.json'
```

**解決方案**:
```bash
# 修改文件權限
chmod 600 ~/.kaggle/kaggle.json

# 確保所有者正確
ls -la ~/.kaggle/kaggle.json

# 如果需要，更改所有者
sudo chown $USER:$USER ~/.kaggle/kaggle.json
```

#### 問題 3: Kaggle 下載速度慢或超時

**解決方案**:
```python
# 增加超時時間
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()

# 使用重試機制
import time
from requests.exceptions import RequestException

max_retries = 3
for i in range(max_retries):
    try:
        api.dataset_download_files('dataset-name', path='data/raw/', unzip=True)
        break
    except RequestException as e:
        if i < max_retries - 1:
            print(f"下載失敗，{5}秒後重試...")
            time.sleep(5)
        else:
            raise
```

---

### 依賴衝突

#### 問題 1: 包版本衝突

**錯誤信息**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**診斷**:
```bash
# 檢查衝突
pip check

# 查看依賴樹
pip install pipdeptree
pipdeptree
```

**解決方案**:

方案 1 - 使用虛擬環境（強烈推薦）:
```bash
# 創建乾淨的虛擬環境
python -m venv venv_new
source venv_new/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

方案 2 - 更新所有包:
```bash
# 列出過時的包
pip list --outdated

# 更新特定包
pip install --upgrade package-name

# 或使用 pip-review
pip install pip-review
pip-review --auto
```

方案 3 - 使用 requirements.txt 鎖定版本:
```bash
# 生成當前環境的精確版本
pip freeze > requirements-lock.txt

# 使用鎖定版本安裝
pip install -r requirements-lock.txt
```

#### 問題 2: NumPy/Pandas 版本不兼容

**錯誤信息**:
```
ImportError: numpy.core.multiarray failed to import
```

**解決方案**:
```bash
# 重新安裝 NumPy 和 Pandas
pip uninstall numpy pandas -y
pip install numpy>=1.24.0 pandas>=2.0.0

# 或重新安裝所有依賴
pip install -r requirements.txt --force-reinstall
```

#### 問題 3: scikit-learn 版本問題

**錯誤信息**:
```
AttributeError: module 'sklearn.cluster' has no attribute 'KMeans'
```

**解決方案**:
```bash
# 確保使用正確版本
pip install scikit-learn>=1.3.0

# 驗證版本
python -c "import sklearn; print(sklearn.__version__)"

# 清除緩存後重新導入
python -c "from sklearn.cluster import KMeans; print('OK')"
```

---

### Python 版本問題

#### 問題: Python 版本過舊

**錯誤信息**:
```
SyntaxError: invalid syntax (f-string requires Python 3.6+)
```

**診斷**:
```bash
# 檢查 Python 版本
python --version

# 檢查可用的 Python 版本
ls /usr/bin/python*
```

**解決方案**:
```bash
# Ubuntu/Debian - 安裝 Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 創建使用特定版本的虛擬環境
python3.11 -m venv venv
source venv/bin/activate

# macOS - 使用 Homebrew
brew install python@3.11

# Windows - 下載安裝包
# https://www.python.org/downloads/
```

---

### 虛擬環境問題

#### 問題 1: 虛擬環境未激活

**症狀**: 安裝的包找不到，或使用了系統 Python

**診斷**:
```bash
# 檢查當前 Python 路徑
which python

# 應該顯示虛擬環境路徑，例如:
# /path/to/project/venv/bin/python

# 檢查 pip 路徑
which pip
```

**解決方案**:
```bash
# 激活虛擬環境
# Linux/macOS:
source venv/bin/activate

# Windows PowerShell:
venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# 驗證
echo $VIRTUAL_ENV  # Linux/macOS
echo %VIRTUAL_ENV%  # Windows
```

#### 問題 2: 虛擬環境損壞

**解決方案**:
```bash
# 刪除舊環境
rm -rf venv

# 創建新環境
python3 -m venv venv
source venv/bin/activate

# 重新安裝依賴
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## 數據問題

### 數據格式錯誤

#### 問題 1: CSV 編碼問題

**錯誤信息**:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```

**解決方案**:
```python
# 嘗試不同編碼
encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'gbk']

for encoding in encodings:
    try:
        df = pd.read_csv('data.csv', encoding=encoding)
        print(f"成功! 使用編碼: {encoding}")
        break
    except UnicodeDecodeError:
        continue
else:
    print("無法解碼文件")

# 或自動檢測編碼
import chardet

with open('data.csv', 'rb') as f:
    result = chardet.detect(f.read())
    encoding = result['encoding']

df = pd.read_csv('data.csv', encoding=encoding)
```

#### 問題 2: 日期格式問題

**錯誤信息**:
```
ValueError: time data '31/12/2024' does not match format '%Y-%m-%d'
```

**解決方案**:
```python
# 使用 pd.to_datetime 的 infer_datetime_format
df['date'] = pd.to_datetime(df['date'], infer_datetime_format=True)

# 或指定格式
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

# 或使用 dayfirst 參數
df['date'] = pd.to_datetime(df['date'], dayfirst=True)

# 處理錯誤
df['date'] = pd.to_datetime(df['date'], errors='coerce')  # 無效日期轉為 NaT
```

#### 問題 3: 分隔符錯誤

**解決方案**:
```python
# CSV 使用分號
df = pd.read_csv('data.csv', sep=';')

# 或使用 delimiter
df = pd.read_csv('data.csv', delimiter='|')

# 自動檢測分隔符
df = pd.read_csv('data.csv', sep=None, engine='python')
```

---

### 缺失值處理

#### 問題 1: 缺失值過多導致聚類失敗

**錯誤信息**:
```
ValueError: Input contains NaN, infinity or a value too large for dtype('float64')
```

**診斷**:
```python
# 檢查缺失值
print("缺失值統計:")
print(df.isnull().sum())

# 計算缺失百分比
missing_pct = (df.isnull().sum() / len(df)) * 100
print("\n缺失百分比:")
print(missing_pct[missing_pct > 0])

# 可視化缺失值
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(12, 6))
sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
plt.title('缺失值熱圖')
plt.show()
```

**解決方案**:

方案 1 - 刪除缺失值:
```python
# 刪除包含任何缺失值的行
df_clean = df.dropna()

# 刪除特定列有缺失值的行
df_clean = df.dropna(subset=['age', 'income'])

# 刪除缺失值過多的列
threshold = 0.5  # 50%
df_clean = df.loc[:, df.isnull().mean() < threshold]
```

方案 2 - 填充缺失值:
```python
# 使用平均值填充
df['age'].fillna(df['age'].mean(), inplace=True)

# 使用中位數填充（對異常值更穩健）
df['income'].fillna(df['income'].median(), inplace=True)

# 使用眾數填充
df['gender'].fillna(df['gender'].mode()[0], inplace=True)

# 向前填充
df['value'].fillna(method='ffill', inplace=True)

# 使用插值
df['value'].interpolate(method='linear', inplace=True)
```

方案 3 - 使用 scikit-learn 的 Imputer:
```python
from sklearn.impute import SimpleImputer

# 數值型特徵
imputer = SimpleImputer(strategy='mean')
df[['age', 'income']] = imputer.fit_transform(df[['age', 'income']])

# 類別型特徵
imputer = SimpleImputer(strategy='most_frequent')
df[['gender', 'city']] = imputer.fit_transform(df[['gender', 'city']])
```

方案 4 - 使用高級 Imputer:
```python
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

# 使用其他特徵預測缺失值
imputer = IterativeImputer(random_state=42)
df_imputed = pd.DataFrame(
    imputer.fit_transform(df),
    columns=df.columns
)
```

#### 問題 2: 無窮大值

**錯誤信息**:
```
ValueError: Input contains infinity
```

**解決方案**:
```python
# 檢查無窮大值
print("無窮大值:")
print(np.isinf(df.select_dtypes(include=[np.number])).sum())

# 替換無窮大值為 NaN
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# 然後處理 NaN
df.fillna(df.median(), inplace=True)

# 或直接替換為特定值
df.replace([np.inf, -np.inf], 0, inplace=True)
```

---

### 數據類型問題

#### 問題: 數據類型錯誤導致計算失敗

**錯誤信息**:
```
TypeError: unsupported operand type(s) for -: 'str' and 'str'
```

**診斷**:
```python
# 檢查數據類型
print(df.dtypes)

# 檢查特定列的唯一值
print(df['column_name'].unique())

# 檢查是否有混合類型
df.apply(lambda x: [type(i) for i in x.unique()])
```

**解決方案**:
```python
# 轉換為數值類型
df['age'] = pd.to_numeric(df['age'], errors='coerce')

# 轉換為整數
df['count'] = df['count'].astype(int)

# 轉換為浮點數
df['price'] = df['price'].astype(float)

# 轉換為日期
df['date'] = pd.to_datetime(df['date'])

# 轉換為類別
df['category'] = df['category'].astype('category')

# 處理字符串中的數字
df['value'] = df['value'].str.replace(',', '').astype(float)
df['percentage'] = df['percentage'].str.replace('%', '').astype(float) / 100
```

---

### 數據驗證失敗

#### 問題: ValidationError 異常

**錯誤信息**:
```python
ValidationError: RFM分析需要的列缺失: InvoiceDate
可用列: customer_id, date, amount
```

**解決方案**:
```python
# 使用異常處理系統
from data_analysis_chatbots.exceptions import ValidationError, raise_if_columns_missing

# 檢查必需列
required_columns = ['CustomerID', 'InvoiceDate', 'Amount']

try:
    raise_if_columns_missing(df, required_columns, "RFM 分析")
except ValidationError as e:
    print(f"錯誤: {e}")
    print(f"缺失的列: {e.missing_columns}")

    # 映射列名
    column_mapping = {
        'customer_id': 'CustomerID',
        'date': 'InvoiceDate',
        'amount': 'Amount'
    }
    df = df.rename(columns=column_mapping)
    print("已重新映射列名")

# 驗證數據範圍
from data_analysis_chatbots.preprocessing import DataValidator

validator = DataValidator(df)
report = validator.generate_report()
print(report)

if report['warnings']:
    print("警告:")
    for warning in report['warnings']:
        print(f"  - {warning}")
```

---

## 性能問題

### 聚類運行緩慢

#### 問題: K-Means 聚類耗時過長

**診斷**:
```python
import time

# 測量執行時間
start_time = time.time()

clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(df, features)

elapsed_time = time.time() - start_time
print(f"執行時間: {elapsed_time:.2f} 秒")

# 檢查數據大小
print(f"數據行數: {len(df):,}")
print(f"特徵數量: {len(features)}")
print(f"數據形狀: {df[features].shape}")
```

**解決方案**:

方案 1 - 使用 MiniBatch K-Means:
```python
from sklearn.cluster import MiniBatchKMeans

# 使用 MiniBatch 版本，速度更快
clusterer = MiniBatchKMeans(n_clusters=5, batch_size=1000, random_state=42)
labels = clusterer.fit_predict(df[features])
```

方案 2 - 降維:
```python
from sklearn.decomposition import PCA

# 使用 PCA 降維
pca = PCA(n_components=10)  # 保留 10 個主成分
features_reduced = pca.fit_transform(df[features])

# 在降維後的數據上聚類
clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(
    pd.DataFrame(features_reduced),
    list(range(10))
)
```

方案 3 - 採樣:
```python
# 在樣本上訓練模型
df_sample = df.sample(n=10000, random_state=42)
clusterer = KMeansClusterer(n_clusters=5)
clusterer.fit(df_sample, features)

# 預測全部數據
labels = clusterer.predict(df, features)
```

方案 4 - 並行處理:
```python
from sklearn.cluster import KMeans

# 使用多核心
clusterer = KMeans(n_clusters=5, n_jobs=-1)  # -1 表示使用所有核心
labels = clusterer.fit_predict(df[features])
```

方案 5 - 配置優化:
```yaml
# config/config.yaml
performance:
  n_jobs: -1  # 使用所有 CPU 核心
  chunk_size: 5000  # 減小塊大小

analysis:
  clustering:
    max_iter: 100  # 減少最大迭代次數（默認 300）
    tol: 1e-3  # 增加收斂容差（默認 1e-4）
```

---

### 可視化卡頓

#### 問題 1: Matplotlib 繪圖緩慢

**解決方案**:
```python
import matplotlib.pyplot as plt

# 方案 1: 減少數據點
if len(df) > 10000:
    df_plot = df.sample(10000, random_state=42)
else:
    df_plot = df

plt.scatter(df_plot['x'], df_plot['y'])

# 方案 2: 使用 hexbin 代替 scatter（大數據）
plt.hexbin(df['x'], df['y'], gridsize=50, cmap='Blues')

# 方案 3: 使用 rasterization
plt.scatter(df['x'], df['y'], rasterized=True)

# 方案 4: 調整 DPI
plt.figure(dpi=72)  # 降低 DPI（默認 100）
```

#### 問題 2: Seaborn 熱圖緩慢

**解決方案**:
```python
import seaborn as sns

# 減少相關矩陣大小
# 只選擇重要特徵
important_features = ['age', 'income', 'spending', 'frequency']
corr_matrix = df[important_features].corr()

# 使用較小的圖形
plt.figure(figsize=(8, 6))  # 而不是 (12, 10)
sns.heatmap(corr_matrix, annot=True, fmt='.2f')
```

#### 問題 3: Plotly 交互式圖表加載慢

**解決方案**:
```python
import plotly.express as px

# 減少數據點
df_plot = df.sample(min(5000, len(df)), random_state=42)

# 使用 scattergl（WebGL 加速）代替 scatter
fig = px.scatter_gl(df_plot, x='x', y='y', color='cluster')

# 禁用不必要的功能
fig.update_layout(
    hovermode=False,  # 禁用懸停
    dragmode=False    # 禁用拖動
)
```

---

### Streamlit 應用性能

#### 問題: Streamlit 重新運行過於頻繁

**解決方案**:
```python
import streamlit as st

# 使用 @st.cache_data 緩存數據
@st.cache_data
def load_data():
    return pd.read_csv('data/raw/Mall_Customers.csv')

# 使用 @st.cache_resource 緩存模型
@st.cache_resource
def load_model():
    return KMeansClusterer(n_clusters=5)

# 使用 session_state 保存狀態
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# 使用 form 減少重新運行
with st.form("clustering_form"):
    n_clusters = st.slider("聚類數量", 2, 10, 5)
    submitted = st.form_submit_button("運行聚類")

    if submitted:
        # 只在提交時運行
        run_clustering(n_clusters)
```

---

## 聚類相關問題

### K-Means 聚類問題

#### 問題 1: 聚類結果不理想

**診斷**:
```python
from sklearn.metrics import silhouette_score, davies_bouldin_score

# 評估聚類質量
silhouette = silhouette_score(df[features], labels)
davies_bouldin = davies_bouldin_score(df[features], labels)

print(f"輪廓係數: {silhouette:.3f}")  # 越高越好，範圍 [-1, 1]
print(f"Davies-Bouldin 指數: {davies_bouldin:.3f}")  # 越低越好

# 檢查聚類大小
print("聚類大小:")
print(pd.Series(labels).value_counts().sort_index())
```

**解決方案**:

方案 1 - 調整聚類數量:
```python
from sklearn.metrics import silhouette_score

# 嘗試不同的聚類數量
silhouette_scores = []
K_range = range(2, 11)

for k in K_range:
    clusterer = KMeansClusterer(n_clusters=k)
    labels = clusterer.fit_predict(df, features)
    score = silhouette_score(df[features], labels)
    silhouette_scores.append(score)
    print(f"k={k}, 輪廓係數={score:.3f}")

# 選擇最佳 k
best_k = K_range[np.argmax(silhouette_scores)]
print(f"\n最佳聚類數量: {best_k}")
```

方案 2 - 特徵標準化:
```python
from sklearn.preprocessing import StandardScaler

# 標準化特徵
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df[features])

# 在標準化數據上聚類
clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(
    pd.DataFrame(df_scaled, columns=features),
    features
)
```

方案 3 - 嘗試不同的初始化方法:
```python
from sklearn.cluster import KMeans

# 使用 k-means++ 初始化（默認）
kmeans1 = KMeans(n_clusters=5, init='k-means++', n_init=10)

# 或嘗試隨機初始化，增加運行次數
kmeans2 = KMeans(n_clusters=5, init='random', n_init=20)

# 比較結果
score1 = silhouette_score(df[features], kmeans1.fit_predict(df[features]))
score2 = silhouette_score(df[features], kmeans2.fit_predict(df[features]))

print(f"k-means++: {score1:.3f}")
print(f"隨機初始化: {score2:.3f}")
```

#### 問題 2: DBSCAN 找不到聚類（全是噪聲）

**錯誤信息**:
```
警告: DBSCAN 未找到任何聚類，所有點都被標記為噪聲
```

**診斷**:
```python
from data_analysis_chatbots.clustering import DBSCANClusterer

dbscan = DBSCANClusterer(eps=0.5, min_samples=5)
labels = dbscan.fit_predict(df, features)

print(f"發現的聚類數: {dbscan.n_clusters_}")
print(f"噪聲點數: {dbscan.n_noise_}")
print(f"噪聲比例: {dbscan.n_noise_ / len(df) * 100:.1f}%")
```

**解決方案**:

方案 1 - 調整 eps 參數:
```python
# eps 太小會導致所有點都是噪聲
# eps 太大會導致所有點聚成一類

# 使用 k-distance 圖找最佳 eps
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt

# 計算 k-distance
k = 5  # min_samples
nbrs = NearestNeighbors(n_neighbors=k).fit(df[features])
distances, indices = nbrs.kneighbors(df[features])

# 排序距離
distances = np.sort(distances[:, k-1], axis=0)

# 繪圖
plt.figure(figsize=(10, 6))
plt.plot(distances)
plt.ylabel(f'{k}-th Nearest Neighbor Distance')
plt.xlabel('Points sorted by distance')
plt.title('K-distance Graph')
plt.grid(True)
plt.show()

# 從圖中找到"肘部"，作為 eps 值
# 例如，如果肘部在 y=0.3，則使用 eps=0.3
dbscan = DBSCANClusterer(eps=0.3, min_samples=5)
```

方案 2 - 調整 min_samples:
```python
# min_samples 越大，聚類越嚴格
# 一般建議: min_samples = 2 * 特徵數量

n_features = len(features)
min_samples = 2 * n_features

dbscan = DBSCANClusterer(eps=0.5, min_samples=min_samples)
```

方案 3 - 特徵縮放:
```python
from sklearn.preprocessing import StandardScaler

# DBSCAN 對特徵尺度敏感
scaler = StandardScaler()
df_scaled = scaler.fit_transform(df[features])

dbscan = DBSCANClusterer(eps=0.5, min_samples=5)
labels = dbscan.fit_predict(
    pd.DataFrame(df_scaled, columns=features),
    features
)
```

---

### RFM 分析問題

#### 問題: RFM 分析缺少必要列

**錯誤信息**:
```python
RFMAnalysisError: RFM分析需要的列缺失: InvoiceDate
```

**解決方案**:
```python
from data_analysis_chatbots.clustering import RFMAnalyzer
from data_analysis_chatbots.exceptions import RFMAnalysisError

# 檢查數據列
print("數據列:", df.columns.tolist())

# 映射列名
column_mapping = {
    'customer_id': 'CustomerID',
    'order_date': 'InvoiceDate',
    'total_amount': 'Amount'
}
df_mapped = df.rename(columns=column_mapping)

# 確保日期格式正確
df_mapped['InvoiceDate'] = pd.to_datetime(df_mapped['InvoiceDate'])

# 執行 RFM 分析
try:
    rfm = RFMAnalyzer(
        df_mapped,
        customer_id_col='CustomerID',
        date_col='InvoiceDate',
        amount_col='Amount'
    )
    rfm_data = rfm.calculate_rfm()
except RFMAnalysisError as e:
    print(f"錯誤: {e}")
    print(f"缺失的列: {e.missing_columns}")
```

---

## Docker 相關問題

### Docker 構建失敗

#### 問題 1: 依賴安裝失敗

**錯誤信息**:
```
ERROR: Could not find a version that satisfies the requirement package-name
```

**解決方案**:
```dockerfile
# 在 Dockerfile 中添加調試信息
RUN pip install --no-cache-dir -r requirements.txt -v

# 或分步安裝
RUN pip install numpy pandas
RUN pip install scikit-learn
RUN pip install streamlit
```

#### 問題 2: 權限錯誤

**錯誤信息**:
```
PermissionError: [Errno 13] Permission denied: '/app/data'
```

**解決方案**:
```dockerfile
# 在 Dockerfile 中確保正確的權限
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /data && \
    chown -R appuser:appuser /app /data

USER appuser
```

```bash
# 或在 docker-compose.yml 中設置
services:
  app:
    user: "1000:1000"
    volumes:
      - ./data:/app/data
```

### Docker 運行問題

#### 問題 1: 容器立即退出

**診斷**:
```bash
# 查看容器日誌
docker logs dac-app

# 查看退出代碼
docker inspect dac-app --format='{{.State.ExitCode}}'

# 運行容器並保持運行
docker run -it --entrypoint /bin/bash data-analysis-chatbots:latest
```

**解決方案**:
```bash
# 檢查 CMD 或 ENTRYPOINT
docker inspect data-analysis-chatbots:latest | grep -A 5 Cmd

# 測試命令
docker run -it data-analysis-chatbots:latest streamlit run app.py --server.port=8501
```

#### 問題 2: 無法連接到容器

**診斷**:
```bash
# 檢查端口映射
docker port dac-app

# 檢查網絡
docker network inspect dac-network

# 測試連接
curl http://localhost:8501/healthz
```

**解決方案**:
```bash
# 確保端口映射正確
docker run -p 8501:8501 data-analysis-chatbots:latest

# 檢查防火牆
sudo ufw status
sudo ufw allow 8501/tcp
```

---

## Streamlit 相關問題

### Streamlit 啟動失敗

#### 問題: 端口已被佔用

**錯誤信息**:
```
OSError: [Errno 48] Address already in use
```

**解決方案**:
```bash
# 查找佔用端口的進程
lsof -i :8501
# 或
netstat -tuln | grep 8501

# 終止進程
kill -9 <PID>

# 或使用不同端口
streamlit run app.py --server.port=8502
```

### Streamlit 緩存問題

#### 問題: 緩存數據過時

**解決方案**:
```python
import streamlit as st

# 清除特定函數的緩存
load_data.clear()

# 或在 UI 中添加清除緩存按鈕
if st.button("清除緩存"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# 添加 TTL (生存時間)
@st.cache_data(ttl=3600)  # 1 小時後過期
def load_data():
    return pd.read_csv('data.csv')
```

---

## 調試技巧

### 1. 啟用詳細日誌

```python
import logging
from loguru import logger

# 設置日誌級別為 DEBUG
logger.remove()
logger.add("logs/debug.log", level="DEBUG", rotation="10 MB")

# 在代碼中添加調試日誌
logger.debug(f"DataFrame 形狀: {df.shape}")
logger.debug(f"特徵列表: {features}")
logger.debug(f"缺失值: {df.isnull().sum().sum()}")
```

### 2. 使用 Python 調試器

```python
# 在代碼中設置斷點
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()

# 常用調試命令:
# n - 下一行
# s - 進入函數
# c - 繼續執行
# p variable - 打印變量
# l - 列出代碼
# q - 退出
```

### 3. 使用 print() 調試

```python
# 添加詳細的 print 語句
print(f"開始聚類, 數據形狀: {df.shape}")
print(f"特徵: {features}")
print(f"前5行:\n{df[features].head()}")
print(f"統計信息:\n{df[features].describe()}")

# 使用 sys.exit() 臨時停止
import sys
print("檢查點 1")
sys.exit()
```

### 4. 檢查中間結果

```python
# 保存中間結果到文件
df_intermediate.to_csv('debug_output.csv', index=False)

# 可視化中間結果
import matplotlib.pyplot as plt
plt.scatter(df['x'], df['y'])
plt.savefig('debug_plot.png')
```

---

## 獲取幫助

### 1. 查看文檔

- **README**: [README.md](README.md) - 專案概述
- **FAQ**: [FAQ.md](FAQ.md) - 常見問題
- **架構**: [ARCHITECTURE.md](ARCHITECTURE.md) - 系統架構
- **部署**: [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南

### 2. 查看示例代碼

```bash
# 運行示例
python examples/complete_analysis_workflow.py
python examples/kmeans_clustering.py

# 查看 Jupyter Notebooks
jupyter notebook notebooks/
```

### 3. 運行測試

```bash
# 運行所有測試
pytest -v

# 運行特定測試
pytest tests/unit/test_clustering.py -v

# 查看測試覆蓋率
pytest --cov=src/data_analysis_chatbots --cov-report=html
```

### 4. 提交 Issue

如果問題仍未解決，請在 GitHub 上提交 Issue:

https://github.com/markl-a/Data-Analysis-with-Chatbots/issues

包含以下信息:
- 問題描述
- 錯誤信息（完整的 traceback）
- 系統信息（OS、Python 版本）
- 復現步驟
- 預期行為 vs 實際行為

### 5. 社區支持

- **GitHub Discussions**: 提問和討論
- **Stack Overflow**: 使用標籤 `data-analysis-chatbots`

---

## 快速診斷檢查表

遇到問題時，按以下順序檢查：

- [ ] **環境激活**: 虛擬環境是否激活？
  ```bash
  which python
  ```

- [ ] **包安裝**: 包是否正確安裝？
  ```bash
  pip list | grep data-analysis-chatbots
  ```

- [ ] **Python 版本**: 版本是否 >= 3.8？
  ```bash
  python --version
  ```

- [ ] **目錄結構**: 是否已初始化？
  ```bash
  python -m data_analysis_chatbots.init --validate
  ```

- [ ] **數據存在**: 數據文件是否存在？
  ```bash
  ls -la data/raw/
  ```

- [ ] **配置文件**: 配置是否正確？
  ```bash
  cat config/config.yaml
  ```

- [ ] **日誌檢查**: 查看錯誤日誌
  ```bash
  tail -f logs/app.log
  ```

- [ ] **測試運行**: 基本功能是否正常？
  ```bash
  pytest tests/unit/ -v
  ```

---

## 常見錯誤速查表

| 錯誤類型 | 常見原因 | 快速解決 |
|---------|---------|---------|
| `ModuleNotFoundError` | 包未安裝 | `pip install -e .` |
| `FileNotFoundError` | 數據未下載 | `python -m data_analysis_chatbots.data_downloader --sample` |
| `MemoryError` | 數據太大 | 使用 `chunksize` 或採樣 |
| `ValueError: NaN` | 缺失值 | `df.fillna(df.mean())` |
| `KeyError` | 列名錯誤 | 檢查 `df.columns` |
| `PermissionError` | 權限不足 | `chmod 755` 或以正確用戶運行 |
| `UnicodeDecodeError` | 編碼問題 | 嘗試 `encoding='latin-1'` |
| `ImportError` | 循環導入 | 清除 `__pycache__` |

---

**最後更新**: 2025-12-21
**版本**: 1.0.0

**反饋**: 如果本指南對你有幫助，或你發現需要補充的內容，請在 GitHub 上提交 Issue 或 PR！
