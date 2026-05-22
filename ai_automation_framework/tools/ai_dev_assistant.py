"""
AI 開發助手工具

提供代碼審查、調試、文檔生成、測試生成等 AI 輔助開發功能
"""

from typing import List, Dict, Optional
from ..llm.base_client import BaseLLMClient
from ..llm import OpenAIClient


class AICodeReviewer:
    """AI 代碼審查工具"""

    def __init__(self, llm_client: BaseLLMClient = None):
        """
        初始化代碼審查工具

        Args:
            llm_client: LLM 客戶端，默認使用 OpenAI
        """
        self.client = llm_client or OpenAIClient()

    def review_code(self, code: str, language: str = "python", context: str = "") -> Dict:
        """
        審查代碼並提供改進建議

        Args:
            code: 要審查的代碼
            language: 編程語言
            context: 額外的上下文信息

        Returns:
            審查結果字典
        """
        prompt = f"""
        請作為資深軟件工程師審查以下 {language} 代碼：

        ```{language}
        {code}
        ```

        {f"上下文: {context}" if context else ""}

        請從以下方面進行審查：

        ## 1. 代碼質量 (1-10分)
        評分並說明原因

        ## 2. 潛在問題
        列出發現的問題（如有）：
        - 🐛 Bug
        - ⚠️ 安全隱患
        - ⚡ 性能問題
        - 💥 邊界情況未處理

        ## 3. 改進建議
        提供具體的改進建議（優先級排序）

        ## 4. 最佳實踐
        指出哪些地方可以遵循最佳實踐

        ## 5. 改進後的代碼
        提供改進後的完整代碼

        以清晰的 Markdown 格式輸出。
        """

        review = self.client.simple_chat(prompt)

        return {
            "original_code": code,
            "language": language,
            "review": review,
            "status": "completed"
        }

    def review_security(self, code: str, language: str = "python") -> Dict:
        """
        專注於安全性的代碼審查

        Args:
            code: 要審查的代碼
            language: 編程語言

        Returns:
            安全審查結果
        """
        prompt = f"""
        請進行安全性審查：

        ```{language}
        {code}
        ```

        檢查以下安全問題：

        ## OWASP Top 10 檢查
        1. 注入攻擊（SQL, NoSQL, Command, LDAP 等）
        2. 身份驗證失敗
        3. 敏感數據暴露
        4. XML 外部實體 (XXE)
        5. 訪問控制失效
        6. 安全配置錯誤
        7. 跨站腳本 (XSS)
        8. 不安全的反序列化
        9. 使用含有已知漏洞的組件
        10. 日誌和監控不足

        ## 其他安全問題
        - 硬編碼的密碼/密鑰
        - 不安全的加密
        - 競態條件
        - 路徑遍歷

        對於每個發現的問題：
        - 嚴重程度（嚴重/高/中/低）
        - 問題描述
        - 攻擊場景
        - 修復建議
        - 修復後的代碼

        以結構化的格式輸出。
        """

        review = self.client.simple_chat(prompt)

        return {
            "code": code,
            "review_type": "security",
            "findings": review,
            "status": "completed"
        }

    def review_performance(self, code: str, language: str = "python") -> Dict:
        """
        專注於性能的代碼審查

        Args:
            code: 要審查的代碼
            language: 編程語言

        Returns:
            性能審查結果
        """
        prompt = f"""
        請進行性能審查：

        ```{language}
        {code}
        ```

        分析：

        ## 1. 時間複雜度
        分析算法的時間複雜度

        ## 2. 空間複雜度
        分析內存使用情況

        ## 3. 性能瓶頸
        識別潛在的性能瓶頸：
        - 不必要的循環
        - 重複計算
        - 數據庫查詢效率
        - I/O 操作
        - 內存洩漏風險

        ## 4. 優化建議
        提供具體的優化方案（含代碼）

        ## 5. 預期性能提升
        估算優化後的性能改進

        以詳細的分析報告形式輸出。
        """

        review = self.client.simple_chat(prompt)

        return {
            "code": code,
            "review_type": "performance",
            "analysis": review,
            "status": "completed"
        }


