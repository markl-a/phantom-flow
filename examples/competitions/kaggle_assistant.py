"""
Kaggle 競賽 AI 助手

這個模塊提供完整的 Kaggle 競賽輔助功能，
使用 AI 加速數據探索、特徵工程、模型選擇和優化。
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_automation_framework.llm import OpenAIClient
from ai_automation_framework.agents import BaseAgent
import pandas as pd
import json
from pathlib import Path


class KaggleDataAnalyst:
    """Kaggle 數據分析助手 - 使用 AI 輔助分析"""

    def __init__(self, api_key: str = None):
        """
        初始化 Kaggle 助手

        Args:
            api_key: OpenAI API key（可選，從環境變量讀取）
        """
        self.client = OpenAIClient(api_key=api_key)
        self.agent = BaseAgent(
            name="DataScientist",
            system_message="""你是一個經驗豐富的 Kaggle 數據科學家。
            你擅長：
            1. 數據探索和可視化
            2. 特徵工程
            3. 模型選擇和優化
            4. 避免過擬合
            5. 集成學習策略

            你的回答要實用、具體，並提供可執行的代碼。
            """
        )

    def analyze_dataset(self, df: pd.DataFrame, target_column: str = None) -> dict:
        """
        全面分析數據集

        Args:
            df: 數據框
            target_column: 目標列名

        Returns:
            包含分析結果和建議的字典
        """
        print("🔍 開始數據分析...")

        # 基礎統計
        summary = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing": df.isnull().sum().to_dict(),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        }

        # 數值列統計
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            summary["numeric_stats"] = df[numeric_cols].describe().to_dict()

        # 分類列統計
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            summary["categorical_stats"] = {
                col: {
                    "unique": df[col].nunique(),
                    "top_values": df[col].value_counts().head(5).to_dict()
                }
                for col in categorical_cols
            }

        # 目標變量分析
        if target_column and target_column in df.columns:
            summary["target_info"] = {
                "dtype": str(df[target_column].dtype),
                "nunique": df[target_column].nunique(),
                "distribution": df[target_column].value_counts().head(10).to_dict()
            }

        # AI 分析
        print("🤖 使用 AI 深度分析...")
        ai_analysis = self._get_ai_analysis(summary, target_column)

        return {
            "summary": summary,
            "ai_insights": ai_analysis
        }

    def _get_ai_analysis(self, summary: dict, target_column: str = None) -> str:
        """使用 AI 分析數據集特徵"""

        prompt = f"""
        請分析以下 Kaggle 數據集：

        **基本信息**：
        - 形狀：{summary['shape']}
        - 列數：{len(summary['columns'])}
        - 內存使用：{summary['memory_usage']}

        **缺失值**：
        {json.dumps(summary['missing'], indent=2)}

        **數據類型**：
        {json.dumps(summary['dtypes'], indent=2)}

        {f"**目標變量**: {target_column}" if target_column else ""}
        {f"分布: {summary.get('target_info', {})}" if target_column else ""}

        請提供：
        1. **數據質量評估**（0-10分）及原因
        2. **主要問題**（列出 3-5 個）
        3. **處理建議**（針對每個問題）
        4. **下一步行動**（優先級排序）

        以清晰的 Markdown 格式回答。
        """

        return self.agent.chat(prompt)

    def suggest_features(self, df: pd.DataFrame, target: str, top_n: int = 10) -> str:
        """
        AI 建議特徵工程

        Args:
            df: 數據框
            target: 目標列
            top_n: 返回建議數量

        Returns:
            特徵工程建議（含代碼）
        """
        print(f"💡 生成 {top_n} 個特徵工程建議...")

        # 準備列信息
        column_info = []
        for col in df.columns:
            if col != target:
                info = {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "nunique": df[col].nunique(),
                    "missing": df[col].isnull().sum(),
                    "sample": df[col].dropna().head(3).tolist() if not df[col].isnull().all() else []
                }
                column_info.append(info)

        prompt = f"""
        Kaggle 特徵工程任務：

        **目標變量**: {target}
        **類型**: {df[target].dtype}

        **現有特徵**：
        {json.dumps(column_info[:20], indent=2)}  # 限制長度

        請提供 {top_n} 個最有潛力的特徵工程建議：

        對於每個建議，提供：
        1. **特徵名稱**
        2. **創建原理**（為什麼有用）
        3. **Python 代碼**（可直接執行）
        4. **預期效果**

        優先考慮：
        - 特徵交互
        - 聚合特徵
        - 時間特徵（如果有）
        - 編碼方法

        以 Python 代碼塊的形式輸出，包含詳細註釋。
        """

        return self.agent.chat(prompt)

    def suggest_models(self, df: pd.DataFrame, target: str, problem_type: str = None) -> str:
        """
        AI 建議模型選擇

        Args:
            df: 數據框
            target: 目標列
            problem_type: 問題類型（'classification' 或 'regression'）

        Returns:
            模型建議和代碼
        """
        print("🎯 分析問題並推薦模型...")

        # 自動判斷問題類型
        if problem_type is None:
            if df[target].dtype in ['int64', 'float64'] and df[target].nunique() > 20:
                problem_type = 'regression'
            else:
                problem_type = 'classification'

        prompt = f"""
        Kaggle 模型選擇任務：

        **問題類型**: {problem_type}
        **數據集大小**: {df.shape}
        **特徵數**: {df.shape[1] - 1}
        **目標變量唯一值**: {df[target].nunique()}

        請推薦 5 個適合的模型，按優先級排序：

        對於每個模型：
        1. **模型名稱**
        2. **為什麼適合**（3個理由）
        3. **優點和缺點**
        4. **基礎實現代碼**（含參數）
        5. **超參數調優建議**

        包括：
        - 傳統模型（如 XGBoost, LightGBM）
        - 神經網絡（如果適用）
        - 集成方法

        提供完整的 Python 代碼示例。
        """

        return self.agent.chat(prompt)

    def debug_error(self, error_message: str, code: str, context: str = "") -> str:
        """
        AI 輔助調試錯誤

        Args:
            error_message: 錯誤信息
            code: 出錯的代碼
            context: 額外上下文

        Returns:
            解決方案
        """
        print("🔧 AI 正在分析錯誤...")

        prompt = f"""
        Kaggle 競賽中遇到錯誤，請幫助解決：

        **錯誤信息**：
        ```
        {error_message}
        ```

        **相關代碼**：
        ```python
        {code}
        ```

        **額外上下文**：
        {context if context else "無"}

        請提供：
        1. **錯誤原因**（詳細解釋）
        2. **修復代碼**（完整可用）
        3. **預防措施**（避免類似錯誤）
        4. **最佳實踐**（相關建議）

        以清晰的格式回答，代碼要完整可執行。
        """

        return self.agent.chat(prompt)

    def optimize_score(self, current_score: float, approach: str, leaderboard_top: float) -> str:
        """
        AI 建議提升分數

        Args:
            current_score: 當前分數
            approach: 當前方法描述
            leaderboard_top: 排行榜頂部分數

        Returns:
            優化建議
        """
        print("📈 生成分數提升建議...")

        gap = leaderboard_top - current_score
        gap_percentage = (gap / leaderboard_top) * 100

        prompt = f"""
        Kaggle 競賽分數優化：

        **當前狀況**：
        - 我的分數：{current_score}
        - 排行榜第一：{leaderboard_top}
        - 差距：{gap:.4f} ({gap_percentage:.2f}%)

        **當前方法**：
        {approach}

        請提供提升計劃：

        **階段 1：快速提升（1-2天）**
        - 可以立即嘗試的 3-5 個方法
        - 預期提升幅度

        **階段 2：穩定優化（3-5天）**
        - 更深入的優化方向
        - 需要的時間投入

        **階段 3：突破瓶頸（如果需要）**
        - 創新性方法
        - 高級技巧

        每個建議包含：
        - 具體行動
        - 實施難度（簡單/中等/困難）
        - 預期效果
        - 代碼示例（如果適用）

        優先考慮性價比高的方法。
        """

        return self.agent.chat(prompt)

    def generate_submission_code(self, model_description: str) -> str:
        """
        AI 生成提交代碼模板

        Args:
            model_description: 模型描述

        Returns:
            提交代碼
        """
        print("📝 生成提交代碼...")

        prompt = f"""
        為以下 Kaggle 模型生成完整的提交代碼：

        **模型描述**：
        {model_description}

        生成包含以下部分的完整代碼：

        1. **導入庫**
        2. **數據加載**
        3. **預處理**（與訓練時一致）
        4. **模型加載**
        5. **預測**
        6. **生成提交文件**（正確格式）
        7. **驗證**（檢查格式、範圍等）

        代碼要求：
        - 完整可執行
        - 包含錯誤處理
        - 有詳細註釋
        - 符合 Kaggle 提交要求

        以 Python 代碼塊形式輸出。
        """

        return self.agent.chat(prompt)


class KaggleWorkflow:
    """完整的 Kaggle 工作流程助手"""

    def __init__(self):
        self.analyst = KaggleDataAnalyst()

    def quick_start(self, train_path: str, test_path: str, target: str):
        """
        Kaggle 競賽快速啟動

        Args:
            train_path: 訓練數據路徑
            test_path: 測試數據路徑
            target: 目標列名
        """
        print("=" * 60)
        print("🚀 Kaggle 競賽快速啟動")
        print("=" * 60)

        # 加載數據
        print("\n📂 加載數據...")
        try:
            # Validate file paths exist
            if not os.path.exists(train_path):
                raise FileNotFoundError(f"Training file not found: {train_path}")
            if not os.path.exists(test_path):
                raise FileNotFoundError(f"Test file not found: {test_path}")

            # Load CSV files
            train_df = pd.read_csv(train_path)
            test_df = pd.read_csv(test_path)

            # Validate loaded data
            if train_df.empty:
                raise ValueError(f"Training file is empty: {train_path}")
            if test_df.empty:
                raise ValueError(f"Test file is empty: {test_path}")

            print(f"訓練集: {train_df.shape}, 測試集: {test_df.shape}")
        except FileNotFoundError as e:
            print(f"❌ 文件錯誤: {e}")
            return None
        except pd.errors.EmptyDataError:
            print(f"❌ CSV 文件為空")
            return None
        except pd.errors.ParserError as e:
            print(f"❌ CSV 解析錯誤: {e}")
            return None
        except Exception as e:
            print(f"❌ 加載數據時出錯: {e}")
            return None

        # Validate target column exists
        if target not in train_df.columns:
            print(f"❌ 目標列 '{target}' 不存在於訓練集中")
            print(f"可用列: {', '.join(train_df.columns)}")
            return None

        # 階段 1: 數據分析
        print("\n" + "=" * 60)
        print("階段 1: 數據探索和分析")
        print("=" * 60)
        try:
            analysis = self.analyst.analyze_dataset(train_df, target)
            print("\n📊 AI 分析結果:")
            print(analysis['ai_insights'])
        except Exception as e:
            print(f"❌ 數據分析錯誤: {e}")
            return None

        # 階段 2: 特徵工程建議
        print("\n" + "=" * 60)
        print("階段 2: 特徵工程建議")
        print("=" * 60)
        try:
            features = self.analyst.suggest_features(train_df, target, top_n=5)
            print("\n💡 特徵建議:")
            print(features)
        except Exception as e:
            print(f"❌ 特徵建議錯誤: {e}")
            features = "特徵建議生成失敗"

        # 階段 3: 模型建議
        print("\n" + "=" * 60)
        print("階段 3: 模型選擇")
        print("=" * 60)
        try:
            models = self.analyst.suggest_models(train_df, target)
            print("\n🎯 模型建議:")
            print(models)
        except Exception as e:
            print(f"❌ 模型建議錯誤: {e}")
            models = "模型建議生成失敗"

        # 總結
        print("\n" + "=" * 60)
        print("✅ 快速啟動完成！")
        print("=" * 60)
        print("\n下一步：")
        print("1. 實施建議的特徵工程")
        print("2. 訓練推薦的模型")
        print("3. 驗證和優化")
        print("4. 生成提交文件")

        return {
            "analysis": analysis,
            "features": features,
            "models": models
        }


def main():
    """
    示例用法
    """
    print("Kaggle AI 助手示例\n")

    # 方法 1: 分析現有數據
    print("方法 1: 分析數據集")
    print("-" * 40)

    # 創建示例數據
    sample_data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5] * 20,
        'feature2': ['A', 'B', 'C', 'D', 'E'] * 20,
        'feature3': [10.5, 20.3, 30.1, 40.8, 50.2] * 20,
        'target': [0, 1, 0, 1, 0] * 20
    })

    analyst = KaggleDataAnalyst()

    # 分析數據
    analysis = analyst.analyze_dataset(sample_data, target_column='target')
    print("\nAI 分析:")
    print(analysis['ai_insights'])

    # 方法 2: 獲取特徵建議
    print("\n\n方法 2: 特徵工程建議")
    print("-" * 40)
    features = analyst.suggest_features(sample_data, 'target', top_n=3)
    print(features)

    # 方法 3: 調試幫助
    print("\n\n方法 3: 調試錯誤")
    print("-" * 40)
    solution = analyst.debug_error(
        error_message="ValueError: Input contains NaN",
        code="model.fit(X_train, y_train)",
        context="使用 XGBoost 訓練模型時出錯"
    )
    print(solution)

    # 方法 4: 完整工作流（如果有真實數據）
    # workflow = KaggleWorkflow()
    # result = workflow.quick_start('train.csv', 'test.csv', 'target')


if __name__ == "__main__":
    # 檢查是否配置了 API key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  警告: 未檢測到 OPENAI_API_KEY 環境變量")
        print("請設置 API key 後再運行此腳本")
        print("\n設置方法:")
        print("export OPENAI_API_KEY='your-api-key-here'")
    else:
        main()
