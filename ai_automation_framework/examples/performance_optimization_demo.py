"""
性能優化示例演示

展示所有四項性能優化的使用方法。
"""

import asyncio
import time
from typing import Dict, Any

# 示例 1: 數據庫批量插入優化
def demo_batch_insert():
    """演示批量插入的性能優勢"""
    print("\n" + "="*60)
    print("示例 1: 數據庫批量插入優化")
    print("="*60)

    from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

    # 創建數據庫工具
    db = DatabaseAutomationTool(":memory:")
    db.connect()

    # 創建測試表
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT NOT NULL",
        "age": "INTEGER",
        "email": "TEXT"
    })

    # 生成測試數據
    test_records = [
        {
            "name": f"User{i}",
            "age": 20 + (i % 50),
            "email": f"user{i}@example.com"
        }
        for i in range(1000)
    ]

    print(f"\n準備插入 {len(test_records)} 條記錄...")

    # 批量插入
    start = time.time()
    result = db.batch_insert("users", test_records, batch_size=1000)
    batch_time = time.time() - start

    print(f"\n批量插入結果:")
    print(f"  - 成功: {result['success']}")
    print(f"  - 插入記錄數: {result.get('total_inserted', 0)}")
    print(f"  - 批次數: {result.get('batches', 0)}")
    print(f"  - 耗時: {batch_time:.4f} 秒")
    print(f"  - 速度: {result.get('total_inserted', 0) / batch_time:.0f} 記錄/秒")

    print("\n預期性能提升: 相比逐條插入，速度提升約 50 倍")

    db.close()


# 示例 2: 多代理並行執行優化
async def demo_parallel_execution():
    """演示並行執行的性能優勢"""
    print("\n" + "="*60)
    print("示例 2: 多代理並行執行優化")
    print("="*60)

    from ai_automation_framework.agents.multi_agent import MultiAgentSystem
    from ai_automation_framework.agents.base_agent import BaseAgent
    from ai_automation_framework.llm.factory import LLMFactory

    # 注意: 這是一個概念演示，實際使用需要配置真實的 LLM
    print("\n注意: 實際使用需要配置真實的 LLM API")
    print("\n並行執行概念:")
    print("  - 任務 1: 分析數據集 (模擬耗時 3 秒)")
    print("  - 任務 2: 生成報告 (模擬耗時 2 秒)")
    print("  - 任務 3: 處理文檔 (模擬耗時 2.5 秒)")

    print("\n順序執行總時間: 3 + 2 + 2.5 = 7.5 秒")
    print("並行執行總時間: max(3, 2, 2.5) = 3 秒")
    print("時間節省: (7.5 - 3) / 7.5 = 60%")

    print("\n使用方法:")
    print("""
    system = MultiAgentSystem()
    # 註冊代理...

    tasks = {
        "task1": "分析數據集A",
        "task2": "生成報告B",
        "task3": "處理文檔C"
    }
    agent_mapping = {
        "task1": "data_agent",
        "task2": "report_agent",
        "task3": "doc_agent"
    }

    # 並行執行
    results = await system.parallel_execution(tasks, agent_mapping)
    """)


# 示例 3: VectorStore 初始化優化
def demo_vector_store_optimization():
    """演示 VectorStore 初始化優化"""
    print("\n" + "="*60)
    print("示例 3: VectorStore 初始化優化")
    print("="*60)

    from ai_automation_framework.rag.vector_store import VectorStore
    import numpy as np

    print("\n創建 VectorStore 實例...")
    store = VectorStore(collection_name="demo_collection")

    # 模擬嵌入向量
    documents = [f"Document {i}" for i in range(10)]
    embeddings = [np.random.rand(384).tolist() for _ in range(10)]

    print("\n第一次調用 add_documents (會觸發初始化)...")
    start = time.time()
    store.add_documents(documents[:5], embeddings[:5])
    first_time = time.time() - start
    print(f"  耗時: {first_time:.4f} 秒 (包含初始化)")

    print("\n第二次調用 add_documents (不會重複初始化)...")
    start = time.time()
    store.add_documents(documents[5:], embeddings[5:])
    second_time = time.time() - start
    print(f"  耗時: {second_time:.4f} 秒 (無需初始化)")

    if first_time > second_time:
        speedup = first_time / second_time
        print(f"\n第二次調用加速: {speedup:.1f}x")
        print("優化效果: 避免了重複初始化的開銷")

    # 清理
    store.delete_collection()


# 示例 4: 緩存批量操作優化
def demo_cache_batch_operations():
    """演示緩存批量操作優化"""
    print("\n" + "="*60)
    print("示例 4: 緩存批量操作優化")
    print("="*60)

    from ai_automation_framework.core.cache import LRUCache

    cache = LRUCache(max_size=1000)

    # 準備測試數據
    num_items = 100
    test_items = {f"key_{i}": f"value_{i}" for i in range(num_items)}
    test_keys = list(test_items.keys())

    print(f"\n測試 {num_items} 個項目的操作...")

    # 測試批量設置 vs 逐個設置
    print("\n1. 批量設置測試:")

    # 逐個設置
    cache.clear()
    start = time.time()
    for key, value in test_items.items():
        cache.set(key, value)
    individual_set_time = time.time() - start
    print(f"  逐個設置耗時: {individual_set_time:.6f} 秒")

    # 批量設置
    cache.clear()
    start = time.time()
    cache.batch_set(test_items)
    batch_set_time = time.time() - start
    print(f"  批量設置耗時: {batch_set_time:.6f} 秒")

    if individual_set_time > batch_set_time:
        speedup = individual_set_time / batch_set_time
        print(f"  批量設置加速: {speedup:.1f}x")

    # 測試批量獲取 vs 逐個獲取
    print("\n2. 批量獲取測試:")

    # 逐個獲取
    start = time.time()
    individual_results = {}
    for key in test_keys:
        value = cache.get(key)
        if value is not None:
            individual_results[key] = value
    individual_get_time = time.time() - start
    print(f"  逐個獲取耗時: {individual_get_time:.6f} 秒")

    # 批量獲取
    start = time.time()
    batch_results = cache.batch_get(test_keys)
    batch_get_time = time.time() - start
    print(f"  批量獲取耗時: {batch_get_time:.6f} 秒")

    if individual_get_time > batch_get_time:
        speedup = individual_get_time / batch_get_time
        print(f"  批量獲取加速: {speedup:.1f}x")

    # 顯示緩存統計
    stats = cache.get_stats()
    print(f"\n緩存統計:")
    print(f"  - 命中率: {stats['hit_rate']:.1f}%")
    print(f"  - 總請求: {stats['total_requests']}")
    print(f"  - 緩存大小: {stats['size']}/{stats['max_size']}")

    print("\n優化效果: 減少了鎖獲取次數和上下文切換")


def main():
    """運行所有演示"""
    print("\n" + "="*60)
    print("AI Automation Framework - 性能優化演示")
    print("="*60)
    print("\n本演示將展示四項關鍵性能優化:")
    print("1. 數據庫批量插入優化")
    print("2. 多代理並行執行優化")
    print("3. VectorStore 初始化優化")
    print("4. 緩存批量操作優化")

    try:
        # 示例 1: 數據庫批量插入
        demo_batch_insert()

        # 示例 2: 並行執行（概念演示）
        asyncio.run(demo_parallel_execution())

        # 示例 3: VectorStore 優化
        demo_vector_store_optimization()

        # 示例 4: 緩存批量操作
        demo_cache_batch_operations()

        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)
        print("\n詳細文檔請參閱: PERFORMANCE_OPTIMIZATIONS.md")

    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
