"""測試數據下載器模塊"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
from pathlib import Path
import os
import subprocess
import pandas as pd
import numpy as np

from data_analysis_chatbots.data_downloader import DataDownloader


@pytest.fixture
def mock_config():
    """創建模擬配置"""
    config = Mock()
    config.get.return_value = 'data/raw'
    config.get_dataset_config.return_value = {
        'dataset_id': 'test/dataset',
        'filename': 'test_data.csv',
        'source': 'kaggle'
    }
    return config


@pytest.fixture
def temp_dir():
    """創建臨時目錄"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_project_root(temp_dir):
    """模擬項目根目錄"""
    return Path(temp_dir)


class TestDataDownloaderInit:
    """測試 DataDownloader 初始化"""

    def test_initialization_with_config(self, mock_config, temp_dir):
        """測試使用配置初始化"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir') as mock_ensure:
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)

                assert downloader.config == mock_config
                assert downloader.project_root == Path(temp_dir)
                # Compare via Path.parts so we're robust to '/' (Linux/macOS)
                # vs '\\' (Windows) separators in the stringified path.
                assert downloader.raw_data_path.parts[-2:] == ('data', 'raw')
                mock_ensure.assert_called_once()

    def test_initialization_without_config(self, temp_dir):
        """測試不提供配置時自動創建"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir') as mock_ensure:
                with patch('data_analysis_chatbots.data_downloader.ConfigLoader') as mock_config_loader:
                    mock_root.return_value = Path(temp_dir)
                    mock_config_instance = Mock()
                    mock_config_instance.get.return_value = 'data/raw'
                    mock_config_loader.return_value = mock_config_instance

                    downloader = DataDownloader()

                    mock_config_loader.assert_called_once()
                    assert downloader.config is not None
                    mock_ensure.assert_called_once()

    def test_raw_data_path_creation(self, mock_config, temp_dir):
        """測試原始數據路徑創建"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir') as mock_ensure:
                mock_root.return_value = Path(temp_dir)
                mock_config.get.return_value = 'custom/data/path'

                downloader = DataDownloader(config=mock_config)

                # Compare via Path.parts (separator-agnostic) — Windows uses
                # '\\' so substring-matching '/' breaks the test cross-platform.
                assert downloader.raw_data_path.parts[-3:] == ('custom', 'data', 'path')
                mock_ensure.assert_called_once_with(downloader.raw_data_path)


class TestCheckKaggleSetup:
    """測試 Kaggle 配置檢查"""

    def test_kaggle_json_not_exists(self, mock_config, temp_dir):
        """測試 kaggle.json 不存在的情況"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    mock_root.return_value = Path(temp_dir)
                    mock_exists.return_value = False

                    downloader = DataDownloader(config=mock_config)
                    result = downloader._check_kaggle_setup()

                    assert result is False

    @pytest.mark.skipif(sys.platform == "win32", reason="Posix-only — uses os.getuid + pwd module")
    def test_kaggle_json_exists_correct_permissions_unix(self, mock_config, temp_dir):
        """測試 Unix 系統下正確的權限"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('os.name', 'posix'):
                        with patch('os.stat') as mock_stat:
                            with patch('os.getuid', return_value=1000):
                                mock_root.return_value = Path(temp_dir)
                                mock_exists.return_value = True

                                # 模擬正確的權限 (600) 和所有權
                                stat_result = Mock()
                                stat_result.st_mode = 0o100600  # 文件類型 + 權限
                                stat_result.st_uid = 1000
                                mock_stat.return_value = stat_result

                                downloader = DataDownloader(config=mock_config)
                                result = downloader._check_kaggle_setup()

                                assert result is True

    @pytest.mark.skipif(sys.platform == "win32", reason="Posix-only — uses os.getuid + pwd module")
    def test_kaggle_json_incorrect_permissions_unix(self, mock_config, temp_dir):
        """測試 Unix 系統下錯誤的權限"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('os.name', 'posix'):
                        with patch('os.stat') as mock_stat:
                            mock_root.return_value = Path(temp_dir)
                            mock_exists.return_value = True

                            # 模擬錯誤的權限 (644)
                            stat_result = Mock()
                            stat_result.st_mode = 0o100644
                            mock_stat.return_value = stat_result

                            downloader = DataDownloader(config=mock_config)
                            result = downloader._check_kaggle_setup()

                            assert result is False

    @pytest.mark.skipif(sys.platform == "win32", reason="Posix-only — uses os.getuid + pwd module")
    def test_kaggle_json_incorrect_ownership_unix(self, mock_config, temp_dir):
        """測試 Unix 系統下錯誤的所有權"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('os.name', 'posix'):
                        with patch('os.stat') as mock_stat:
                            with patch('os.getuid', return_value=1000):
                                with patch('pwd.getpwuid') as mock_getpwuid:
                                    mock_root.return_value = Path(temp_dir)
                                    mock_exists.return_value = True

                                    # 模擬正確的權限但錯誤的所有權
                                    stat_result = Mock()
                                    stat_result.st_mode = 0o100600
                                    stat_result.st_uid = 2000  # 不同的用戶
                                    mock_stat.return_value = stat_result

                                    # 模擬 pwd.getpwuid
                                    user1 = Mock()
                                    user1.pw_name = 'user1'
                                    user2 = Mock()
                                    user2.pw_name = 'user2'
                                    mock_getpwuid.side_effect = lambda uid: user1 if uid == 1000 else user2

                                    downloader = DataDownloader(config=mock_config)
                                    result = downloader._check_kaggle_setup()

                                    assert result is False

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_kaggle_json_exists_windows(self, mock_config, temp_dir):
        """測試 Windows 系統下的情況"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch.object(Path, 'exists', return_value=True):
                    mock_root.return_value = Path(temp_dir)

                    downloader = DataDownloader(config=mock_config)
                    result = downloader._check_kaggle_setup()

                    # Windows 系統不檢查權限，只要文件存在即可
                    assert result is True

    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_kaggle_json_exists_on_windows_mock(self, mock_config, temp_dir):
        """測試 Windows 系統下的情況 (使用 Mock)"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch.object(Path, 'exists', return_value=True):
                    mock_root.return_value = Path(temp_dir)

                    downloader = DataDownloader(config=mock_config)
                    result = downloader._check_kaggle_setup()

                    # Windows 系統不檢查權限，只要文件存在即可
                    assert result is True

    @pytest.mark.skipif(sys.platform == "win32", reason="Posix-only — uses os.getuid + pwd module")
    def test_kaggle_json_ownership_check_keyerror(self, mock_config, temp_dir):
        """測試獲取用戶信息失敗的情況"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('os.name', 'posix'):
                        with patch('os.stat') as mock_stat:
                            with patch('os.getuid', return_value=1000):
                                with patch('pwd.getpwuid', side_effect=KeyError):
                                    mock_root.return_value = Path(temp_dir)
                                    mock_exists.return_value = True

                                    stat_result = Mock()
                                    stat_result.st_mode = 0o100600
                                    stat_result.st_uid = 2000
                                    mock_stat.return_value = stat_result

                                    downloader = DataDownloader(config=mock_config)
                                    result = downloader._check_kaggle_setup()

                                    # 應該使用 UID 作為後備
                                    assert result is False


