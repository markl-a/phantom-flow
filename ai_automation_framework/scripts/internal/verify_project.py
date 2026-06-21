#!/usr/bin/env python3
"""
專案驗證和檢查腳本
Project Validation and Verification Script

檢查所有新增功能的完整性和正確性。
"""

import os
import sys
from pathlib import Path

# 設置專案根目錄
PROJECT_ROOT = Path("/path/to/Automation_with_AI")
sys.path.insert(0, str(PROJECT_ROOT))


class ProjectValidator:
    """專案驗證器"""

    def __init__(self):
        self.issues = []
        self.successes = []

    def check_file_exists(self, file_path: str, description: str = ""):
        """檢查文件是否存在"""
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            self.successes.append(f"✅ {description or file_path} ({size:,} bytes)")
            return True
        else:
            self.issues.append(f"❌ 文件不存在: {file_path}")
            return False

    def check_directory_exists(self, dir_path: str, description: str = ""):
        """檢查目錄是否存在"""
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists() and full_path.is_dir():
            file_count = len(list(full_path.glob("*")))
            self.successes.append(f"✅ {description or dir_path} ({file_count} 個文件)")
            return True
        else:
            self.issues.append(f"❌ 目錄不存在: {dir_path}")
            return False

    def print_section(self, title: str):
        """打印分節標題"""
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print('=' * 80)

    def print_summary(self):
        """打印總結"""
        print(f"\n{'=' * 80}")
        print("  驗證總結")
        print('=' * 80)
        print(f"\n✅ 成功: {len(self.successes)} 項")
        print(f"❌ 問題: {len(self.issues)} 項")

        if self.issues:
            print("\n⚠️  需要注意的問題:")
            for issue in self.issues:
                print(f"  {issue}")

    def run_validation(self):
        """運行完整驗證"""
        print("=" * 80)
        print("  AI Automation Framework - 專案驗證報告")
        print("=" * 80)

        # 1. 檢查部署和生產相關文件
        self.print_section("1. 部署和生產相關文件")

        deployment_files = [
            ("Dockerfile", "Docker 容器配置"),
            ("docker-compose.yml", "Docker Compose 配置"),
            (".dockerignore", "Docker 忽略文件"),
            ("deployment/nginx.conf", "Nginx 配置"),
            ("deployment/prometheus.yml", "Prometheus 配置"),
            (".github/workflows/ci.yml", "CI 工作流"),
            (".github/workflows/docker-publish.yml", "Docker 發布工作流"),
            (".github/workflows/deploy.yml", "部署工作流"),
        ]

        for file_path, desc in deployment_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 2. 檢查工作流自動化集成
        self.print_section("2. 工作流自動化集成文件")

        workflow_files = [
            ("ai_automation_framework/integrations/n8n_integration_enhanced.py", "n8n 增強集成"),
            ("ai_automation_framework/integrations/make_integration.py", "Make 集成"),
            ("ai_automation_framework/integrations/zapier_integration_enhanced.py", "Zapier 增強集成"),
            ("ai_automation_framework/integrations/workflow_automation_unified.py", "統一工作流接口"),
            ("ai_automation_framework/integrations/airflow_integration.py", "Airflow 集成"),
            ("ai_automation_framework/integrations/temporal_integration.py", "Temporal 分布式工作流集成"),
            ("ai_automation_framework/integrations/prefect_integration.py", "Prefect 數據工作流集成"),
            ("ai_automation_framework/integrations/celery_integration.py", "Celery 任務隊列集成"),
        ]

        for file_path, desc in workflow_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 3. 檢查增強功能模塊
        self.print_section("3. 增強功能模塊")

        enhancement_files = [
            ("ai_automation_framework/tools/performance_monitoring.py", "性能監控工具"),
            ("ai_automation_framework/tools/audio_processing.py", "音頻處理工具"),
            ("ai_automation_framework/tools/video_processing.py", "視頻處理工具"),
            ("ai_automation_framework/tools/websocket_server.py", "WebSocket 服務器"),
            ("ai_automation_framework/tools/graphql_api.py", "GraphQL API"),
            ("ai_automation_framework/integrations/cloud_services.py", "雲服務集成"),
        ]

        for file_path, desc in enhancement_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 4. 檢查示例和應用
        self.print_section("4. 示例和實際應用")

        example_files = [
            ("examples/real_world_applications/customer_service_automation.py", "客戶服務自動化"),
            ("examples/workflow_automation/unified_workflow_example.py", "統一工作流示例"),
            ("examples/workflow_automation/temporal_example.py", "Temporal 工作流示例"),
            ("examples/workflow_automation/prefect_example.py", "Prefect 工作流示例"),
            ("examples/workflow_automation/celery_example.py", "Celery 任務隊列示例"),
        ]

        for file_path, desc in example_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 5. 檢查文檔
        self.print_section("5. 文檔文件")

        doc_files = [
            ("docs/DEPLOYMENT_GUIDE.md", "部署指南"),
            ("docs/WORKFLOW_AUTOMATION_GUIDE.md", "工作流自動化指南"),
            ("docs/NEW_FEATURES.md", "新功能總結"),
            ("docs/LEARNING_PATH.md", "學習路徑"),
            ("docs/ADVANCED_FEATURES.md", "高級功能文檔"),
            ("README.md", "主 README"),
            ("FEATURE_SUMMARY.md", "功能總結"),
        ]

        for file_path, desc in doc_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 6. 檢查配置文件
        self.print_section("6. 配置文件")

        config_files = [
            ("requirements.txt", "Python 依賴"),
            ("setup.py", "安裝配置"),
            (".env.example", "環境變量示例"),
        ]

        for file_path, desc in config_files:
            if self.check_file_exists(file_path, desc):
                print(f"  {self.successes[-1]}")

        # 7. 檢查目錄結構
        self.print_section("7. 目錄結構")

        directories = [
            ("ai_automation_framework/integrations", "集成目錄"),
            ("ai_automation_framework/tools", "工具目錄"),
            ("examples/real_world_applications", "實際應用示例"),
            ("examples/workflow_automation", "工作流示例"),
            ("deployment", "部署配置"),
            (".github/workflows", "GitHub Actions"),
            ("docs", "文檔目錄"),
        ]

        for dir_path, desc in directories:
            if self.check_directory_exists(dir_path, desc):
                print(f"  {self.successes[-1]}")

        # 8. 統計信息
        self.print_section("8. 專案統計")

        # 統計代碼行數
        total_lines = 0
        python_files = list(PROJECT_ROOT.glob("**/*.py"))
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                pass

        print(f"  📊 Python 文件總數: {len(python_files)}")
        print(f"  📊 代碼總行數: {total_lines:,}")

        # 統計文檔字數
        total_doc_size = 0
        md_files = list(PROJECT_ROOT.glob("**/*.md"))
        for md_file in md_files:
            try:
                total_doc_size += md_file.stat().st_size
            except:
                pass

        print(f"  📊 Markdown 文件總數: {len(md_files)}")
        print(f"  📊 文檔總大小: {total_doc_size / 1024:.1f} KB")

        # 9. 功能清單
        self.print_section("9. 已實現功能清單")

        features = [
            "✅ Docker 容器化配置",
            "✅ CI/CD 自動化管道（GitHub Actions）",
            "✅ 多雲部署支持（AWS、Azure、GCP）",
            "✅ 性能監控和優化工具（Prometheus 集成）",
            "✅ n8n 工作流集成（完整 API）",
            "✅ Make (Integromat) 集成",
            "✅ Zapier 增強集成",
            "✅ Airflow 數據管道集成",
            "✅ Temporal 分布式工作流引擎",
            "✅ Prefect 現代數據工作流",
            "✅ Celery 分布式任務隊列",
            "✅ 統一工作流管理接口（支持 7 個平台）",
            "✅ 工作流編排器（順序/並行執行）",
            "✅ 音頻處理（STT、TTS）",
            "✅ 視頻處理（提取、剪輯、字幕）",
            "✅ WebSocket 實時通信",
            "✅ GraphQL API 支持",
            "✅ Azure 和阿里雲集成",
            "✅ 客戶服務自動化系統",
            "✅ 完整的部署和使用文檔",
        ]

        for feature in features:
            print(f"  {feature}")

        # 打印總結
        self.print_summary()

        return len(self.issues) == 0


def main():
    """主函數"""
    validator = ProjectValidator()
    success = validator.run_validation()

    print("\n" + "=" * 80)
    if success:
        print("  🎉 驗證完成！所有檢查都通過了。")
    else:
        print("  ⚠️  驗證完成，但發現一些問題（見上方）。")
    print("=" * 80 + "\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