class AIDebugAssistant:
    """AI 調試助手"""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.client = llm_client or OpenAIClient()

    def debug_error(
        self,
        error_message: str,
        code: str,
        stack_trace: str = "",
        context: str = ""
    ) -> Dict:
        """
        分析錯誤並提供解決方案

        Args:
            error_message: 錯誤信息
            code: 相關代碼
            stack_trace: 堆棧跟蹤
            context: 額外上下文

        Returns:
            調試結果
        """
        # 構建可選的堆棧跟蹤和上下文部分
        stack_trace_section = f"## 堆棧跟蹤\n```\n{stack_trace}\n```" if stack_trace else ""
        context_section = f"## 額外上下文\n{context}" if context else ""

        prompt = f"""
        幫助調試以下錯誤：

        ## 錯誤信息
        ```
        {error_message}
        ```

        ## 相關代碼
        ```python
        {code}
        ```

        {stack_trace_section}

        {context_section}

        請提供：

        ## 1. 錯誤分析
        - 錯誤類型
        - 發生原因
        - 問題根源

        ## 2. 解決方案
        提供 2-3 種可能的解決方案，按優先級排序。

        對於每個方案：
        - 解決方法描述
        - 修復後的完整代碼
        - 為什麼這個方案有效
        - 可能的副作用

        ## 3. 預防措施
        如何避免類似錯誤

        ## 4. 相關資源
        相關的文檔鏈接或學習資源

        以清晰、實用的格式輸出。
        """

        solution = self.client.simple_chat(prompt)

        return {
            "error": error_message,
            "code": code,
            "solution": solution,
            "status": "analyzed"
        }

    def explain_code(self, code: str, language: str = "python", detail_level: str = "medium") -> str:
        """
        解釋代碼的工作原理

        Args:
            code: 要解釋的代碼
            language: 編程語言
            detail_level: 詳細程度（simple/medium/detailed）

        Returns:
            代碼解釋
        """
        detail_instructions = {
            "simple": "用簡單的語言解釋，適合初學者",
            "medium": "提供中等詳細度的解釋，包含關鍵概念",
            "detailed": "提供詳細的逐行解釋，包含所有細節"
        }

        # Build optional detailed analysis section
        detailed_analysis = "## 逐行分析\n逐行解釋代碼" if detail_level == "detailed" else ""

        prompt = f"""
        請解釋以下 {language} 代碼：

        ```{language}
        {code}
        ```

        要求：{detail_instructions.get(detail_level, detail_instructions["medium"])}

        解釋格式：

        ## 概述
        用一段話說明代碼的整體作用

        ## 詳細解釋
        逐步解釋代碼的工作原理

        ## 關鍵概念
        解釋用到的重要概念

        ## 實際應用
        這種代碼在實際中的應用場景

        {detailed_analysis}

        清晰、易懂、有教育意義。
        """

        return self.client.simple_chat(prompt)

    def suggest_fixes(self, code: str, issue_description: str) -> Dict:
        """
        根據問題描述建議修復方案

        Args:
            code: 有問題的代碼
            issue_description: 問題描述

        Returns:
            修復建議
        """
        prompt = f"""
        代碼存在以下問題：

        **問題描述**：
        {issue_description}

        **當前代碼**：
        ```python
        {code}
        ```

        請提供：

        ## 1. 問題診斷
        分析為什麼會出現這個問題

        ## 2. 修復方案（至少 2 個）

        ### 方案 A：[方案名稱]
        - 優點
        - 缺點
        - 適用場景
        - 修復後的代碼

        ### 方案 B：[方案名稱]
        - 優點
        - 缺點
        - 適用場景
        - 修復後的代碼

        ## 3. 推薦方案
        說明推薦哪個方案及原因

        ## 4. 測試建議
        如何測試修復是否有效

        提供完整、可執行的代碼。
        """

        suggestions = self.client.simple_chat(prompt)

        return {
            "issue": issue_description,
            "original_code": code,
            "suggestions": suggestions,
            "status": "completed"
        }


