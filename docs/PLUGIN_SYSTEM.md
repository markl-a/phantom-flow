# AI Automation Framework - Plugin System

## Overview

The AI Automation Framework includes a comprehensive plugin system that allows you to extend the framework with custom functionality. The plugin system provides:

- **Plugin base class** with lifecycle hooks (on_load, on_unload, on_enable, on_disable)
- **PluginManager** for discovering and loading plugins
- **Dependency resolution** to ensure plugins load in the correct order
- **Configuration support** for plugin-specific settings
- **Hot reload capability** (planned)
- **Plugin isolation** and error handling
- **Plugin metadata** (name, version, author, description, dependencies)

## Architecture

### Core Components

1. **Plugin**: Abstract base class that all plugins must inherit from
2. **PluginManager**: Main interface for managing plugins
3. **PluginRegistry**: Registry for tracking loaded plugins
4. **PluginLoader**: Loads plugins from files or packages
5. **DependencyResolver**: Resolves plugin dependencies using topological sort
6. **PluginMetadata**: Stores plugin information
7. **PluginConfig**: Stores plugin configuration

### Plugin States

Plugins can be in one of five states:

- `UNLOADED`: Plugin is not loaded
- `LOADED`: Plugin is loaded but not enabled
- `ENABLED`: Plugin is active and providing functionality
- `DISABLED`: Plugin is loaded but temporarily disabled
- `ERROR`: Plugin encountered an error

### Lifecycle Hooks

Plugins implement four lifecycle hooks:

```python
class MyPlugin(Plugin):
    def on_load(self) -> None:
        """Called when plugin is loaded. Initialize resources here."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded. Clean up resources here."""
        pass

    def on_enable(self) -> None:
        """Called when plugin is enabled. Start providing functionality."""
        pass

    def on_disable(self) -> None:
        """Called when plugin is disabled. Stop providing functionality."""
        pass

    def on_config_change(self, new_config: PluginConfig) -> None:
        """Called when configuration changes."""
        pass
```

## Creating a Plugin

### Step 1: Create Plugin Class

Create a Python file with your plugin class:

```python
# my_plugin.py
from ai_automation_framework.core.plugins import (
    Plugin,
    PluginMetadata,
    PluginConfig,
    PluginLoadError,
    PluginError
)


class MyPlugin(Plugin):
    """My custom plugin."""

    def on_load(self) -> None:
        """Initialize plugin resources."""
        self.logger.info("Loading MyPlugin...")
        # Initialize your resources here
        self._data = []

    def on_unload(self) -> None:
        """Clean up plugin resources."""
        self.logger.info("Unloading MyPlugin...")
        # Clean up resources
        self._data = None

    def on_enable(self) -> None:
        """Enable plugin functionality."""
        self.logger.info("Enabling MyPlugin...")
        # Start providing functionality

    def on_disable(self) -> None:
        """Disable plugin functionality."""
        self.logger.info("Disabling MyPlugin...")
        # Stop providing functionality

    # Add your custom methods
    def process_data(self, data: str) -> str:
        """Custom plugin method."""
        return f"MyPlugin processed: {data}"


# Export the plugin class
Plugin = MyPlugin
```

### Step 2: Create Metadata File

Create a YAML file with plugin metadata:

```yaml
# plugin.yaml
name: my_plugin
version: 1.0.0
author: Your Name
description: My custom plugin for doing awesome things
dependencies:
  - other_plugin  # Optional: list plugins this depends on
entry_point: Plugin
compatible_versions:
  - 1.0.0
tags:
  - custom
  - example
config_schema:
  type: object
  properties:
    setting1:
      type: string
      default: "value1"
    setting2:
      type: integer
      default: 42
```

### Step 3: Directory Structure

Organize your plugin files:

```
plugins/
├── my_plugin/
│   ├── plugin.yaml      # Metadata
│   └── plugin.py        # Plugin code
└── another_plugin/
    ├── plugin.yaml
    └── plugin.py
```

