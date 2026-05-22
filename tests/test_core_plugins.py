"""Comprehensive tests for the plugins module."""

import json
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from ai_automation_framework.core.plugins import (
    Plugin,
    PluginConfig,
    PluginDependencyError,
    PluginError,
    PluginLoadError,
    PluginLoader,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    PluginState,
    DependencyResolver,
    PluginConfigurationError,
)


# Test fixtures - Mock Plugin Classes
class SimplePlugin(Plugin):
    """Simple test plugin."""

    def __init__(self, metadata: PluginMetadata, config: PluginConfig = None):
        super().__init__(metadata, config)
        self.load_called = False
        self.unload_called = False
        self.enable_called = False
        self.disable_called = False

    def on_load(self) -> None:
        self.load_called = True

    def on_unload(self) -> None:
        self.unload_called = True

    def on_enable(self) -> None:
        self.enable_called = True

    def on_disable(self) -> None:
        self.disable_called = True


class FailingLoadPlugin(Plugin):
    """Plugin that fails to load."""

    def on_load(self) -> None:
        raise RuntimeError("Load failed")

    def on_unload(self) -> None:
        pass

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass


class FailingEnablePlugin(Plugin):
    """Plugin that fails to enable."""

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass

    def on_enable(self) -> None:
        raise RuntimeError("Enable failed")

    def on_disable(self) -> None:
        pass


class ConfigurablePlugin(Plugin):
    """Plugin with configuration handling."""

    def __init__(self, metadata: PluginMetadata, config: PluginConfig = None):
        super().__init__(metadata, config)
        self.config_changed = False

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass

    def on_config_change(self, new_config: PluginConfig) -> None:
        super().on_config_change(new_config)
        self.config_changed = True


# Test PluginMetadata
class TestPluginMetadata:
    """Tests for PluginMetadata dataclass."""

    def test_metadata_creation(self):
        """Test basic metadata creation."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin description"
        )
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.description == "Test plugin description"
        assert metadata.dependencies == []
        assert metadata.config_schema is None
        assert metadata.entry_point == "Plugin"
        assert metadata.compatible_versions == []
        assert metadata.tags == []

    def test_metadata_with_dependencies(self):
        """Test metadata with dependencies."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            dependencies=["dep1", "dep2"]
        )
        assert metadata.dependencies == ["dep1", "dep2"]

    def test_metadata_to_dict(self):
        """Test metadata to_dict conversion."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            dependencies=["dep1"],
            tags=["tag1", "tag2"]
        )
        data = metadata.to_dict()
        assert data["name"] == "test_plugin"
        assert data["version"] == "1.0.0"
        assert data["author"] == "Test Author"
        assert data["description"] == "Test plugin"
        assert data["dependencies"] == ["dep1"]
        assert data["tags"] == ["tag1", "tag2"]

    def test_metadata_from_dict_complete(self):
        """Test metadata from_dict with all fields."""
        data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Test plugin",
            "dependencies": ["dep1"],
            "config_schema": {"type": "object"},
            "entry_point": "CustomPlugin",
            "compatible_versions": ["1.0", "2.0"],
            "tags": ["tag1"]
        }
        metadata = PluginMetadata.from_dict(data)
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.dependencies == ["dep1"]
        assert metadata.config_schema == {"type": "object"}
        assert metadata.entry_point == "CustomPlugin"
        assert metadata.compatible_versions == ["1.0", "2.0"]
        assert metadata.tags == ["tag1"]

    def test_metadata_from_dict_minimal(self):
        """Test metadata from_dict with minimal required fields."""
        data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Test plugin"
        }
        metadata = PluginMetadata.from_dict(data)
        assert metadata.name == "test_plugin"
        assert metadata.dependencies == []
        assert metadata.entry_point == "Plugin"

    def test_metadata_from_dict_missing_fields(self):
        """Test metadata from_dict with missing required fields."""
        data = {
            "name": "test_plugin",
            "version": "1.0.0"
        }
        with pytest.raises(ValueError, match="Missing required metadata fields"):
            PluginMetadata.from_dict(data)


# Test PluginConfig
class TestPluginConfig:
    """Tests for PluginConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = PluginConfig()
        assert config.enabled is True
        assert config.priority == 100
        assert config.settings == {}

    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = PluginConfig(
            enabled=False,
            priority=50,
            settings={"key": "value"}
        )
        assert config.enabled is False
        assert config.priority == 50
        assert config.settings == {"key": "value"}

    def test_config_priority_validation(self):
        """Test priority validation."""
        with pytest.raises(ValueError, match="priority must be non-negative"):
            PluginConfig(priority=-1)

    def test_config_valid_priority(self):
        """Test valid priority values."""
        config = PluginConfig(priority=0)
        assert config.priority == 0

        config = PluginConfig(priority=1000)
        assert config.priority == 1000


