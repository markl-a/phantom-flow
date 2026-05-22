#!/usr/bin/env python3
"""
Temporal 工作流示例
Temporal Workflow Examples

展示如何使用 Temporal.io 進行分布式工作流編排。
"""

import asyncio
from datetime import timedelta
from typing import List, Dict, Any

# 導入 Temporal 集成
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.integrations.temporal_integration import (
    TemporalIntegration,
    TemporalWorkflowBuilder
)


# ==================== 示例 1: 基本工作流定義 ====================

async def example_basic_workflow():
    """示例 1: 基本工作流執行"""
    print("\n" + "=" * 80)
    print("示例 1: 基本 Temporal 工作流")
    print("=" * 80)

    # 初始化 Temporal 集成
    temporal = TemporalIntegration(
        server_url="localhost:7233",
        namespace="default"
    )

    # 連接到 Temporal
    print("\n連接到 Temporal 服務器...")
    await temporal.connect()

    # 定義簡單的 Activity
    @temporal.create_activity()
    async def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """處理數據的 Activity"""
        print(f"  處理數據: {data}")
        return {
            "processed": True,
            "original": data,
            "result": f"Processed: {data.get('value', 'N/A')}"
        }

    # 定義工作流
    @temporal.create_workflow()
    async def data_processing_workflow(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """數據處理工作流"""
        print(f"  開始工作流，輸入: {input_data}")

        # 執行 activity
        result = await process_data(input_data)

        return result

    # 啟動工作流
    print("\n啟動工作流...")
    workflow_result = await temporal.start_workflow(
        workflow_id="data-processing-001",
        workflow_type="data_processing_workflow",
        args=[{"value": "test data", "timestamp": "2025-01-01"}]
    )

    print(f"✅ 工作流已啟動: {workflow_result}")

    # 等待完成
    if workflow_result.get('success'):
        print("\n等待工作流完成...")
        result = await temporal.get_workflow_result(workflow_result['workflow_id'])
        print(f"✅ 工作流結果: {result}")


# ==================== 示例 2: 複雜工作流 - 順序執行 ====================

async def example_sequential_workflow():
    """示例 2: 順序執行多個步驟"""
    print("\n" + "=" * 80)
    print("示例 2: 順序執行工作流")
    print("=" * 80)

    temporal = TemporalIntegration()
    await temporal.connect()

    # 定義多個 Activities
    @temporal.create_activity()
    async def step1_fetch_data(source: str) -> Dict[str, Any]:
        """步驟 1: 獲取數據"""
        print(f"  [步驟 1] 從 {source} 獲取數據")
        return {"data": f"Data from {source}", "records": 100}

    @temporal.create_activity()
    async def step2_transform_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """步驟 2: 轉換數據"""
        print(f"  [步驟 2] 轉換數據: {data['records']} 條記錄")
        return {"transformed": data['data'], "count": data['records']}

    @temporal.create_activity()
    async def step3_save_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """步驟 3: 保存數據"""
        print(f"  [步驟 3] 保存 {data['count']} 條記錄")
        return {"saved": True, "count": data['count']}

    # 定義順序工作流
    @temporal.create_workflow()
    async def etl_workflow(source: str) -> Dict[str, Any]:
        """ETL 工作流"""
        print(f"\n開始 ETL 工作流，源: {source}")

        # 步驟 1: 獲取
        raw_data = await step1_fetch_data(source)

        # 步驟 2: 轉換
        transformed = await step2_transform_data(raw_data)

        # 步驟 3: 保存
        result = await step3_save_data(transformed)

        return result

    # 啟動 ETL 工作流
    print("\n啟動 ETL 工作流...")
    result = await temporal.start_workflow(
        workflow_id="etl-workflow-001",
        workflow_type="etl_workflow",
        args=["database-A"]
    )

    print(f"✅ ETL 工作流已啟動: {result}")


# ==================== 示例 3: 工作流構建器 ====================

async def example_workflow_builder():
    """示例 3: 使用工作流構建器"""
    print("\n" + "=" * 80)
    print("示例 3: 使用 Temporal 工作流構建器")
    print("=" * 80)

    temporal = TemporalIntegration()
    await temporal.connect()

    # 創建構建器
    builder = TemporalWorkflowBuilder()

    # 註冊 activities
    @builder.register_activity(name="send_email")
    async def send_email(to: str, subject: str, body: str) -> bool:
        """發送郵件"""
        print(f"  發送郵件到 {to}")
        print(f"  主題: {subject}")
        return True

    @builder.register_activity(name="create_ticket")
    async def create_ticket(title: str, description: str) -> Dict[str, Any]:
        """創建工單"""
        print(f"  創建工單: {title}")
        return {"ticket_id": "TKT-12345", "status": "open"}

    @builder.register_activity(name="notify_slack")
    async def notify_slack(channel: str, message: str) -> bool:
        """發送 Slack 通知"""
        print(f"  發送 Slack 通知到 {channel}")
        print(f"  消息: {message}")
        return True

    # 註冊工作流
    @builder.register_workflow(name="customer_onboarding")
    async def customer_onboarding_workflow(customer_email: str, customer_name: str):
        """客戶入職工作流"""
        print(f"\n開始客戶入職流程: {customer_name}")

        # 發送歡迎郵件
        await send_email(
            to=customer_email,
            subject=f"歡迎, {customer_name}!",
            body="感謝您加入我們的服務..."
        )

        # 創建支持工單
        ticket = await create_ticket(
            title=f"新客戶入職: {customer_name}",
            description="請安排入職培訓"
        )

        # 通知團隊
        await notify_slack(
            channel="#customer-success",
            message=f"新客戶 {customer_name} 已入職，工單 {ticket['ticket_id']}"
        )

        return {"success": True, "ticket": ticket}

    # 啟動客戶入職工作流
    print("\n啟動客戶入職工作流...")
    result = await temporal.start_workflow(
        workflow_id="onboarding-001",
        workflow_type="customer_onboarding",
        args=["john@example.com", "John Doe"]
    )

    print(f"✅ 客戶入職工作流已啟動: {result}")


# ==================== 示例 4: 工作流查詢和信號 ====================

async def example_workflow_signals():
    """示例 4: 工作流信號和查詢"""
    print("\n" + "=" * 80)
    print("示例 4: 工作流信號和查詢")
    print("=" * 80)

    temporal = TemporalIntegration()
    await temporal.connect()

    # 定義帶有信號的工作流
    @temporal.create_workflow()
    async def approval_workflow(request_id: str) -> Dict[str, Any]:
        """需要審批的工作流"""
        print(f"\n等待審批: {request_id}")

        # 在實際場景中，這裡會等待信號
        # approved = await workflow.wait_condition(lambda: approval_received)

        return {"approved": True, "request_id": request_id}

    # 啟動審批工作流
    print("\n啟動審批工作流...")
    workflow_result = await temporal.start_workflow(
        workflow_id="approval-001",
        workflow_type="approval_workflow",
        args=["REQ-12345"]
    )

    if workflow_result.get('success'):
        workflow_id = workflow_result['workflow_id']

        # 查詢工作流狀態
        print("\n查詢工作流狀態...")
        status = await temporal.query_workflow(
            workflow_id=workflow_id,
            query_type="get_status"
        )
        print(f"  工作流狀態: {status}")

        # 發送審批信號
        print("\n發送審批信號...")
        signal_result = await temporal.signal_workflow(
            workflow_id=workflow_id,
            signal_name="approve",
            args=[{"approver": "manager@example.com", "approved": True}]
        )
        print(f"  信號已發送: {signal_result}")


# ==================== 示例 5: 批量工作流執行 ====================

async def example_batch_workflows():
    """示例 5: 批量執行工作流"""
    print("\n" + "=" * 80)
    print("示例 5: 批量工作流執行")
    print("=" * 80)

    temporal = TemporalIntegration()
    await temporal.connect()

    # 定義批處理 activity
    @temporal.create_activity()
    async def process_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """處理單個項目"""
        print(f"  處理項目: {item['id']}")
        return {"id": item['id'], "processed": True}

    # 定義批處理工作流
    @temporal.create_workflow()
    async def batch_processing_workflow(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批處理工作流"""
        print(f"\n批處理 {len(items)} 個項目")

        results = []
        for item in items:
            result = await process_item(item)
            results.append(result)

        return results

    # 準備批量數據
    items = [
        {"id": "item-001", "value": 100},
        {"id": "item-002", "value": 200},
        {"id": "item-003", "value": 300},
        {"id": "item-004", "value": 400},
        {"id": "item-005", "value": 500}
    ]

    # 啟動批處理工作流
    print(f"\n啟動批處理工作流，處理 {len(items)} 個項目...")
    result = await temporal.start_workflow(
        workflow_id="batch-processing-001",
        workflow_type="batch_processing_workflow",
        args=[items]
    )

    print(f"✅ 批處理工作流已啟動: {result}")


# ==================== 示例 6: 工作流取消和終止 ====================

async def example_workflow_cancellation():
    """示例 6: 工作流取消和終止"""
    print("\n" + "=" * 80)
    print("示例 6: 工作流取消和終止")
    print("=" * 80)

    temporal = TemporalIntegration()
    await temporal.connect()

    # 定義長時間運行的工作流
    @temporal.create_workflow()
    async def long_running_workflow(duration: int) -> Dict[str, Any]:
        """長時間運行的工作流"""
        print(f"\n開始長時間運行的工作流 ({duration} 秒)")

        # 在實際場景中，這裡會有長時間運行的任務
        # await asyncio.sleep(duration)

        return {"completed": True, "duration": duration}

    # 啟動長時間運行的工作流
    print("\n啟動長時間運行的工作流...")
    result = await temporal.start_workflow(
        workflow_id="long-running-001",
        workflow_type="long_running_workflow",
        args=[300]  # 5 分鐘
    )

    if result.get('success'):
        workflow_id = result['workflow_id']

        # 稍後取消工作流
        print("\n取消工作流...")
        cancel_result = await temporal.cancel_workflow(workflow_id)
        print(f"  工作流已取消: {cancel_result}")

        # 或者終止工作流
        # print("\n終止工作流...")
        # terminate_result = await temporal.terminate_workflow(
        #     workflow_id,
        #     reason="用戶請求終止"
        # )
        # print(f"  工作流已終止: {terminate_result}")


# ==================== 主函數 ====================

async def main():
    """運行所有示例"""
    print("\n" + "=" * 80)
    print("  Temporal 工作流集成 - 完整示例")
    print("=" * 80)

    try:
        # 示例 1: 基本工作流
        await example_basic_workflow()

        # 示例 2: 順序執行
        await example_sequential_workflow()

        # 示例 3: 工作流構建器
        await example_workflow_builder()

        # 示例 4: 信號和查詢
        await example_workflow_signals()

        # 示例 5: 批量執行
        await example_batch_workflows()

        # 示例 6: 取消和終止
        await example_workflow_cancellation()

        print("\n" + "=" * 80)
        print("  ✅ 所有示例執行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 注意: 運行此示例前需要:
    # 1. 安裝 Temporal: pip install temporalio
    # 2. 啟動 Temporal 服務器: temporal server start-dev
    # 3. 配置環境變量（如需要）

    print("\n⚠️  注意: 此示例需要 Temporal 服務器運行在 localhost:7233")
    print("請確保已安裝並啟動 Temporal 服務器")
    print("安裝: pip install temporalio")
    print("啟動: temporal server start-dev\n")

    # 運行示例
    asyncio.run(main())