Or use a flat structure:

```
plugins/
├── my_plugin.py
├── my_plugin.yaml
├── another_plugin.py
└── another_plugin.yaml
```

## Using the Plugin System

### Basic Usage

```python
from ai_automation_framework.core.plugins import PluginManager

# Create plugin manager with auto-discovery
manager = PluginManager(
    plugin_dirs=["./plugins"],
    auto_discover=True
)

# Get a plugin
plugin = manager.get_plugin("my_plugin")

# Use the plugin
if plugin and plugin.state == PluginState.ENABLED:
    result = plugin.process_data("hello")
    print(result)

# Cleanup
manager.shutdown()
```

### Manual Plugin Loading

```python
from pathlib import Path
from ai_automation_framework.core.plugins import (
    PluginManager,
    PluginMetadata,
    PluginConfig
)

manager = PluginManager(auto_discover=False)

# Define metadata
metadata = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    author="Your Name",
    description="My plugin",
    dependencies=[]
)

# Define configuration
config = PluginConfig(
    enabled=True,
    priority=100,
    settings={"setting1": "custom_value"}
)

# Load the plugin
plugin = manager.load_plugin(
    metadata,
    file_path=Path("./plugins/my_plugin.py"),
    config=config
)
```

### Plugin Management

```python
# List all plugins
plugins = manager.list_plugins()
for info in plugins:
    print(f"{info['name']}: {info['state']}")

# Enable/disable plugins
manager.enable_plugin("my_plugin")
manager.disable_plugin("my_plugin")

# Get enabled plugins
enabled = manager.get_enabled_plugins()

# Configure a plugin
new_config = PluginConfig(
    enabled=True,
    priority=50,
    settings={"setting1": "new_value"}
)
manager.configure_plugin("my_plugin", new_config)

# Get plugin info
info = manager.get_plugin_info("my_plugin")
print(info)
```

### Context Manager

```python
# Automatic cleanup with context manager
with PluginManager(plugin_dirs=["./plugins"]) as manager:
    plugin = manager.get_plugin("my_plugin")
    # Use plugin...
# Automatically shuts down on exit
```

## Plugin Dependencies

### Declaring Dependencies

In your `plugin.yaml`:

```yaml
name: my_advanced_plugin
version: 1.0.0
author: Your Name
description: Plugin that depends on others
dependencies:
  - base_plugin
  - utility_plugin
```

### Dependency Resolution

The plugin system automatically:
1. Resolves dependencies using topological sort
2. Loads plugins in the correct order
3. Ensures dependencies are enabled before dependent plugins
4. Prevents disabling plugins that others depend on

```python
# Dependencies are automatically handled
manager = PluginManager(
    plugin_dirs=["./plugins"],
    auto_discover=True  # Discovers and loads in correct order
)
```

### Circular Dependency Detection

The system detects and prevents circular dependencies:

```python
# If plugin A depends on B, and B depends on A:
# PluginDependencyError: Circular dependency detected
```

## Configuration

### Plugin Configuration Schema

Define configuration schema in metadata:

```yaml
config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: API key for the service
    timeout:
      type: integer
      default: 30
    enabled:
      type: boolean
      default: true
```

### Using Configuration

```python
class MyPlugin(Plugin):
    def on_enable(self) -> None:
        # Access configuration
        api_key = self.config.settings.get("api_key")
        timeout = self.config.settings.get("timeout", 30)

        # Use configuration values
        self.client = SomeClient(api_key=api_key, timeout=timeout)

    def on_config_change(self, new_config: PluginConfig) -> None:
        """Handle configuration changes."""
        super().on_config_change(new_config)

        # Update client with new config
        if hasattr(self, "client"):
            self.client.update_config(new_config.settings)
```

## Error Handling

### Plugin Errors