class AIDocGenerator:
    """AI 文檔生成工具"""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.client = llm_client or OpenAIClient()

    def generate_docstring(self, code: str, style: str = "google") -> str:
        """
        為代碼生成文檔字符串

        Args:
            code: 函數或類的代碼
            style: 文檔風格（google/numpy/sphinx）

        Returns:
            帶文檔的代碼
        """
        style_examples = {
            "google": """
            Google 風格示例：
            def function(arg1, arg2):
                \"\"\"
                簡短描述

                詳細描述（可選）

                Args:
                    arg1 (type): 參數描述
                    arg2 (type): 參數描述

                Returns:
                    type: 返回值描述

                Raises:
                    ErrorType: 錯誤描述
                \"\"\"
            """,
            "numpy": """
            NumPy 風格示例：
            def function(arg1, arg2):
                \"\"\"
                簡短描述

                詳細描述

                Parameters
                ----------
                arg1 : type
                    參數描述
                arg2 : type
                    參數描述

                Returns
                -------
                type
                    返回值描述
                \"\"\"
            """,
            "sphinx": """
            Sphinx 風格示例：
            def function(arg1, arg2):
                \"\"\"
                簡短描述

                詳細描述

                :param arg1: 參數描述
                :type arg1: type
                :param arg2: 參數描述
                :type arg2: type
                :return: 返回值描述
                :rtype: type
                \"\"\"
            """
        }

        prompt = f"""
        為以下代碼生成 {style} 風格的文檔字符串：

        ```python
        {code}
        ```

        參考格式：
        {style_examples.get(style, style_examples["google"])}

        要求：
        1. 清楚描述功能
        2. 說明所有參數
        3. 描述返回值
        4. 註明可能的異常
        5. 提供使用示例（如果適用）

        只輸出完整的帶文檔的代碼，不需要額外解釋。
        """

        return self.client.simple_chat(prompt)

    def generate_readme(
        self,
        project_name: str,
        description: str,
        code_files: List[str] = None
    ) -> str:
        """
        生成項目 README

        Args:
            project_name: 項目名稱
            description: 項目描述
            code_files: 代碼文件列表（可選）

        Returns:
            README 內容
        """
        prompt = f"""
        為以下項目生成專業的 README.md：

        **項目名稱**: {project_name}
        **項目描述**: {description}

        {f"**主要文件**: {', '.join(code_files)}" if code_files else ""}

        生成包含以下部分的 README：

        # {project_name}

        ## 📝 簡介
        [項目的簡短介紹]

        ## ✨ 特性
        - 特性 1
        - 特性 2
        ...

        ## 🚀 快速開始

        ### 安裝
        ```bash
        # 安裝步驟
        ```

        ### 使用
        ```python
        # 基本使用示例
        ```

        ## 📖 文檔

        ### API 參考
        [主要 API 說明]

        ### 示例
        [更多示例]

        ## 🤝 貢獻
        [貢獻指南]

        ## 📄 許可證
        [許可證信息]

        ## 👥 作者
        [作者信息]

        以專業、清晰、吸引人的方式編寫。
        使用適當的 emoji 和格式。
        """

        return self.client.simple_chat(prompt)

    def generate_api_docs(self, code: str) -> str:
        """
        生成 API 文檔

        Args:
            code: 包含多個函數/類的代碼

        Returns:
            API 文檔
        """
        prompt = f"""
        為以下代碼生成完整的 API 文檔：

        ```python
        {code}
        ```

        生成格式：

        # API 文檔

        ## 概述
        [模塊簡介]

        ## 類

        ### ClassName
        [類描述]

        **初始化參數**:
        - `param1` (type): 描述
        - `param2` (type): 描述

        **方法**:

        #### method_name(param1, param2)
        [方法描述]

        **參數**:
        - `param1` (type): 描述
        - `param2` (type): 描述

        **返回值**:
        - type: 描述

        **示例**:
        ```python
        # 使用示例
        ```

        ## 函數

        ### function_name(param1, param2)
        [函數描述]

        ...

        以完整、專業的方式編寫文檔。
        """

        return self.client.simple_chat(prompt)


class AITestGenerator:
    """AI 測試生成工具"""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.client = llm_client or OpenAIClient()

    def generate_unit_tests(
        self,
        code: str,
        framework: str = "pytest"
    ) -> str:
        """
        生成單元測試

        Args:
            code: 要測試的代碼
            framework: 測試框架（pytest/unittest）

        Returns:
            測試代碼
        """
        prompt = f"""
        為以下代碼生成完整的 {framework} 單元測試：

        ```python
        {code}
        ```

        測試要求：

        ## 1. 測試覆蓋
        - 正常情況測試
        - 邊界情況測試
        - 異常情況測試
        - 邊緣情況測試

        ## 2. 測試組織
        - 使用清晰的測試名稱
        - 每個測試一個斷言重點
        - 使用 fixtures（如果需要）
        - 適當的 mock

        ## 3. 代碼質量
        - 遵循 {framework} 最佳實踐
        - 包含詳細註釋
        - 測試獨立性
        - 可重複運行

        生成完整、可執行的測試代碼。
        包含所有必要的導入和設置。
        """

        return self.client.simple_chat(prompt)

    def generate_integration_tests(self, components: List[str], description: str) -> str:
        """
        生成集成測試

        Args:
            components: 要測試的組件列表
            description: 系統描述

        Returns:
            集成測試代碼
        """
        prompt = f"""
        為以下系統生成集成測試：

        **系統描述**: {description}

        **組件**:
        {chr(10).join(f"- {comp}" for comp in components)}

        生成集成測試，包括：

        ## 1. 組件間交互測試
        測試組件之間的協作

        ## 2. 端到端測試
        測試完整的用戶流程

        ## 3. 數據流測試
        測試數據在系統中的流動

        ## 4. 錯誤處理測試
        測試系統的錯誤處理和恢復

        使用 pytest 框架。
        包含 fixtures、mocks 和清理代碼。
        """

        return self.client.simple_chat(prompt)

    def generate_test_data(self, data_description: str, num_samples: int = 10) -> str:
        """
        生成測試數據

        Args:
            data_description: 數據描述
            num_samples: 樣本數量

        Returns:
            測試數據生成代碼
        """
        prompt = f"""
        生成測試數據：

        **數據描述**: {data_description}
        **樣本數量**: {num_samples}

        生成 Python 代碼來創建測試數據：

        1. 包含正常數據
        2. 包含邊界情況數據
        3. 包含無效數據
        4. 數據要多樣化

        返回：
        - 數據生成函數
        - 使用示例
        - 數據驗證函數

        以完整的 Python 代碼形式輸出。
        """

        return self.client.simple_chat(prompt)