# Test Plugin Base Class
class TestPluginBase:
    """Tests for Plugin abstract base class."""

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        config = PluginConfig(priority=50)
        plugin = SimplePlugin(metadata, config)

        assert plugin.metadata == metadata
        assert plugin.config == config
        assert plugin.state == PluginState.UNLOADED
        assert plugin._error is None

    def test_plugin_default_config(self):
        """Test plugin with default configuration."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)
        assert plugin.config.enabled is True
        assert plugin.config.priority == 100

    def test_plugin_lifecycle_methods(self):
        """Test plugin lifecycle methods are called."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)

        plugin.on_load()
        assert plugin.load_called

        plugin.on_enable()
        assert plugin.enable_called

        plugin.on_disable()
        assert plugin.disable_called

        plugin.on_unload()
        assert plugin.unload_called

    def test_plugin_config_change(self):
        """Test plugin configuration change handling."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = ConfigurablePlugin(metadata)

        new_config = PluginConfig(enabled=False, priority=200)
        plugin.on_config_change(new_config)

        assert plugin.config == new_config
        assert plugin.config_changed

    def test_plugin_error_handling(self):
        """Test plugin error state management."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)

        assert plugin.get_error() is None

        error = RuntimeError("Test error")
        plugin._set_error(error)

        assert plugin.get_error() == error
        assert plugin.state == PluginState.ERROR

    def test_plugin_repr(self):
        """Test plugin string representation."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)
        plugin.state = PluginState.LOADED

        repr_str = repr(plugin)
        assert "test_plugin" in repr_str
        assert "1.0.0" in repr_str
        assert "loaded" in repr_str


# Test PluginRegistry
class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = PluginRegistry()
        assert registry.get_all() == {}

    def test_register_plugin(self):
        """Test plugin registration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)

        registry.register(plugin)
        assert registry.get("test_plugin") == plugin

    def test_register_duplicate_plugin(self):
        """Test registering duplicate plugin raises error."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin1 = SimplePlugin(metadata)
        plugin2 = SimplePlugin(metadata)

        registry.register(plugin1)
        with pytest.raises(PluginError, match="already registered"):
            registry.register(plugin2)

    def test_unregister_plugin(self):
        """Test plugin unregistration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test"
        )
        plugin = SimplePlugin(metadata)

        registry.register(plugin)
        registry.unregister("test_plugin")
        assert registry.get("test_plugin") is None

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering nonexistent plugin raises error."""
        registry = PluginRegistry()
        with pytest.raises(PluginError, match="not registered"):
            registry.unregister("nonexistent")

    def test_get_all_plugins(self):
        """Test getting all plugins."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata("plugin1", "1.0", "Test", "Test")
        metadata2 = PluginMetadata("plugin2", "1.0", "Test", "Test")
        plugin1 = SimplePlugin(metadata1)
        plugin2 = SimplePlugin(metadata2)

        registry.register(plugin1)
        registry.register(plugin2)

        all_plugins = registry.get_all()
        assert len(all_plugins) == 2
        assert "plugin1" in all_plugins
        assert "plugin2" in all_plugins

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata("plugin1", "1.0", "Test", "Test")
        metadata2 = PluginMetadata("plugin2", "1.0", "Test", "Test")
        plugin1 = SimplePlugin(metadata1)
        plugin2 = SimplePlugin(metadata2)

        plugin1.state = PluginState.ENABLED
        plugin2.state = PluginState.LOADED

        registry.register(plugin1)
        registry.register(plugin2)

        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0] == plugin1

    def test_register_hook(self):
        """Test hook registration."""
        registry = PluginRegistry()
        callback = Mock()

        registry.register_hook("test_hook", callback)
        # Verify by calling the hook
        registry.call_hooks("test_hook")
        callback.assert_called_once()

    def test_call_hooks(self):
        """Test calling hooks with arguments."""
        registry = PluginRegistry()
        callback1 = Mock(return_value="result1")
        callback2 = Mock(return_value="result2")

        registry.register_hook("test_hook", callback1)
        registry.register_hook("test_hook", callback2)

        results = registry.call_hooks("test_hook", "arg1", key="value")

        callback1.assert_called_once_with("arg1", key="value")
        callback2.assert_called_once_with("arg1", key="value")
        assert results == ["result1", "result2"]

    def test_call_hooks_with_exception(self):
        """Test calling hooks when one raises exception."""
        registry = PluginRegistry()
        callback1 = Mock(side_effect=RuntimeError("Error"))
        callback2 = Mock(return_value="result")

        registry.register_hook("test_hook", callback1)
        registry.register_hook("test_hook", callback2)

        results = registry.call_hooks("test_hook")

        # Second callback should still execute
        callback2.assert_called_once()
        assert results == ["result"]