```python
from ai_automation_framework.core.plugins import (
    PluginError,
    PluginLoadError,
    PluginDependencyError,
    PluginConfigurationError
)

try:
    plugin = manager.load_plugin(metadata, file_path="./plugin.py")
except PluginLoadError as e:
    print(f"Failed to load plugin: {e}")
except PluginDependencyError as e:
    print(f"Dependency error: {e}")
```

### Error State

When a plugin encounters an error, it enters the `ERROR` state:

```python
plugin = manager.get_plugin("my_plugin")
if plugin.state == PluginState.ERROR:
    error = plugin.get_error()
    print(f"Plugin error: {error}")
```

### Graceful Error Handling

The plugin system handles errors gracefully:

```python
# If a plugin fails to load, others continue
manager = PluginManager(plugin_dirs=["./plugins"])

# Failed plugins are logged but don't stop the system
for name, plugin in manager.get_all_plugins().items():
    if plugin.state == PluginState.ERROR:
        print(f"{name} failed: {plugin.get_error()}")
```

## Advanced Features

### Plugin Registry Hooks

Register callbacks for plugin events:

```python
def on_plugin_loaded(plugin):
    print(f"Plugin loaded: {plugin.metadata.name}")

manager.registry.register_hook("plugin_loaded", on_plugin_loaded)

# Call hooks
manager.registry.call_hooks("plugin_loaded", plugin)
```

### Plugin Priority

Control plugin loading priority:

```python
config = PluginConfig(
    priority=10  # Lower number = higher priority
)

# Plugins are sorted by priority
plugins = manager.list_plugins()  # Already sorted by priority
```

### Plugin Discovery

Discover plugins without loading:

```python
# Discover plugins in a directory
metadata_list = manager.discover_plugins()

for metadata in metadata_list:
    print(f"Found: {metadata.name} v{metadata.version}")
    print(f"  Dependencies: {metadata.dependencies}")
```

### Plugin Isolation

Each plugin runs in isolation with:

