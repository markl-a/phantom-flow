"""
AI 輔助開發工具演示

展示如何使用 AI 來輔助日常開發工作：
- 代碼審查
- 調試
- 文檔生成
- 測試生成
- 代碼重構
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_automation_framework.tools.ai_dev_assistant import (
    AICodeReviewer,
    AIDebugAssistant,
    AIDocGenerator,
    AITestGenerator,
    AIRefactoringAssistant,
    quick_code_review,
    quick_debug,
    quick_doc_gen,
    quick_test_gen
)


# ==================== 示例代碼 ====================

SAMPLE_CODE_1 = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price'] * item['quantity']
    return total

def apply_discount(total, discount):
    return total - (total * discount / 100)

def process_order(items, discount_code):
    total = calculate_total(items)
    if discount_code == "SUMMER":
        discount = 20
    elif discount_code == "WINTER":
        discount = 15
    else:
        discount = 0
    final_total = apply_discount(total, discount)
    return final_total
"""

SAMPLE_CODE_2 = """
class UserManager:
    def __init__(self, database):
        self.db = database
        self.users = []

    def add_user(self, username, password):
        # 直接存儲密碼 (安全問題！)
        user = {
            'username': username,
            'password': password
        }
        self.users.append(user)
        self.db.save(user)

    def get_user(self, username):
        for user in self.users:
            if user['username'] == username:
                return user
        return None

    def delete_user(self, username):
        user = self.get_user(username)
        if user:
            self.users.remove(user)
            self.db.delete(user)
"""

SAMPLE_ERROR = """
File "script.py", line 15, in calculate_average
    return sum(numbers) / len(numbers)
ZeroDivisionError: division by zero
"""

SAMPLE_CODE_WITH_ERROR = """
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

def process_data(data):
    values = [item['value'] for item in data]
    avg = calculate_average(values)
    return avg
"""


# ==================== 演示函數 ====================

def demo_code_review():
    """演示代碼審查功能"""
    print("=" * 70)
    print("🔍 演示 1: AI 代碼審查")
    print("=" * 70)

    reviewer = AICodeReviewer()

    print("\n審查的代碼:")
    print("-" * 70)
    print(SAMPLE_CODE_1)
    print("-" * 70)

    print("\n🤖 AI 正在審查代碼...")
    result = reviewer.review_code(
        code=SAMPLE_CODE_1,
        language="python",
        context="這是一個電商訂單處理系統的一部分"
    )

    print("\n📊 審查結果:")
    print(result['review'])

    # 安全審查
    print("\n\n" + "=" * 70)
    print("🔒 安全性審查")
    print("=" * 70)

    print("\n審查的代碼:")
    print("-" * 70)
    print(SAMPLE_CODE_2)
    print("-" * 70)

    print("\n🤖 AI 正在進行安全審查...")
    security_result = reviewer.review_security(SAMPLE_CODE_2)

    print("\n🔒 安全審查結果:")
    print(security_result['findings'])


def demo_debug_assistant():
    """演示調試助手功能"""
    print("\n\n" + "=" * 70)
    print("🐛 演示 2: AI 調試助手")
    print("=" * 70)

    debugger = AIDebugAssistant()

    print("\n錯誤信息:")
    print("-" * 70)
    print(SAMPLE_ERROR)
    print("-" * 70)

    print("\n相關代碼:")
    print("-" * 70)
    print(SAMPLE_CODE_WITH_ERROR)
    print("-" * 70)

    print("\n🤖 AI 正在分析錯誤...")
    result = debugger.debug_error(
        error_message=SAMPLE_ERROR,
        code=SAMPLE_CODE_WITH_ERROR,
        context="處理用戶上傳的數據時出錯"
    )

    print("\n💡 解決方案:")
    print(result['solution'])

    # 代碼解釋
    print("\n\n" + "=" * 70)
    print("📖 代碼解釋")
    print("=" * 70)

    complex_code = """
    def fibonacci(n, memo={}):
        if n in memo:
            return memo[n]
        if n <= 2:
            return 1
        memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
        return memo[n]
    """

    print("\n要解釋的代碼:")
    print("-" * 70)
    print(complex_code)
    print("-" * 70)

    print("\n🤖 AI 正在解釋代碼...")
    explanation = debugger.explain_code(complex_code, detail_level="detailed")

    print("\n📝 代碼解釋:")
    print(explanation)


