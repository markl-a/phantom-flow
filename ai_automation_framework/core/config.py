"""Configuration management for the AI Automation Framework."""

import os
import json
import yaml
from typing import Optional, Dict, Any, Type, TypeVar, Union
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError


T = TypeVar('T')


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


class Config(BaseModel):
    """
    Configuration class for AI Automation Framework.

    Loads configuration from environment variables and provides
    a centralized way to access settings.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    cohere_api_key: Optional[str] = Field(default=None, description="Cohere API key")

    # Model Configuration
    default_model: str = Field(default="gpt-4o", description="Default LLM model")
    default_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Default embedding model"
    )
    max_tokens: int = Field(default=4096, description="Maximum tokens for generation")
    temperature: float = Field(default=0.7, description="Temperature for generation")

    # Vector Database
    chroma_persist_directory: str = Field(
        default="./data/chroma",
        description="ChromaDB persistence directory"
    )
    vector_db_type: str = Field(default="chroma", description="Vector database type")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/ai_automation.log", description="Log file path")

    # Paths
    data_dir: Path = Field(default=Path("./data"), description="Data directory")
    logs_dir: Path = Field(default=Path("./logs"), description="Logs directory")

    # Internal tracking for reload capability
    _source_file: Optional[str] = None
    _env_prefix: str = "AI_FRAMEWORK_"

    # Validators
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is positive."""
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        return v

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator('vector_db_type')
    @classmethod
    def validate_vector_db_type(cls, v: str) -> str:
        """Validate vector database type."""
        valid_types = {"chroma", "pinecone", "weaviate", "qdrant"}
        if v.lower() not in valid_types:
            raise ValueError(f"vector_db_type must be one of {valid_types}")
        return v.lower()

    @classmethod
    def from_env(cls, env_file: Optional[str] = None, prefix: str = "AI_FRAMEWORK_") -> "Config":
        """
        Load configuration from environment variables with optional prefix support.

        Args:
            env_file: Path to .env file. If None, uses default .env
            prefix: Environment variable prefix (e.g., 'AI_FRAMEWORK_')

        Returns:
            Config instance

        Raises:
            ConfigValidationError: If configuration validation fails
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
            """Get environment variable with or without prefix."""
            # Try with prefix first
            value: Optional[str] = os.getenv(f"{prefix}{key}")
            if value is not None:
                return value
            # Fall back to key without prefix
            return os.getenv(key, default)

        try:
            config = cls(
                openai_api_key=get_env("OPENAI_API_KEY"),
                anthropic_api_key=get_env("ANTHROPIC_API_KEY"),
                google_api_key=get_env("GOOGLE_API_KEY"),
                cohere_api_key=get_env("COHERE_API_KEY"),
                default_model=get_env("DEFAULT_MODEL", "gpt-4o"),
                default_embedding_model=get_env("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small"),
                max_tokens=int(get_env("MAX_TOKENS", "4096")),
                temperature=float(get_env("TEMPERATURE", "0.7")),
                chroma_persist_directory=get_env("CHROMA_PERSIST_DIRECTORY", "./data/chroma"),
                vector_db_type=get_env("VECTOR_DB_TYPE", "chroma"),
                log_level=get_env("LOG_LEVEL", "INFO"),
                log_file=get_env("LOG_FILE", "./logs/ai_automation.log"),
            )
            config._env_prefix = prefix
            if env_file:
                config._source_file = env_file
            return config
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e

    @classmethod
    def from_yaml(cls, yaml_file: Union[str, Path]) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            yaml_file: Path to YAML configuration file

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ConfigValidationError: If configuration validation fails
        """
        yaml_path = Path(yaml_file)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")

        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            # Convert path strings to Path objects
            if 'data_dir' in data and isinstance(data['data_dir'], str):
                data['data_dir'] = Path(data['data_dir'])
            if 'logs_dir' in data and isinstance(data['logs_dir'], str):
                data['logs_dir'] = Path(data['logs_dir'])

            config = cls(**data)
            config._source_file = str(yaml_path)
            return config
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e
        except Exception as e:
            raise ConfigValidationError(f"Failed to load YAML config: {e}") from e

    @classmethod
    def from_json(cls, json_file: Union[str, Path]) -> "Config":
        """
        Load configuration from JSON file.

        Args:
            json_file: Path to JSON configuration file

        Returns:
            Config instance

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ConfigValidationError: If configuration validation fails
        """
        json_path = Path(json_file)
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Convert path strings to Path objects
            if 'data_dir' in data and isinstance(data['data_dir'], str):
                data['data_dir'] = Path(data['data_dir'])
            if 'logs_dir' in data and isinstance(data['logs_dir'], str):
                data['logs_dir'] = Path(data['logs_dir'])

            config = cls(**data)
            config._source_file = str(json_path)
            return config
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e
        except Exception as e:
            raise ConfigValidationError(f"Failed to load JSON config: {e}") from e

    def reload(self) -> None:
        """
        Reload configuration from the original source.

        Raises:
            RuntimeError: If no source file was recorded
            ConfigValidationError: If configuration validation fails
        """
        if not self._source_file:
            raise RuntimeError("Cannot reload: no source file recorded")

        source_path = Path(self._source_file)
        suffix = source_path.suffix.lower()

        if suffix in ['.yaml', '.yml']:
            new_config = self.from_yaml(self._source_file)
        elif suffix == '.json':
            new_config = self.from_json(self._source_file)
        elif suffix == '.env':
            new_config = self.from_env(self._source_file, self._env_prefix)
        else:
            raise RuntimeError(f"Cannot reload from unsupported file type: {suffix}")

        # Update all fields from new config
        for field_name in self.model_fields.keys():
            if not field_name.startswith('_'):
                setattr(self, field_name, getattr(new_config, field_name))

    def get_or_default(self, key: str, default: T, cast_type: Optional[Type[T]] = None) -> T:
        """
        Get configuration value with type casting and default fallback.

        Args:
            key: Configuration key
            default: Default value if key not found
            cast_type: Type to cast the value to (optional)

        Returns:
            Configuration value or default

        Examples:
            >>> config.get_or_default('max_tokens', 1000, int)
            >>> config.get_or_default('custom_key', 'default_value', str)
        """
        try:
            value = getattr(self, key, default)

            # If cast_type is specified, try to cast the value
            if cast_type is not None and value is not None:
                if cast_type == bool:
                    # Special handling for boolean casting
                    if isinstance(value, str):
                        return cast_type(value.lower() in ('true', '1', 'yes', 'on'))
                    return cast_type(value)
                elif cast_type == Path:
                    return Path(str(value))
                else:
                    return cast_type(value)

            return value
        except (AttributeError, ValueError, TypeError):
            return default

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_directory).parent.mkdir(parents=True, exist_ok=True)

    def to_dict(self, exclude_none: bool = False, exclude_private: bool = True) -> Dict[str, Any]:
        """
        Convert config to dictionary.

        Args:
            exclude_none: Exclude fields with None values
            exclude_private: Exclude private fields (starting with _)

        Returns:
            Dictionary representation of config
        """
        data = self.model_dump(exclude_none=exclude_none)

        # Convert Path objects to strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)

        # Remove private fields if requested
        if exclude_private:
            data = {k: v for k, v in data.items() if not k.startswith('_')}

        return data

    def to_json(self, file_path: Optional[Union[str, Path]] = None,
                indent: int = 2, exclude_none: bool = False) -> str:
        """
        Export configuration to JSON format.

        Args:
            file_path: Optional file path to write JSON to
            indent: JSON indentation level
            exclude_none: Exclude fields with None values

        Returns:
            JSON string representation

        Raises:
            IOError: If writing to file fails
        """
        data = self.to_dict(exclude_none=exclude_none, exclude_private=True)
        json_str = json.dumps(data, indent=indent)

        if file_path:
            try:
                output_path = Path(file_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(json_str)
            except Exception as e:
                raise IOError(f"Failed to write JSON to {file_path}: {e}") from e

        return json_str

    def to_yaml(self, file_path: Optional[Union[str, Path]] = None,
                exclude_none: bool = False) -> str:
        """
        Export configuration to YAML format.

        Args:
            file_path: Optional file path to write YAML to
            exclude_none: Exclude fields with None values

        Returns:
            YAML string representation

        Raises:
            IOError: If writing to file fails
        """
        data = self.to_dict(exclude_none=exclude_none, exclude_private=True)
        yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)

        if file_path:
            try:
                output_path = Path(file_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(yaml_str)
            except Exception as e:
                raise IOError(f"Failed to write YAML to {file_path}: {e}") from e

        return yaml_str

    def validate_config(self) -> bool:
        """
        Validate the current configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            # Re-validate using Pydantic
            self.model_validate(self.model_dump())
            return True
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}") from e


# Global config instance
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None, prefix: str = "AI_FRAMEWORK_",
               reload: bool = False) -> Config:
    """
    Get or create global config instance.

    Args:
        env_file: Path to .env file
        prefix: Environment variable prefix
        reload: Force reload of configuration

    Returns:
        Config instance
    """
    global _config
    if _config is None or reload:
        _config = Config.from_env(env_file, prefix)
        _config.ensure_directories()
    return _config


def reset_config() -> None:
    """Reset the global config instance."""
    global _config
    _config = None
