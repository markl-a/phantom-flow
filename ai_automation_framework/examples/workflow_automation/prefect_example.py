#!/usr/bin/env python3
"""
Prefect 工作流示例
Prefect Workflow Examples

展示如何使用 Prefect 進行現代化數據工作流編排。
"""

import asyncio
from datetime import timedelta, datetime
from typing import List, Dict, Any

# 導入 Prefect 集成
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.integrations.prefect_integration import (
    PrefectIntegration,
    PrefectFlowBuilder,
    PrefectScheduler
)


# ==================== 示例 1: 基本 Flow 和 Task ====================

async def example_basic_flow():
    """示例 1: 基本 Prefect Flow 和 Task"""
    print("\n" + "=" * 80)
    print("示例 1: 基本 Prefect Flow")
    print("=" * 80)

    # 初始化 Prefect 集成
    prefect = PrefectIntegration()

    # 定義 Task
    @prefect.create_task(name="extract_data")
    async def extract_data(source: str) -> Dict[str, Any]:
        """提取數據"""
        print(f"  從 {source} 提取數據")
        return {"source": source, "records": 1000, "timestamp": datetime.now().isoformat()}

    @prefect.create_task(name="transform_data")
    async def transform_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """轉換數據"""
        print(f"  轉換 {data['records']} 條記錄")
        return {
            "transformed": True,
            "records": data['records'],
            "source": data['source']
        }

    @prefect.create_task(name="load_data")
    async def load_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """加載數據"""
        print(f"  加載 {data['records']} 條記錄到目標系統")
        return {
            "loaded": True,
            "count": data['records'],
            "success": True
        }

    # 定義 Flow
    @prefect.create_flow(name="etl_pipeline")
    async def etl_pipeline(source: str = "database"):
        """ETL Pipeline Flow"""
        print(f"\n開始 ETL Pipeline，源: {source}")

        # 執行 tasks
        raw_data = await extract_data(source)
        transformed = await transform_data(raw_data)
        result = await load_data(transformed)

        return result

    # 創建 Flow Run
    print("\n創建 Flow Run...")
    flow_run = await prefect.create_flow_run(
        flow_name="etl_pipeline",
        parameters={"source": "production-db"}
    )

    print(f"✅ Flow Run 已創建: {flow_run}")

    # 等待完成
    if flow_run.get('success'):
        print("\n等待 Flow 完成...")
        result = await prefect.wait_for_flow_run(flow_run['flow_run_id'])
        print(f"✅ Flow 執行結果: {result}")


# ==================== 示例 2: 並行任務執行 ====================