# Test PluginLoader
class TestPluginLoader:
    """Tests for PluginLoader."""

    def test_loader_initialization(self):
        """Test loader initialization."""
        loader = PluginLoader()
        assert loader is not None

    def test_load_from_file(self, tmp_path):
        """Test loading plugin from file."""
        # Create a plugin file
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin, PluginMetadata, PluginConfig

class TestPlugin(Plugin):
    def on_load(self):
        pass

    def on_unload(self):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass
""")

        loader = PluginLoader()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test",
            entry_point="TestPlugin"
        )

        plugin = loader.load_from_file(plugin_file, metadata)
        assert plugin is not None
        assert plugin.metadata == metadata

    def test_load_from_file_not_found(self):
        """Test loading from nonexistent file."""
        loader = PluginLoader()
        metadata = PluginMetadata("test", "1.0", "Test", "Test")

        with pytest.raises(PluginLoadError, match="not found"):
            loader.load_from_file("/nonexistent/file.py", metadata)

    def test_load_from_file_invalid_entry_point(self, tmp_path):
        """Test loading plugin with invalid entry point."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("# Empty file")

        loader = PluginLoader()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test",
            entry_point="NonexistentClass"
        )

        with pytest.raises(PluginLoadError, match="Entry point.*not found"):
            loader.load_from_file(plugin_file, metadata)

    def test_load_from_file_not_plugin_subclass(self, tmp_path):
        """Test loading class that doesn't inherit from Plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
class NotAPlugin:
    pass
""")

        loader = PluginLoader()
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test",
            entry_point="NotAPlugin"
        )

        with pytest.raises(PluginLoadError, match="must inherit from Plugin"):
            loader.load_from_file(plugin_file, metadata)

    def test_discover_plugins(self, tmp_path):
        """Test discovering plugins in directory."""
        # Create plugin directory structure
        plugin_dir = tmp_path / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True)

        metadata_file = plugin_dir / "plugin.yaml"
        metadata_file.write_text("""
name: test_plugin
version: 1.0.0
author: Test Author
description: Test plugin
dependencies:
  - dep1
tags:
  - test
""")

        loader = PluginLoader()
        discovered = loader.discover_plugins(tmp_path / "plugins")

        assert len(discovered) == 1
        assert discovered[0].name == "test_plugin"
        assert discovered[0].version == "1.0.0"
        assert discovered[0].dependencies == ["dep1"]

    def test_discover_plugins_json(self, tmp_path):
        """Test discovering plugins with JSON metadata."""
        plugin_dir = tmp_path / "plugins" / "test_plugin"
        plugin_dir.mkdir(parents=True)

        metadata_file = plugin_dir / "plugin.json"
        metadata_data = {
            "name": "test_plugin",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "Test plugin"
        }
        metadata_file.write_text(json.dumps(metadata_data))

        loader = PluginLoader()
        discovered = loader.discover_plugins(tmp_path / "plugins", pattern="plugin.json")

        assert len(discovered) == 1
        assert discovered[0].name == "test_plugin"

    def test_discover_plugins_nonexistent_directory(self):
        """Test discovering plugins in nonexistent directory."""
        loader = PluginLoader()
        discovered = loader.discover_plugins("/nonexistent/directory")
        assert discovered == []

    def test_discover_plugins_invalid_metadata(self, tmp_path):
        """Test discovering plugins with invalid metadata."""
        plugin_dir = tmp_path / "plugins" / "bad_plugin"
        plugin_dir.mkdir(parents=True)

        metadata_file = plugin_dir / "plugin.yaml"
        metadata_file.write_text("invalid: yaml: content")

        loader = PluginLoader()
        discovered = loader.discover_plugins(tmp_path / "plugins")

        # Should skip invalid metadata
        assert len(discovered) == 0


