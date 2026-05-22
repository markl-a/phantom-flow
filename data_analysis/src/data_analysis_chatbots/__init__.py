"""
Data Analysis with Chatbots
===========================

A comprehensive framework for customer analytics and segmentation using AI-powered chatbots.

Modules:
    - preprocessing: Data cleaning and preprocessing utilities
    - clustering: Customer segmentation and clustering algorithms
    - visualization: Data visualization tools
    - marketing: Marketing strategy and campaign management
    - exceptions: Custom exception classes
    - init: Project initialization utilities
    - kaggle_downloader: Kaggle dataset download utilities
"""

__version__ = "1.0.0"
__author__ = "賴祺清"

from .config_loader import ConfigLoader
from .data_loader import DataLoader
from .utils import setup_logging, ensure_dir

# Import Kaggle downloader
from .kaggle_downloader import KaggleDatasetDownloader, quick_download, setup_kaggle_credentials

# Import exceptions for convenient access
from .exceptions import (
    DataAnalysisError,
    DataLoadError,
    DataDownloadError,
    ValidationError,
    ClusteringError,
    RFMAnalysisError,
    CLVPredictionError,
    ConfigurationError,
    VisualizationError,
    PreprocessingError,
    ModelSaveError,
    ModelLoadError,
    FeatureEngineeringError,
    CampaignError,
)

# Import initialization utilities
from .init import initialize_project, validate_project_structure, get_project_root

# Import model utilities
from . import model_utils

__all__ = [
    # Core utilities
    "ConfigLoader",
    "DataLoader",
    "setup_logging",
    "ensure_dir",
    # Kaggle downloader
    "KaggleDatasetDownloader",
    "quick_download",
    "setup_kaggle_credentials",
    # Exceptions
    "DataAnalysisError",
    "DataLoadError",
    "DataDownloadError",
    "ValidationError",
    "ClusteringError",
    "RFMAnalysisError",
    "CLVPredictionError",
    "ConfigurationError",
    "VisualizationError",
    "PreprocessingError",
    "ModelSaveError",
    "ModelLoadError",
    "FeatureEngineeringError",
    "CampaignError",
    # Initialization
    "initialize_project",
    "validate_project_structure",
    "get_project_root",
    # Model utilities
    "model_utils",
]