def demo_doc_generator():
    """演示文檔生成功能"""
    print("\n\n" + "=" * 70)
    print("📚 演示 3: AI 文檔生成")
    print("=" * 70)

    generator = AIDocGenerator()

    # 函數文檔
    undocumented_code = """
def fetch_user_data(user_id, include_history=False, timeout=30):
    if not user_id:
        raise ValueError("user_id is required")

    data = api_client.get(f"/users/{user_id}", timeout=timeout)

    if include_history:
        history = api_client.get(f"/users/{user_id}/history")
        data['history'] = history

    return data
"""

    print("\n未文檔化的代碼:")
    print("-" * 70)
    print(undocumented_code)
    print("-" * 70)

    print("\n🤖 AI 正在生成文檔...")
    documented = generator.generate_docstring(undocumented_code, style="google")

    print("\n📝 生成的文檔:")
    print(documented)

    # README 生成
    print("\n\n" + "=" * 70)
    print("📄 README 生成")
    print("=" * 70)

    print("\n🤖 AI 正在生成 README...")
    readme = generator.generate_readme(
        project_name="智能數據處理器",
        description="一個使用 AI 輔助的智能數據處理和分析工具",
        code_files=["processor.py", "analyzer.py", "visualizer.py"]
    )

    print("\n📄 生成的 README:")
    print(readme)


def demo_test_generator():
    """演示測試生成功能"""
    print("\n\n" + "=" * 70)
    print("🧪 演示 4: AI 測試生成")
    print("=" * 70)

    generator = AITestGenerator()

    test_code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, base, exponent):
        return base ** exponent
"""

    print("\n要測試的代碼:")
    print("-" * 70)
    print(test_code)
    print("-" * 70)

    print("\n🤖 AI 正在生成測試...")
    tests = generator.generate_unit_tests(test_code, framework="pytest")

    print("\n🧪 生成的測試:")
    print(tests)

    # 測試數據生成
    print("\n\n" + "=" * 70)
    print("📊 測試數據生成")
    print("=" * 70)

    print("\n🤖 AI 正在生成測試數據...")
    test_data = generator.generate_test_data(
        data_description="用戶註冊數據，包含用戶名、郵箱、年齡、性別",
        num_samples=10
    )

    print("\n📊 測試數據生成代碼:")
    print(test_data)


def demo_refactoring():
    """演示重構助手功能"""
    print("\n\n" + "=" * 70)
    print("♻️ 演示 5: AI 重構助手")
    print("=" * 70)

    assistant = AIRefactoringAssistant()

    messy_code = """
def process(data):
    result = []
    for item in data:
        if item['type'] == 'A':
            if item['status'] == 'active':
                if item['value'] > 100:
                    result.append({'id': item['id'], 'processed': True, 'value': item['value'] * 1.1})
                else:
                    result.append({'id': item['id'], 'processed': True, 'value': item['value']})
            else:
                result.append({'id': item['id'], 'processed': False, 'value': item['value']})
        elif item['type'] == 'B':
            if item['status'] == 'active':
                result.append({'id': item['id'], 'processed': True, 'value': item['value'] * 1.05})
            else:
                result.append({'id': item['id'], 'processed': False, 'value': item['value']})
    return result
"""

    print("\n待重構的代碼:")
    print("-" * 70)
    print(messy_code)
    print("-" * 70)

    print("\n🤖 AI 正在分析並提供重構建議...")
    refactoring = assistant.suggest_refactoring(
        code=messy_code,
        focus="readability"
    )

    print("\n♻️ 重構建議:")
    print(refactoring['suggestions'])

    # 設計模式應用
    print("\n\n" + "=" * 70)
    print("🎨 設計模式建議")
    print("=" * 70)

    rigid_code = """