# Test DependencyResolver
class TestDependencyResolver:
    """Tests for DependencyResolver."""

    def test_resolve_no_dependencies(self):
        """Test resolving plugins with no dependencies."""
        resolver = DependencyResolver()
        metadata1 = PluginMetadata("plugin1", "1.0", "Test", "Test")
        metadata2 = PluginMetadata("plugin2", "1.0", "Test", "Test")

        resolved = resolver.resolve([metadata1, metadata2])

        assert len(resolved) == 2
        assert metadata1 in resolved
        assert metadata2 in resolved

    def test_resolve_simple_dependency(self):
        """Test resolving simple dependency chain."""
        resolver = DependencyResolver()
        metadata1 = PluginMetadata("plugin1", "1.0", "Test", "Test")
        metadata2 = PluginMetadata(
            "plugin2", "1.0", "Test", "Test",
            dependencies=["plugin1"]
        )

        resolved = resolver.resolve([metadata2, metadata1])

        assert len(resolved) == 2
        assert resolved[0] == metadata1  # plugin1 should be first
        assert resolved[1] == metadata2  # plugin2 depends on plugin1

    def test_resolve_complex_dependencies(self):
        """Test resolving complex dependency graph."""
        resolver = DependencyResolver()
        metadata1 = PluginMetadata("plugin1", "1.0", "Test", "Test")
        metadata2 = PluginMetadata(
            "plugin2", "1.0", "Test", "Test",
            dependencies=["plugin1"]
        )
        metadata3 = PluginMetadata(
            "plugin3", "1.0", "Test", "Test",
            dependencies=["plugin1", "plugin2"]
        )

        resolved = resolver.resolve([metadata3, metadata2, metadata1])

        assert len(resolved) == 3
        # plugin1 should come first
        assert resolved[0] == metadata1
        # plugin2 should come before plugin3
        plugin2_idx = resolved.index(metadata2)
        plugin3_idx = resolved.index(metadata3)
        assert plugin2_idx < plugin3_idx

    def test_resolve_circular_dependency(self):
        """Test detecting circular dependencies."""
        resolver = DependencyResolver()
        metadata1 = PluginMetadata(
            "plugin1", "1.0", "Test", "Test",
            dependencies=["plugin2"]
        )
        metadata2 = PluginMetadata(
            "plugin2", "1.0", "Test", "Test",
            dependencies=["plugin1"]
        )

        with pytest.raises(PluginDependencyError, match="Circular dependency"):
            resolver.resolve([metadata1, metadata2])

    def test_resolve_missing_dependency(self):
        """Test detecting missing dependencies."""
        resolver = DependencyResolver()
        metadata = PluginMetadata(
            "plugin1", "1.0", "Test", "Test",
            dependencies=["nonexistent"]
        )

        with pytest.raises(PluginDependencyError, match="not available"):
            resolver.resolve([metadata])

    def test_resolve_with_available_dependencies(self):
        """Test resolving with pre-available dependencies."""
        resolver = DependencyResolver()
        metadata = PluginMetadata(
            "plugin1", "1.0", "Test", "Test",
            dependencies=["external_dep"]
        )

        resolved = resolver.resolve([metadata], available={"external_dep"})
        assert len(resolved) == 1
        assert resolved[0] == metadata


