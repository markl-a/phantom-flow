"""
Hackathon 快速啟動模板

24 小時內從零到完整項目的 AI 輔助開發工具
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.agents import BaseAgent
from datetime import datetime
import json


class HackathonStarter:
    """Hackathon 項目快速啟動助手"""

    def __init__(self, project_name: str, problem_statement: str):
        """
        初始化 Hackathon 項目

        Args:
            project_name: 項目名稱
            problem_statement: 問題陳述
        """
        self.project_name = project_name
        self.problem = problem_statement
        self.client = OpenAIClient()

        # 創建專業團隊代理
        self.pm = BaseAgent(
            name="ProductManager",
            system_message="""你是產品經理，擅長需求分析和產品設計。
            你的職責是理解問題、定義需求、確定 MVP 範圍。"""
        )

        self.architect = BaseAgent(
            name="SolutionArchitect",
            system_message="""你是解決方案架構師，擅長系統設計。
            你的職責是設計簡單但可擴展的架構，選擇合適的技術棧。"""
        )

        self.developer = BaseAgent(
            name="Developer",
            system_message="""你是全棧開發者，擅長快速實現。
            你的職責是提供可執行的代碼、最佳實踐、實施建議。"""
        )

        self.presenter = BaseAgent(
            name="Presenter",
            system_message="""你是演示專家，擅長講故事和展示。
            你的職責是設計吸引人的演示，突出項目價值。"""
        )

    def run_quick_start(self) -> dict:
        """
        完整的快速啟動流程

        Returns:
            包含所有規劃結果的字典
        """
        print("=" * 70)
        print(f"🚀 Hackathon 項目快速啟動: {self.project_name}")
        print("=" * 70)
        print(f"問題: {self.problem}")
        print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)

        results = {}

        # 階段 1: 需求分析 (10分鐘)
        print("\n" + "▶" * 35)
        print("📋 階段 1: 需求分析 (預計 10 分鐘)")
        print("▶" * 35)
        results['requirements'] = self.analyze_requirements()
        print("\n✅ 需求分析完成")

        # 階段 2: 架構設計 (20分鐘)
        print("\n" + "▶" * 35)
        print("🏗️ 階段 2: 架構設計 (預計 20 分鐘)")
        print("▶" * 35)
        results['architecture'] = self.design_architecture(results['requirements'])
        print("\n✅ 架構設計完成")

        # 階段 3: 任務分解 (10分鐘)
        print("\n" + "▶" * 35)
        print("✅ 階段 3: 任務分解 (預計 10 分鐘)")
        print("▶" * 35)
        results['tasks'] = self.create_task_breakdown(results['architecture'])
        print("\n✅ 任務分解完成")

        # 階段 4: 代碼結構 (20分鐘)
        print("\n" + "▶" * 35)
        print("💻 階段 4: 代碼結構生成 (預計 20 分鐘)")
        print("▶" * 35)
        results['code_structure'] = self.generate_code_structure(results['architecture'])
        print("\n✅ 代碼結構完成")

        # 階段 5: 實施指南 (10分鐘)
        print("\n" + "▶" * 35)
        print("📖 階段 5: 實施指南 (預計 10 分鐘)")
        print("▶" * 35)
        results['implementation_guide'] = self.create_implementation_guide(results['tasks'])
        print("\n✅ 實施指南完成")

        # 階段 6: 演示準備 (10分鐘)
        print("\n" + "▶" * 35)
        print("🎤 階段 6: 演示準備 (預計 10 分鐘)")
        print("▶" * 35)
        results['pitch_deck'] = self.generate_pitch_deck()
        print("\n✅ 演示準備完成")

        # 總結
        print("\n" + "=" * 70)
        print("🎉 快速啟動完成！總耗時約 90 分鐘")
        print("=" * 70)
        print("\n📊 生成的文檔:")
        print("  ✓ 需求分析文檔")
        print("  ✓ 系統架構設計")
        print("  ✓ 詳細任務列表")
        print("  ✓ 代碼項目結構")
        print("  ✓ 實施指南")
        print("  ✓ 演示文稿大綱")
        print("\n🚀 現在可以開始編碼了！")

        return results

    def analyze_requirements(self) -> str:
        """階段 1: AI 需求分析"""

        prompt = f"""
        Hackathon 問題分析：

        **項目名稱**: {self.project_name}
        **問題陳述**:
        {self.problem}

        **限制條件**:
        - 時間: 24 小時
        - 團隊: 1-4 人
        - 必須有可演示的產品

        請進行需求分析，輸出：

        ## 1. 核心需求 (Must-Have)
        列出 3-5 個核心功能，這些是 MVP 必須的。

        ## 2. 重要需求 (Should-Have)
        列出 2-3 個重要但非必需的功能。

        ## 3. 可選需求 (Nice-to-Have)
        列出 1-2 個如果有時間可以添加的功能。

        ## 4. MVP 定義
        清楚描述最小可行產品應該是什麼樣的。

        ## 5. 技術棧建議
        推薦適合快速開發的技術棧（前端、後端、AI、數據庫等）。

        ## 6. 成功標準
        如何判斷項目是否成功？

        以清晰的 Markdown 格式輸出，每個部分包含具體的要點。
        """

        result = self.pm.chat(prompt)
        print(result)
        return result

    def design_architecture(self, requirements: str) -> str:
        """階段 2: AI 架構設計"""

        prompt = f"""
        基於以下需求設計系統架構：

        {requirements}

        請設計：

        ## 1. 系統架構圖
        用文字描述系統的主要組件和它們之間的關係。

        ## 2. 主要模塊
        列出 3-5 個主要模塊，每個模塊包括：
        - 模塊名稱
        - 職責
        - 輸入/輸出
        - 技術選型

        ## 3. 數據流
        描述數據如何在系統中流動。

        ## 4. API 設計
        列出主要的 API 端點（如果適用）。

        ## 5. AI 集成方案
        如何集成 AI 功能（使用本框架）。

        ## 6. 部署方案
        快速部署到哪裡（Vercel, Heroku, etc.）。

        原則：
        - 簡單優先
        - 快速實現
        - 容易演示
        - 使用熟悉的技術

        以清晰的 Markdown 格式輸出。
        """

        result = self.architect.chat(prompt)
        print(result)
        return result

    def create_task_breakdown(self, architecture: str) -> str:
        """階段 3: AI 任務分解"""

        prompt = f"""
        基於以下架構，創建 24 小時開發計劃：

        {architecture}

        請創建詳細的任務列表，按時間段組織：

        ## 第 1-2 小時：項目設置
        - [ ] 任務 1
        - [ ] 任務 2
        ...

        ## 第 3-8 小時：核心功能開發
        - [ ] 任務 1 (預計 2h)
        - [ ] 任務 2 (預計 3h)
        ...

        ## 第 9-12 小時：功能完善
        - [ ] 任務 1
        ...

        ## 第 13-18 小時：集成和測試
        - [ ] 任務 1
        ...

        ## 第 19-21 小時：優化和打磨
        - [ ] 任務 1
        ...

        ## 第 22-24 小時：演示準備
        - [ ] 任務 1
        ...

        每個任務包含：
        - 具體的行動項
        - 預估時間
        - 優先級 (P0/P1/P2)
        - 驗收標準

        確保：
        - 任務具體可執行
        - 時間分配合理
        - 有緩衝時間
        - 優先保證核心功能

        以 Markdown checklist 格式輸出。
        """

        result = self.client.simple_chat(prompt)
        print(result)
        return result

    def generate_code_structure(self, architecture: str) -> str:
        """階段 4: AI 生成代碼結構"""

        prompt = f"""
        基於以下架構生成項目代碼結構：

        {architecture}

        請生成：

        ## 1. 項目目錄結構
        ```
        project_name/
        ├── frontend/
        ├── backend/
        ├── ...
        └── README.md
        ```

        ## 2. 主要文件及其職責
        列出每個重要文件和它的作用。

        ## 3. 核心代碼框架
        為主要文件提供代碼框架（含註釋）。

        包括：
        - 後端主文件（FastAPI/Flask）
        - AI 集成代碼（使用本框架）
        - 前端主組件（React/Vue）
        - 配置文件
        - requirements.txt / package.json

        代碼要求：
        - 完整可運行
        - 包含必要的導入
        - 有清晰註釋
        - 遵循最佳實踐

        ## 4. 環境配置
        .env.example 內容

        ## 5. README 模板
        基礎的 README.md 內容

        以代碼塊形式輸出，分段清晰。
        """

        result = self.developer.chat(prompt)
        print(result)
        return result

    def create_implementation_guide(self, tasks: str) -> str:
        """階段 5: AI 實施指南"""

        prompt = f"""
        基於任務列表，創建實施指南：

        {tasks}

        請創建：

        ## 1. 快速開始 (前 2 小時)
        具體要做什麼，一步一步的指引。

        ## 2. 開發節奏 (中間 18 小時)
        - 每 2-3 小時的檢查點
        - 每個階段的目標
        - 如何保持進度

        ## 3. 最後衝刺 (最後 4 小時)
        - 優先級判斷
        - 取捨策略
        - 演示準備

        ## 4. 常見陷阱
        列出 5-7 個常見錯誤和如何避免。

        ## 5. 時間管理技巧
        - 如何避免過度設計
        - 如何快速決策
        - 何時尋求幫助

        ## 6. 可用的快捷方式
        - 可以使用的工具
        - 可以複用的代碼
        - 可以簡化的功能

        ## 7. 演示準備清單
        - [ ] 檢查項 1
        - [ ] 檢查項 2
        ...

        實用、具體、可執行。
        """

        result = self.client.simple_chat(prompt)
        print(result)
        return result

    def generate_pitch_deck(self) -> str:
        """階段 6: AI 生成演示文稿"""

        prompt = f"""
        為以下項目創建 5 分鐘演示文稿大綱：

        **項目**: {self.project_name}
        **問題**: {self.problem}

        創建演示文稿結構：

        ## 幻燈片 1: 標題 (10秒)
        - 標題: [項目名稱]
        - 副標題: [一句話描述]
        - 團隊名稱

        ## 幻燈片 2: 問題陳述 (30秒)
        - 標題: "我們要解決的問題"
        - 要點:
          * 問題是什麼
          * 為什麼重要
          * 當前的痛點
        - 演講要點: [如何打動評委]

        ## 幻燈片 3: 解決方案 (45秒)
        - 標題: "我們的解決方案"
        - 要點:
          * 核心方案
          * 創新之處
          * 為什麼有效
        - 演講要點: [強調亮點]

        ## 幻燈片 4: 產品演示 (2分鐘)
        - 標題: "產品演示"
        - 演示流程:
          1. 步驟 1
          2. 步驟 2
          3. 步驟 3
        - 演講要點: [邊演示邊講解]

        ## 幻燈片 5: 技術亮點 (1分鐘)
        - 標題: "技術創新"
        - 要點:
          * 使用的關鍵技術
          * AI 如何應用
          * 技術優勢
        - 演講要點: [展示技術實力]

        ## 幻燈片 6: 商業價值 (30秒)
        - 標題: "影響力"
        - 要點:
          * 目標用戶
          * 市場規模
          * 未來發展
        - 演講要點: [描繪願景]

        ## 幻燈片 7: 總結 (10秒)
        - 標題: "謝謝"
        - 要點:
          * 項目名稱
          * 聯繫方式
          * GitHub 鏈接

        對於每張幻燈片，提供：
        - 視覺建議（用什麼圖片/圖表）
        - 演講稿要點
        - 注意事項

        讓演示吸引人、清晰、令人印象深刻！
        """

        result = self.presenter.chat(prompt)
        print(result)
        return result

    def save_results(self, results: dict, output_dir: str = "."):
        """
        保存所有結果到文件

        Args:
            results: 所有生成的結果
            output_dir: 輸出目錄
        """
        import os

        # 創建項目目錄
        project_dir = os.path.join(output_dir, self.project_name.replace(" ", "_"))
        os.makedirs(project_dir, exist_ok=True)

        # 保存各個文檔
        files = {
            "01_requirements.md": results['requirements'],
            "02_architecture.md": results['architecture'],
            "03_tasks.md": results['tasks'],
            "04_code_structure.md": results['code_structure'],
            "05_implementation_guide.md": results['implementation_guide'],
            "06_pitch_deck.md": results['pitch_deck']
        }

        for filename, content in files.items():
            filepath = os.path.join(project_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        # 創建主 README
        readme_content = f"""# {self.project_name}