class TestDownloadDataset:
    """測試數據集下載"""

    def test_download_dataset_success(self, mock_config, temp_dir):
        """測試成功下載數據集"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists') as mock_exists:
                    with patch('subprocess.run') as mock_run:
                        mock_root.return_value = Path(temp_dir)
                        mock_exists.return_value = False  # 文件不存在

                        # 模擬成功的 subprocess 調用
                        mock_result = Mock()
                        mock_result.returncode = 0
                        mock_result.stderr = ''
                        mock_run.return_value = mock_result

                        downloader = DataDownloader(config=mock_config)

                        # Mock _check_kaggle_setup to return True
                        with patch.object(downloader, '_check_kaggle_setup', return_value=True):
                            result = downloader.download_dataset('test_dataset')

                        assert result is True
                        mock_run.assert_called_once()
                        call_args = mock_run.call_args[0][0]
                        assert 'kaggle' in call_args
                        assert 'datasets' in call_args
                        assert 'download' in call_args

    def test_download_dataset_already_exists(self, mock_config, temp_dir):
        """測試數據集已存在的情況"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)

                # Mock file exists
                with patch.object(Path, 'exists', return_value=True):
                    result = downloader.download_dataset('test_dataset', force=False)

                assert result is True

    def test_download_dataset_force_redownload(self, mock_config, temp_dir):
        """測試強制重新下載"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('subprocess.run') as mock_run:
                    mock_root.return_value = Path(temp_dir)

                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_run.return_value = mock_result

                    downloader = DataDownloader(config=mock_config)

                    with patch.object(Path, 'exists', return_value=True):
                        with patch.object(downloader, '_check_kaggle_setup', return_value=True):
                            result = downloader.download_dataset('test_dataset', force=True)

                    assert result is True
                    mock_run.assert_called_once()

    def test_download_dataset_not_from_kaggle(self, mock_config, temp_dir):
        """測試非 Kaggle 來源的數據集"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                # 設置非 Kaggle 來源
                mock_config.get_dataset_config.return_value = {
                    'dataset_id': 'test/dataset',
                    'filename': 'test_data.csv',
                    'source': 'manual'
                }

                downloader = DataDownloader(config=mock_config)
                result = downloader.download_dataset('test_dataset')

                assert result is False

    def test_download_dataset_kaggle_not_configured(self, mock_config, temp_dir):
        """測試 Kaggle 未配置的情況"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('pathlib.Path.exists', return_value=False):
                    mock_root.return_value = Path(temp_dir)

                    downloader = DataDownloader(config=mock_config)

                    # Mock file doesn't exist yet
                    with patch.object(Path, 'exists', return_value=False):
                        result = downloader.download_dataset('test_dataset')

                    assert result is False

    def test_download_dataset_subprocess_error(self, mock_config, temp_dir):
        """測試 subprocess 執行失敗"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('subprocess.run') as mock_run:
                    mock_root.return_value = Path(temp_dir)

                    # 模擬失敗的 subprocess 調用
                    mock_result = Mock()
                    mock_result.returncode = 1
                    mock_result.stderr = 'Error: Dataset not found'
                    mock_run.return_value = mock_result

                    downloader = DataDownloader(config=mock_config)

                    with patch.object(Path, 'exists', return_value=False):
                        with patch.object(downloader, '_check_kaggle_setup', return_value=True):
                            result = downloader.download_dataset('test_dataset')

                    assert result is False

    def test_download_dataset_exception(self, mock_config, temp_dir):
        """測試下載過程中發生異常"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                # 配置拋出 KeyError 異常（更具體的異常類型）
                mock_config.get_dataset_config.side_effect = KeyError("missing_key")

                downloader = DataDownloader(config=mock_config)
                result = downloader.download_dataset('test_dataset')

                assert result is False

    def test_download_dataset_command_structure(self, mock_config, temp_dir):
        """測試下載命令結構"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                with patch('subprocess.run') as mock_run:
                    mock_root.return_value = Path(temp_dir)

                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_run.return_value = mock_result

                    mock_config.get_dataset_config.return_value = {
                        'dataset_id': 'owner/dataset-name',
                        'filename': 'data.csv',
                        'source': 'kaggle'
                    }

                    downloader = DataDownloader(config=mock_config)

                    with patch.object(Path, 'exists', return_value=False):
                        with patch.object(downloader, '_check_kaggle_setup', return_value=True):
                            downloader.download_dataset('test_dataset')

                    # 驗證命令結構
                    call_args = mock_run.call_args[0][0]
                    assert call_args[0] == 'kaggle'
                    assert call_args[1] == 'datasets'
                    assert call_args[2] == 'download'
                    assert '-d' in call_args
                    assert 'owner/dataset-name' in call_args
                    assert '-p' in call_args
                    assert '--unzip' in call_args


