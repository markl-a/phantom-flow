"""Configuration loader for the Data Analysis with Chatbots project."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and manage configuration settings."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigLoader.

        Args:
            config_path: Path to the configuration file. If None, uses default path.
        """
        if config_path is None:
            # Default to config/config.yaml
            self.config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports nested keys with dot notation,
                 e.g., 'paths.data_root'). An empty string returns the entire
                 loaded config dict — convenient for "give me everything"
                 callers without needing a separate accessor.
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        # Empty key = whole config (matches the "give me everything" idiom).
        if key == "":
            return self.config

        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_paths(self) -> Dict[str, str]:
        """Get all path configurations."""
        return self.get('paths', {})

    def get_dataset_config(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dataset configuration dictionary
        """
        datasets = self.get('datasets', {})
        if dataset_name not in datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found in configuration")

        return datasets[dataset_name]

    def get_analysis_config(self, analysis_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific analysis type.

        Args:
            analysis_type: Type of analysis (e.g., 'rfm', 'clustering', 'clv')

        Returns:
            Analysis configuration dictionary
        """
        analysis = self.get('analysis', {})
        if analysis_type not in analysis:
            raise ValueError(f"Analysis type '{analysis_type}' not found in configuration")

        return analysis[analysis_type]

    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()

    def __repr__(self):
        return f"ConfigLoader(config_path='{self.config_path}')"
