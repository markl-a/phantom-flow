# 📦 安裝指南

本文檔提供詳細的安裝步驟和常見問題解決方案。

## 系統要求

### 最低要求
- **操作系統**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 或更高版本
- **內存**: 最少 4GB RAM
- **硬盤空間**: 最少 2GB 可用空間

### 推薦配置
- **Python**: 3.10 或 3.11
- **內存**: 8GB+ RAM
- **處理器**: 多核處理器
- **硬盤空間**: 5GB+ 可用空間(包含數據集)

## 安裝步驟

### 步驟 1: 檢查 Python 版本

```bash
python --version
# 或
python3 --version
```

應該顯示 Python 3.8 或更高版本。如果沒有安裝,請訪問 [python.org](https://www.python.org/downloads/) 下載。

### 步驟 2: 克隆專案

```bash
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots
```

### 步驟 3: 創建虛擬環境

強烈建議使用虛擬環境來隔離專案依賴:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

激活後,命令提示符前會顯示 `(venv)`。

### 步驟 4: 升級 pip

```bash
python -m pip install --upgrade pip
```

### 步驟 5: 安裝依賴

```bash
pip install -r requirements.txt
```

這將安裝所有必需的包,包括:
- numpy, pandas (數據處理)
- scikit-learn (機器學習)
- matplotlib, seaborn (可視化)
- nltk (自然語言處理)
- streamlit (儀表板)
- 以及其他依賴

### 步驟 6: 安裝專案包

以開發模式安裝專案:

```bash
pip install -e .
```

`-e` 選項表示"editable"模式,允許你修改源代碼而無需重新安裝。

### 步驟 7: 驗證安裝

```python
python -c "from data_analysis_chatbots import DataLoader; print('安裝成功!')"
```

如果看到"安裝成功!",表示安裝完成。

## 下載數據集

### 選項 1: 使用 Kaggle API (推薦)

1. **獲取 Kaggle API 憑證**
   - 訪問 https://www.kaggle.com/account
   - 滾動到 "API" 部分
   - 點擊 "Create New API Token"
   - 下載 `kaggle.json` 文件

2. **配置 Kaggle API**

   **Windows:**
   ```bash
   mkdir %USERPROFILE%\.kaggle
   copy kaggle.json %USERPROFILE%\.kaggle\
   ```

   **macOS/Linux:**
   ```bash
   mkdir -p ~/.kaggle
   cp kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

3. **下載數據集**
   ```bash
   # 下載所有數據集
   python -m data_analysis_chatbots.data_downloader --all

   # 或下載特定數據集
   python -m data_analysis_chatbots.data_downloader --dataset mall_customers
   ```

### 選項 2: 使用範例數據

如果不想下載真實數據集,可以生成範例數據用於測試:

```bash
python -m data_analysis_chatbots.data_downloader --sample
```

### 選項 3: 手動下載

直接從 Kaggle 下載並放置到 `data/raw/` 目錄:

1. [NLP Disaster Tweets](https://www.kaggle.com/datasets/vbmokin/nlp-with-disaster-tweets-cleaning-data)
2. [E-Commerce Data](https://www.kaggle.com/datasets/carrie1/ecommerce-data)
3. [Mall Customer Segmentation](https://www.kaggle.com/datasets/vjchoudhary7/customer-segmentation-tutorial-in-python)
4. [Customer Personality Analysis](https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis)
5. [Marketing Segmentation](https://www.kaggle.com/datasets/fahmidachowdhury/customer-segmentation-data-for-marketing-analysis)

## 可選組件

### Jupyter Notebook (互動式分析)

```bash
pip install jupyter
```

啟動 Jupyter:
```bash
jupyter notebook
```

### Streamlit (互動式儀表板)

已包含在 requirements.txt 中,如需單獨安裝:

```bash
pip install streamlit
```

### 開發工具 (代碼格式化和測試)

```bash
pip install -e ".[dev]"
```

這將安裝:
- pytest (測試框架)
- black (代碼格式化)
- flake8 (代碼檢查)
- isort (導入排序)

## 常見問題

### Q1: 安裝依賴時出現權限錯誤

**問題**: `PermissionError` 或 `Access denied`

**解決方案**:
```bash
# 使用 --user 選項
pip install --user -r requirements.txt

# 或使用虛擬環境(推薦)
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Q2: 找不到 Python 3.8+

**問題**: 系統只有 Python 2.7 或更舊版本

**解決方案**:
- Windows: 從 [python.org](https://www.python.org/) 下載最新版本
- macOS: 使用 Homebrew `brew install python@3.11`
- Ubuntu/Debian: `sudo apt update && sudo apt install python3.11`

### Q3: NumPy/Pandas 安裝失敗

**問題**: 編譯錯誤或找不到編譯器

**解決方案**:

**Windows**:
```bash
# 使用預編譯的 wheel 文件
pip install --only-binary :all: numpy pandas
```

**macOS**:
```bash
# 安裝 Xcode Command Line Tools
xcode-select --install
```

**Linux**:
```bash
# 安裝開發工具
sudo apt install python3-dev build-essential
```

### Q4: NLTK 數據下載失敗

**問題**: NLTK stopwords 或其他數據包找不到

**解決方案**:
```python
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
```

### Q5: Kaggle API 403 錯誤

**問題**: `403 Forbidden` 錯誤

**解決方案**:
1. 確認 `kaggle.json` 在正確位置 (`~/.kaggle/`)
2. 檢查文件權限: `chmod 600 ~/.kaggle/kaggle.json`
3. 確認在 Kaggle 網站上接受了競賽規則

### Q6: 內存不足錯誤

**問題**: `MemoryError` 在處理大數據集時

**解決方案**:
```python
# 使用分塊讀取
import pandas as pd
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process(chunk)

# 或減少數據精度
df = pd.read_csv('file.csv', dtype={'float_column': 'float32'})
```

### Q7: Matplotlib 圖表不顯示

**問題**: 調用 `plt.show()` 後沒有圖表顯示

**解決方案**:

**Jupyter Notebook**:
```python
%matplotlib inline
```

**普通 Python 腳本**:
```python
import matplotlib.pyplot as plt
plt.ion()  # 開啟互動模式
```

## 驗證安裝

運行以下測試確保一切正常:

```python
# test_installation.py
from data_analysis_chatbots import (
    ConfigLoader,
    DataLoader,
    DataValidator,
    KMeansClusterer,
    RFMAnalyzer,
    CLVPredictor,
    CampaignManager,
    Plotter
)

print("✓ 所有模塊導入成功!")

# 測試配置加載
config = ConfigLoader()
print(f"✓ 配置加載成功: {config.get('project.name')}")

# 測試數據加載器
loader = DataLoader()
print(f"✓ 數據加載器初始化成功")

print("\n🎉 安裝驗證完成!")
```

運行測試:
```bash
python test_installation.py
```

## 更新專案

保持專案最新:

```bash
# 更新代碼
git pull origin main

# 更新依賴
pip install --upgrade -r requirements.txt

# 重新安裝專案
pip install -e .
```

## 卸載

完全移除專案:

```bash
# 停用虛擬環境
deactivate

# 刪除虛擬環境
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# 刪除專案目錄
cd ..
rm -rf Data-Analysis-with-Chatbots  # macOS/Linux
rmdir /s Data-Analysis-with-Chatbots  # Windows
```

## 需要幫助?

- 查看 [README.md](README.md) 獲取使用指南
- 查看 [docs/](docs/) 獲取詳細文檔
- 在 [GitHub Issues](https://github.com/markl-a/Data-Analysis-with-Chatbots/issues) 報告問題

---

**祝你使用愉快!** 🚀