class ReportGenerator:
    def generate_report(self, data, format):
        if format == 'pdf':
            # PDF 生成邏輯
            pass
        elif format == 'excel':
            # Excel 生成邏輯
            pass
        elif format == 'html':
            # HTML 生成邏輯
            pass
        else:
            raise ValueError("Unsupported format")
"""

    print("\n當前代碼:")
    print("-" * 70)
    print(rigid_code)
    print("-" * 70)

    print("\n🤖 AI 正在建議設計模式...")
    pattern_suggestion = assistant.apply_design_patterns(
        code=rigid_code,
        problem="代碼難以擴展，添加新格式需要修改現有代碼"
    )

    print("\n🎨 設計模式建議:")
    print(pattern_suggestion)


def demo_quick_functions():
    """演示便捷函數"""
    print("\n\n" + "=" * 70)
    print("⚡ 演示 6: 便捷函數（快速使用）")
    print("=" * 70)

    simple_code = """
def greet(name):
    return "Hello, " + name
"""

    print("\n1. 快速代碼審查:")
    print("-" * 70)
    review = quick_code_review(simple_code)
    print(review[:500] + "..." if len(review) > 500 else review)

    print("\n\n2. 快速調試:")
    print("-" * 70)
    solution = quick_debug(
        "NameError: name 'username' is not defined",
        "print(usrname)"  # 拼寫錯誤
    )
    print(solution[:500] + "..." if len(solution) > 500 else solution)

    print("\n\n3. 快速文檔生成:")
    print("-" * 70)
    documented = quick_doc_gen(simple_code)
    print(documented)

    print("\n\n4. 快速測試生成:")
    print("-" * 70)
    tests = quick_test_gen(simple_code)
    print(tests[:500] + "..." if len(tests) > 500 else tests)


def main():
    """
    主函數 - 運行所有演示
    """
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "AI 輔助開發工具完整演示" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")

    print("\n這個演示將展示如何使用 AI 來輔助日常開發工作。")
    print("\n包含的功能：")
    print("  1. 代碼審查（質量、安全性、性能）")
    print("  2. 調試助手（錯誤分析、代碼解釋）")
    print("  3. 文檔生成（Docstring、README、API文檔）")
    print("  4. 測試生成（單元測試、測試數據）")
    print("  5. 代碼重構（改進建議、設計模式）")
    print("  6. 便捷函數（快速使用）")

    print("\n" + "=" * 70)
    input("\n按 Enter 開始演示...")

    try:
        # 運行所有演示
        demo_code_review()

        print("\n" + "=" * 70)
        input("\n按 Enter 繼續下一個演示...")
        demo_debug_assistant()

        print("\n" + "=" * 70)
        input("\n按 Enter 繼續下一個演示...")
        demo_doc_generator()

        print("\n" + "=" * 70)
        input("\n按 Enter 繼續下一個演示...")
        demo_test_generator()

        print("\n" + "=" * 70)
        input("\n按 Enter 繼續下一個演示...")
        demo_refactoring()

        print("\n" + "=" * 70)
        input("\n按 Enter 查看便捷函數演示...")
        demo_quick_functions()

        # 總結
        print("\n\n" + "=" * 70)
        print("✅ 所有演示完成！")
        print("=" * 70)
        print("\n💡 提示：")
        print("  - 這些工具可以大大提高開發效率")
        print("  - 建議將它們集成到日常工作流程中")
        print("  - 可以根據需要自定義提示詞")
        print("  - 結合 IDE 使用效果更佳")
        print("\n📚 更多信息請查看文檔")

    except KeyboardInterrupt:
        print("\n\n⚠️ 演示被中斷")
    except Exception as e:
        print(f"\n\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 檢查環境
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("=" * 70)
        print("⚠️  警告: 未檢測到 OPENAI_API_KEY 環境變量")
        print("=" * 70)
        print("\n這個演示需要 OpenAI API key 才能運行。")
        print("\n設置方法:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\n或在 .env 文件中配置:")
        print("  OPENAI_API_KEY=your-api-key-here")
        print("=" * 70)
    else:
        main()