# Test PluginManager
class TestPluginManager:
    """Tests for PluginManager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        assert manager is not None
        assert len(manager.plugin_dirs) == 0

    def test_add_plugin_directory(self, tmp_path):
        """Test adding plugin directory."""
        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        manager.add_plugin_directory(tmp_path)

        assert tmp_path in manager.plugin_dirs

    def test_load_plugin_file(self, tmp_path):
        """Test loading plugin from file."""
        # Create plugin file
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        self.loaded = True

    def on_unload(self):
        pass

    def on_enable(self):
        self.enabled = True

    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test",
            entry_point="TestPlugin"
        )
        config = PluginConfig(enabled=False)  # Don't auto-enable

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)

        assert plugin is not None
        assert plugin.state == PluginState.LOADED
        assert hasattr(plugin, 'loaded') and plugin.loaded

    def test_load_plugin_already_loaded(self, tmp_path):
        """Test loading already loaded plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        plugin1 = manager.load_plugin(metadata, file_path=plugin_file, config=config)
        plugin2 = manager.load_plugin(metadata, file_path=plugin_file, config=config)

        assert plugin1 == plugin2

    def test_unload_plugin(self, tmp_path):
        """Test unloading plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        self.unloaded = True
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)
        manager.unload_plugin("test")

        assert manager.get_plugin("test") is None
        assert hasattr(plugin, 'unloaded') and plugin.unloaded

    def test_enable_plugin(self, tmp_path):
        """Test enabling plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        self.enabled = True
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)
        manager.enable_plugin("test")

        assert plugin.state == PluginState.ENABLED
        assert hasattr(plugin, 'enabled') and plugin.enabled

    def test_enable_plugin_with_missing_dependency(self, tmp_path):
        """Test enabling plugin with missing dependency."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata(
            "test", "1.0", "Test", "Test",
            dependencies=["missing_dep"],
            entry_point="TestPlugin"
        )
        config = PluginConfig(enabled=False)

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)

        with pytest.raises(PluginDependencyError, match="not enabled"):
            manager.enable_plugin("test")

    def test_disable_plugin(self, tmp_path):
        """Test disabling plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        self.disabled = True
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")

        plugin = manager.load_plugin(metadata, file_path=plugin_file)
        manager.disable_plugin("test")

        assert plugin.state == PluginState.DISABLED
        assert hasattr(plugin, 'disabled') and plugin.disabled

    def test_disable_plugin_with_dependent(self, tmp_path):
        """Test disabling plugin that has dependents."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)

        # Load base plugin
        metadata1 = PluginMetadata("base", "1.0", "Test", "Test", entry_point="TestPlugin")
        plugin1 = manager.load_plugin(metadata1, file_path=plugin_file)

        # Load dependent plugin
        metadata2 = PluginMetadata(
            "dependent", "1.0", "Test", "Test",
            dependencies=["base"],
            entry_point="TestPlugin"
        )
        plugin2 = manager.load_plugin(metadata2, file_path=plugin_file)

        # Try to disable base plugin
        with pytest.raises(PluginDependencyError, match="depends on it"):
            manager.disable_plugin("base")

    def test_configure_plugin(self, tmp_path):
        """Test configuring plugin."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin, PluginConfig

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
    def on_config_change(self, new_config: PluginConfig):
        super().on_config_change(new_config)
        self.config_changed = True
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)

        new_config = PluginConfig(priority=200)
        manager.configure_plugin("test", new_config)

        assert plugin.config.priority == 200
        assert hasattr(plugin, 'config_changed') and plugin.config_changed

    def test_configure_plugin_not_loaded(self):
        """Test configuring plugin that's not loaded."""
        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        config = PluginConfig(priority=200)

        # Should not raise error, config is stored for later
        manager.configure_plugin("nonexistent", config)
        assert manager._configs["nonexistent"] == config

    def test_get_plugin_info(self, tmp_path):
        """Test getting plugin info."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata(
            "test", "1.0.0", "Test Author", "Test Description",
            dependencies=["dep1"],
            entry_point="TestPlugin"
        )
        # Don't auto-enable due to unmet dependencies
        config = PluginConfig(enabled=False)

        manager.load_plugin(metadata, file_path=plugin_file, config=config)
        info = manager.get_plugin_info("test")

        assert info is not None
        assert info["name"] == "test"
        assert info["version"] == "1.0.0"
        assert info["author"] == "Test Author"
        assert info["description"] == "Test Description"
        assert info["dependencies"] == ["dep1"]
        assert info["state"] == "loaded"

    def test_list_plugins(self, tmp_path):
        """Test listing all plugins."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)

        metadata1 = PluginMetadata("test1", "1.0", "Test", "Test", entry_point="TestPlugin")
        metadata2 = PluginMetadata("test2", "1.0", "Test", "Test", entry_point="TestPlugin")
        config1 = PluginConfig(priority=100, enabled=False)
        config2 = PluginConfig(priority=50, enabled=False)

        manager.load_plugin(metadata1, file_path=plugin_file, config=config1)
        manager.load_plugin(metadata2, file_path=plugin_file, config=config2)

        plugins = manager.list_plugins()
        assert len(plugins) == 2
        # Should be sorted by priority
        assert plugins[0]["name"] == "test2"  # priority 50
        assert plugins[1]["name"] == "test1"  # priority 100

    def test_shutdown(self, tmp_path):
        """Test manager shutdown."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")

        manager.load_plugin(metadata, file_path=plugin_file)
        manager.shutdown()

        assert len(manager.get_all_plugins()) == 0

    def test_context_manager(self, tmp_path):
        """Test using manager as context manager."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        with PluginManager(plugin_dirs=[], auto_discover=False) as manager:
            metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
            manager.load_plugin(metadata, file_path=plugin_file)
            assert len(manager.get_all_plugins()) == 1

        # After context exit, should be shut down
        assert len(manager.get_all_plugins()) == 0


