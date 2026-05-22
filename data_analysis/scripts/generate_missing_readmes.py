"""批量生成Kaggle解決方案的README文檔

此腳本為缺少README的Kaggle解決方案自動生成標準化的文檔。
"""

import json
import re
from pathlib import Path
from typing import Dict, List


def get_solution_info(solution_path: Path) -> Dict[str, str]:
    """從solution.py提取信息"""
    solution_file = solution_path / "solution.py"

    if not solution_file.exists():
        return {}

    try:
        content = solution_file.read_text(encoding='utf-8')

        # 嘗試提取docstring
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        description = docstring_match.group(1).strip() if docstring_match else ""

        return {
            'description': description,
            'has_sklearn': 'sklearn' in content,
            'has_tensorflow': 'tensorflow' in content or 'keras' in content,
            'has_pytorch': 'torch' in content,
            'has_xgboost': 'xgboost' in content,
            'has_lightgbm': 'lightgbm' in content,
        }
    except Exception as e:
        print(f"Warning: Could not read {solution_file}: {e}")
        return {}


def generate_readme(category: str, solution_name: str, solution_path: Path) -> str:
    """生成README內容"""

    # 從solution獲取信息
    info = get_solution_info(solution_path)

    # 解析名稱
    # 例如: "01_titanic_survival" -> "01", "Titanic Survival Prediction"
    match = re.match(r'(\d+)_(.*)', solution_name)
    if match:
        number, name_part = match.groups()
        title = name_part.replace('_', ' ').title()
    else:
        number = "?"
        title = solution_name.replace('_', ' ').title()

    # 分類名稱映射
    category_names = {
        '01_structured_data': '結構化數據與分類',
        '02_time_series': '時間序列分析',
        '03_nlp': '自然語言處理',
        '04_recommendation': '推薦系統',
        '05_computer_vision': '計算機視覺',
        '06_clustering': '聚類與無監督學習',
        '07_special_domains': '特殊領域應用',
        '08_deep_learning': '深度學習',
        '09_audio_signal': '音訊與信號處理',
        '10_anomaly_detection': '異常檢測',
        '11_graph_networks': '圖神經網絡',
        '12_geospatial': '地理空間分析',
        '13_feature_engineering': '特徵工程',
        '14_ensemble_methods': '集成學習方法',
        '15_bayesian_methods': '貝葉斯方法',
        '16_optimization': '優化算法',
        '17_multimodal': '多模態學習',
    }

    category_display = category_names.get(category, category.replace('_', ' ').title())

    # 確定使用的技術棧
    tech_stack = []
    if info.get('has_sklearn'):
        tech_stack.append('Scikit-learn')
    if info.get('has_tensorflow'):
        tech_stack.append('TensorFlow/Keras')
    if info.get('has_pytorch'):
        tech_stack.append('PyTorch')
    if info.get('has_xgboost'):
        tech_stack.append('XGBoost')
    if info.get('has_lightgbm'):
        tech_stack.append('LightGBM')

    if not tech_stack:
        tech_stack = ['Python', 'Pandas', 'NumPy']

    # 生成README內容
    readme_content = f"""# {title}

**分類**: {category_display}
**難度**: 中級
**技術棧**: {', '.join(tech_stack)}

## 📊 專案描述

{info.get('description') or f'這是一個關於{title}的機器學習解決方案，展示如何處理{category_display}相關的問題。'}

## 🎯 目標

- 理解問題的業務背景和數據特徵
- 實現完整的數據預處理流程
- 訓練和優化機器學習模型
- 評估模型性能並生成預測結果

## 📁 文件結構

```
{solution_name}/
├── solution.py          # 主要解決方案代碼
├── README.md           # 本文檔
└── requirements.txt    # Python依賴（如需要）
```

## 🚀 使用方法

### 運行解決方案

```bash
# 直接運行
python solution.py

# 或從專案根目錄運行
python kaggle_solutions/{category}/{solution_name}/solution.py
```

### 自定義參數

打開 `solution.py` 並修改相關參數來調整模型配置。

## 📈 方法論

### 1. 數據探索
- 加載數據並檢查基本統計信息
- 可視化數據分佈和特徵關係
- 識別缺失值和異常值

### 2. 特徵工程
- 處理缺失值
- 編碼類別特徵
- 特徵縮放和標準化
- 創建新特徵（如需要）

### 3. 模型訓練
- 選擇合適的算法
- 訓練基準模型
- 超參數調優
- 交叉驗證

### 4. 模型評估
- 計算性能指標
- 分析預測錯誤
- 可視化結果

## 🔧 技術要點

### 使用的算法

- **主要算法**: 根據問題特性選擇
- **評估指標**: 準確率、F1分數、ROC-AUC等
- **優化方法**: 網格搜索、貝葉斯優化等

### 關鍵技術

{chr(10).join(f'- {tech}' for tech in tech_stack)}

## 📊 預期結果

運行此解決方案後，您將獲得:
- 訓練好的模型
- 預測結果
- 性能評估報告
- 可視化圖表（如適用）

## 💡 改進建議

- 嘗試不同的特徵工程方法
- 使用更複雜的模型（如集成方法）
- 進行更詳細的錯誤分析
- 優化超參數配置

## 📚 相關資源

- [Kaggle競賽列表](https://www.kaggle.com/competitions)
- [Scikit-learn文檔](https://scikit-learn.org/)
- [專案主README](../../README.md)

## 📝 注意事項

- 確保已安裝所需的Python包
- 數據文件路徑可能需要根據實際情況調整
- 某些解決方案可能需要GPU加速

---

**作者**: Data Analysis with Chatbots Team
**最後更新**: 2025-01-18
**專案**: [Data-Analysis-with-Chatbots](https://github.com/markl-a/Data-Analysis-with-Chatbots)
"""

    return readme_content


def process_batch(missing_items: List[Dict], batch_size: int = 50) -> List[List[Dict]]:
    """將任務分批處理"""
    batches = []
    for i in range(0, len(missing_items), batch_size):
        batches.append(missing_items[i:i+batch_size])
    return batches


def main():
    """主函數"""
    # 讀取缺失列表
    with open('/tmp/missing_readmes.json', 'r') as f:
        missing_items = json.load(f)

    print(f"需要創建 {len(missing_items)} 個README文檔")
    print("=" * 60)

    # 分批處理（每批50個）
    batches = process_batch(missing_items, batch_size=50)

    for batch_idx, batch in enumerate(batches, 1):
        print(f"\n處理第 {batch_idx}/{len(batches)} 批 ({len(batch)} 個)...")

        created_count = 0
        for item in batch:
            category = item['category']
            name = item['name']
            path = Path(item['path'])

            readme_path = path / "README.md"

            if not readme_path.exists():
                try:
                    content = generate_readme(category, name, path)
                    readme_path.write_text(content, encoding='utf-8')
                    created_count += 1
                    print(f"  ✓ {category}/{name}")
                except Exception as e:
                    print(f"  ✗ {category}/{name}: {e}")

        print(f"\n第{batch_idx}批完成: 創建了 {created_count}/{len(batch)} 個README")

        # 返回批次信息以便調用者決定是否commit
        yield batch_idx, len(batches), created_count, batch


if __name__ == '__main__':
    for batch_info in main():
        pass

    print("\n" + "=" * 60)
    print("所有README創建完成！")