class TestDownloadAllDatasets:
    """測試下載所有數據集"""

    def test_download_all_datasets_success(self, temp_dir):
        """測試成功下載所有數據集"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                # 創建一個新的 mock_config
                local_mock_config = Mock()
                local_mock_config.get.side_effect = lambda key, default=None: {
                    'paths.raw_data': 'data/raw',
                    'datasets': {
                        'dataset1': {'source': 'kaggle'},
                        'dataset2': {'source': 'kaggle'},
                        'dataset3': {'source': 'kaggle'}
                    }
                }.get(key, default)

                downloader = DataDownloader(config=local_mock_config)

                # Mock download_dataset 方法
                with patch.object(downloader, 'download_dataset', return_value=True) as mock_download:
                    downloader.download_all_datasets()

                    # 應該調用三次
                    assert mock_download.call_count == 3
                    mock_download.assert_any_call('dataset1', False)
                    mock_download.assert_any_call('dataset2', False)
                    mock_download.assert_any_call('dataset3', False)

    def test_download_all_datasets_with_force(self, temp_dir):
        """測試強制下載所有數據集"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                local_mock_config = Mock()
                local_mock_config.get.side_effect = lambda key, default=None: {
                    'paths.raw_data': 'data/raw',
                    'datasets': {
                        'dataset1': {'source': 'kaggle'}
                    }
                }.get(key, default)

                downloader = DataDownloader(config=local_mock_config)

                with patch.object(downloader, 'download_dataset', return_value=True) as mock_download:
                    downloader.download_all_datasets(force=True)

                    mock_download.assert_called_once_with('dataset1', True)

    def test_download_all_datasets_partial_failure(self, temp_dir):
        """測試部分下載失敗"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                local_mock_config = Mock()
                local_mock_config.get.side_effect = lambda key, default=None: {
                    'paths.raw_data': 'data/raw',
                    'datasets': {
                        'dataset1': {'source': 'kaggle'},
                        'dataset2': {'source': 'kaggle'},
                        'dataset3': {'source': 'kaggle'}
                    }
                }.get(key, default)

                downloader = DataDownloader(config=local_mock_config)

                # 模擬第二個下載失敗
                with patch.object(downloader, 'download_dataset', side_effect=[True, False, True]):
                    downloader.download_all_datasets()
                    # 應該繼續執行，不拋出異常

    def test_download_all_datasets_empty(self, temp_dir):
        """測試空數據集列表"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                local_mock_config = Mock()
                local_mock_config.get.side_effect = lambda key, default=None: {
                    'paths.raw_data': 'data/raw',
                    'datasets': {}
                }.get(key, default)

                downloader = DataDownloader(config=local_mock_config)

                with patch.object(downloader, 'download_dataset') as mock_download:
                    downloader.download_all_datasets()

                    mock_download.assert_not_called()


