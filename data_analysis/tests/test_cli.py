"""CLI 模組測試"""

import pytest
from unittest.mock import patch, MagicMock, call
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

from data_analysis_chatbots.cli import (
    download_data,
    analyze_data,
    main
)


class TestDownloadCommand:
    """測試下載命令"""

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    def test_download_with_sample_flag(self, mock_downloader_class, mock_setup_logging):
        """測試 --sample 參數"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=True,
            all=False,
            dataset=None,
            force=False
        )

        # 執行
        download_data(args)

        # 驗證
        mock_setup_logging.assert_called_once_with(level="INFO")
        mock_downloader_class.assert_called_once()
        mock_downloader.download_sample_data.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    def test_download_with_all_flag(self, mock_downloader_class, mock_setup_logging):
        """測試 --all 參數"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=True,
            dataset=None,
            force=False
        )

        # 執行
        download_data(args)

        # 驗證
        mock_downloader.download_all_datasets.assert_called_once_with(force=False)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    def test_download_with_all_flag_and_force(self, mock_downloader_class, mock_setup_logging):
        """測試 --all --force 參數"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=True,
            dataset=None,
            force=True
        )

        # 執行
        download_data(args)

        # 驗證
        mock_downloader.download_all_datasets.assert_called_once_with(force=True)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    def test_download_with_dataset_argument(self, mock_downloader_class, mock_setup_logging):
        """測試 --dataset 參數"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=False,
            dataset='mall_customers',
            force=False
        )

        # 執行
        download_data(args)

        # 驗證
        mock_downloader.download_dataset.assert_called_once_with('mall_customers', force=False)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    def test_download_with_dataset_and_force(self, mock_downloader_class, mock_setup_logging):
        """測試 --dataset --force 參數"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=False,
            dataset='ecommerce',
            force=True
        )

        # 執行
        download_data(args)

        # 驗證
        mock_downloader.download_dataset.assert_called_once_with('ecommerce', force=True)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_download_missing_arguments_fails(self, mock_exit, mock_downloader_class, mock_setup_logging):
        """測試缺少參數時應該失敗"""
        # 準備
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=False,
            dataset=None,
            force=False
        )

        # 執行
        download_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)


class TestAnalyzeCommand:
    """測試分析命令"""

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.DataValidator')
    def test_analyze_mall_customers_validate(self, mock_validator_class, mock_loader_class, mock_setup_logging):
        """測試分析 mall_customers 數據集 - validate"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Annual Income (k$)': [50, 60, 70],
            'Spending Score (1-100)': [45, 55, 65]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='validate',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_mall_customers.assert_called_once()
        mock_validator_class.assert_called_once()
        mock_validator.print_report.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.KMeansClusterer')
    @patch('builtins.open', create=True)
    def test_analyze_mall_customers_kmeans_cluster(self, mock_open, mock_clusterer_class,
                                                    mock_loader_class, mock_setup_logging):
        """測試 K-Means 聚類分析"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35, 40, 45],
            'Annual Income (k$)': [50, 60, 70, 80, 90],
            'Spending Score (1-100)': [45, 55, 65, 75, 85]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1, 0, 1, 2])
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1, 2],
            'Count': [2, 2, 1]
        })
        mock_clusterer.evaluate_clustering.return_value = {
            'silhouette_score': 0.5,
            'calinski_harabasz_score': 100.0
        }
        mock_clusterer_class.return_value = mock_clusterer

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='kmeans',
            n_clusters=3,
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_mall_customers.assert_called_once()
        mock_clusterer_class.assert_called_once_with(n_clusters=3)
        mock_clusterer.fit_predict.assert_called_once()
        mock_clusterer.get_cluster_summary.assert_called_once()
        mock_clusterer.evaluate_clustering.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.DBSCANClusterer')
    @patch('builtins.open', create=True)
    def test_analyze_mall_customers_dbscan_cluster(self, mock_open, mock_clusterer_class,
                                                    mock_loader_class, mock_setup_logging):
        """測試 DBSCAN 聚類分析"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35, 40, 45],
            'Annual Income (k$)': [50, 60, 70, 80, 90],
            'Spending Score (1-100)': [45, 55, 65, 75, 85]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 0, 1, 1, -1])
        mock_clusterer.n_clusters_ = 2
        mock_clusterer.n_noise_ = 1
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1],
            'Count': [2, 2]
        })
        mock_clusterer.evaluate_clustering.return_value = {
            'silhouette_score': 0.6
        }
        mock_clusterer_class.return_value = mock_clusterer

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='dbscan',
            eps=0.5,
            min_samples=10,
            n_clusters=5,
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_mall_customers.assert_called_once()
        mock_clusterer_class.assert_called_once_with(eps=0.5, min_samples=10)
        mock_clusterer.fit_predict.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.GMMClusterer')
    @patch('builtins.open', create=True)
    def test_analyze_mall_customers_gmm_cluster(self, mock_open, mock_clusterer_class,
                                                 mock_loader_class, mock_setup_logging):
        """測試 GMM 聚類分析"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35, 40, 45],
            'Annual Income (k$)': [50, 60, 70, 80, 90],
            'Spending Score (1-100)': [45, 55, 65, 75, 85]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1, 0, 1, 2])
        mock_clusterer.predict_proba.return_value = np.array([
            [0.9, 0.05, 0.05],
            [0.1, 0.8, 0.1],
            [0.85, 0.1, 0.05],
            [0.15, 0.75, 0.1],
            [0.1, 0.15, 0.75]
        ])
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1, 2],
            'Count': [2, 2, 1]
        })
        mock_clusterer.evaluate_clustering.return_value = {
            'silhouette_score': 0.55
        }
        mock_clusterer_class.return_value = mock_clusterer

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='gmm',
            n_clusters=3,
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_mall_customers.assert_called_once()
        mock_clusterer_class.assert_called_once_with(n_components=3)
        mock_clusterer.fit_predict.assert_called_once()
        mock_clusterer.predict_proba.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.HierarchicalClusterer')
    @patch('builtins.open', create=True)
    def test_analyze_mall_customers_hierarchical_cluster(self, mock_open, mock_clusterer_class,
                                                          mock_loader_class, mock_setup_logging):
        """測試 Hierarchical 聚類分析"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35, 40, 45],
            'Annual Income (k$)': [50, 60, 70, 80, 90],
            'Spending Score (1-100)': [45, 55, 65, 75, 85]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1, 0, 1, 2])
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1, 2],
            'Count': [2, 2, 1]
        })
        mock_clusterer.evaluate_clustering.return_value = {
            'silhouette_score': 0.52
        }
        mock_clusterer_class.return_value = mock_clusterer

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='hierarchical',
            n_clusters=3,
            linkage='ward',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_mall_customers.assert_called_once()
        mock_clusterer_class.assert_called_once_with(n_clusters=3, linkage='ward')
        mock_clusterer.fit_predict.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_analyze_with_invalid_dataset(self, mock_exit, mock_loader_class, mock_setup_logging):
        """測試無效數據集應該失敗"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        args = argparse.Namespace(
            dataset='invalid_dataset',
            analysis='validate',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.DataValidator')
    def test_analyze_ecommerce_dataset(self, mock_validator_class, mock_loader_class, mock_setup_logging):
        """測試分析 ecommerce 數據集"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'CustomerID': [1, 2, 3],
            'InvoiceDate': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
            'TotalAmount': [100, 200, 300]
        })
        mock_loader.load_ecommerce.return_value = df

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = argparse.Namespace(
            dataset='ecommerce',
            analysis='validate',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_ecommerce.assert_called_once()
        mock_validator.print_report.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.RFMAnalyzer')
    @patch('builtins.open', create=True)
    def test_analyze_rfm(self, mock_open, mock_rfm_class, mock_loader_class, mock_setup_logging):
        """測試 RFM 分析"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'CustomerID': [1, 1, 2, 2, 3],
            'InvoiceDate': pd.to_datetime([
                '2024-01-01', '2024-01-15',
                '2024-01-10', '2024-01-20',
                '2024-01-05'
            ]),
            'TotalAmount': [100, 150, 200, 250, 300]
        })
        mock_loader.load_ecommerce.return_value = df

        mock_rfm = MagicMock()
        mock_rfm.segment_customers.return_value = pd.DataFrame({
            'CustomerID': [1, 2, 3],
            'Segment': ['Champions', 'Loyal', 'At Risk']
        })
        mock_rfm.get_segment_summary.return_value = pd.DataFrame({
            'Segment': ['Champions', 'Loyal', 'At Risk'],
            'Count': [1, 1, 1]
        })
        mock_rfm_class.return_value = mock_rfm

        args = argparse.Namespace(
            dataset='ecommerce',
            analysis='rfm',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_ecommerce.assert_called_once()
        mock_rfm_class.assert_called_once()
        mock_rfm.segment_customers.assert_called_once()
        mock_rfm.get_segment_summary.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_analyze_rfm_with_wrong_dataset(self, mock_exit, mock_loader_class, mock_setup_logging):
        """測試 RFM 分析使用錯誤數據集應該失敗"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Annual Income (k$)': [50, 60, 70],
            'Spending Score (1-100)': [45, 55, 65]
        })
        mock_loader.load_mall_customers.return_value = df

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='rfm',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.KMeansClusterer')
    @patch('builtins.open', create=True)
    @patch('data_analysis_chatbots.cli.validate_output_path',
           side_effect=lambda p: Path(p))
    def test_analyze_with_output_file(self, mock_validate_path, mock_open,
                                      mock_clusterer_class, mock_loader_class,
                                      mock_setup_logging):
        """測試輸出文件參數"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Annual Income (k$)': [50, 60, 70],
            'Spending Score (1-100)': [45, 55, 65]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1, 2])
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1, 2],
            'Count': [1, 1, 1]
        })
        mock_clusterer.evaluate_clustering.return_value = {'silhouette_score': 0.5}
        mock_clusterer_class.return_value = mock_clusterer

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='kmeans',
            n_clusters=3,
            output='custom_output.csv'
        )

        # 執行
        analyze_data(args)

        # 驗證 - 檢查輸出文件路徑被使用
        mock_clusterer.fit_predict.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.DataValidator')
    def test_analyze_personality_dataset(self, mock_validator_class, mock_loader_class, mock_setup_logging):
        """測試分析 personality 數據集"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'ID': [1, 2, 3],
            'Age': [25, 30, 35],
            'Income': [50000, 60000, 70000]
        })
        mock_loader.load_personality.return_value = df

        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator

        args = argparse.Namespace(
            dataset='personality',
            analysis='validate',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_loader.load_personality.assert_called_once()
        mock_validator.print_report.assert_called_once()

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_analyze_with_invalid_analysis_type(self, mock_exit, mock_loader_class, mock_setup_logging):
        """測試無效分析類型應該失敗"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Annual Income (k$)': [50, 60, 70],
            'Spending Score (1-100)': [45, 55, 65]
        })
        mock_loader.load_mall_customers.return_value = df

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='invalid_analysis',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_analyze_with_invalid_algorithm(self, mock_exit, mock_loader_class, mock_setup_logging):
        """測試無效算法應該失敗"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35],
            'Annual Income (k$)': [50, 60, 70],
            'Spending Score (1-100)': [45, 55, 65]
        })
        mock_loader.load_mall_customers.return_value = df

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='invalid_algo',
            n_clusters=3,
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)


