# 性能優化快速參考

## 快速導航

### 1. 數據庫批量插入 (50倍加速)
```python
from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

db = DatabaseAutomationTool()
records = [{"name": "User1", "age": 25}, ...]
result = db.batch_insert("users", records, batch_size=1000)
```

### 2. 多代理並行執行 (60-70%時間節省)
```python
from ai_automation_framework.agents.multi_agent import MultiAgentSystem

system = MultiAgentSystem()
tasks = {"task1": "任務描述1", "task2": "任務描述2"}
agent_mapping = {"task1": "agent1", "task2": "agent2"}
results = await system.parallel_execution(tasks, agent_mapping)
```

### 3. VectorStore 初始化優化 (自動優化)
```python
from ai_automation_framework.rag.vector_store import VectorStore

# 創建後自動使用 _initialized 標誌
store = VectorStore()
store.add_documents(docs, embeddings)  # 第一次會初始化
store.search(query)  # 不會重複初始化
```

### 4. 緩存批量操作 (80-90%鎖競爭減少)
```python
from ai_automation_framework.core.cache import LRUCache

cache = LRUCache()

# 批量設置
items = {"key1": "value1", "key2": "value2"}
cache.batch_set(items, ttl=300)

# 批量獲取
results = cache.batch_get(["key1", "key2"])
```

## 性能對比

| 優化項目 | 優化前 | 優化後 | 提升幅度 |
|---------|--------|--------|----------|
| 批量插入1000條記錄 | ~50秒 | ~1秒 | 50倍 |
| 3個並行任務執行 | 7.5秒 | 3秒 | 60% |
| 重複初始化調用 | 每次初始化 | 僅首次 | 顯著 |
| 批量緩存操作100項 | 100次鎖 | 1次鎖 | 90% |

## 何時使用

- ✅ **batch_insert**: 插入 >100 條記錄
- ✅ **parallel_execution**: 3+ 個獨立任務
- ✅ **VectorStore**: 頻繁調用向量操作
- ✅ **batch_get/set**: 需要操作多個緩存項

## 詳細文檔

- 完整報告: `PERFORMANCE_OPTIMIZATIONS.md`
- 示例代碼: `examples/performance_optimization_demo.py`
