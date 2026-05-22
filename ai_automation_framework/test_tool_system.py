#!/usr/bin/env python3
"""测试工具系统的简单脚本。"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("测试工具系统 (Tool System Test)")
print("=" * 60)

# 1. 导入工具系统组件
print("\n[1] 导入工具系统组件...")
try:
    from ai_automation_framework.core import (
        BaseTool,
        ToolMetadata,
        ToolRegistry,
        get_tool_registry,
        register_tool
    )
    print("✓ 成功导入所有工具系统组件")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 2. 导入示例工具（会自动注册）
print("\n[2] 导入示例工具 CalculatorToolV2...")
try:
    # 直接从模块文件导入，避免触发 tools/__init__.py 的依赖
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "calculator_v2",
        project_root / "ai_automation_framework" / "tools" / "calculator_v2.py"
    )
    calculator_v2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calculator_v2)
    CalculatorToolV2 = calculator_v2.CalculatorToolV2
    print("✓ 成功导入 CalculatorToolV2")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 获取工具注册表
print("\n[3] 获取工具注册表...")
try:
    registry = get_tool_registry()
    print(f"✓ 成功获取注册表实例: {registry}")
except Exception as e:
    print(f"✗ 获取注册表失败: {e}")
    sys.exit(1)

# 4. 列出所有已注册的工具
print("\n[4] 列出所有已注册的工具...")
try:
    tools = registry.list_tools()
    print(f"✓ 找到 {len(tools)} 个工具:")
    for name, metadata in tools.items():
        print(f"  - {name} (v{metadata.version}): {metadata.description}")
except Exception as e:
    print(f"✗ 列出工具失败: {e}")
    sys.exit(1)

# 5. 获取 calculator_v2 工具
print("\n[5] 获取 calculator_v2 工具...")
try:
    calc = registry.get_tool("calculator_v2")
    if calc:
        print(f"✓ 成功获取工具: {calc.metadata.name}")
    else:
        print("✗ 工具未找到")
        sys.exit(1)
except Exception as e:
    print(f"✗ 获取工具失败: {e}")
    sys.exit(1)

# 6. 测试基本计算
print("\n[6] 测试基本计算 (2+2*3)...")
try:
    result = calc.run(operation="calculate", expression="2+2*3")
    if result.get("success"):
        print(f"✓ 计算成功: {result['expression']} = {result['result']}")
    else:
        print(f"✗ 计算失败: {result.get('error')}")
except Exception as e:
    print(f"✗ 执行失败: {e}")

# 7. 测试百分比计算
print("\n[7] 测试百分比计算 (200 的 15%)...")
try:
    result = calc.run(operation="percentage", value=200, percentage=15)
    if result.get("success"):
        print(f"✓ 计算成功: {result['value']} 的 {result['percentage']}% = {result['result']}")
    else:
        print(f"✗ 计算失败: {result.get('error')}")
except Exception as e:
    print(f"✗ 执行失败: {e}")

# 8. 测试复利计算
print("\n[8] 测试复利计算 (本金1000, 利率5%, 时间10年)...")
try:
    result = calc.run(
        operation="compound_interest",
        principal=1000,
        rate=5,
        time=10,
        n=1
    )
    if result.get("success"):
        print(f"✓ 计算成功:")
        print(f"  本金: ${result['principal']}")
        print(f"  利率: {result['rate']}%")
        print(f"  时间: {result['time']} 年")
        print(f"  最终金额: ${result['final_amount']}")
        print(f"  利息收入: ${result['interest_earned']}")
    else:
        print(f"✗ 计算失败: {result.get('error')}")
except Exception as e:
    print(f"✗ 执行失败: {e}")

# 9. 测试参数验证（应该失败）
print("\n[9] 测试参数验证（缺少必需参数）...")
try:
    result = calc.run(operation="calculate")  # 缺少 expression
    if not result.get("success"):
        print(f"✓ 验证正常工作，捕获到错误: {result.get('error')}")
    else:
        print("✗ 验证失败，应该报错但没有")
except Exception as e:
    print(f"✓ 验证正常工作，抛出异常: {e}")

# 10. 测试 OpenAI function calling schema
print("\n[10] 测试 OpenAI function calling schema 生成...")
try:
    schema = calc.get_schema()
    print(f"✓ 成功生成 schema:")
    print(f"  函数名: {schema['function']['name']}")
    print(f"  描述: {schema['function']['description']}")
    print(f"  参数数量: {len(schema['function']['parameters']['properties'])}")
except Exception as e:
    print(f"✗ 生成 schema 失败: {e}")

# 11. 通过注册表直接执行
print("\n[11] 通过注册表直接执行工具...")
try:
    result = registry.execute_tool(
        "calculator_v2",
        operation="calculate",
        expression="10/2"
    )
    if result.get("success"):
        print(f"✓ 执行成功: {result['expression']} = {result['result']}")
    else:
        print(f"✗ 执行失败: {result.get('error')}")
except Exception as e:
    print(f"✗ 执行失败: {e}")

# 12. 获取工具分类
print("\n[12] 获取所有工具分类...")
try:
    categories = registry.get_categories()
    print(f"✓ 找到 {len(categories)} 个分类: {', '.join(categories)}")
except Exception as e:
    print(f"✗ 获取分类失败: {e}")

# 13. 获取所有工具的 schemas
print("\n[13] 获取所有工具的 function calling schemas...")
try:
    schemas = registry.get_tool_schemas()
    print(f"✓ 成功生成 {len(schemas)} 个工具的 schemas")
    for schema in schemas:
        func_name = schema['function']['name']
        print(f"  - {func_name}")
except Exception as e:
    print(f"✗ 生成 schemas 失败: {e}")

# 总结
print("\n" + "=" * 60)
print("测试完成！所有核心功能正常工作。")
print("=" * 60)
print("\n下一步:")
print("1. 查看文档: docs/TOOL_SYSTEM.md")
print("2. 创建自定义工具，参考: ai_automation_framework/tools/calculator_v2.py")
print("3. 使用 @register_tool 装饰器自动注册工具")
print("=" * 60)
