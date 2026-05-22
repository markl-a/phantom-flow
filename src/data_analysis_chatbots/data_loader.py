"""Data loader for various datasets used in the project.

提供安全的數據加載功能，包括：
- 文件類型驗證
- 文件大小限制
- 路徑安全檢查
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Union
from loguru import logger

from .config_loader import ConfigLoader
from .utils import get_project_root, ensure_dir
from .exceptions import ValidationError


# 安全配置
ALLOWED_EXTENSIONS: Set[str] = {'.csv', '.xlsx', '.xls', '.json', '.parquet'}
MAX_FILE_SIZE_MB: int = 500  # 最大文件大小（MB）


def validate_data_file(
    file_path: Path,
    allowed_extensions: Optional[Set[str]] = None,
    max_size_mb: Optional[int] = None
) -> None:
    """驗證數據文件的安全性

    Args:
        file_path: 文件路徑
        allowed_extensions: 允許的文件擴展名集合
        max_size_mb: 最大文件大小（MB）

    Raises:
        ValidationError: 當文件驗證失敗時
        FileNotFoundError: 當文件不存在時
    """
    file_path = Path(file_path)

    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    if max_size_mb is None:
        max_size_mb = MAX_FILE_SIZE_MB

    # 檢查文件是否存在
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 檢查是否是文件（而非目錄）
    if not file_path.is_file():
        raise ValidationError(f"路徑不是文件: {file_path}")

    # 檢查文件擴展名
    extension = file_path.suffix.lower()
    if extension not in allowed_extensions:
        raise ValidationError(
            f"不支持的文件類型: {extension}。"
            f"允許的類型: {', '.join(allowed_extensions)}"
        )

    # 檢查文件大小
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValidationError(
            f"文件過大: {file_size_mb:.2f} MB。"
            f"最大允許: {max_size_mb} MB"
        )

    # 檢查符號鏈接（防止路徑遍歷）
    try:
        resolved_path = file_path.resolve(strict=True)
        # 確保解析後的路徑仍在預期目錄內
        if not str(resolved_path).startswith(str(file_path.parent.resolve())):
            raise ValidationError(f"潛在的路徑遍歷攻擊: {file_path}")
    except OSError as e:
        raise ValidationError(f"無法解析路徑: {file_path}. 錯誤: {e}")

    logger.debug(f"文件驗證通過: {file_path} ({file_size_mb:.2f} MB)")


class DataLoader:
    """Load and manage datasets for analysis."""

    def __init__(self, config: Optional[ConfigLoader] = None) -> None:
        """
        Initialize the DataLoader.

        Args:
            config: Configuration loader instance. If None, creates a new one.
        """
        self.config = config or ConfigLoader()
        self.project_root = get_project_root()
        self._setup_paths()

    def _setup_paths(self) -> None:
        """Setup data paths from configuration."""
        paths = self.config.get_paths()
        self.data_root = self.project_root / paths.get('data_root', 'data')
        self.raw_data_path = self.project_root / paths.get('raw_data', 'data/raw')
        self.processed_data_path = self.project_root / paths.get('processed_data', 'data/processed')
        self.outputs_path = self.project_root / paths.get('outputs', 'data/outputs')

        # Ensure directories exist
        for path in [self.raw_data_path, self.processed_data_path, self.outputs_path]:
            ensure_dir(path)

    def load_dataset(self, dataset_name: str, data_type: str = 'raw') -> pd.DataFrame:
        """
        Load a dataset by name.

        Args:
            dataset_name: Name of the dataset (e.g., 'disaster_tweets', 'ecommerce')
            data_type: Type of data to load ('raw' or 'processed')

        Returns:
            DataFrame containing the dataset

        Raises:
            FileNotFoundError: If the dataset file doesn't exist
            ValueError: If the dataset name is not recognized
        """
        try:
            dataset_config = self.config.get_dataset_config(dataset_name)
            filename = dataset_config.get('filename')

            if data_type == 'raw':
                file_path = self.raw_data_path / filename
            elif data_type == 'processed':
                file_path = self.processed_data_path / filename
            else:
                raise ValueError(f"Invalid data_type: {data_type}. Must be 'raw' or 'processed'")

            if not file_path.exists():
                logger.warning(f"Dataset file not found: {file_path}")
                logger.info(f"To download datasets, run: python -m data_analysis_chatbots.data_downloader")
                raise FileNotFoundError(f"Dataset file not found: {file_path}")

            # 驗證文件安全性
            try:
                validate_data_file(file_path)
            except ValidationError as e:
                logger.error(f"File validation failed: {e}")
                raise

            # Load the data
            logger.info(f"Loading dataset: {dataset_name} from {file_path}")
            df = pd.read_csv(file_path)
            logger.success(f"Successfully loaded {len(df)} rows from {dataset_name}")

            return df

        except Exception as e:
            logger.error(f"Error loading dataset {dataset_name}: {e}")
            raise

    def load_disaster_tweets(self, data_type: str = 'raw') -> pd.DataFrame:
        """Load the Disaster Tweets dataset."""
        return self.load_dataset('disaster_tweets', data_type)

    def load_ecommerce(self, data_type: str = 'raw') -> pd.DataFrame:
        """Load the E-Commerce dataset."""
        return self.load_dataset('ecommerce', data_type)

    def load_mall_customers(self, data_type: str = 'raw') -> pd.DataFrame:
        """Load the Mall Customers dataset."""
        return self.load_dataset('mall_customers', data_type)

    def load_personality(self, data_type: str = 'raw') -> pd.DataFrame:
        """Load the Customer Personality Analysis dataset."""
        return self.load_dataset('personality', data_type)

    def load_marketing_segmentation(self, data_type: str = 'raw') -> pd.DataFrame:
        """Load the Marketing Segmentation dataset."""
        return self.load_dataset('marketing_segmentation', data_type)

    def save_processed_data(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Save processed data to the processed data directory.

        Args:
            df: DataFrame to save
            filename: Name of the file to save

        Returns:
            Path to the saved file
        """
        file_path = self.processed_data_path / filename
        logger.info(f"Saving processed data to {file_path}")
        df.to_csv(file_path, index=False)
        logger.success(f"Successfully saved {len(df)} rows to {filename}")
        return file_path

    def save_output(self, df: pd.DataFrame, filename: str, file_format: str = 'csv') -> Path:
        """
        Save analysis output to the outputs directory.

        Args:
            df: DataFrame to save
            filename: Name of the file to save
            file_format: Format to save ('csv', 'excel', 'json')

        Returns:
            Path to the saved file
        """
        if not filename.endswith(f'.{file_format}'):
            filename = f"{filename}.{file_format}"

        file_path = self.outputs_path / filename
        logger.info(f"Saving output to {file_path}")

        if file_format == 'csv':
            df.to_csv(file_path, index=False)
        elif file_format == 'excel':
            df.to_excel(file_path, index=False)
        elif file_format == 'json':
            df.to_json(file_path, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        logger.success(f"Successfully saved output to {filename}")
        return file_path

    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get information about a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dictionary containing dataset information
        """
        return self.config.get_dataset_config(dataset_name)

    def list_available_datasets(self) -> List[str]:
        """
        List all available datasets in the configuration.

        Returns:
            List of dataset names
        """
        datasets = self.config.get('datasets', {})
        return list(datasets.keys())

    # ── generic file IO helpers ──────────────────────────────────────────
    # The methods above (`load_disaster_tweets`, `load_ecommerce`, etc.)
    # are dataset-specific shortcuts that look the path up via the config
    # registry. The methods below are generic readers any caller can use
    # to load arbitrary CSV / Excel files without registering them first.

    def load_csv(self, path: Union[str, Path], **kwargs: Any) -> pd.DataFrame:
        """Read a CSV file into a DataFrame.

        Thin wrapper around ``pandas.read_csv`` — every kwarg
        (``encoding``, ``parse_dates``, ``index_col``, ``sep``, ...)
        is forwarded verbatim. Raises ``FileNotFoundError`` if the
        path doesn't exist.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        return pd.read_csv(p, **kwargs)

    def load_excel(self, path: Union[str, Path], **kwargs: Any) -> pd.DataFrame:
        """Read an Excel file into a DataFrame (wraps ``pandas.read_excel``)."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")
        return pd.read_excel(p, **kwargs)

    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required: List[str]) -> bool:
        """Return True iff every column in ``required`` is present in ``df``."""
        return all(col in df.columns for col in required)

    @staticmethod
    def get_data_info(df: pd.DataFrame) -> Dict[str, Any]:
        """Return basic shape / dtype / null information about a DataFrame."""
        return {
            'shape':         df.shape,
            'columns':       list(df.columns),
            'dtypes':        {col: str(dt) for col, dt in df.dtypes.items()},
            'null_counts':   {col: int(n) for col, n in df.isnull().sum().items()},
            'memory_usage':  int(df.memory_usage(deep=True).sum()),
        }

    @staticmethod
    def sample_data(df: pd.DataFrame, n: int = 10, random_state: Optional[int] = None) -> pd.DataFrame:
        """Return a random sample of ``n`` rows from ``df``.

        If ``n`` exceeds ``len(df)`` the full frame is returned instead
        of raising — convenient for small fixtures in tests.
        """
        n = min(n, len(df))
        return df.sample(n=n, random_state=random_state)
