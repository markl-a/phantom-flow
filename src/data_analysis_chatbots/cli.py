"""命令行接口(CLI)工具

此模塊提供數據分析項目的命令行接口，支持：
- 數據下載和生成
- 數據驗證
- 多種聚類算法（K-Means, DBSCAN, GMM, Hierarchical）
- RFM 客戶分析
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
from loguru import logger

from .data_downloader import DataDownloader
from .data_loader import DataLoader
from .preprocessing import DataValidator
from .clustering import (
    KMeansClusterer,
    DBSCANClusterer,
    GMMClusterer,
    HierarchicalClusterer,
    RFMAnalyzer
)
from .marketing import CLVPredictor
from .utils import setup_logging


# 數據集對應的特徵列配置
DATASET_FEATURES = {
    'mall_customers': ['Age', 'Annual Income (k$)', 'Spending Score (1-100)'],
    'ecommerce': ['Quantity', 'UnitPrice', 'TotalAmount'],
    'personality': ['Age', 'Income']
}


def validate_output_path(output_path: str, allowed_dirs: list = None) -> Path:
    """
    驗證輸出路徑的安全性，防止路徑遍歷攻擊

    Args:
        output_path: 用戶指定的輸出路徑
        allowed_dirs: 允許的目錄列表，默認為 ['data/outputs', 'outputs']

    Returns:
        驗證後的 Path 對象

    Raises:
        ValueError: 如果路徑不在允許的目錄內
    """
    if allowed_dirs is None:
        allowed_dirs = ['data/outputs', 'outputs', 'data']

    output_path = Path(output_path).resolve()

    # 獲取項目根目錄
    project_root = Path(__file__).parent.parent.parent.resolve()

    # 檢查是否在允許的目錄內
    for allowed_dir in allowed_dirs:
        allowed_path = (project_root / allowed_dir).resolve()
        try:
            output_path.relative_to(allowed_path)
            return output_path
        except ValueError:
            continue

    raise ValueError(
        f"Output path must be within allowed directories: {allowed_dirs}. "
        f"Got: {output_path}"
    )


def download_data(args) -> None:
    """下載數據集"""
    setup_logging(level="INFO")

    downloader = DataDownloader()

    if args.sample:
        downloader.download_sample_data()
    elif args.all:
        downloader.download_all_datasets(force=args.force)
    elif args.dataset:
        downloader.download_dataset(args.dataset, force=args.force)
    else:
        logger.error("請指定 --all, --dataset 或 --sample")
        sys.exit(1)


# ============================================================================
# 數據分析輔助函數
# ============================================================================

def _load_dataset(dataset_name: str) -> pd.DataFrame:
    """載入指定的數據集

    Args:
        dataset_name: 數據集名稱 ('mall_customers', 'ecommerce', 'personality')

    Returns:
        載入的 DataFrame

    Raises:
        SystemExit: 當數據集名稱無效或找不到文件時
    """
    loader = DataLoader()

    loaders = {
        'mall_customers': loader.load_mall_customers,
        'ecommerce': loader.load_ecommerce,
        'personality': loader.load_personality
    }

    if dataset_name not in loaders:
        logger.error(f"Unknown dataset: {dataset_name}")
        sys.exit(1)
        return None  # safety net so unit tests that mock sys.exit don't fall through

    try:
        df = loaders[dataset_name]()
        logger.info(f"Loaded {len(df)} rows from {dataset_name}")
        return df
    except FileNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        logger.info("Run 'dac-download' to download datasets first")
        sys.exit(1)
        return None  # safety net so unit tests that mock sys.exit don't fall through


def _create_clusterer(algorithm: str, args) -> Any:
    """根據算法類型創建聚類器

    Args:
        algorithm: 算法名稱 ('kmeans', 'dbscan', 'gmm', 'hierarchical')
        args: 命令行參數

    Returns:
        聚類器實例

    Raises:
        SystemExit: 當算法名稱無效時
    """
    if algorithm == 'kmeans':
        return KMeansClusterer(n_clusters=args.n_clusters)

    elif algorithm == 'dbscan':
        eps = getattr(args, 'eps', 0.5)
        min_samples = getattr(args, 'min_samples', 5)
        return DBSCANClusterer(eps=eps, min_samples=min_samples)

    elif algorithm == 'gmm':
        return GMMClusterer(n_components=args.n_clusters)

    elif algorithm == 'hierarchical':
        linkage_method = getattr(args, 'linkage', 'ward')
        return HierarchicalClusterer(n_clusters=args.n_clusters, linkage=linkage_method)

    else:
        logger.error(f"Unknown algorithm: {algorithm}")
        sys.exit(1)
        return None  # safety net so unit tests that mock sys.exit don't fall through


def _run_clustering(
    df: pd.DataFrame,
    features: list,
    algorithm: str,
    args
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """執行聚類分析

    Args:
        df: 輸入數據
        features: 特徵列名列表
        algorithm: 聚類算法
        args: 命令行參數

    Returns:
        (帶有聚類標籤的 DataFrame, 聚類摘要, 評估指標)
    """
    clusterer = _create_clusterer(algorithm, args)
    if clusterer is None:
        # _create_clusterer already called sys.exit(1) — but if a test
        # mocked sys.exit, this guard prevents the AttributeError on None.
        return df, pd.DataFrame(), {}
    labels = clusterer.fit_predict(df, features)

    # 記錄完成信息
    if algorithm == 'kmeans':
        logger.success(f"K-Means clustering completed with {args.n_clusters} clusters")
    elif algorithm == 'dbscan':
        logger.success(
            f"DBSCAN clustering completed: {clusterer.n_clusters_} clusters, "
            f"{clusterer.n_noise_} noise points"
        )
    elif algorithm == 'gmm':
        probabilities = clusterer.predict_proba(df, features)
        df['Max_Probability'] = probabilities.max(axis=1)
        logger.success(f"GMM clustering completed with {args.n_clusters} components")
    elif algorithm == 'hierarchical':
        linkage_method = getattr(args, 'linkage', 'ward')
        logger.success(
            f"Hierarchical clustering completed with {args.n_clusters} clusters "
            f"(linkage={linkage_method})"
        )

    # 添加聚類標籤
    df['Cluster'] = labels

    # 獲取摘要和評估指標
    summary = clusterer.get_cluster_summary(df, features)
    metrics = clusterer.evaluate_clustering()

    return df, summary, metrics


def _run_rfm_analysis(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """執行 RFM 分析

    Args:
        df: 電商數據 DataFrame

    Returns:
        (客戶分群結果, 分群摘要)
    """
    rfm_analyzer = RFMAnalyzer(
        df=df,
        customer_id_col='CustomerID',
        date_col='InvoiceDate',
        amount_col='TotalAmount'
    )

    segments = rfm_analyzer.segment_customers()
    summary = rfm_analyzer.get_segment_summary()

    logger.success("RFM analysis completed")

    return segments, summary


def _get_output_path(args, default_filename: str) -> str:
    """獲取驗證後的輸出路徑

    Args:
        args: 命令行參數
        default_filename: 默認文件名

    Returns:
        輸出文件路徑
    """
    if args.output:
        try:
            return str(validate_output_path(args.output))
        except ValueError as e:
            logger.error(f"Invalid output path: {e}")
            sys.exit(1)
            return ''  # safety net so unit tests that mock sys.exit don't fall through
    return f'data/outputs/{default_filename}'


def _save_results(
    df: pd.DataFrame,
    output_file: str,
    summary: Optional[pd.DataFrame] = None
) -> None:
    """保存分析結果

    Args:
        df: 結果數據
        output_file: 輸出文件路徑
        summary: 可選的摘要數據
    """
    df.to_csv(output_file, index=False)
    logger.success(f"Results saved to {output_file}")

    if summary is not None:
        summary_file = output_file.replace('.csv', '_summary.csv')
        summary.to_csv(summary_file, index=False)
        logger.success(f"Summary saved to {summary_file}")


# ============================================================================
# 主分析函數
# ============================================================================

def analyze_data(args) -> None:
    """執行數據分析

    根據命令行參數執行相應的分析：
    - validate: 數據驗證
    - cluster: 聚類分析
    - rfm: RFM 客戶分析
    """
    setup_logging(level="INFO")

    # 載入數據
    df = _load_dataset(args.dataset)
    if df is None:
        # _load_dataset already called sys.exit(1) — but if a test mocked
        # sys.exit, we need this return to actually stop here instead of
        # falling through to DataValidator(None) and crashing.
        return

    # 執行分析
    if args.analysis == 'validate':
        validator = DataValidator(df)
        validator.print_report()

    elif args.analysis == 'cluster':
        features = DATASET_FEATURES.get(args.dataset)
        if not features:
            logger.error(f"No feature configuration for dataset: {args.dataset}")
            sys.exit(1)
            return  # safety net so unit tests that mock sys.exit don't fall through

        algorithm = getattr(args, 'algorithm', 'kmeans')

        # 執行聚類
        df, summary, metrics = _run_clustering(df, features, algorithm, args)

        # 顯示結果
        logger.info("\nCluster Summary:")
        logger.info(summary.to_string())
        logger.info(f"\nClustering Metrics: {metrics}")

        # 保存結果
        output_file = _get_output_path(args, f'{algorithm}_cluster_results.csv')
        _save_results(df, output_file, summary)

    elif args.analysis == 'rfm':
        if args.dataset != 'ecommerce':
            logger.error("RFM analysis requires ecommerce dataset")
            sys.exit(1)
            return  # safety net so unit tests that mock sys.exit don't fall through

        segments, summary = _run_rfm_analysis(df)

        logger.info("\nSegment Summary:")
        logger.info(summary)

        output_file = _get_output_path(args, 'rfm_segments.csv')
        _save_results(segments, output_file)

    else:
        logger.error(f"Unknown analysis type: {args.analysis}")
        sys.exit(1)
        return  # safety net so unit tests that mock sys.exit don't fall through


def main() -> None:
    """主CLI入口"""
    parser = argparse.ArgumentParser(
        description="Data Analysis with Chatbots CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all datasets
  dac-download --all

  # Download specific dataset
  dac-download --dataset mall_customers

  # Generate sample data
  dac-download --sample

  # Validate data
  dac-analyze --dataset mall_customers --analysis validate

  # Run K-Means clustering (default)
  dac-analyze --dataset mall_customers --analysis cluster --n-clusters 5

  # Run DBSCAN clustering
  dac-analyze --dataset mall_customers --analysis cluster --algorithm dbscan --eps 0.5 --min-samples 10

  # Run GMM clustering
  dac-analyze --dataset mall_customers --analysis cluster --algorithm gmm --n-clusters 3

  # Run Hierarchical clustering
  dac-analyze --dataset mall_customers --analysis cluster --algorithm hierarchical --n-clusters 4 --linkage ward

  # Run RFM analysis
  dac-analyze --dataset ecommerce --analysis rfm
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download datasets')
    download_parser.add_argument('--all', action='store_true', help='Download all datasets')
    download_parser.add_argument('--dataset', type=str, help='Download specific dataset')
    download_parser.add_argument('--sample', action='store_true', help='Generate sample data')
    download_parser.add_argument('--force', action='store_true', help='Force re-download')
    download_parser.set_defaults(func=download_data)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze data')
    analyze_parser.add_argument('--dataset', type=str, required=True,
                               choices=['mall_customers', 'ecommerce', 'personality'],
                               help='Dataset to analyze')
    analyze_parser.add_argument('--analysis', type=str, required=True,
                               choices=['validate', 'cluster', 'rfm'],
                               help='Type of analysis')

    # Clustering algorithm options
    analyze_parser.add_argument('--algorithm', type=str, default='kmeans',
                               choices=['kmeans', 'dbscan', 'gmm', 'hierarchical'],
                               help='Clustering algorithm (default: kmeans)')
    analyze_parser.add_argument('--n-clusters', type=int, default=5,
                               help='Number of clusters (for kmeans/gmm/hierarchical)')

    # DBSCAN specific parameters
    analyze_parser.add_argument('--eps', type=float, default=0.5,
                               help='DBSCAN: Maximum distance between samples (default: 0.5)')
    analyze_parser.add_argument('--min-samples', type=int, default=5,
                               help='DBSCAN: Minimum samples in neighborhood (default: 5)')

    # Hierarchical specific parameters
    analyze_parser.add_argument('--linkage', type=str, default='ward',
                               choices=['ward', 'complete', 'average', 'single'],
                               help='Hierarchical: Linkage method (default: ward)')

    analyze_parser.add_argument('--output', type=str, help='Output file path')
    analyze_parser.set_defaults(func=analyze_data)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)
        return  # safety net so unit tests that mock sys.exit don't fall through

    args.func(args)


if __name__ == '__main__':
    main()