# Test Plugin Lifecycle
class TestPluginLifecycle:
    """Tests for complete plugin lifecycle."""

    def test_full_lifecycle(self, tmp_path):
        """Test complete plugin lifecycle: load -> enable -> disable -> unload."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.events = []

    def on_load(self):
        self.events.append('loaded')

    def on_unload(self):
        self.events.append('unloaded')

    def on_enable(self):
        self.events.append('enabled')

    def on_disable(self):
        self.events.append('disabled')
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        # Load
        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)
        assert plugin.state == PluginState.LOADED
        assert 'loaded' in plugin.events

        # Enable
        manager.enable_plugin("test")
        assert plugin.state == PluginState.ENABLED
        assert 'enabled' in plugin.events

        # Disable
        manager.disable_plugin("test")
        assert plugin.state == PluginState.DISABLED
        assert 'disabled' in plugin.events

        # Unload
        manager.unload_plugin("test")
        assert 'unloaded' in plugin.events

    def test_auto_enable_on_load(self, tmp_path):
        """Test plugin auto-enabled when config.enabled=True."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        pass
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=True)

        plugin = manager.load_plugin(metadata, file_path=plugin_file, config=config)
        assert plugin.state == PluginState.ENABLED

    def test_load_failure_sets_error_state(self, tmp_path):
        """Test that load failure sets error state."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text("""
from ai_automation_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def on_load(self):
        raise RuntimeError("Load failed")
    def on_unload(self):
        pass
    def on_enable(self):
        pass
    def on_disable(self):
        pass
""")

        manager = PluginManager(plugin_dirs=[], auto_discover=False)
        metadata = PluginMetadata("test", "1.0", "Test", "Test", entry_point="TestPlugin")
        config = PluginConfig(enabled=False)

        with pytest.raises(PluginLoadError):
            manager.load_plugin(metadata, file_path=plugin_file, config=config)


# Test Edge Cases
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_plugin_with_no_dependencies_field(self):
        """Test plugin metadata without dependencies field."""
        metadata = PluginMetadata("test", "1.0", "Test", "Test")
        assert metadata.dependencies == []

    def test_empty_plugin_directory(self, tmp_path):
        """Test discovering from empty directory."""
        manager = PluginManager(plugin_dirs=[tmp_path], auto_discover=False)
        discovered = manager.discover_plugins()
        assert discovered == []

    def test_plugin_state_transitions(self):
        """Test valid state transitions."""
        metadata = PluginMetadata("test", "1.0", "Test", "Test")
        plugin = SimplePlugin(metadata)

        # UNLOADED -> LOADED
        plugin.state = PluginState.LOADED
        assert plugin.state == PluginState.LOADED

        # LOADED -> ENABLED
        plugin.state = PluginState.ENABLED
        assert plugin.state == PluginState.ENABLED

        # ENABLED -> DISABLED
        plugin.state = PluginState.DISABLED
        assert plugin.state == PluginState.DISABLED

        # Any -> ERROR
        plugin.state = PluginState.ERROR
        assert plugin.state == PluginState.ERROR

    def test_multiple_plugin_managers(self):
        """Test multiple plugin managers can coexist."""
        manager1 = PluginManager(plugin_dirs=[], auto_discover=False)
        manager2 = PluginManager(plugin_dirs=[], auto_discover=False)

        assert manager1 is not manager2
        assert manager1.registry is not manager2.registry
