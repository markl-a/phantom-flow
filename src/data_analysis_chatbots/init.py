"""專案初始化工具

此模塊用於初始化專案目錄結構,確保所有必要的目錄和文件都存在。
"""

from pathlib import Path
from typing import List, Optional

from loguru import logger


def get_project_root() -> Path:
    """獲取專案根目錄

    Returns:
        Path: 專案根目錄路徑
    """
    # 從當前文件位置向上查找專案根目錄
    current_file = Path(__file__).resolve()
    # src/data_analysis_chatbots/init.py -> 向上3層到專案根目錄
    project_root = current_file.parent.parent.parent
    return project_root


def ensure_dir(directory: Path, description: str = "") -> None:
    """確保目錄存在,如果不存在則創建

    Args:
        directory: 目錄路徑
        description: 目錄描述(用於日誌)
    """
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        desc_str = f" ({description})" if description else ""
        logger.info(f"✓ 創建目錄: {directory}{desc_str}")
    else:
        logger.debug(f"目錄已存在: {directory}")


def create_gitkeep(directory: Path) -> None:
    """在目錄中創建.gitkeep文件以確保空目錄被git追蹤

    Args:
        directory: 目錄路徑
    """
    gitkeep_file = directory / '.gitkeep'
    if not gitkeep_file.exists():
        gitkeep_file.touch()
        logger.debug(f"創建 .gitkeep: {gitkeep_file}")


def initialize_project(verbose: bool = True, create_examples: bool = False) -> None:
    """初始化專案目錄結構

    創建所有必要的目錄,包括:
    - data/ (原始數據、處理後數據、輸出)
    - models/ (保存的模型)
    - logs/ (日誌文件)
    - outputs/ (分析結果)

    Args:
        verbose: 是否顯示詳細日誌
        create_examples: 是否創建示例文件
    """
    if verbose:
        logger.info("開始初始化專案目錄結構...")

    root = get_project_root()

    # 定義需要創建的目錄結構
    directories = [
        (root / 'data', "數據根目錄"),
        (root / 'data' / 'raw', "原始數據"),
        (root / 'data' / 'processed', "處理後的數據"),
        (root / 'data' / 'outputs', "分析輸出結果"),
        (root / 'models', "保存的模型文件"),
        (root / 'logs', "日誌文件"),
        (root / 'outputs', "通用輸出目錄"),
        (root / 'outputs' / 'plots', "圖表輸出"),
        (root / 'outputs' / 'reports', "報告輸出"),
    ]

    # 創建所有目錄
    for dir_path, description in directories:
        ensure_dir(dir_path, description)
        # 為空目錄創建.gitkeep
        create_gitkeep(dir_path)

    # 創建README文件在關鍵目錄
    if create_examples:
        _create_directory_readmes(root)

    if verbose:
        logger.success(f"✓ 專案目錄結構初始化完成!")
        logger.info(f"專案根目錄: {root}")
        logger.info("您現在可以開始使用數據分析工具了。")


def _create_directory_readmes(root: Path) -> None:
    """在關鍵目錄創建README文件

    Args:
        root: 專案根目錄
    """
    # data/README.md
    data_readme = root / 'data' / 'README.md'
    if not data_readme.exists():
        data_readme.write_text("""# 數據目錄

此目錄用於存儲專案使用的數據文件。

## 目錄結構

- `raw/` - 原始數據文件(從Kaggle或其他來源下載)
- `processed/` - 經過清洗和預處理的數據
- `outputs/` - 分析結果和導出的數據

## 使用方法

1. 下載數據集:
```bash
python -m data_analysis_chatbots.data_downloader --all
```

2. 數據會自動保存到相應的子目錄中

## 注意事項

- 原始數據文件較大,已添加到.gitignore
- 請勿手動修改raw/目錄中的文件
- processed/目錄中的文件可以重新生成
""")
        logger.info(f"創建說明文件: {data_readme}")

    # models/README.md
    models_readme = root / 'models' / 'README.md'
    if not models_readme.exists():
        models_readme.write_text("""# 模型目錄

此目錄用於存儲訓練好的機器學習模型。

## 文件格式

- `.pkl` - Scikit-learn模型(使用joblib保存)
- `.h5` - Keras/TensorFlow模型
- `.pt` - PyTorch模型

## 命名規範

推薦使用以下命名格式:
```
{model_type}_{dataset}_{date}.pkl

例如:
kmeans_mall_customers_20250118.pkl
rfm_analyzer_ecommerce_20250118.pkl
```

## 加載模型

```python
from joblib import load

model = load('models/kmeans_mall_customers_20250118.pkl')
predictions = model.predict(new_data)
```
""")
        logger.info(f"創建說明文件: {models_readme}")


def validate_project_structure(root: Optional[Path] = None) -> bool:
    """驗證專案目錄結構是否完整

    Args:
        root: 專案根目錄(默認自動檢測)

    Returns:
        bool: 目錄結構是否完整
    """
    if root is None:
        root = get_project_root()

    required_dirs = [
        'data',
        'data/raw',
        'data/processed',
        'data/outputs',
        'models',
        'logs',
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            logger.warning(f"缺少目錄: {dir_name}")

    if missing_dirs:
        logger.error(f"發現 {len(missing_dirs)} 個缺失的目錄")
        logger.info("運行 'python -m data_analysis_chatbots.init' 來初始化目錄結構")
        return False
    else:
        logger.success("✓ 專案目錄結構完整")
        return True


def main() -> None:
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="初始化 Data Analysis with Chatbots 專案目錄結構",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化目錄結構
  python -m data_analysis_chatbots.init

  # 初始化並創建示例README文件
  python -m data_analysis_chatbots.init --with-examples

  # 驗證目錄結構
  python -m data_analysis_chatbots.init --validate
        """
    )

    parser.add_argument(
        '--with-examples',
        action='store_true',
        help='創建示例README文件'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='僅驗證目錄結構,不創建新目錄'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='靜默模式(減少輸出)'
    )

    args = parser.parse_args()

    # 配置日誌級別
    if args.quiet:
        logger.remove()
        logger.add(lambda msg: None)  # 禁用所有輸出

    if args.validate:
        # 僅驗證
        is_valid = validate_project_structure()
        import sys
        sys.exit(0 if is_valid else 1)
    else:
        # 初始化
        initialize_project(
            verbose=not args.quiet,
            create_examples=args.with_examples
        )


if __name__ == '__main__':
    main()
