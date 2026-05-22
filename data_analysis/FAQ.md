# 常見問題解答 (FAQ)

## 📌 目錄

- [安裝問題](#安裝問題)
- [使用問題](#使用問題)
- [聚類算法選擇](#聚類算法選擇)
- [性能優化](#性能優化)
- [錯誤處理](#錯誤處理)
- [數據處理](#數據處理)
- [AI輔助](#ai輔助)
- [進階主題](#進階主題)

---

## 安裝問題

### Q1: 安裝時出現依賴錯誤怎麼辦?

**A:** 首先確保使用Python 3.8+版本:

```bash
python --version  # 應該是3.8或更高
```

推薦使用虛擬環境:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### Q2: 為什麼運行時提示找不到數據目錄?

**A:** 在首次使用前需要初始化專案結構:

```bash
python -m data_analysis_chatbots.init --with-examples
```

這會創建所有必要的目錄(data/, models/, logs/等)。

### Q3: Kaggle數據集下載失敗怎麼辦?

**A:** 有幾種解決方案:

1. **配置Kaggle API**(推薦):
```bash
# 從 https://www.kaggle.com/account 下載 kaggle.json
mkdir -p ~/.kaggle
mv kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

2. **手動下載**: 從Kaggle網站下載後放到`data/raw/`目錄

3. **使用示例數據**:
```bash
python -m data_analysis_chatbots.data_downloader --sample
```

---

## 使用問題

### Q4: 如何選擇合適的聚類算法?

**A:** 根據數據特徵和需求選擇:

| 場景 | 推薦算法 | 原因 |
|------|---------|------|
| 數據呈球形分佈 | K-Means | 快速、簡單、效果好 |
| 數據有任意形狀 | DBSCAN | 能發現非球形聚類 |
| 需要概率性結果 | GMM | 提供軟聚類概率 |
| 需要可視化層次結構 | Hierarchical | 樹狀圖直觀 |
| 不知道聚類數量 | DBSCAN或Hierarchical | 不需預設K值 |
| 有很多異常點 | DBSCAN | 自動檢測噪聲 |
| 數據量很大(>10萬) | K-Means或Mini-Batch K-Means | 速度快 |
| 數據量較小(<1萬) | Hierarchical或GMM | 精度高 |

**示例**:
```python
from data_analysis_chatbots.clustering import *

# 場景1: 客戶分群(球形,已知3-5類)
clusterer = KMeansClusterer(n_clusters=4)

# 場景2: 異常檢測(任意形狀)
clusterer = DBSCANClusterer(eps=0.5, min_samples=10)

# 場景3: 軟分群(需要概率)
clusterer = GMMClusterer(n_components=3)

# 場景4: 探索性分析(不知道K值)
clusterer = HierarchicalClusterer()
optimal_k, _ = clusterer.find_optimal_clusters(df, features, max_clusters=10)
clusterer = HierarchicalClusterer(n_clusters=optimal_k)
```

### Q5: 如何解釋聚類結果給業務團隊?

**A:** 使用`get_cluster_summary()`生成易懂的摘要:

```python
# 1. 獲取統計摘要
summary = clusterer.get_cluster_summary(df, features)
print(summary)

# 2. 為每個聚類命名
cluster_names = {
    0: "高價值客戶",
    1: "潛在客戶",
    2: "流失風險客戶"
}

# 3. 添加業務解釋
df['Cluster_Name'] = df['Cluster'].map(cluster_names)

# 4. 可視化
from data_analysis_chatbots.visualization import Plotter
plotter = Plotter()
plotter.plot_clusters(df, 'Income', 'Spending', 'Cluster')
```

### Q6: 如何處理混合數據類型(數值+類別)?

**A:** 需要先進行特徵工程:

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

# 1. 分離數值和類別特徵
numeric_features = ['Age', 'Income', 'Spending']
categorical_features = ['Gender', 'Category']

# 2. 編碼類別特徵
df_encoded = df.copy()
for col in categorical_features:
    le = LabelEncoder()
    df_encoded[col + '_encoded'] = le.fit_transform(df[col])

# 3. 標準化所有特徵
all_features = numeric_features + [c + '_encoded' for c in categorical_features]
clusterer = KMeansClusterer(n_clusters=3, normalize=True)
labels = clusterer.fit_predict(df_encoded, all_features)
```

或使用Gower距離(需要額外庫):
```bash
pip install gower
```

---

## 聚類算法選擇

### Q7: K-Means和GMM有什麼區別?

**A:** 主要區別:

| 特性 | K-Means | GMM |
|------|---------|-----|
| 聚類類型 | 硬聚類(每點屬於一個類) | 軟聚類(提供概率) |
| 聚類形狀 | 球形 | 橢圓形 |
| 輸出 | 類別標籤 | 概率 + 標籤 |
| 速度 | 快 | 較慢 |
| 不確定性 | 無 | 有 |

**使用建議**:
- 需要確定性分類 → K-Means
- 需要概率性分類 → GMM
- 數據有橢圓形分佈 → GMM
- 數據量大 → K-Means

### Q8: DBSCAN的eps和min_samples如何設置?

**A:** 推薦方法:

```python
# 方法1: 使用內置工具自動推薦
clusterer = DBSCANClusterer(min_samples=5)
recommended_eps, k_distances = clusterer.find_optimal_eps(
    df,
    features,
    k=5  # 通常設為min_samples
)
print(f"推薦eps: {recommended_eps}")

# 方法2: 繪製K距離圖手動選擇
import matplotlib.pyplot as plt
plt.plot(k_distances)
plt.xlabel('點索引')
plt.ylabel('K距離')
plt.title('K距離圖 - 肘部為最優eps')
plt.show()

# 方法3: 經驗規則
# min_samples = 數據維度 + 1
# 對於2D數據: min_samples = 3-5
# 對於高維數據: min_samples = 2 * 維度
```

### Q9: 聚類數量K值如何確定?

**A:** 多種方法:

```python
from data_analysis_chatbots.clustering import KMeansClusterer, GMMClusterer

# 方法1: 肘部法(K-Means)
clusterer = KMeansClusterer()
optimal_k, wcss = clusterer.find_optimal_k(df, features, max_k=10)

# 方法2: 輪廓係數(最大值)
from sklearn.metrics import silhouette_score
scores = []
for k in range(2, 11):
    kmeans = KMeansClusterer(n_clusters=k)
    labels = kmeans.fit_predict(df, features)
    score = silhouette_score(df[features], labels)
    scores.append(score)
optimal_k = scores.index(max(scores)) + 2

# 方法3: BIC/AIC(GMM)
gmm = GMMClusterer()
optimal_k, bics = gmm.find_optimal_components(df, features, max_components=10)

# 方法4: 業務知識
# 例如: 客戶分群通常3-7類比較合適
```

---

## 性能優化

### Q10: 處理大數據集(>100萬行)時很慢怎麼辦?

**A:** 幾種優化策略:

```python
# 1. 使用Mini-Batch K-Means(內存友好)
from sklearn.cluster import MiniBatchKMeans
model = MiniBatchKMeans(n_clusters=5, batch_size=1000)

# 2. 數據採樣
sample_size = 10000
df_sample = df.sample(n=sample_size, random_state=42)
clusterer.fit(df_sample, features)
# 然後預測全部數據
labels = clusterer.predict(df, features)

# 3. 特徵選擇(減少維度)
from sklearn.decomposition import PCA
pca = PCA(n_components=10)  # 降到10維
df_reduced = pca.fit_transform(df[features])

# 4. 並行處理(需要Dask)
import dask.dataframe as dd
ddf = dd.from_pandas(df, npartitions=4)
```

### Q11: 如何加速模型訓練?

**A:** 調整參數和使用緩存:

```python
# 1. K-Means: 減少max_iter和n_init
clusterer = KMeansClusterer(
    n_clusters=5,
    max_iter=100,  # 默認300
    n_init=5       # 默認10
)

# 2. GMM: 減少迭代次數
gmm = GMMClusterer(
    n_components=3,
    max_iter=50,   # 默認100
    covariance_type='diag'  # 比'full'快
)

# 3. 保存訓練好的模型
from joblib import dump, load
dump(clusterer.model, 'models/kmeans_model.pkl')
# 之後直接加載
clusterer.model = load('models/kmeans_model.pkl')

# 4. 使用GPU(需要CUDA和cuML)
# pip install cuml
from cuml.cluster import KMeans as cuKMeans
```

---

## 錯誤處理

### Q12: 出現"ValidationError: 特徵數據包含NaN值"怎麼辦?

**A:** 先處理缺失值:

```python
from data_analysis_chatbots.preprocessing import DataValidator

# 1. 檢查缺失值
validator = DataValidator(df)
validator.print_report()

# 2. 處理策略
# 方法A: 刪除含缺失值的行
df_clean = df.dropna(subset=features)

# 方法B: 填充缺失值
df_clean = df.copy()
for col in numeric_features:
    df_clean[col].fillna(df_clean[col].median(), inplace=True)

# 方法C: 使用插值
df_clean = df.interpolate(method='linear')

# 方法D: 使用KNN填充
from sklearn.impute import KNNImputer
imputer = KNNImputer(n_neighbors=5)
df_clean[features] = imputer.fit_transform(df[features])
```

### Q13: 聚類結果全部是同一類怎麼辦?

**A:** 幾個可能原因:

```python
# 原因1: 數據未標準化
# 解決: 確保normalize=True
clusterer = KMeansClusterer(n_clusters=3, normalize=True)

# 原因2: 特徵尺度差異太大
# 解決: 手動標準化
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df[features] = scaler.fit_transform(df[features])

# 原因3: K值設置不當
# 解決: 使用自動K值選擇
optimal_k, _ = clusterer.find_optimal_k(df, features)

# 原因4: 數據本身沒有明顯聚類結構
# 解決: 檢查數據分佈
import seaborn as sns
sns.pairplot(df[features])
```

---

## 數據處理

### Q14: 如何處理類別不平衡(某些聚類太小)?

**A:** 幾種策略:

```python
# 1. 調整聚類數量
# 減少K值可能會合併小聚類

# 2. 使用不同的聚類算法
# DBSCAN會自動將小聚類標記為噪聲
clusterer = DBSCANClusterer(eps=0.5, min_samples=10)

# 3. 重採樣
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X, labels)

# 4. 分層聚類
# 先對大類進行聚類,再對小類單獨處理
```

### Q15: 如何驗證聚類結果的穩定性?

**A:** 使用交叉驗證:

```python
from sklearn.model_selection import KFold
import numpy as np

def cross_validate_clustering(df, features, n_clusters=3, n_splits=5):
    """交叉驗證聚類穩定性"""
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    silhouette_scores = []

    for train_idx, test_idx in kfold.split(df):
        df_train = df.iloc[train_idx]
        df_test = df.iloc[test_idx]

        clusterer = KMeansClusterer(n_clusters=n_clusters)
        clusterer.fit(df_train, features)
        test_labels = clusterer.predict(df_test, features)

        from sklearn.metrics import silhouette_score
        score = silhouette_score(df_test[features], test_labels)
        silhouette_scores.append(score)

    print(f"平均輪廓係數: {np.mean(silhouette_scores):.3f} ± {np.std(silhouette_scores):.3f}")
    return silhouette_scores

scores = cross_validate_clustering(df, features)
```

---

## AI輔助

### Q16: 如何使用AI(ChatGPT/Claude)幫助分析聚類結果?

**A:** 參考[AI_ASSISTANCE_GUIDE.md](AI_ASSISTANCE_GUIDE.md),以下是快速示例:

```python
# 1. 導出聚類摘要
summary = clusterer.get_cluster_summary(df, features)
summary.to_csv('cluster_summary.csv')

# 2. 準備提示詞給AI
prompt = f"""
我對客戶數據進行了K-means聚類,得到以下4個聚類:

{summary.to_string()}

請幫我:
1. 為每個聚類命名
2. 提供業務解釋
3. 建議針對性營銷策略
"""

# 複製到ChatGPT/Claude並獲取建議
```

### Q17: AI生成的代碼有錯誤怎麼辦?

**A:** 遵循這些原則:

1. **驗證建議**: 總是在測試數據上先運行
2. **查看文檔**: 對照本專案的API文檔
3. **使用專案異常**: 利用自定義異常獲取清晰錯誤信息
4. **漸進式開發**: 一次測試一小段代碼

```python
# 好的實踐
try:
    # AI生成的代碼
    clusterer = KMeansClusterer(n_clusters=5)
    labels = clusterer.fit_predict(df, features)
except Exception as e:
    print(f"錯誤類型: {type(e).__name__}")
    print(f"錯誤信息: {str(e)}")
    # 調整代碼後重試
```

---

## 進階主題

### Q18: 如何實現自定義聚類算法?

**A:** 繼承基類並實現必要方法:

```python
from data_analysis_chatbots.clustering import KMeansClusterer
from sklearn.cluster import SpectralClustering

class SpectralClusterer(KMeansClusterer):
    """譜聚類實現"""

    def __init__(self, n_clusters=3, **kwargs):
        super().__init__(n_clusters=n_clusters)
        self.model = SpectralClustering(
            n_clusters=n_clusters,
            **kwargs
        )

    def fit(self, df, feature_columns):
        # 自定義實現
        X = df[feature_columns].values
        self.labels_ = self.model.fit_predict(X)
        return self

# 使用
clusterer = SpectralClusterer(n_clusters=3)
labels = clusterer.fit_predict(df, features)
```

### Q19: 如何部署聚類模型到生產環境?

**A:** 幾種方式:

```python
# 方式1: 保存模型文件
from joblib import dump, load

# 訓練和保存
clusterer = KMeansClusterer(n_clusters=5)
clusterer.fit(df, features)
dump(clusterer, 'models/production_model.pkl')

# 生產環境加載
clusterer = load('models/production_model.pkl')
new_labels = clusterer.predict(new_df, features)

# 方式2: REST API(參考API文檔)
# 方式3: Streamlit Web App(已包含在專案中)
streamlit run app.py

# 方式4: Docker容器
docker build -t data-analysis-chatbots .
docker run -p 8501:8501 data-analysis-chatbots
```

### Q20: 如何監控模型性能退化?

**A:** 建立監控系統:

```python
import numpy as np
from datetime import datetime

class ClusteringMonitor:
    """聚類模型監控器"""

    def __init__(self, baseline_metrics):
        self.baseline = baseline_metrics
        self.history = []

    def check_performance(self, clusterer, df, features):
        """檢查當前性能"""
        metrics = clusterer.evaluate_clustering(df, features)

        # 與基線比較
        silhouette_drop = self.baseline['silhouette_score'] - metrics['silhouette_score']

        alert = {
            'timestamp': datetime.now(),
            'metrics': metrics,
            'silhouette_drop': silhouette_drop,
            'needs_retrain': silhouette_drop > 0.1  # 閾值
        }

        self.history.append(alert)

        if alert['needs_retrain']:
            print("⚠️  模型性能下降,建議重新訓練!")

        return alert

# 使用
baseline = clusterer.evaluate_clustering(df_train, features)
monitor = ClusteringMonitor(baseline)

# 定期檢查
alert = monitor.check_performance(clusterer, df_new, features)
```

---

## 更多幫助

- 📖 **完整教程**: [TUTORIAL.md](TUTORIAL.md)
- 🤖 **AI輔助指南**: [AI_ASSISTANCE_GUIDE.md](AI_ASSISTANCE_GUIDE.md)
- 📊 **案例研究**: [CASE_STUDIES.md](CASE_STUDIES.md)
- 🏆 **Kaggle競賽**: [KAGGLE_COMPETITIONS_SUGGESTIONS.md](KAGGLE_COMPETITIONS_SUGGESTIONS.md)
- 💬 **問題反饋**: [GitHub Issues](https://github.com/markl-a/Data-Analysis-with-Chatbots/issues)

---

**最後更新**: 2025年1月18日
