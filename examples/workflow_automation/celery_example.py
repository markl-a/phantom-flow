#!/usr/bin/env python3
"""
Celery 任務隊列示例
Celery Task Queue Examples

展示如何使用 Celery 進行分布式任務隊列管理。
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 導入 Celery 集成
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai_automation_framework.integrations.celery_integration import (
    CeleryIntegration,
    CeleryTaskBuilder,
    CeleryMonitor,
    create_sample_tasks
)

try:
    from celery.schedules import crontab
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    crontab = None


# ==================== 示例 1: 基本任務執行 ====================

def example_basic_tasks():
    """示例 1: 基本任務執行"""
    print("\n" + "=" * 80)
    print("示例 1: 基本 Celery 任務")
    print("=" * 80)

    # 初始化 Celery 集成
    celery = CeleryIntegration(
        broker_url="redis://localhost:6379/0",
        backend_url="redis://localhost:6379/0"
    )

    # 創建示例任務
    print("\n創建示例任務...")
    sample_tasks = create_sample_tasks(celery.app)

    # 執行加法任務
    print("\n執行加法任務...")
    result = celery.send_task(
        task_name="sample.add",
        args=[10, 20]
    )

    print(f"✅ 任務已發送: {result}")

    # 等待結果
    if result.get('success'):
        print("\n等待任務完成...")
        time.sleep(2)

        task_result = celery.get_task_result(result['task_id'])
        print(f"✅ 任務結果: {task_result}")


# ==================== 示例 2: 自定義任務定義 ====================

def example_custom_tasks():
    """示例 2: 自定義任務定義"""
    print("\n" + "=" * 80)
    print("示例 2: 自定義任務定義")
    print("=" * 80)

    celery = CeleryIntegration()

    # 定義自定義任務
    @celery.create_task(name="process_user_data")
    def process_user_data(user_id: int, action: str):
        """處理用戶數據"""
        print(f"  處理用戶 {user_id} 的動作: {action}")
        time.sleep(1)  # 模擬處理時間
        return {
            "user_id": user_id,
            "action": action,
            "processed_at": datetime.now().isoformat(),
            "success": True
        }

    @celery.create_task(name="send_email")
    def send_email(to: str, subject: str, body: str):
        """發送郵件任務"""
        print(f"  發送郵件到: {to}")
        print(f"  主題: {subject}")
        time.sleep(0.5)  # 模擬發送時間
        return {"sent": True, "to": to, "timestamp": datetime.now().isoformat()}

    @celery.create_task(name="generate_report")
    def generate_report(report_type: str, date: str):
        """生成報告任務"""
        print(f"  生成 {report_type} 報告，日期: {date}")
        time.sleep(2)  # 模擬報告生成
        return {
            "report_type": report_type,
            "date": date,
            "status": "completed",
            "file_url": f"/reports/{report_type}_{date}.pdf"
        }

    # 執行自定義任務
    print("\n執行用戶數據處理任務...")
    result1 = celery.send_task(
        task_name="process_user_data",
        args=[12345, "profile_update"]
    )
    print(f"✅ 任務已發送: {result1}")

    print("\n執行郵件發送任務...")
    result2 = celery.send_task(
        task_name="send_email",
        kwargs={
            "to": "user@example.com",
            "subject": "歡迎！",
            "body": "感謝您註冊我們的服務"
        }
    )
    print(f"✅ 任務已發送: {result2}")

    print("\n執行報告生成任務...")
    result3 = celery.send_task(
        task_name="generate_report",
        args=["sales", "2025-01-01"]
    )
    print(f"✅ 任務已發送: {result3}")


# ==================== 示例 3: 延遲和定時任務 ====================

def example_delayed_tasks():
    """示例 3: 延遲和定時任務"""
    print("\n" + "=" * 80)
    print("示例 3: 延遲和定時任務")
    print("=" * 80)

    celery = CeleryIntegration()

    # 定義延遲任務
    @celery.create_task(name="send_reminder")
    def send_reminder(user_id: int, message: str):
        """發送提醒"""
        print(f"  發送提醒給用戶 {user_id}: {message}")
        return {"reminded": True, "user_id": user_id}

    # 5 秒後執行
    print("\n發送延遲 5 秒的任務...")
    result1 = celery.send_task(
        task_name="send_reminder",
        args=[123, "您有一個待辦事項"],
        countdown=5
    )
    print(f"✅ 延遲任務已發送: {result1}")

    # 指定執行時間
    eta = datetime.now() + timedelta(seconds=10)
    print(f"\n發送定時任務（10秒後執行: {eta}）...")
    result2 = celery.send_task(
        task_name="send_reminder",
        args=[456, "會議即將開始"],
        eta=eta
    )
    print(f"✅ 定時任務已發送: {result2}")

    # 帶過期時間的任務
    print("\n發送帶過期時間的任務（30秒內有效）...")
    result3 = celery.send_task(
        task_name="send_reminder",
        args=[789, "臨時通知"],
        countdown=5,
        expires=30
    )
    print(f"✅ 帶過期時間的任務已發送: {result3}")


# ==================== 示例 4: 任務鏈（Chain） ====================

def example_task_chains():
    """示例 4: 任務鏈 - 順序執行"""
    print("\n" + "=" * 80)
    print("示例 4: 任務鏈（順序執行）")
    print("=" * 80)

    celery = CeleryIntegration()

    # 定義鏈式任務
    @celery.create_task(name="fetch_user")
    def fetch_user(user_id: int):
        """獲取用戶"""
        print(f"  [步驟 1] 獲取用戶 {user_id}")
        time.sleep(0.5)
        return {"user_id": user_id, "name": "John Doe", "email": "john@example.com"}

    @celery.create_task(name="update_profile")
    def update_profile(user_data: Dict[str, Any]):
        """更新用戶資料"""
        print(f"  [步驟 2] 更新用戶 {user_data['user_id']} 的資料")
        time.sleep(0.5)
        user_data['updated'] = True
        user_data['last_update'] = datetime.now().isoformat()
        return user_data

    @celery.create_task(name="send_confirmation")
    def send_confirmation(user_data: Dict[str, Any]):
        """發送確認郵件"""
        print(f"  [步驟 3] 發送確認郵件到 {user_data['email']}")
        time.sleep(0.5)
        return {
            "confirmed": True,
            "user": user_data,
            "sent_at": datetime.now().isoformat()
        }

    # 創建任務鏈
    print("\n創建任務鏈...")
    from celery import chain

    task_chain = chain(
        fetch_user.s(12345),
        update_profile.s(),
        send_confirmation.s()
    )

    # 這裡需要直接使用 Celery API，因為集成封裝暫不支持簽名
    print("  任務鏈: fetch_user -> update_profile -> send_confirmation")
    print("  注: 實際執行需要 Celery Worker 運行")


# ==================== 示例 5: 任務組（Group） ====================

def example_task_groups():
    """示例 5: 任務組 - 並行執行"""
    print("\n" + "=" * 80)
    print("示例 5: 任務組（並行執行）")
    print("=" * 80)

    celery = CeleryIntegration()

    # 定義可並行的任務
    @celery.create_task(name="process_file")
    def process_file(file_path: str):
        """處理文件"""
        print(f"  處理文件: {file_path}")
        time.sleep(1)
        return {
            "file": file_path,
            "processed": True,
            "size": 1024
        }

    # 創建任務組
    print("\n創建任務組（並行處理多個文件）...")
    files = [
        "/data/file1.txt",
        "/data/file2.txt",
        "/data/file3.txt",
        "/data/file4.txt"
    ]

    from celery import group

    task_group = group(process_file.s(file) for file in files)

    print(f"  任務組: 並行處理 {len(files)} 個文件")
    print("  注: 實際執行需要 Celery Worker 運行")


# ==================== 示例 6: 週期性任務 ====================

def example_periodic_tasks():
    """示例 6: 週期性任務"""
    print("\n" + "=" * 80)
    print("示例 6: 週期性任務")
    print("=" * 80)

    if not HAS_CELERY:
        print("  需要安裝 Celery")
        return

    celery = CeleryIntegration()

    # 定義週期性任務
    @celery.create_task(name="cleanup_task")
    def cleanup_task():
        """清理任務"""
        print("  執行清理任務")
        return {"cleaned": True, "timestamp": datetime.now().isoformat()}

    @celery.create_task(name="backup_task")
    def backup_task():
        """備份任務"""
        print("  執行備份任務")
        return {"backed_up": True, "timestamp": datetime.now().isoformat()}

    # 添加每小時執行的任務
    print("\n添加每小時執行的清理任務...")
    result1 = celery.add_periodic_task(
        schedule=timedelta(hours=1),
        task_name="cleanup_task",
        name="hourly_cleanup"
    )
    print(f"✅ 週期性任務已添加: {result1}")

    # 添加每天凌晨 2 點執行的備份任務
    print("\n添加每天凌晨 2 點的備份任務...")
    result2 = celery.add_periodic_task(
        schedule=crontab(hour=2, minute=0),
        task_name="backup_task",
        name="daily_backup_2am"
    )
    print(f"✅ 週期性任務已添加: {result2}")

    # 添加每週一早上 9 點的報告任務
    print("\n添加每週一早上 9 點的報告任務...")
    result3 = celery.add_periodic_task(
        schedule=crontab(hour=9, minute=0, day_of_week=1),
        task_name="generate_report",
        args=["weekly", datetime.now().strftime("%Y-%m-%d")],
        name="weekly_report_monday_9am"
    )
    print(f"✅ 週期性任務已添加: {result3}")

    print("\n注: 週期性任務需要 Celery Beat 運行: celery -A your_app beat")


# ==================== 示例 7: 任務監控 ====================

def example_task_monitoring():
    """示例 7: 任務監控"""
    print("\n" + "=" * 80)
    print("示例 7: 任務監控")
    print("=" * 80)

    celery = CeleryIntegration()
    monitor = CeleryMonitor(celery.app)

    # 獲取活動任務
    print("\n獲取活動任務...")
    active = celery.get_active_tasks()
    print(f"✅ 活動任務: {active}")

    # 獲取計劃任務
    print("\n獲取計劃任務...")
    scheduled = celery.get_scheduled_tasks()
    print(f"✅ 計劃任務: {scheduled}")

    # 獲取統計信息
    print("\n獲取 Celery 統計信息...")
    stats = monitor.get_stats()
    print(f"✅ 統計信息: {stats}")

    # 獲取 Worker 統計
    print("\n獲取 Worker 統計...")
    worker_stats = monitor.get_worker_stats()
    print(f"✅ Worker 統計: {worker_stats}")

    # Ping Workers
    print("\n Ping Celery Workers...")
    ping_result = monitor.ping_workers()
    print(f"✅ Ping 結果: {ping_result}")


# ==================== 示例 8: 任務構建器 ====================

def example_task_builder():
    """示例 8: 使用任務構建器"""
    print("\n" + "=" * 80)
    print("示例 8: 使用 Celery 任務構建器")
    print("=" * 80)

    celery = CeleryIntegration()
    builder = CeleryTaskBuilder(celery.app)

    # 註冊任務
    @builder.register_task
    def analyze_data(data: Dict[str, Any]):
        """分析數據"""
        print(f"  分析數據: {len(data)} 個鍵")
        time.sleep(1)
        return {
            "analyzed": True,
            "data_keys": list(data.keys()),
            "timestamp": datetime.now().isoformat()
        }

    @builder.register_task(name="transform_data")
    def transform_data(data: Dict[str, Any]):
        """轉換數據"""
        print(f"  轉換數據")
        time.sleep(0.5)
        return {
            "transformed": True,
            "original_keys": list(data.keys()),
            "timestamp": datetime.now().isoformat()
        }

    # 獲取註冊的任務
    print("\n獲取註冊的任務...")
    analyze_task = builder.get_task("analyze_data")
    transform_task = builder.get_task("transform_data")

    print(f"  已註冊任務: analyze_data, transform_data")

    # 創建工作流
    print("\n創建任務鏈工作流...")
    from celery import chain

    workflow = builder.create_workflow(
        workflow_type="chain",
        tasks=[
            analyze_task.s({"key1": "value1", "key2": "value2"}),
            transform_task.s()
        ]
    )

    print("  工作流已創建: analyze_data -> transform_data")


# ==================== 示例 9: 任務撤銷 ====================

def example_task_revocation():
    """示例 9: 任務撤銷"""
    print("\n" + "=" * 80)
    print("示例 9: 任務撤銷")
    print("=" * 80)

    celery = CeleryIntegration()

    # 定義長時間運行的任務
    @celery.create_task(name="long_running_task")
    def long_running_task(duration: int):
        """長時間運行的任務"""
        print(f"  開始長時間任務（{duration} 秒）")
        for i in range(duration):
            print(f"    進度: {i+1}/{duration}")
            time.sleep(1)
        return {"completed": True, "duration": duration}

    # 發送長時間任務
    print("\n發送長時間任務（30秒）...")
    result = celery.send_task(
        task_name="long_running_task",
        args=[30]
    )

    if result.get('success'):
        task_id = result['task_id']
        print(f"✅ 任務已發送: {task_id}")

        # 等待一會兒
        print("\n等待 3 秒...")
        time.sleep(3)

        # 撤銷任務
        print("\n撤銷任務...")
        revoke_result = celery.revoke_task(
            task_id=task_id,
            terminate=True
        )
        print(f"✅ 任務已撤銷: {revoke_result}")


# ==================== 示例 10: 完整的電商訂單處理流程 ====================

def example_ecommerce_workflow():
    """示例 10: 完整的電商訂單處理流程"""
    print("\n" + "=" * 80)
    print("示例 10: 電商訂單處理流程")
    print("=" * 80)

    celery = CeleryIntegration()
    builder = CeleryTaskBuilder(celery.app)

    # 定義訂單處理的各個步驟
    @builder.register_task(name="validate_order")
    def validate_order(order: Dict[str, Any]):
        """驗證訂單"""
        print(f"  [步驟 1] 驗證訂單: {order['order_id']}")
        time.sleep(0.3)
        order['validated'] = True
        return order

    @builder.register_task(name="check_inventory")
    def check_inventory(order: Dict[str, Any]):
        """檢查庫存"""
        print(f"  [步驟 2] 檢查庫存")
        time.sleep(0.5)
        order['inventory_checked'] = True
        order['in_stock'] = True
        return order

    @builder.register_task(name="process_payment")
    def process_payment(order: Dict[str, Any]):
        """處理支付"""
        print(f"  [步驟 3] 處理支付: ${order['amount']}")
        time.sleep(0.7)
        order['payment_processed'] = True
        order['transaction_id'] = "TXN-12345"
        return order

    @builder.register_task(name="create_shipment")
    def create_shipment(order: Dict[str, Any]):
        """創建發貨"""
        print(f"  [步驟 4] 創建發貨")
        time.sleep(0.4)
        order['shipment_created'] = True
        order['tracking_number'] = "TRACK-67890"
        return order

    @builder.register_task(name="notify_customer")
    def notify_customer(order: Dict[str, Any]):
        """通知客戶"""
        print(f"  [步驟 5] 通知客戶: {order['customer_email']}")
        time.sleep(0.3)
        order['customer_notified'] = True
        return order

    # 創建訂單處理工作流
    print("\n創建訂單處理工作流...")

    order_data = {
        "order_id": "ORD-20250101-001",
        "customer_email": "customer@example.com",
        "items": ["Product A", "Product B"],
        "amount": 299.99
    }

    # 使用任務鏈創建完整流程
    from celery import chain

    order_workflow = chain(
        validate_order.s(order_data),
        check_inventory.s(),
        process_payment.s(),
        create_shipment.s(),
        notify_customer.s()
    )

    print("  工作流: 驗證 -> 庫存 -> 支付 -> 發貨 -> 通知")
    print("  注: 實際執行需要 Celery Worker 運行")


# ==================== 主函數 ====================

def main():
    """運行所有示例"""
    print("\n" + "=" * 80)
    print("  Celery 任務隊列集成 - 完整示例")
    print("=" * 80)

    if not HAS_CELERY:
        print("\n❌ 錯誤: 需要安裝 Celery")
        print("安裝: pip install celery[redis]")
        return

    try:
        # 示例 1: 基本任務
        example_basic_tasks()

        # 示例 2: 自定義任務
        example_custom_tasks()

        # 示例 3: 延遲任務
        example_delayed_tasks()

        # 示例 4: 任務鏈
        example_task_chains()

        # 示例 5: 任務組
        example_task_groups()

        # 示例 6: 週期性任務
        example_periodic_tasks()

        # 示例 7: 任務監控
        example_task_monitoring()

        # 示例 8: 任務構建器
        example_task_builder()

        # 示例 9: 任務撤銷
        example_task_revocation()

        # 示例 10: 電商工作流
        example_ecommerce_workflow()

        print("\n" + "=" * 80)
        print("  ✅ 所有示例執行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 注意: 運行此示例前需要:
    # 1. 安裝 Celery: pip install celery[redis]
    # 2. 啟動 Redis: redis-server
    # 3. 啟動 Celery Worker: celery -A your_app worker --loglevel=info
    # 4. 啟動 Celery Beat (週期性任務): celery -A your_app beat

    print("\n⚠️  注意: 此示例需要 Redis 和 Celery Worker 運行")
    print("請確保已安裝並啟動相關服務:")
    print("  1. 安裝: pip install celery[redis]")
    print("  2. Redis: redis-server")
    print("  3. Worker: celery -A celery_integration worker --loglevel=info")
    print("  4. Beat: celery -A celery_integration beat\n")

    # 運行示例
    main()
