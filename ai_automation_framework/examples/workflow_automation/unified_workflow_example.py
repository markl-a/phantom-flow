"""
統一工作流自動化示例
Unified Workflow Automation Example

展示如何使用統一接口集成和管理多個工作流自動化平台。
"""

import os
from ai_automation_framework.integrations.workflow_automation_unified import (
    UnifiedWorkflowManager,
    WorkflowOrchestrator,
    WorkflowPlatform
)


def example_1_single_platform():
    """示例 1: 單平台工作流觸發"""
    print("=" * 60)
    print("示例 1: 單平台工作流觸發 - n8n")
    print("=" * 60)

    # 創建統一管理器
    manager = UnifiedWorkflowManager()

    # 註冊 n8n 平台
    manager.register_n8n(
        base_url="http://localhost:5678",
        api_key=os.getenv("N8N_API_KEY")
    )

    # 觸發 n8n 工作流
    result = manager.trigger_workflow(
        platform=WorkflowPlatform.N8N,
        workflow_id="workflow_123",
        data={
            "customer_name": "John Doe",
            "order_id": "ORD-001",
            "total_amount": 99.99
        }
    )

    print(f"\n執行結果:")
    print(f"成功: {result.get('success')}")
    if result.get('success'):
        print(f"執行 ID: {result.get('data', {}).get('id')}")
    else:
        print(f"錯誤: {result.get('error')}")


def example_2_multi_platform():
    """示例 2: 多平台集成"""
    print("\n" + "=" * 60)
    print("示例 2: 多平台集成")
    print("=" * 60)

    manager = UnifiedWorkflowManager()

    # 註冊多個平台
    manager.register_n8n(
        base_url=os.getenv("N8N_BASE_URL", "http://localhost:5678"),
        api_key=os.getenv("N8N_API_KEY")
    )

    manager.register_zapier(
        webhook_url=os.getenv("ZAPIER_WEBHOOK_URL"),
        api_key=os.getenv("ZAPIER_API_KEY")
    )

    manager.register_make(
        api_token=os.getenv("MAKE_API_TOKEN")
    )

    # 列出各平台的工作流
    print("\n📋 列出工作流:")

    for platform in [WorkflowPlatform.N8N, WorkflowPlatform.MAKE]:
        print(f"\n{platform.value} 工作流:")
        result = manager.list_workflows(platform)
        if result.get('success'):
            workflows = result.get('data', [])
            print(f"  找到 {len(workflows) if isinstance(workflows, list) else '?'} 個工作流")
        else:
            print(f"  錯誤: {result.get('error')}")


def example_3_broadcast_trigger():
    """示例 3: 廣播觸發 - 同時觸發多個平台"""
    print("\n" + "=" * 60)
    print("示例 3: 廣播觸發多個平台")
    print("=" * 60)

    manager = UnifiedWorkflowManager()

    # 註冊平台
    manager.register_n8n(base_url="http://localhost:5678")
    manager.register_zapier(webhook_url=os.getenv("ZAPIER_WEBHOOK_URL"))
    manager.register_make(api_token=os.getenv("MAKE_API_TOKEN"))

    # 同時觸發多個平台的工作流
    results = manager.broadcast_trigger(
        platforms=[
            WorkflowPlatform.N8N,
            WorkflowPlatform.ZAPIER,
            WorkflowPlatform.MAKE
        ],
        workflow_configs={
            "n8n": "workflow_notify",
            "zapier": "https://hooks.zapier.com/hooks/catch/xxx/yyy/",
            "make": "scenario_123"
        },
        data={
            "event": "新訂單",
            "customer": "Jane Smith",
            "amount": 149.99
        }
    )

    print("\n📡 廣播結果:")
    for platform, result in results.items():
        status = "✅ 成功" if result.get('success') else "❌ 失敗"
        print(f"{platform}: {status}")
        if not result.get('success'):
            print(f"  錯誤: {result.get('error')}")


def example_4_sequential_workflow():
    """示例 4: 順序工作流 - 步驟之間傳遞數據"""
    print("\n" + "=" * 60)
    print("示例 4: 順序工作流執行")
    print("=" * 60)

    manager = UnifiedWorkflowManager()
    manager.register_n8n(base_url="http://localhost:5678")
    manager.register_make(api_token=os.getenv("MAKE_API_TOKEN"))

    # 創建編排器
    orchestrator = WorkflowOrchestrator(manager)

    # 定義順序步驟
    steps = [
        {
            "platform": WorkflowPlatform.N8N,
            "workflow_id": "data_extraction",
            "data": {
                "source": "database",
                "table": "customers"
            },
            "use_previous_output": False
        },
        {
            "platform": WorkflowPlatform.MAKE,
            "workflow_id": "data_transformation",
            "use_previous_output": True  # 使用上一步的輸出
        },
        {
            "platform": WorkflowPlatform.N8N,
            "workflow_id": "data_notification",
            "use_previous_output": True
        }
    ]

    print("\n🔄 執行順序工作流:")
    result = orchestrator.execute_sequential(steps)

    if result.get('success'):
        print("✅ 所有步驟執行成功")
        for step_result in result['results']:
            print(f"  步驟 {step_result['step']}: {step_result['platform'].value} - 完成")
    else:
        print(f"❌ 在步驟 {result.get('failed_at_step')} 失敗")