async def example_parallel_tasks():
    """示例 2: 並行執行多個任務"""
    print("\n" + "=" * 80)
    print("示例 2: 並行任務執行")
    print("=" * 80)

    prefect = PrefectIntegration()

    # 定義可並行的任務
    @prefect.create_task(name="fetch_api_data")
    async def fetch_api_data(api_name: str) -> Dict[str, Any]:
        """從 API 獲取數據"""
        print(f"  從 {api_name} API 獲取數據")
        await asyncio.sleep(1)  # 模擬 API 調用
        return {"api": api_name, "data": f"Data from {api_name}", "count": 100}

    @prefect.create_task(name="aggregate_results")
    async def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合結果"""
        print(f"  聚合 {len(results)} 個結果")
        total_count = sum(r['count'] for r in results)
        return {
            "total_apis": len(results),
            "total_records": total_count,
            "apis": [r['api'] for r in results]
        }

    # 定義並行 Flow
    @prefect.create_flow(name="parallel_api_fetcher")
    async def parallel_api_fetcher(api_list: List[str]):
        """並行獲取多個 API 數據"""
        print(f"\n並行獲取 {len(api_list)} 個 API 的數據")

        # 並行執行多個任務
        tasks = [fetch_api_data(api) for api in api_list]
        results = await asyncio.gather(*tasks)

        # 聚合結果
        aggregated = await aggregate_results(list(results))

        return aggregated

    # 運行並行 Flow
    print("\n創建並行 Flow Run...")
    api_list = ["weather-api", "stocks-api", "news-api", "social-api"]

    flow_run = await prefect.create_flow_run(
        flow_name="parallel_api_fetcher",
        parameters={"api_list": api_list}
    )

    print(f"✅ 並行 Flow Run 已創建: {flow_run}")


# ==================== 示例 3: Flow 構建器 ====================

async def example_flow_builder():
    """示例 3: 使用 Flow 構建器"""
    print("\n" + "=" * 80)
    print("示例 3: 使用 Prefect Flow 構建器")
    print("=" * 80)

    prefect = PrefectIntegration()
    builder = PrefectFlowBuilder()

    # 註冊任務
    @builder.register_task(name="send_notification", retries=3, retry_delay_seconds=10)
    async def send_notification(recipient: str, message: str) -> bool:
        """發送通知"""
        print(f"  發送通知給 {recipient}: {message}")
        return True

    @builder.register_task(name="process_order")
    async def process_order(order_id: str) -> Dict[str, Any]:
        """處理訂單"""
        print(f"  處理訂單: {order_id}")
        return {
            "order_id": order_id,
            "status": "processed",
            "amount": 99.99
        }

    @builder.register_task(name="update_inventory")
    async def update_inventory(order: Dict[str, Any]) -> bool:
        """更新庫存"""
        print(f"  更新庫存，訂單: {order['order_id']}")
        return True

    # 註冊 Flow
    @builder.register_flow(name="order_fulfillment")
    async def order_fulfillment(order_id: str, customer_email: str):
        """訂單履行流程"""
        print(f"\n開始訂單履行流程: {order_id}")

        # 處理訂單
        order = await process_order(order_id)

        # 更新庫存
        await update_inventory(order)

        # 發送通知
        await send_notification(
            recipient=customer_email,
            message=f"您的訂單 {order_id} 已處理，金額: ${order['amount']}"
        )

        return {"success": True, "order": order}

    # 創建 Flow Run
    print("\n創建訂單履行 Flow Run...")
    flow_run = await prefect.create_flow_run(
        flow_name="order_fulfillment",
        parameters={
            "order_id": "ORD-12345",
            "customer_email": "customer@example.com"
        }
    )

    print(f"✅ 訂單履行 Flow Run 已創建: {flow_run}")


# ==================== 示例 4: 定時調度 ====================

async def example_scheduled_flows():
    """示例 4: 定時調度 Flow"""
    print("\n" + "=" * 80)
    print("示例 4: 定時調度 Flow")
    print("=" * 80)

    prefect = PrefectIntegration()
    scheduler = PrefectScheduler()

    # 定義需要定時執行的 Flow
    @prefect.create_flow(name="daily_report")
    async def daily_report(report_date: str):
        """每日報告 Flow"""
        print(f"\n生成 {report_date} 的每日報告")

        # 模擬報告生成
        report = {
            "date": report_date,
            "total_sales": 10000,
            "total_orders": 150,
            "average_order_value": 66.67
        }

        print(f"  報告已生成: {report}")
        return report

    # 創建每日調度
    print("\n創建每日調度...")
    schedule_result = await scheduler.create_cron_schedule(
        flow_name="daily_report",
        cron="0 8 * * *",  # 每天早上 8 點
        schedule_name="daily_report_8am",
        parameters={"report_date": datetime.now().strftime("%Y-%m-%d")}
    )

    print(f"✅ 每日調度已創建: {schedule_result}")

    # 創建間隔調度
    print("\n創建間隔調度...")
    interval_result = await scheduler.create_interval_schedule(
        flow_name="daily_report",
        interval_seconds=3600,  # 每小時
        schedule_name="hourly_report",
        parameters={"report_date": datetime.now().strftime("%Y-%m-%d")}
    )

    print(f"✅ 間隔調度已創建: {interval_result}")

    # 列出所有調度
    print("\n列出所有調度...")
    schedules = await scheduler.list_schedules()
    print(f"  當前調度數量: {len(schedules.get('deployments', []))}")


# ==================== 示例 5: Flow Run 監控 ====================

async def example_flow_monitoring():
    """示例 5: Flow Run 監控"""
    print("\n" + "=" * 80)
    print("示例 5: Flow Run 監控")
    print("=" * 80)

    prefect = PrefectIntegration()

    # 定義可監控的 Flow
    @prefect.create_flow(name="data_processing")
    async def data_processing(batch_size: int = 100):
        """數據處理 Flow"""
        print(f"\n處理 {batch_size} 條數據")

        for i in range(0, batch_size, 10):
            print(f"  處理進度: {i}/{batch_size}")
            await asyncio.sleep(0.1)

        return {"processed": batch_size, "success": True}

    # 創建 Flow Run
    print("\n創建 Flow Run...")
    flow_run = await prefect.create_flow_run(
        flow_name="data_processing",
        parameters={"batch_size": 100}
    )

    if flow_run.get('success'):
        flow_run_id = flow_run['flow_run_id']

        # 監控 Flow Run
        print("\n監控 Flow Run 狀態...")
        status = await prefect.get_flow_run_status(flow_run_id)
        print(f"  狀態: {status}")

        # 獲取日誌
        print("\n獲取 Flow Run 日誌...")
        logs = await prefect.get_flow_run_logs(flow_run_id)
        print(f"  日誌條數: {logs.get('log_count', 0)}")

        # 如果需要取消
        # print("\n取消 Flow Run...")
        # cancel_result = await prefect.cancel_flow_run(flow_run_id)
        # print(f"  取消結果: {cancel_result}")


# ==================== 示例 6: 錯誤處理和重試 ====================

async def example_error_handling():
    """示例 6: 錯誤處理和重試"""
    print("\n" + "=" * 80)
    print("示例 6: 錯誤處理和重試")
    print("=" * 80)

    prefect = PrefectIntegration()

    # 定義可能失敗的任務（帶重試）
    @prefect.create_task(
        name="unreliable_api_call",
        retries=3,
        retry_delay_seconds=5
    )
    async def unreliable_api_call(api_url: str) -> Dict[str, Any]:
        """可能失敗的 API 調用"""
        print(f"  調用 API: {api_url}")

        # 模擬有時會失敗的 API
        import random
        if random.random() < 0.3:  # 30% 失敗率
            raise Exception("API 調用失敗")

        return {"status": "success", "data": "API response"}

    @prefect.create_task(name="fallback_handler")
    async def fallback_handler(error: str) -> Dict[str, Any]:
        """錯誤回退處理"""
        print(f"  執行回退處理: {error}")
        return {"status": "fallback", "error": error}

    # 定義帶錯誤處理的 Flow
    @prefect.create_flow(name="resilient_api_flow")
    async def resilient_api_flow(api_url: str):
        """具有彈性的 API Flow"""
        print(f"\n調用 API: {api_url}")

        try:
            # 嘗試調用 API
            result = await unreliable_api_call(api_url)
            return result
        except Exception as e:
            # 如果失敗，執行回退
            print(f"  API 調用失敗，執行回退: {e}")
            result = await fallback_handler(str(e))
            return result

    # 創建 Flow Run
    print("\n創建帶錯誤處理的 Flow Run...")
    flow_run = await prefect.create_flow_run(
        flow_name="resilient_api_flow",
        parameters={"api_url": "https://api.example.com/data"}
    )

    print(f"✅ Flow Run 已創建: {flow_run}")


# ==================== 示例 7: 數據管道 ====================

async def example_data_pipeline():
    """示例 7: 完整的數據管道"""
    print("\n" + "=" * 80)
    print("示例 7: 完整的數據管道")
    print("=" * 80)

    prefect = PrefectIntegration()
    builder = PrefectFlowBuilder()

    # 定義數據管道的各個階段
    @builder.register_task(name="ingest_data")
    async def ingest_data(sources: List[str]) -> List[Dict[str, Any]]:
        """數據攝取"""
        print(f"  從 {len(sources)} 個源攝取數據")
        data_chunks = []
        for source in sources:
            data_chunks.append({
                "source": source,
                "records": 1000,
                "timestamp": datetime.now().isoformat()
            })
        return data_chunks

    @builder.register_task(name="validate_data")
    async def validate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """數據驗證"""
        print(f"  驗證 {len(data)} 個數據塊")
        validated = []
        for chunk in data:
            chunk['validated'] = True
            chunk['validation_timestamp'] = datetime.now().isoformat()
            validated.append(chunk)
        return validated

    @builder.register_task(name="enrich_data")
    async def enrich_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """數據豐富化"""
        print(f"  豐富化 {len(data)} 個數據塊")
        enriched = []
        for chunk in data:
            chunk['enriched'] = True
            chunk['metadata'] = {"quality_score": 0.95}
            enriched.append(chunk)
        return enriched

    @builder.register_task(name="store_data")
    async def store_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """數據存儲"""
        total_records = sum(chunk['records'] for chunk in data)
        print(f"  存儲 {total_records} 條記錄")
        return {
            "stored": True,
            "total_records": total_records,
            "chunks": len(data)
        }

    # 定義完整管道 Flow
    @builder.register_flow(name="data_pipeline")
    async def data_pipeline(sources: List[str]):
        """完整的數據管道"""
        print(f"\n啟動數據管道，源數量: {len(sources)}")

        # 階段 1: 攝取
        raw_data = await ingest_data(sources)

        # 階段 2: 驗證
        validated_data = await validate_data(raw_data)

        # 階段 3: 豐富化
        enriched_data = await enrich_data(validated_data)

        # 階段 4: 存儲
        result = await store_data(enriched_data)

        return result

    # 運行數據管道
    print("\n創建數據管道 Flow Run...")
    sources = ["source-A", "source-B", "source-C"]

    flow_run = await prefect.create_flow_run(
        flow_name="data_pipeline",
        parameters={"sources": sources}
    )

    print(f"✅ 數據管道 Flow Run 已創建: {flow_run}")


# ==================== 主函數 ====================

async def main():
    """運行所有示例"""
    print("\n" + "=" * 80)
    print("  Prefect 工作流集成 - 完整示例")
    print("=" * 80)

    try:
        # 示例 1: 基本 Flow
        await example_basic_flow()

        # 示例 2: 並行任務
        await example_parallel_tasks()

        # 示例 3: Flow 構建器
        await example_flow_builder()

        # 示例 4: 定時調度
        await example_scheduled_flows()

        # 示例 5: Flow 監控
        await example_flow_monitoring()

        # 示例 6: 錯誤處理
        await example_error_handling()

        # 示例 7: 數據管道
        await example_data_pipeline()

        print("\n" + "=" * 80)
        print("  ✅ 所有示例執行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 注意: 運行此示例前需要:
    # 1. 安裝 Prefect: pip install prefect
    # 2. 啟動 Prefect 服務器: prefect server start
    # 3. 配置環境變量（如需要）

    print("\n⚠️  注意: 此示例需要 Prefect 服務器運行")
    print("請確保已安裝並啟動 Prefect")
    print("安裝: pip install prefect")
    print("啟動: prefect server start\n")

    # 運行示例
    asyncio.run(main())