class AIRefactoringAssistant:
    """AI 重構助手"""

    def __init__(self, llm_client: BaseLLMClient = None):
        self.client = llm_client or OpenAIClient()

    def suggest_refactoring(self, code: str, focus: str = "general") -> Dict:
        """
        建議代碼重構

        Args:
            code: 要重構的代碼
            focus: 重構重點（general/performance/readability/maintainability）

        Returns:
            重構建議
        """
        focus_descriptions = {
            "general": "全面的代碼質量改進",
            "performance": "性能優化",
            "readability": "可讀性提升",
            "maintainability": "可維護性改進"
        }

        prompt = f"""
        請對以下代碼進行重構分析：

        ```python
        {code}
        ```

        **重構重點**: {focus_descriptions.get(focus, "全面改進")}

        分析並提供：

        ## 1. 當前問題
        列出代碼存在的問題（代碼異味）：
        - 重複代碼
        - 過長的函數
        - 過多的參數
        - 複雜的條件邏輯
        - 違反 SOLID 原則
        - 等等

        ## 2. 重構建議
        針對每個問題提供具體的重構方案：

        ### 建議 1: [重構名稱]
        - 問題描述
        - 重構方法
        - 預期效果
        - 重構後的代碼

        ### 建議 2: [重構名稱]
        ...

        ## 3. 優先級
        按重要性排序重構建議

        ## 4. 完整重構版本
        提供完全重構後的代碼

        ## 5. 重構前後對比
        - 代碼行數
        - 複雜度
        - 可讀性
        - 可測試性

        以清晰、實用的格式輸出。
        """

        suggestions = self.client.simple_chat(prompt)

        return {
            "original_code": code,
            "focus": focus,
            "suggestions": suggestions,
            "status": "completed"
        }

    def apply_design_patterns(self, code: str, problem: str) -> str:
        """
        建議並應用設計模式

        Args:
            code: 當前代碼
            problem: 要解決的問題

        Returns:
            應用設計模式後的代碼
        """
        prompt = f"""
        代碼重構 - 設計模式應用：

        **問題**: {problem}

        **當前代碼**:
        ```python
        {code}
        ```

        分析並提供：

        ## 1. 適用的設計模式
        推薦 2-3 個適合的設計模式：
        - 模式名稱
        - 為什麼適合
        - 解決什麼問題

        ## 2. 推薦方案
        選擇最合適的設計模式並說明原因

        ## 3. 實現代碼
        提供使用推薦設計模式的完整實現：
        - 清晰的類結構
        - 詳細的註釋
        - 使用示例

        ## 4. 優勢分析
        使用此設計模式的優勢：
        - 靈活性
        - 可擴展性
        - 可維護性
        - 可測試性

        以專業、教育性的方式呈現。
        """

        return self.client.simple_chat(prompt)


# 便捷函數

def quick_code_review(code: str, language: str = "python") -> str:
    """
    快速代碼審查

    Args:
        code: 代碼
        language: 語言

    Returns:
        審查結果
    """
    reviewer = AICodeReviewer()
    result = reviewer.review_code(code, language)
    return result['review']


def quick_debug(error: str, code: str) -> str:
    """
    快速調試

    Args:
        error: 錯誤信息
        code: 代碼

    Returns:
        解決方案
    """
    debugger = AIDebugAssistant()
    result = debugger.debug_error(error, code)
    return result['solution']


def quick_doc_gen(code: str, style: str = "google") -> str:
    """
    快速生成文檔

    Args:
        code: 代碼
        style: 文檔風格

    Returns:
        帶文檔的代碼
    """
    generator = AIDocGenerator()
    return generator.generate_docstring(code, style)


def quick_test_gen(code: str, framework: str = "pytest") -> str:
    """
    快速生成測試

    Args:
        code: 代碼
        framework: 測試框架

    Returns:
        測試代碼
    """
    generator = AITestGenerator()
    return generator.generate_unit_tests(code, framework)