- Separate logger instance
- Thread-safe operations
- Error containment (errors don't crash other plugins)
- Resource cleanup on unload

## Best Practices

### 1. Use Lifecycle Hooks Correctly

```python
class WellDesignedPlugin(Plugin):
    def on_load(self) -> None:
        """Load: Initialize resources that don't depend on other plugins."""
        self._cache = {}
        self._config_file = Path("config.json")

    def on_enable(self) -> None:
        """Enable: Start services and connect to other plugins."""
        self._start_service()
        self._connect_to_dependencies()

    def on_disable(self) -> None:
        """Disable: Stop services but keep resources."""
        self._stop_service()
        # Keep self._cache intact

    def on_unload(self) -> None:
        """Unload: Clean up all resources."""
        self._cache.clear()
        self._cache = None
```

### 2. Handle Configuration Changes

```python
def on_config_change(self, new_config: PluginConfig) -> None:
    """React to configuration changes."""
    super().on_config_change(new_config)

    # Restart service with new config if enabled
    if self.state == PluginState.ENABLED:
        self._restart_with_config(new_config)
```

### 3. Use Proper Logging

```python
def on_load(self) -> None:
    self.logger.info("Loading plugin...")
    try:
        # ... initialization code ...
        self.logger.info("Plugin loaded successfully")
    except Exception as e:
        self.logger.error(f"Failed to load: {e}", exc_info=True)
        raise PluginLoadError(f"Load failed: {e}") from e
```

### 4. Validate Dependencies

```python
def on_enable(self) -> None:
    """Ensure dependencies are available."""
    required_plugin = self.manager.get_plugin("required_plugin")
    if not required_plugin or required_plugin.state != PluginState.ENABLED:
        raise PluginError("Required plugin not available")
```

### 5. Clean Resource Management

```python
def on_unload(self) -> None:
    """Clean up all resources."""
    # Close file handles
    if hasattr(self, "_file"):
        self._file.close()

    # Disconnect from services
    if hasattr(self, "_client"):
        self._client.disconnect()

    # Clear caches
    if hasattr(self, "_cache"):
        self._cache.clear()
```

## API Reference

### PluginManager

```python
PluginManager(
    plugin_dirs: List[Path] = None,
    auto_discover: bool = True
)
```

**Methods:**
- `add_plugin_directory(directory)`: Add a plugin search directory
- `discover_plugins()`: Discover all plugins in configured directories
- `load_plugin(metadata, file_path, package_name, config)`: Load a plugin
- `unload_plugin(name)`: Unload a plugin
- `enable_plugin(name)`: Enable a plugin
- `disable_plugin(name)`: Disable a plugin
- `configure_plugin(name, config)`: Update plugin configuration
- `get_plugin(name)`: Get a plugin by name
- `get_all_plugins()`: Get all loaded plugins
- `get_enabled_plugins()`: Get all enabled plugins
- `get_plugin_info(name)`: Get plugin information
- `list_plugins()`: List all plugins with info
- `shutdown()`: Shutdown and cleanup all plugins

### Plugin

```python
Plugin(metadata: PluginMetadata, config: PluginConfig = None)
```

**Abstract Methods:**
- `on_load()`: Called when plugin is loaded
- `on_unload()`: Called when plugin is unloaded
- `on_enable()`: Called when plugin is enabled
- `on_disable()`: Called when plugin is disabled

**Methods:**
- `on_config_change(new_config)`: Called when configuration changes
- `get_error()`: Get the last error that occurred

**Attributes:**
- `metadata`: Plugin metadata
- `config`: Plugin configuration
- `state`: Current plugin state
- `logger`: Plugin logger instance

### PluginMetadata

```python
PluginMetadata(
    name: str,
    version: str,
    author: str,
    description: str,
    dependencies: List[str] = [],
    config_schema: Dict = None,
    entry_point: str = "Plugin",
    compatible_versions: List[str] = [],
    tags: List[str] = []
)
```

### PluginConfig

```python
PluginConfig(
    enabled: bool = True,
    priority: int = 100,
    settings: Dict[str, Any] = {}
)
```

## Examples

See the `examples/plugins/` directory for complete working examples:

- `example_plugin.py`: Basic plugin demonstrating all features
- `plugin_system_demo.py`: Complete demonstration of the plugin system

Run the demo:

```bash
python3 examples/plugin_system_demo.py
```

## Troubleshooting

### Plugin Not Found

```python
# Check plugin directories
manager = PluginManager(plugin_dirs=["./plugins"])
print(f"Searching in: {manager.plugin_dirs}")

# Manually discover
metadata_list = manager.discover_plugins()
print(f"Found: {[m.name for m in metadata_list]}")
```

### Dependency Issues

```python
# Check plugin dependencies
plugin = manager.get_plugin("my_plugin")
print(f"Dependencies: {plugin.metadata.dependencies}")

# Verify dependencies are loaded
for dep_name in plugin.metadata.dependencies:
    dep = manager.get_plugin(dep_name)
    if dep:
        print(f"  {dep_name}: {dep.state.value}")
    else:
        print(f"  {dep_name}: NOT LOADED")
```

### Plugin Errors

```python
# Check for errors
plugin = manager.get_plugin("my_plugin")
if plugin.state == PluginState.ERROR:
    error = plugin.get_error()
    print(f"Error: {error}")
    import traceback
    traceback.print_exception(type(error), error, error.__traceback__)
```

## Future Enhancements

Planned features for future releases:

1. **Hot Reload**: Reload plugins without restarting
2. **Plugin Sandboxing**: Enhanced isolation using subprocess/containers
3. **Plugin Marketplace**: Discover and install plugins from registry
4. **Version Compatibility**: Automatic version checking
5. **Plugin Analytics**: Track plugin usage and performance
6. **Plugin Templates**: Scaffolding for new plugins
7. **Plugin Testing Framework**: Tools for testing plugins

## Contributing

To contribute a plugin or improve the plugin system, please see CONTRIBUTING.md.

## License

The plugin system is part of the AI Automation Framework and is licensed under the same terms.