## 問題陳述
{self.problem}

## 生成時間
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 文檔
- [需求分析](01_requirements.md)
- [架構設計](02_architecture.md)
- [任務列表](03_tasks.md)
- [代碼結構](04_code_structure.md)
- [實施指南](05_implementation_guide.md)
- [演示文稿](06_pitch_deck.md)

## 快速開始
查看 `05_implementation_guide.md` 開始開發。

祝你在 Hackathon 中取得好成績！🚀
"""
        with open(os.path.join(project_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"\n💾 所有文檔已保存到: {project_dir}")


def main():
    """示例用法"""

    # 示例 1: 快速啟動
    print("Hackathon 快速啟動示例\n")

    project = HackathonStarter(
        project_name="AI 醫療診斷助手",
        problem_statement="""
        設計一個 AI 系統幫助醫生快速診斷常見疾病。

        要求：
        1. 患者輸入症狀
        2. 系統分析可能的疾病
        3. 提供診斷建議和依據
        4. 參考醫學知識庫
        5. 生成診斷報告

        目標用戶：基層醫療機構的醫生
        """
    )

    # 運行完整流程
    results = project.run_quick_start()

    # 保存結果（可選）
    save_option = input("\n是否保存結果到文件？(y/n): ")
    if save_option.lower() == 'y':
        project.save_results(results, output_dir="./hackathon_projects")

    print("\n" + "=" * 70)
    print("✨ 完成！現在你有了完整的 Hackathon 項目規劃。")
    print("   開始編碼吧！祝你好運！🚀")
    print("=" * 70)


if __name__ == "__main__":
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未檢測到 OPENAI_API_KEY 環境變量")
        print("請設置 API key 後再運行此腳本\n")
        print("設置方法:")
        print("export OPENAI_API_KEY='your-api-key-here'")
    else:
        main()
