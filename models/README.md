# 模型目錄

此目錄用於存儲訓練好的機器學習模型。

## 文件格式

- `.pkl` - Scikit-learn模型(使用joblib保存)
- `.h5` - Keras/TensorFlow模型
- `.pt` - PyTorch模型

## 命名規範

推薦使用以下命名格式:
```
{model_type}_{dataset}_{date}.pkl

例如:
kmeans_mall_customers_20250118.pkl
rfm_analyzer_ecommerce_20250118.pkl
```

## 加載模型

```python
from joblib import load

model = load('models/kmeans_mall_customers_20250118.pkl')
predictions = model.predict(new_data)
```