class TestDownloadSampleData:
    """測試創建樣本數據"""

    def test_download_sample_data_creates_files(self, mock_config, temp_dir):
        """測試創建樣本數據文件"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                # 運行方法
                downloader.download_sample_data()

                # 驗證文件創建
                assert (Path(temp_dir) / 'disaster_tweets.csv').exists()
                assert (Path(temp_dir) / 'ecommerce_data.csv').exists()
                assert (Path(temp_dir) / 'Mall_Customers.csv').exists()

    def test_download_sample_data_disaster_tweets_structure(self, mock_config, temp_dir):
        """測試災難推文樣本數據結構"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                downloader.download_sample_data()

                # 讀取並驗證災難推文數據
                df = pd.read_csv(Path(temp_dir) / 'disaster_tweets.csv')
                assert len(df) == 100
                assert 'id' in df.columns
                assert 'text' in df.columns
                assert 'target' in df.columns
                assert df['target'].min() >= 0
                assert df['target'].max() <= 1

    def test_download_sample_data_ecommerce_structure(self, mock_config, temp_dir):
        """測試電子商務樣本數據結構"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                downloader.download_sample_data()

                # 讀取並驗證電子商務數據
                df = pd.read_csv(Path(temp_dir) / 'ecommerce_data.csv')
                assert len(df) == 1000
                assert 'InvoiceNo' in df.columns
                assert 'StockCode' in df.columns
                assert 'Description' in df.columns
                assert 'Quantity' in df.columns
                assert 'InvoiceDate' in df.columns
                assert 'UnitPrice' in df.columns
                assert 'CustomerID' in df.columns
                assert 'Country' in df.columns

    def test_download_sample_data_mall_customers_structure(self, mock_config, temp_dir):
        """測試商場客戶樣本數據結構"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                downloader.download_sample_data()

                # 讀取並驗證商場客戶數據
                df = pd.read_csv(Path(temp_dir) / 'Mall_Customers.csv')
                assert len(df) == 200
                assert 'CustomerID' in df.columns
                assert 'Gender' in df.columns
                assert 'Age' in df.columns
                assert 'Annual Income (k$)' in df.columns
                assert 'Spending Score (1-100)' in df.columns

                # 驗證數據範圍
                assert df['Age'].min() >= 18
                assert df['Age'].max() <= 70
                assert df['Spending Score (1-100)'].min() >= 1
                assert df['Spending Score (1-100)'].max() <= 100

    def test_download_sample_data_content_validity(self, mock_config, temp_dir):
        """測試樣本數據內容有效性"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                downloader.download_sample_data()

                # 檢查電子商務數據的國家選項
                df_ecommerce = pd.read_csv(Path(temp_dir) / 'ecommerce_data.csv')
                countries = df_ecommerce['Country'].unique()
                assert all(country in ['USA', 'UK', 'Canada', 'Australia'] for country in countries)

                # 檢查商場客戶的性別選項
                df_mall = pd.read_csv(Path(temp_dir) / 'Mall_Customers.csv')
                genders = df_mall['Gender'].unique()
                assert all(gender in ['Male', 'Female'] for gender in genders)

    def test_download_sample_data_no_exceptions(self, mock_config, temp_dir):
        """測試創建樣本數據不拋出異常"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader = DataDownloader(config=mock_config)
                downloader.raw_data_path = Path(temp_dir)

                # 應該不拋出任何異常
                try:
                    downloader.download_sample_data()
                    success = True
                except Exception:
                    success = False

                assert success is True