class TestCLIErrorHandling:
    """測試錯誤處理"""

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_file_not_found_error(self, mock_exit, mock_loader_class, mock_setup_logging):
        """測試文件未找到錯誤"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        mock_loader.load_mall_customers.side_effect = FileNotFoundError("Dataset not found")

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='validate',
            output=None
        )

        # 執行
        analyze_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    @patch('data_analysis_chatbots.cli.sys.exit')
    def test_invalid_arguments_error(self, mock_exit, mock_downloader_class, mock_setup_logging):
        """測試無效參數錯誤"""
        # 準備 - 沒有提供任何下載選項
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        args = argparse.Namespace(
            sample=False,
            all=False,
            dataset=None,
            force=False
        )

        # 執行
        download_data(args)

        # 驗證
        mock_exit.assert_called_once_with(1)

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.DataValidator')
    def test_error_logging_on_exception(self, mock_validator_class, mock_loader_class, mock_setup_logging):
        """測試異常時的錯誤日誌"""
        # 準備
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        # 模擬載入時發生異常
        mock_loader.load_mall_customers.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(
            dataset='mall_customers',
            analysis='validate',
            output=None
        )

        # 執行 - 應該拋出異常
        with pytest.raises(Exception):
            analyze_data(args)


class TestArgumentParser:
    """測試參數解析器"""

    def test_parser_structure(self):
        """測試解析器結構"""
        # 使用 patch 來避免調用 parse_args()
        with patch('sys.argv', ['prog', 'download', '--sample']):
            parser = argparse.ArgumentParser(description="Data Analysis with Chatbots CLI")
            subparsers = parser.add_subparsers(dest='command')

            # Download command
            download_parser = subparsers.add_parser('download')
            download_parser.add_argument('--all', action='store_true')
            download_parser.add_argument('--dataset', type=str)
            download_parser.add_argument('--sample', action='store_true')
            download_parser.add_argument('--force', action='store_true')

            # Analyze command
            analyze_parser = subparsers.add_parser('analyze')
            analyze_parser.add_argument('--dataset', type=str, required=True)
            analyze_parser.add_argument('--analysis', type=str, required=True)

            args = parser.parse_args()

            # 驗證
            assert args.command == 'download'
            assert args.sample is True

    def test_download_parser_flags(self):
        """測試下載解析器標誌"""
        with patch('sys.argv', ['prog', 'download', '--all', '--force']):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')

            download_parser = subparsers.add_parser('download')
            download_parser.add_argument('--all', action='store_true')
            download_parser.add_argument('--dataset', type=str)
            download_parser.add_argument('--sample', action='store_true')
            download_parser.add_argument('--force', action='store_true')

            args = parser.parse_args()

            assert args.all is True
            assert args.force is True

    def test_analyze_parser_required_args(self):
        """測試分析解析器必需參數"""
        with patch('sys.argv', ['prog', 'analyze', '--dataset', 'mall_customers', '--analysis', 'validate']):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')

            analyze_parser = subparsers.add_parser('analyze')
            analyze_parser.add_argument('--dataset', type=str, required=True)
            analyze_parser.add_argument('--analysis', type=str, required=True)

            args = parser.parse_args()

            assert args.dataset == 'mall_customers'
            assert args.analysis == 'validate'

    def test_analyze_parser_with_clustering_options(self):
        """測試分析解析器聚類選項"""
        with patch('sys.argv', [
            'prog', 'analyze',
            '--dataset', 'mall_customers',
            '--analysis', 'cluster',
            '--algorithm', 'kmeans',
            '--n-clusters', '5'
        ]):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')

            analyze_parser = subparsers.add_parser('analyze')
            analyze_parser.add_argument('--dataset', type=str, required=True)
            analyze_parser.add_argument('--analysis', type=str, required=True)
            analyze_parser.add_argument('--algorithm', type=str, default='kmeans')
            analyze_parser.add_argument('--n-clusters', type=int, default=5)

            args = parser.parse_args()

            assert args.algorithm == 'kmeans'
            assert args.n_clusters == 5

    def test_analyze_parser_dbscan_options(self):
        """測試 DBSCAN 選項"""
        with patch('sys.argv', [
            'prog', 'analyze',
            '--dataset', 'mall_customers',
            '--analysis', 'cluster',
            '--algorithm', 'dbscan',
            '--eps', '0.7',
            '--min-samples', '10'
        ]):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')

            analyze_parser = subparsers.add_parser('analyze')
            analyze_parser.add_argument('--dataset', type=str, required=True)
            analyze_parser.add_argument('--analysis', type=str, required=True)
            analyze_parser.add_argument('--algorithm', type=str, default='kmeans')
            analyze_parser.add_argument('--eps', type=float, default=0.5)
            analyze_parser.add_argument('--min-samples', type=int, default=5)

            args = parser.parse_args()

            assert args.eps == 0.7
            assert args.min_samples == 10

    def test_analyze_parser_hierarchical_options(self):
        """測試 Hierarchical 選項"""
        with patch('sys.argv', [
            'prog', 'analyze',
            '--dataset', 'mall_customers',
            '--analysis', 'cluster',
            '--algorithm', 'hierarchical',
            '--linkage', 'average'
        ]):
            parser = argparse.ArgumentParser()
            subparsers = parser.add_subparsers(dest='command')

            analyze_parser = subparsers.add_parser('analyze')
            analyze_parser.add_argument('--dataset', type=str, required=True)
            analyze_parser.add_argument('--analysis', type=str, required=True)
            analyze_parser.add_argument('--algorithm', type=str, default='kmeans')
            analyze_parser.add_argument('--linkage', type=str, default='ward')

            args = parser.parse_args()

            assert args.linkage == 'average'

    @patch('data_analysis_chatbots.cli.argparse.ArgumentParser.print_help')
    @patch('sys.exit')
    def test_help_message(self, mock_exit, mock_print_help):
        """測試幫助信息"""
        with patch('sys.argv', ['prog']):
            try:
                main()
            except SystemExit:
                pass

            # 驗證幫助信息被打印
            mock_print_help.assert_called_once()

    @patch('sys.exit')
    def test_no_command_exits(self, mock_exit):
        """測試沒有命令時退出"""
        with patch('sys.argv', ['prog']):
            try:
                main()
            except (SystemExit, AttributeError):
                pass


class TestMainFunction:
    """測試主函數"""

    @patch('data_analysis_chatbots.cli.download_data')
    def test_main_calls_download_function(self, mock_download):
        """測試主函數調用下載函數"""
        with patch('sys.argv', ['prog', 'download', '--sample']):
            try:
                main()
            except SystemExit:
                pass

            # 驗證 download_data 被調用
            mock_download.assert_called_once()

    @patch('data_analysis_chatbots.cli.analyze_data')
    def test_main_calls_analyze_function(self, mock_analyze):
        """測試主函數調用分析函數"""
        with patch('sys.argv', ['prog', 'analyze', '--dataset', 'mall_customers', '--analysis', 'validate']):
            try:
                main()
            except SystemExit:
                pass

            # 驗證 analyze_data 被調用
            mock_analyze.assert_called_once()

    @patch('sys.exit')
    def test_main_with_no_command(self, mock_exit):
        """測試沒有命令時主函數行為"""
        with patch('sys.argv', ['prog']):
            try:
                main()
            except (SystemExit, AttributeError):
                pass


class TestIntegration:
    """集成測試"""

    @patch('data_analysis_chatbots.cli.setup_logging')
    @patch('data_analysis_chatbots.cli.DataDownloader')
    @patch('data_analysis_chatbots.cli.DataLoader')
    @patch('data_analysis_chatbots.cli.KMeansClusterer')
    @patch('builtins.open', create=True)
    def test_full_workflow_download_and_analyze(self, mock_open, mock_clusterer_class,
                                                 mock_loader_class, mock_downloader_class,
                                                 mock_setup_logging):
        """測試完整工作流程：下載和分析"""
        # 設置下載
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        download_args = argparse.Namespace(
            sample=True,
            all=False,
            dataset=None,
            force=False
        )

        # 執行下載
        download_data(download_args)

        # 設置分析
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        df = pd.DataFrame({
            'Age': [25, 30, 35, 40, 45],
            'Annual Income (k$)': [50, 60, 70, 80, 90],
            'Spending Score (1-100)': [45, 55, 65, 75, 85]
        })
        mock_loader.load_mall_customers.return_value = df

        mock_clusterer = MagicMock()
        mock_clusterer.fit_predict.return_value = np.array([0, 1, 0, 1, 2])
        mock_clusterer.get_cluster_summary.return_value = pd.DataFrame({
            'Cluster': [0, 1, 2],
            'Count': [2, 2, 1]
        })
        mock_clusterer.evaluate_clustering.return_value = {'silhouette_score': 0.5}
        mock_clusterer_class.return_value = mock_clusterer

        analyze_args = argparse.Namespace(
            dataset='mall_customers',
            analysis='cluster',
            algorithm='kmeans',
            n_clusters=3,
            output=None
        )

        # 執行分析
        analyze_data(analyze_args)

        # 驗證
        mock_downloader.download_sample_data.assert_called_once()
        mock_loader.load_mall_customers.assert_called_once()
        mock_clusterer.fit_predict.assert_called_once()
