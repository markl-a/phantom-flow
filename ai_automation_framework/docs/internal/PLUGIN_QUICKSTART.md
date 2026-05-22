# Plugin System Quick Start Guide

## Installation

The plugin system is included in `ai_automation_framework.core.plugins`.

## Basic Usage

```python
from ai_automation_framework.core.plugins import PluginManager

# Create plugin manager
manager = PluginManager(
    plugin_dirs=["./plugins"],
    auto_discover=True
)

# Get and use a plugin
plugin = manager.get_plugin("my_plugin")
if plugin:
    result = plugin.some_method()

# Cleanup
manager.shutdown()
```

## Creating a Plugin

### 1. Create plugin.py

```python
from ai_automation_framework.core.plugins import Plugin, PluginMetadata, PluginConfig

class MyPlugin(Plugin):
    def on_load(self):
        self.logger.info("Loading...")

    def on_unload(self):
        self.logger.info("Unloading...")

    def on_enable(self):
        self.logger.info("Enabling...")

    def on_disable(self):
        self.logger.info("Disabling...")

    def my_method(self, data):
        return f"Processed: {data}"

# Export
Plugin = MyPlugin
```

### 2. Create plugin.yaml

```yaml
name: my_plugin
version: 1.0.0
author: Your Name
description: My awesome plugin
dependencies: []
entry_point: Plugin
tags:
  - example
```

### 3. Place in plugins directory

```
plugins/
├── my_plugin/
│   ├── plugin.yaml
│   └── plugin.py
```

## Key Features

- **Lifecycle Management**: Load, enable, disable, unload plugins
- **Dependency Resolution**: Automatically loads dependencies first
- **Configuration**: Per-plugin configuration with validation
- **Error Handling**: Graceful error handling and recovery
- **Thread Safety**: Safe concurrent operations
- **Auto Discovery**: Automatically find and load plugins

## Examples

Run the demo:
```bash
python3 examples/plugin_system_demo.py
```

Test dependencies:
```bash
python3 examples/test_plugin_dependencies.py
```

## Documentation

See `/home/user/Automation_with_AI/docs/PLUGIN_SYSTEM.md` for complete documentation.

## API Quick Reference

### PluginManager
- `load_plugin(metadata, file_path, config)` - Load a plugin
- `enable_plugin(name)` - Enable a plugin
- `disable_plugin(name)` - Disable a plugin
- `get_plugin(name)` - Get plugin by name
- `list_plugins()` - List all plugins
- `shutdown()` - Cleanup all plugins

### Plugin States
- `UNLOADED` - Not loaded
- `LOADED` - Loaded but not enabled
- `ENABLED` - Active and running
- `DISABLED` - Loaded but disabled
- `ERROR` - Error occurred

### Lifecycle Hooks
- `on_load()` - Initialize resources
- `on_unload()` - Cleanup resources
- `on_enable()` - Start functionality
- `on_disable()` - Stop functionality
- `on_config_change(config)` - Handle config changes
