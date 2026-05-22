"""Data downloader for Kaggle datasets."""

import os
import subprocess
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger

from .config_loader import ConfigLoader
from .utils import get_project_root, ensure_dir, setup_logging


class DataDownloader:
    """Download datasets from Kaggle."""

    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        Initialize the DataDownloader.

        Args:
            config: Configuration loader instance. If None, creates a new one.
        """
        self.config = config or ConfigLoader()
        self.project_root = get_project_root()
        self.raw_data_path = self.project_root / self.config.get('paths.raw_data', 'data/raw')
        ensure_dir(self.raw_data_path)

    def _check_kaggle_setup(self) -> bool:
        """
        Check if Kaggle API is properly configured.

        Returns:
            True if Kaggle is configured, False otherwise
        """
        kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
        if not kaggle_json.exists():
            logger.error("Kaggle API credentials not found!")
            logger.info("To use Kaggle API:")
            logger.info("1. Go to https://www.kaggle.com/account")
            logger.info("2. Click 'Create New API Token'")
            logger.info("3. Save the kaggle.json file to ~/.kaggle/")
            logger.info("4. Run: chmod 600 ~/.kaggle/kaggle.json")
            return False

        # Check permissions (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            stat_info = os.stat(kaggle_json)
            current_permissions = stat_info.st_mode & 0o777

            # 檢查文件權限是否正確 (必須是 600)
            if current_permissions != 0o600:
                logger.error("Kaggle credentials file has incorrect permissions!")
                logger.error(f"Current permissions: {oct(current_permissions)}")
                logger.error("Required permissions: 0o600 (rw-------)")
                logger.info("")
                logger.info("Security Risk: Your API credentials are exposed to other users!")
                logger.info("")
                logger.info("To fix this issue, run:")
                logger.info(f"  chmod 600 {kaggle_json}")
                logger.info("")
                logger.info("This will:")
                logger.info("  - Give read/write access to owner only")
                logger.info("  - Remove all access from group and others")
                return False

            # 檢查文件所有權
            current_uid = os.getuid()
            file_uid = stat_info.st_uid
            if current_uid != file_uid:
                import pwd
                try:
                    file_owner = pwd.getpwuid(file_uid).pw_name
                    current_user = pwd.getpwuid(current_uid).pw_name
                except KeyError:
                    file_owner = str(file_uid)
                    current_user = str(current_uid)

                logger.error("Kaggle credentials file has incorrect ownership!")
                logger.error(f"File owner: {file_owner} (UID: {file_uid})")
                logger.error(f"Current user: {current_user} (UID: {current_uid})")
                logger.info("")
                logger.info("To fix this issue, run:")
                logger.info(f"  sudo chown {current_user} {kaggle_json}")
                logger.info(f"  chmod 600 {kaggle_json}")
                return False

        return True

    def download_dataset(self, dataset_name: str, force: bool = False) -> bool:
        """
        Download a dataset from Kaggle.

        Args:
            dataset_name: Name of the dataset configuration
            force: If True, re-download even if file exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get dataset configuration
            dataset_config = self.config.get_dataset_config(dataset_name)
            dataset_id = dataset_config.get('dataset_id')
            filename = dataset_config.get('filename')
            source = dataset_config.get('source')

            if source != 'kaggle':
                logger.warning(f"Dataset {dataset_name} is not from Kaggle. Source: {source}")
                return False

            # Check if file already exists
            file_path = self.raw_data_path / filename
            if file_path.exists() and not force:
                logger.info(f"Dataset {dataset_name} already exists at {file_path}")
                logger.info("Use force=True to re-download")
                return True

            # Check Kaggle setup
            if not self._check_kaggle_setup():
                return False

            logger.info(f"Downloading dataset: {dataset_name} ({dataset_id})")

            # Download using Kaggle API
            cmd = [
                'kaggle', 'datasets', 'download',
                '-d', dataset_id,
                '-p', str(self.raw_data_path),
                '--unzip'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.success(f"Successfully downloaded {dataset_name}")
                return True
            else:
                logger.error(f"Failed to download {dataset_name}")
                logger.error(f"Error: {result.stderr}")
                return False

        except (subprocess.SubprocessError, OSError, KeyError, ValueError, FileNotFoundError) as e:
            logger.error(f"Error downloading dataset {dataset_name}: {e}")
            return False

    def download_all_datasets(self, force: bool = False):
        """
        Download all datasets defined in the configuration.

        Args:
            force: If True, re-download even if files exist
        """
        datasets = self.config.get('datasets', {})
        total = len(datasets)
        success_count = 0

        logger.info(f"Starting download of {total} datasets...")

        for dataset_name in datasets.keys():
            logger.info(f"\n{'='*60}")
            logger.info(f"Dataset {success_count + 1}/{total}: {dataset_name}")
            logger.info(f"{'='*60}")

            if self.download_dataset(dataset_name, force):
                success_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Download completed: {success_count}/{total} successful")
        logger.info(f"{'='*60}")

    def download_sample_data(self):
        """
        Create sample datasets for testing when Kaggle data is not available.
        """
        import numpy as np

        logger.info("Creating sample datasets for testing...")

        # Sample Disaster Tweets
        disaster_tweets = pd.DataFrame({
            'id': range(1, 101),
            'text': [f"Sample disaster tweet {i}" for i in range(1, 101)],
            'target': np.random.randint(0, 2, 100)
        })
        disaster_path = self.raw_data_path / 'disaster_tweets.csv'
        disaster_tweets.to_csv(disaster_path, index=False)
        logger.success(f"Created sample disaster tweets: {disaster_path}")

        # Sample E-Commerce Data
        ecommerce = pd.DataFrame({
            'InvoiceNo': [f'INV{i:05d}' for i in range(1, 1001)],
            'StockCode': [f'ITEM{i%50:03d}' for i in range(1, 1001)],
            'Description': [f'Product {i%50}' for i in range(1, 1001)],
            'Quantity': np.random.randint(1, 20, 1000),
            'InvoiceDate': pd.date_range('2024-01-01', periods=1000, freq='H'),
            'UnitPrice': np.random.uniform(5, 100, 1000).round(2),
            'CustomerID': np.random.randint(1000, 1200, 1000),
            'Country': np.random.choice(['USA', 'UK', 'Canada', 'Australia'], 1000)
        })
        ecommerce_path = self.raw_data_path / 'ecommerce_data.csv'
        ecommerce.to_csv(ecommerce_path, index=False)
        logger.success(f"Created sample e-commerce data: {ecommerce_path}")

        # Sample Mall Customers
        mall_customers = pd.DataFrame({
            'CustomerID': range(1, 201),
            'Gender': np.random.choice(['Male', 'Female'], 200),
            'Age': np.random.randint(18, 70, 200),
            'Annual Income (k$)': np.random.randint(15, 140, 200),
            'Spending Score (1-100)': np.random.randint(1, 100, 200)
        })
        mall_path = self.raw_data_path / 'Mall_Customers.csv'
        mall_customers.to_csv(mall_path, index=False)
        logger.success(f"Created sample mall customers: {mall_path}")

        logger.success("All sample datasets created successfully!")


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Download datasets for Data Analysis with Chatbots')
    parser.add_argument('--dataset', type=str, help='Specific dataset to download')
    parser.add_argument('--all', action='store_true', help='Download all datasets')
    parser.add_argument('--force', action='store_true', help='Force re-download existing datasets')
    parser.add_argument('--sample', action='store_true', help='Create sample datasets for testing')

    args = parser.parse_args()

    # Setup logging
    setup_logging(level="INFO")

    downloader = DataDownloader()

    if args.sample:
        downloader.download_sample_data()
    elif args.all:
        downloader.download_all_datasets(force=args.force)
    elif args.dataset:
        downloader.download_dataset(args.dataset, force=args.force)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