def example_5_parallel_workflow():
    """示例 5: 並行工作流 - 同時執行多個獨立任務"""
    print("\n" + "=" * 60)
    print("示例 5: 並行工作流執行")
    print("=" * 60)

    manager = UnifiedWorkflowManager()
    manager.register_n8n(base_url="http://localhost:5678")
    manager.register_zapier(webhook_url=os.getenv("ZAPIER_WEBHOOK_URL"))
    manager.register_make(api_token=os.getenv("MAKE_API_TOKEN"))

    orchestrator = WorkflowOrchestrator(manager)

    # 定義並行任務
    workflows = [
        {
            "platform": WorkflowPlatform.N8N,
            "workflow_id": "send_email_notification",
            "data": {"recipient": "admin@example.com", "subject": "報告"}
        },
        {
            "platform": WorkflowPlatform.ZAPIER,
            "workflow_id": "https://hooks.zapier.com/hooks/catch/xxx/yyy/",
            "data": {"action": "log_event", "event_type": "order_completed"}
        },
        {
            "platform": WorkflowPlatform.MAKE,
            "workflow_id": "update_crm",
            "data": {"customer_id": "CUST-123", "status": "active"}
        }
    ]

    print("\n⚡ 並行執行工作流:")
    result = orchestrator.execute_parallel(workflows)

    print(f"\n總體狀態: {'✅ 全部成功' if result.get('success') else '⚠️ 部分失敗'}")

    for workflow_result in result['results']:
        platform = workflow_result['platform'].value
        success = workflow_result['result'].get('success', False)
        status = "✅" if success else "❌"
        print(f"  {status} {platform}")


def example_6_ai_workflow_integration():
    """示例 6: AI + 工作流集成"""
    print("\n" + "=" * 60)
    print("示例 6: AI + 工作流集成")
    print("=" * 60)

    from ai_automation_framework.llm.openai_client import OpenAIClient

    # 初始化 AI 客戶端
    ai_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))

    # 使用 AI 生成內容
    print("\n🤖 使用 AI 生成內容...")
    content = ai_client.simple_chat(
        "為一個電商平台生成一條促銷郵件標題，要求簡潔有力。"
    )
    print(f"AI 生成: {content}")

    # 將 AI 生成的內容通過工作流發送
    manager = UnifiedWorkflowManager()
    manager.register_zapier(webhook_url=os.getenv("ZAPIER_WEBHOOK_URL"))

    print("\n📧 通過 Zapier 發送郵件...")
    result = manager.trigger_workflow(
        platform=WorkflowPlatform.ZAPIER,
        workflow_id=os.getenv("ZAPIER_EMAIL_WEBHOOK"),
        data={
            "action": "send_email",
            "to": "marketing@example.com",
            "subject": content.strip(),
            "body": "這是 AI 生成的促銷郵件標題，請審閱。"
        }
    )

    if result.get('success'):
        print("✅ 郵件發送成功")
    else:
        print(f"❌ 發送失敗: {result.get('error')}")


def example_7_error_handling():
    """示例 7: 錯誤處理和重試"""
    print("\n" + "=" * 60)
    print("示例 7: 錯誤處理和重試")
    print("=" * 60)

    manager = UnifiedWorkflowManager()
    manager.register_n8n(base_url="http://localhost:5678")

    max_retries = 3
    retry_delay = 2  # 秒

    print(f"\n🔄 嘗試觸發工作流（最多重試 {max_retries} 次）...")

    for attempt in range(max_retries):
        print(f"\n嘗試 {attempt + 1}/{max_retries}:")

        result = manager.trigger_workflow(
            platform=WorkflowPlatform.N8N,
            workflow_id="potentially_failing_workflow",
            data={"attempt": attempt + 1}
        )

        if result.get('success'):
            print("✅ 執行成功")
            break
        else:
            print(f"❌ 執行失敗: {result.get('error')}")

            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒後重試...")
                import time
                time.sleep(retry_delay)
            else:
                print("⚠️ 已達到最大重試次數")


def main():
    """主函數 - 運行所有示例"""
    print("\n" + "=" * 80)
    print("統一工作流自動化示例")
    print("=" * 80)

    print("\n⚠️  注意: 這些示例需要配置相應的環境變量:")
    print("  - N8N_BASE_URL")
    print("  - N8N_API_KEY")
    print("  - ZAPIER_WEBHOOK_URL")
    print("  - ZAPIER_API_KEY")
    print("  - MAKE_API_TOKEN")
    print("  - OPENAI_API_KEY")

    print("\n選擇要運行的示例:")
    print("1. 單平台工作流觸發 (n8n)")
    print("2. 多平台集成")
    print("3. 廣播觸發多個平台")
    print("4. 順序工作流執行")
    print("5. 並行工作流執行")
    print("6. AI + 工作流集成")
    print("7. 錯誤處理和重試")
    print("0. 運行所有示例")

    choice = input("\n請輸入選項 (0-7): ").strip()

    examples = {
        "1": example_1_single_platform,
        "2": example_2_multi_platform,
        "3": example_3_broadcast_trigger,
        "4": example_4_sequential_workflow,
        "5": example_5_parallel_workflow,
        "6": example_6_ai_workflow_integration,
        "7": example_7_error_handling,
    }

    if choice == "0":
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n❌ 示例執行錯誤: {e}")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n❌ 示例執行錯誤: {e}")
    else:
        print("無效的選項")

    print("\n" + "=" * 80)
    print("示例演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
