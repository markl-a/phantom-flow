#!/usr/bin/env python3
"""
依賴檢查腳本
Dependency Check Script

檢查 requirements.txt 是否包含所有新功能所需的依賴。
"""

def check_dependencies():
    """檢查依賴"""
    with open('/path/to/Automation_with_AI/requirements.txt', 'r') as f:
        requirements = f.read()

    print("=" * 80)
    print("  依賴檢查報告")
    print("=" * 80)

    # 定義所需的依賴及其用途
    required_deps = {
        # 核心依賴
        "Core Libraries": [
            ("openai", "OpenAI API 客戶端"),
            ("anthropic", "Anthropic/Claude API 客戶端"),
            ("langchain", "LangChain 框架"),
            ("python-dotenv", "環境變量管理"),
            ("pydantic", "數據驗證"),
            ("requests", "HTTP 請求"),
        ],

        # 性能監控
        "Performance Monitoring": [
            ("prometheus-client", "Prometheus 指標"),
            ("psutil", "系統資源監控"),
            ("redis", "緩存和消息隊列"),
        ],

        # 音頻處理
        "Audio Processing": [
            ("google-cloud-speech", "Google 語音轉文字"),
            ("google-cloud-texttospeech", "Google 文字轉語音"),
            ("azure-cognitiveservices-speech", "Azure 語音服務"),
        ],

        # 視頻處理
        "Video Processing": [
            ("opencv-python", "視頻處理"),
            ("moviepy", "視頻編輯"),
            ("ffmpeg-python", "FFmpeg 綁定"),
        ],

        # 實時通信
        "Real-time Communication": [
            ("websockets", "WebSocket 協議"),
        ],

        # API 框架
        "API Frameworks": [
            ("graphene", "GraphQL 服務器"),
            ("flask", "Web 框架"),
            ("flask-graphql", "Flask GraphQL 集成"),
            ("fastapi", "FastAPI 框架"),
            ("uvicorn", "ASGI 服務器"),
        ],

        # 雲服務
        "Cloud Services": [
            ("azure-storage-blob", "Azure Blob Storage"),
            ("azure-cosmos", "Azure Cosmos DB"),
            ("azure-identity", "Azure 認證"),
            ("boto3", "AWS SDK"),
            ("google-cloud-storage", "Google Cloud Storage"),
            ("oss2", "阿里雲 OSS"),
            ("aliyun-python-sdk-core", "阿里雲 SDK"),
        ],

        # 自動化工具
        "Automation Tools": [
            ("beautifulsoup4", "網頁解析"),
            ("selenium", "瀏覽器自動化"),
            ("playwright", "現代瀏覽器自動化"),
            ("pillow", "圖像處理"),
            ("openpyxl", "Excel 處理"),
            ("schedule", "任務調度"),
        ],

        # 工作流編排框架
        "Workflow Orchestration": [
            ("temporalio", "Temporal.io 分布式工作流引擎"),
            ("prefect", "Prefect 現代數據工作流"),
            ("celery", "Celery 分布式任務隊列"),
        ],
    }

    print()
    total_checked = 0
    total_found = 0
    missing = []

    for category, deps in required_deps.items():
        print(f"\n{'─' * 80}")
        print(f"📦 {category}")
        print('─' * 80)

        for dep_name, description in deps:
            total_checked += 1
            if dep_name.lower() in requirements.lower():
                print(f"  ✅ {dep_name:35} - {description}")
                total_found += 1
            else:
                print(f"  ❌ {dep_name:35} - {description} [缺失]")
                missing.append((dep_name, description))

    # 總結
    print(f"\n{'=' * 80}")
    print("  總結")
    print('=' * 80)
    print(f"\n  檢查的依賴總數: {total_checked}")
    print(f"  已包含的依賴: {total_found}")
    print(f"  缺失的依賴: {len(missing)}")

    coverage = (total_found / total_checked * 100) if total_checked > 0 else 0
    print(f"  覆蓋率: {coverage:.1f}%")

    if missing:
        print(f"\n  ⚠️  缺失的依賴:")
        for dep_name, description in missing:
            print(f"    - {dep_name} ({description})")
        print(f"\n  建議執行: pip install " + " ".join([d[0] for d in missing]))
    else:
        print(f"\n  🎉 所有必需的依賴都已包含！")

    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    check_dependencies()
