# 📖 快速開始指南

## 5分鐘快速體驗

### 方式1: 使用範例腳本

```bash
# 執行完整分析工作流程
python examples/complete_analysis_workflow.py
```

這個腳本會自動：
- 生成範例數據
- 執行K-means聚類
- 進行RFM分析
- 預測CLV
- 創建營銷活動
- 保存所有結果到 `data/outputs/`

### 方式2: 使用Streamlit儀表板

```bash
# 啟動互動式儀表板
streamlit run app.py
```

在瀏覽器中打開 http://localhost:8501，即可使用互動式界面！

### 方式3: 使用Jupyter Notebook

```bash
# 啟動Jupyter
jupyter notebook

# 打開任一notebook:
# - notebooks/01_mall_customer_clustering.ipynb
# - notebooks/02_rfm_clv_analysis.ipynb
```

### 方式4: 使用Python代碼

```python
from data_analysis_chatbots import DataLoader, KMeansClusterer

# 載入數據（會自動生成範例數據）
loader = DataLoader()
try:
    df = loader.load_mall_customers()
except:
    # 生成範例數據
    import pandas as pd, numpy as np
    np.random.seed(42)
    df = pd.DataFrame({
        'Age': np.random.randint(18, 70, 200),
        'Annual Income (k$)': np.random.randint(15, 140, 200),
        'Spending Score (1-100)': np.random.randint(1, 100, 200)
    })

# 執行聚類
clusterer = KMeansClusterer(n_clusters=5)
labels = clusterer.fit_predict(df, df.columns.tolist())

print(f"✓ 完成聚類！分成 {len(set(labels))} 個群組")
```

## 完整功能展示

### RFM分析 + CLV預測
```python
from data_analysis_chatbots.clustering import RFMAnalyzer
from data_analysis_chatbots.marketing import CLVPredictor

# RFM分析
rfm = RFMAnalyzer(df, 'CustomerID', 'Date', 'Amount')
segments = rfm.segment_customers()

# CLV預測
clv = CLVPredictor(discount_rate=0.1)
predictions = clv.calculate_rfm_based_clv(segments)

print(f"平均CLV: ${predictions['Predicted_CLV'].mean():.2f}")
```

### 營銷活動設計
```python
from data_analysis_chatbots.marketing import CampaignManager

mgr = CampaignManager(df, 'CustomerID')
vip = mgr.create_campaign('VIP優惠', {'Income': {'min': 80}})
roi = mgr.calculate_campaign_roi('VIP優惠', 50, 0.2, 500)

print(f"預期ROI: {roi['roi_percentage']:.1f}%")
```

## 常見問題

**Q: 如何下載真實數據集？**
```bash
python -m data_analysis_chatbots.data_downloader --sample
```

**Q: 如何運行測試？**
```bash
pytest tests/
```

**Q: 如何查看所有CLI命令？**
```bash
python -m data_analysis_chatbots.cli --help
```

---
更多詳情請查看 [README.md](README.md) 和 [INSTALLATION.md](INSTALLATION.md)