class TestEdgeCases:
    """測試邊界情況"""

    def test_download_with_invalid_dataset_name(self, mock_config, temp_dir):
        """測試使用無效的數據集名稱"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                mock_config.get_dataset_config.side_effect = ValueError("Dataset not found")

                downloader = DataDownloader(config=mock_config)
                result = downloader.download_dataset('invalid_dataset')

                assert result is False

    def test_multiple_initializations(self, mock_config, temp_dir):
        """測試多次初始化"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)

                downloader1 = DataDownloader(config=mock_config)
                downloader2 = DataDownloader(config=mock_config)

                # 兩個實例應該獨立
                assert downloader1 is not downloader2
                assert downloader1.config == downloader2.config

    def test_path_with_spaces(self, mock_config, temp_dir):
        """測試包含空格的路徑"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)
                mock_config.get.return_value = 'data with spaces/raw'

                downloader = DataDownloader(config=mock_config)

                # Compare via Path.parts (separator-agnostic).
                assert downloader.raw_data_path.parts[-2:] == ('data with spaces', 'raw')

    def test_unicode_in_paths(self, mock_config, temp_dir):
        """測試路徑中的 Unicode 字符"""
        with patch('data_analysis_chatbots.data_downloader.get_project_root') as mock_root:
            with patch('data_analysis_chatbots.data_downloader.ensure_dir'):
                mock_root.return_value = Path(temp_dir)
                mock_config.get.return_value = 'data/數據/raw'

                downloader = DataDownloader(config=mock_config)

                assert '數據' in str(downloader.raw_data_path)
