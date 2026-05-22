"""
Example demonstrating enhanced configuration management features.

This example shows how to use:
1. Config validation
2. Loading from YAML/JSON files
3. Environment variable prefix support
4. Config reload capability
5. get_or_default method with type casting
6. Config export to dict/JSON/YAML
"""

import tempfile
from pathlib import Path
from ai_automation_framework.core.config import Config, ConfigValidationError, get_config, reset_config


def example_validation():
    """Example of configuration validation."""
    print("\n" + "="*60)
    print("1. Configuration Validation")
    print("="*60)

    # Valid configuration
    try:
        config = Config(
            max_tokens=2000,
            temperature=0.8,
            log_level="DEBUG"
        )
        print(f"✓ Valid config created: model={config.default_model}, temp={config.temperature}")
    except ValueError as e:
        print(f"✗ Validation failed: {e}")

    # Invalid configuration (will raise error)
    try:
        config = Config(temperature=3.0)  # Temperature must be 0-2
        print("✗ Should have failed!")
    except ValueError as e:
        print(f"✓ Validation caught invalid temperature: {e}")


def example_yaml_json_loading():
    """Example of loading configuration from YAML/JSON files."""
    print("\n" + "="*60)
    print("2. Loading from YAML/JSON Files")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create YAML config
        yaml_file = Path(tmpdir) / "config.yaml"
        yaml_content = """
default_model: gpt-4
max_tokens: 3000
temperature: 0.7
log_level: INFO
openai_api_key: sk-test-key
"""
        yaml_file.write_text(yaml_content)

        # Load from YAML
        config = Config.from_yaml(yaml_file)
        print(f"✓ Loaded from YAML: model={config.default_model}, tokens={config.max_tokens}")

        # Export to JSON
        json_file = Path(tmpdir) / "config.json"
        config.to_json(json_file)
        print(f"✓ Exported to JSON: {json_file}")

        # Load from JSON
        config2 = Config.from_json(json_file)
        print(f"✓ Loaded from JSON: model={config2.default_model}")


def example_env_prefix():
    """Example of environment variable prefix support."""
    print("\n" + "="*60)
    print("3. Environment Variable Prefix Support")
    print("="*60)

    import os

    # Set environment variables with prefix
    os.environ["AI_FRAMEWORK_DEFAULT_MODEL"] = "claude-3-opus"
    os.environ["AI_FRAMEWORK_MAX_TOKENS"] = "4096"
    os.environ["AI_FRAMEWORK_TEMPERATURE"] = "0.5"

    # Load with prefix
    config = Config.from_env(prefix="AI_FRAMEWORK_")
    print(f"✓ Loaded with prefix: model={config.default_model}, tokens={config.max_tokens}")

    # Cleanup
    for key in ["DEFAULT_MODEL", "MAX_TOKENS", "TEMPERATURE"]:
        os.environ.pop(f"AI_FRAMEWORK_{key}", None)


def example_reload():
    """Example of configuration reload capability."""
    print("\n" + "="*60)
    print("4. Configuration Reload")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_file = Path(tmpdir) / "config.yaml"

        # Initial config
        yaml_file.write_text("default_model: gpt-3.5-turbo\nmax_tokens: 1000\n")
        config = Config.from_yaml(yaml_file)
        print(f"✓ Initial: model={config.default_model}, tokens={config.max_tokens}")

        # Modify config file
        yaml_file.write_text("default_model: gpt-4\nmax_tokens: 4000\n")

        # Reload
        config.reload()
        print(f"✓ After reload: model={config.default_model}, tokens={config.max_tokens}")


def example_get_or_default():
    """Example of get_or_default with type casting."""
    print("\n" + "="*60)
    print("5. get_or_default with Type Casting")
    print("="*60)

    config = Config(max_tokens=2048, temperature=0.7)

    # Get existing value
    tokens = config.get_or_default("max_tokens", 1000, int)
    print(f"✓ Existing value: max_tokens={tokens}")

    # Get with default (key doesn't exist)
    custom_value = config.get_or_default("custom_timeout", 30, int)
    print(f"✓ Default value: custom_timeout={custom_value}")

    # Type casting
    temp_str = config.get_or_default("temperature", "0.5", float)
    print(f"✓ Type cast: temperature={temp_str} (type: {type(temp_str).__name__})")


def example_export():
    """Example of exporting configuration."""
    print("\n" + "="*60)
    print("6. Export Configuration")
    print("="*60)

    config = Config(
        default_model="gpt-4",
        max_tokens=2000,
        temperature=0.8,
        openai_api_key="sk-test-key"
    )

    # Export to dict
    config_dict = config.to_dict(exclude_none=True)
    print(f"✓ Exported to dict with {len(config_dict)} fields")

    # Export to JSON string
    json_str = config.to_json(indent=2, exclude_none=True)
    print(f"✓ Exported to JSON ({len(json_str)} chars)")
    print(f"  First 100 chars: {json_str[:100]}...")

    # Export to YAML string
    yaml_str = config.to_yaml(exclude_none=True)
    print(f"✓ Exported to YAML ({len(yaml_str)} chars)")

    # Save to file
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "exported_config.json"
        config.to_json(output_file)
        print(f"✓ Saved to file: {output_file.name}")


def example_global_config():
    """Example of using global config with reload."""
    print("\n" + "="*60)
    print("7. Global Config Management")
    print("="*60)

    import os

    # Set environment variable
    os.environ["AI_FRAMEWORK_DEFAULT_MODEL"] = "claude-3-sonnet"

    # Get global config (singleton pattern)
    config1 = get_config(prefix="AI_FRAMEWORK_")
    print(f"✓ First access: model={config1.default_model}")

    # Get again (returns same instance)
    config2 = get_config()
    print(f"✓ Second access (same instance): {config1 is config2}")

    # Force reload
    os.environ["AI_FRAMEWORK_DEFAULT_MODEL"] = "claude-3-opus"
    config3 = get_config(reload=True)
    print(f"✓ After reload: model={config3.default_model}")

    # Reset global config
    reset_config()
    print("✓ Global config reset")

    # Cleanup
    os.environ.pop("AI_FRAMEWORK_DEFAULT_MODEL", None)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Enhanced Configuration Management Examples")
    print("="*60)

    example_validation()
    example_yaml_json_loading()
    example_env_prefix()
    example_reload()
    example_get_or_default()
    example_export()
    example_global_config()

    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60)
