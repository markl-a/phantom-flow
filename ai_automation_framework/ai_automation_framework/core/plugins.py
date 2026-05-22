"""Plugin system for extensibility in the AI Automation Framework."""

import importlib
import importlib.util
import inspect
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    Union,
)
from collections import defaultdict
import threading
import json
import yaml

from pydantic import BaseModel, Field, ValidationError, field_validator

from ai_automation_framework.core.logger import get_logger


logger = get_logger(__name__)


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Exception raised when plugin fails to load."""
    pass


class PluginDependencyError(PluginError):
    """Exception raised when plugin dependencies cannot be resolved."""
    pass


class PluginConfigurationError(PluginError):
    """Exception raised when plugin configuration is invalid."""
    pass


@dataclass
class PluginMetadata:
    """
    Metadata for a plugin.

    Attributes:
        name: Plugin name (unique identifier)
        version: Plugin version string
        author: Plugin author
        description: Plugin description
        dependencies: List of plugin names this plugin depends on
        config_schema: Optional configuration schema
        entry_point: Entry point class name
        compatible_versions: Framework versions this plugin is compatible with
        tags: Optional tags for categorization
    """

    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    entry_point: str = "Plugin"
    compatible_versions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "config_schema": self.config_schema,
            "entry_point": self.entry_point,
            "compatible_versions": self.compatible_versions,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginMetadata":
        """
        Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            PluginMetadata instance

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {"name", "version", "author", "description"}
        missing = required_fields - set(data.keys())
        if missing:
            raise ValueError(f"Missing required metadata fields: {missing}")

        return cls(
            name=data["name"],
            version=data["version"],
            author=data["author"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
            config_schema=data.get("config_schema"),
            entry_point=data.get("entry_point", "Plugin"),
            compatible_versions=data.get("compatible_versions", []),
            tags=data.get("tags", []),
        )


class PluginConfig(BaseModel):
    """
    Configuration for a plugin instance.

    Plugins can have custom configuration that extends this base.
    """

    enabled: bool = Field(default=True, description="Whether plugin is enabled")
    priority: int = Field(default=100, description="Plugin priority (lower = higher priority)")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Plugin-specific settings")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority is non-negative."""
        if v < 0:
            raise ValueError("priority must be non-negative")
        return v


class Plugin(ABC):
    """
    Base class for all plugins.

    Plugins must inherit from this class and implement the lifecycle hooks.
    """

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        """
        Initialize the plugin.

        Args:
            metadata: Plugin metadata
            config: Plugin configuration
        """
        self.metadata = metadata
        self.config = config or PluginConfig()
        self.state = PluginState.UNLOADED
        self.logger = get_logger(f"plugin.{metadata.name}")
        self._lock = threading.RLock()
        self._error: Optional[Exception] = None

    @abstractmethod
    def on_load(self) -> None:
        """
        Called when plugin is loaded.

        This is where you should initialize resources that don't depend
        on other plugins or framework state.

        Raises:
            PluginLoadError: If loading fails
        """
        pass

    @abstractmethod
    def on_unload(self) -> None:
        """
        Called when plugin is unloaded.

        This is where you should clean up resources allocated in on_load.
        """
        pass

    @abstractmethod
    def on_enable(self) -> None:
        """
        Called when plugin is enabled.

        This is where you should start providing plugin functionality.

        Raises:
            PluginError: If enabling fails
        """
        pass

    @abstractmethod
    def on_disable(self) -> None:
        """
        Called when plugin is disabled.

        This is where you should stop providing plugin functionality
        but keep resources allocated.
        """
        pass

    def on_config_change(self, new_config: PluginConfig) -> None:
        """
        Called when plugin configuration changes.

        Default implementation just updates the config.
        Override to handle config changes.

        Args:
            new_config: New configuration
        """
        self.config = new_config
        self.logger.info(f"Configuration updated for plugin {self.metadata.name}")

    def get_error(self) -> Optional[Exception]:
        """
        Get the last error that occurred in the plugin.

        Returns:
            Last exception or None
        """
        return self._error

    def _set_error(self, error: Exception) -> None:
        """Set plugin error state."""
        self._error = error
        self.state = PluginState.ERROR

    def __repr__(self) -> str:
        """String representation of the plugin."""
        return (
            f"<Plugin {self.metadata.name} "
            f"version={self.metadata.version} "
            f"state={self.state.value}>"
        )


class PluginRegistry:
    """
    Registry for managing loaded plugins.

    Provides a central location to register and lookup plugins.
    """

    def __init__(self):
        """Initialize the plugin registry."""
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self.logger = get_logger(f"{__name__}.PluginRegistry")

    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin to register

        Raises:
            PluginError: If plugin with same name already registered
        """
        with self._lock:
            if plugin.metadata.name in self._plugins:
                raise PluginError(
                    f"Plugin {plugin.metadata.name} is already registered"
                )
            self._plugins[plugin.metadata.name] = plugin
            self.logger.info(f"Registered plugin: {plugin.metadata.name}")

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If plugin not found
        """
        with self._lock:
            if name not in self._plugins:
                raise PluginError(f"Plugin {name} is not registered")
            del self._plugins[name]
            self.logger.info(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Optional[Plugin]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)

    def get_all(self) -> Dict[str, Plugin]:
        """
        Get all registered plugins.

        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        return self._plugins.copy()

    def get_enabled(self) -> List[Plugin]:
        """
        Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return [
            p for p in self._plugins.values()
            if p.state == PluginState.ENABLED
        ]

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register a hook callback.

        Args:
            hook_name: Name of the hook
            callback: Callback function
        """
        with self._lock:
            self._hooks[hook_name].append(callback)
            self.logger.debug(f"Registered hook: {hook_name}")

    def call_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all callbacks registered for a hook.

        Args:
            hook_name: Name of the hook
            *args: Positional arguments for callbacks
            **kwargs: Keyword arguments for callbacks

        Returns:
            List of return values from callbacks
        """
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Error calling hook {hook_name}: {e}",
                    exc_info=True
                )
        return results


class PluginLoader:
    """
    Loader for discovering and loading plugins from various sources.
    """

    def __init__(self):
        """Initialize the plugin loader."""
        self.logger = get_logger(f"{__name__}.PluginLoader")

    def load_from_file(
        self,
        file_path: Union[str, Path],
        metadata: PluginMetadata,
        config: Optional[PluginConfig] = None
    ) -> Plugin:
        """
        Load a plugin from a Python file.

        Args:
            file_path: Path to the plugin file
            metadata: Plugin metadata
            config: Optional plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise PluginLoadError(f"Plugin file not found: {file_path}")

        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}",
                file_path
            )
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Failed to create module spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Get the plugin class
            plugin_class = getattr(module, metadata.entry_point, None)
            if plugin_class is None:
                raise PluginLoadError(
                    f"Entry point {metadata.entry_point} not found in {file_path}"
                )

            if not issubclass(plugin_class, Plugin):
                raise PluginLoadError(
                    f"Plugin class {metadata.entry_point} must inherit from Plugin"
                )

            # Create plugin instance
            plugin = plugin_class(metadata, config)
            self.logger.info(f"Loaded plugin from file: {metadata.name}")
            return plugin

        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin from {file_path}: {e}"
            ) from e

    def load_from_package(
        self,
        package_name: str,
        metadata: PluginMetadata,
        config: Optional[PluginConfig] = None
    ) -> Plugin:
        """
        Load a plugin from an installed package.

        Args:
            package_name: Name of the package
            metadata: Plugin metadata
            config: Optional plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        try:
            # Import the package
            module = importlib.import_module(package_name)

            # Get the plugin class
            plugin_class = getattr(module, metadata.entry_point, None)
            if plugin_class is None:
                raise PluginLoadError(
                    f"Entry point {metadata.entry_point} not found in {package_name}"
                )

            if not issubclass(plugin_class, Plugin):
                raise PluginLoadError(
                    f"Plugin class {metadata.entry_point} must inherit from Plugin"
                )

            # Create plugin instance
            plugin = plugin_class(metadata, config)
            self.logger.info(f"Loaded plugin from package: {metadata.name}")
            return plugin

        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import package {package_name}: {e}"
            ) from e
        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin from {package_name}: {e}"
            ) from e

    def discover_plugins(
        self,
        directory: Union[str, Path],
        pattern: str = "plugin.yaml"
    ) -> List[PluginMetadata]:
        """
        Discover plugins in a directory by looking for metadata files.

        Args:
            directory: Directory to search
            pattern: Metadata file pattern (default: plugin.yaml)

        Returns:
            List of discovered plugin metadata
        """
        directory = Path(directory)
        if not directory.exists():
            self.logger.warning(f"Plugin directory not found: {directory}")
            return []

        discovered = []
        for metadata_file in directory.rglob(pattern):
            try:
                metadata = self._load_metadata_file(metadata_file)
                discovered.append(metadata)
                self.logger.debug(f"Discovered plugin: {metadata.name}")
            except Exception as e:
                self.logger.error(
                    f"Failed to load metadata from {metadata_file}: {e}",
                    exc_info=True
                )

        return discovered

    def _load_metadata_file(self, file_path: Path) -> PluginMetadata:
        """
        Load plugin metadata from a file.

        Args:
            file_path: Path to metadata file

        Returns:
            Plugin metadata

        Raises:
            ValueError: If metadata is invalid
        """
        suffix = file_path.suffix.lower()

        with open(file_path, 'r') as f:
            if suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported metadata file format: {suffix}")

        return PluginMetadata.from_dict(data)


class DependencyResolver:
    """
    Resolves plugin dependencies and determines load order.
    """

    def __init__(self):
        """Initialize the dependency resolver."""
        self.logger = get_logger(f"{__name__}.DependencyResolver")

    def resolve(
        self,
        plugins: List[PluginMetadata],
        available: Optional[Set[str]] = None
    ) -> List[PluginMetadata]:
        """
        Resolve plugin dependencies and return load order.

        Uses topological sort to determine correct loading order.

        Args:
            plugins: List of plugin metadata
            available: Set of already available plugin names

        Returns:
            List of plugins in load order

        Raises:
            PluginDependencyError: If dependencies cannot be resolved
        """
        available = available or set()
        plugin_map = {p.name: p for p in plugins}

        # Build dependency graph
        graph: Dict[str, Set[str]] = {p.name: set(p.dependencies) for p in plugins}

        # Validate all dependencies exist
        for name, deps in graph.items():
            for dep in deps:
                if dep not in plugin_map and dep not in available:
                    raise PluginDependencyError(
                        f"Plugin {name} depends on {dep} which is not available"
                    )

        # Topological sort
        result = []
        visited = set(available)
        visiting = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise PluginDependencyError(
                    f"Circular dependency detected involving {name}"
                )

            visiting.add(name)
            for dep in graph.get(name, []):
                if dep in plugin_map:  # Only visit deps that need to be loaded
                    visit(dep)
            visiting.remove(name)
            visited.add(name)

            if name in plugin_map:
                result.append(plugin_map[name])

        for plugin in plugins:
            visit(plugin.name)

        self.logger.info(f"Resolved load order: {[p.name for p in result]}")
        return result


class PluginManager:
    """
    Main plugin manager for the framework.

    Handles plugin discovery, loading, lifecycle management, and dependency resolution.
    """

    def __init__(
        self,
        plugin_dirs: Optional[List[Union[str, Path]]] = None,
        auto_discover: bool = True
    ):
        """
        Initialize the plugin manager.

        Args:
            plugin_dirs: Directories to search for plugins
            auto_discover: Automatically discover plugins on init
        """
        self.plugin_dirs = [Path(d) for d in (plugin_dirs or [])]
        self.registry = PluginRegistry()
        self.loader = PluginLoader()
        self.resolver = DependencyResolver()
        self.logger = get_logger(f"{__name__}.PluginManager")
        self._lock = threading.RLock()
        self._configs: Dict[str, PluginConfig] = {}

        if auto_discover:
            self.discover_and_load()

    def add_plugin_directory(self, directory: Union[str, Path]) -> None:
        """
        Add a directory to search for plugins.

        Args:
            directory: Directory path
        """
        directory = Path(directory)
        if directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            self.logger.info(f"Added plugin directory: {directory}")

    def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover all plugins in configured directories.

        Returns:
            List of discovered plugin metadata
        """
        all_metadata = []
        for directory in self.plugin_dirs:
            metadata_list = self.loader.discover_plugins(directory)
            all_metadata.extend(metadata_list)

        self.logger.info(f"Discovered {len(all_metadata)} plugins")
        return all_metadata

    def load_plugin(
        self,
        metadata: PluginMetadata,
        file_path: Optional[Union[str, Path]] = None,
        package_name: Optional[str] = None,
        config: Optional[PluginConfig] = None
    ) -> Plugin:
        """
        Load a single plugin.

        Args:
            metadata: Plugin metadata
            file_path: Path to plugin file (for file-based plugins)
            package_name: Package name (for package-based plugins)
            config: Optional plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        with self._lock:
            # Check if already loaded
            existing = self.registry.get(metadata.name)
            if existing is not None:
                self.logger.warning(f"Plugin {metadata.name} is already loaded")
                return existing

            # Get or create config
            if config is None:
                config = self._configs.get(metadata.name, PluginConfig())

            # Load the plugin
            if file_path is not None:
                plugin = self.loader.load_from_file(file_path, metadata, config)
            elif package_name is not None:
                plugin = self.loader.load_from_package(package_name, metadata, config)
            else:
                raise PluginLoadError(
                    "Either file_path or package_name must be provided"
                )

            # Call on_load hook
            try:
                plugin.on_load()
                plugin.state = PluginState.LOADED
            except Exception as e:
                plugin._set_error(e)
                self.logger.error(
                    f"Error loading plugin {metadata.name}: {e}",
                    exc_info=True
                )
                raise PluginLoadError(
                    f"Failed to load plugin {metadata.name}: {e}"
                ) from e

            # Register the plugin
            self.registry.register(plugin)

            # Auto-enable if configured
            if config.enabled:
                try:
                    self.enable_plugin(metadata.name)
                except Exception as e:
                    self.logger.error(
                        f"Failed to auto-enable plugin {metadata.name}: {e}"
                    )

            return plugin

    def unload_plugin(self, name: str) -> None:
        """
        Unload a plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If plugin not found or unload fails
        """
        with self._lock:
            plugin = self.registry.get(name)
            if plugin is None:
                raise PluginError(f"Plugin {name} is not loaded")

            # Disable if enabled
            if plugin.state == PluginState.ENABLED:
                self.disable_plugin(name)

            # Call on_unload hook
            try:
                plugin.on_unload()
                plugin.state = PluginState.UNLOADED
            except Exception as e:
                plugin._set_error(e)
                self.logger.error(
                    f"Error unloading plugin {name}: {e}",
                    exc_info=True
                )

            # Unregister the plugin
            self.registry.unregister(name)
            self.logger.info(f"Unloaded plugin: {name}")

    def enable_plugin(self, name: str) -> None:
        """
        Enable a plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If plugin not found or enable fails
        """
        with self._lock:
            plugin = self.registry.get(name)
            if plugin is None:
                raise PluginError(f"Plugin {name} is not loaded")

            if plugin.state == PluginState.ENABLED:
                self.logger.warning(f"Plugin {name} is already enabled")
                return

            # Check dependencies are enabled
            for dep_name in plugin.metadata.dependencies:
                dep = self.registry.get(dep_name)
                if dep is None or dep.state != PluginState.ENABLED:
                    raise PluginDependencyError(
                        f"Cannot enable {name}: dependency {dep_name} is not enabled"
                    )

            # Call on_enable hook
            try:
                plugin.on_enable()
                plugin.state = PluginState.ENABLED
                self.logger.info(f"Enabled plugin: {name}")
            except Exception as e:
                plugin._set_error(e)
                self.logger.error(
                    f"Error enabling plugin {name}: {e}",
                    exc_info=True
                )
                raise PluginError(f"Failed to enable plugin {name}: {e}") from e

    def disable_plugin(self, name: str) -> None:
        """
        Disable a plugin.

        Args:
            name: Plugin name

        Raises:
            PluginError: If plugin not found
        """
        with self._lock:
            plugin = self.registry.get(name)
            if plugin is None:
                raise PluginError(f"Plugin {name} is not loaded")

            if plugin.state != PluginState.ENABLED:
                self.logger.warning(f"Plugin {name} is not enabled")
                return

            # Check if other enabled plugins depend on this
            for other_plugin in self.registry.get_enabled():
                if name in other_plugin.metadata.dependencies:
                    raise PluginDependencyError(
                        f"Cannot disable {name}: plugin {other_plugin.metadata.name} depends on it"
                    )

            # Call on_disable hook
            try:
                plugin.on_disable()
                plugin.state = PluginState.DISABLED
                self.logger.info(f"Disabled plugin: {name}")
            except Exception as e:
                plugin._set_error(e)
                self.logger.error(
                    f"Error disabling plugin {name}: {e}",
                    exc_info=True
                )

    def reload_plugin(self, name: str) -> None:
        """
        Reload a plugin (unload and load again).

        Args:
            name: Plugin name

        Raises:
            PluginError: If reload fails
        """
        with self._lock:
            plugin = self.registry.get(name)
            if plugin is None:
                raise PluginError(f"Plugin {name} is not loaded")

            # Store metadata and config
            metadata = plugin.metadata
            config = plugin.config

            # Store file path if available (simplified - in real impl would track this)
            # For now, we'll raise an error as we need the source
            raise NotImplementedError(
                "Hot reload requires tracking plugin source. "
                "Please unload and load manually."
            )

    def configure_plugin(self, name: str, config: PluginConfig) -> None:
        """
        Update plugin configuration.

        Args:
            name: Plugin name
            config: New configuration

        Raises:
            PluginError: If plugin not found
        """
        with self._lock:
            plugin = self.registry.get(name)
            if plugin is None:
                # Store for when plugin is loaded
                self._configs[name] = config
                return

            # Call on_config_change hook
            try:
                plugin.on_config_change(config)
            except Exception as e:
                self.logger.error(
                    f"Error updating config for plugin {name}: {e}",
                    exc_info=True
                )

    def discover_and_load(self) -> List[Plugin]:
        """
        Discover and load all plugins in configured directories.

        Returns:
            List of loaded plugins
        """
        # Discover plugins
        metadata_list = self.discover_plugins()

        if not metadata_list:
            self.logger.info("No plugins discovered")
            return []

        # Resolve dependencies
        try:
            ordered_metadata = self.resolver.resolve(metadata_list)
        except PluginDependencyError as e:
            self.logger.error(f"Failed to resolve dependencies: {e}")
            return []

        # Load plugins in order
        loaded = []
        for metadata in ordered_metadata:
            try:
                # Find the plugin file
                plugin_file = self._find_plugin_file(metadata)
                if plugin_file:
                    plugin = self.load_plugin(metadata, file_path=plugin_file)
                    loaded.append(plugin)
                else:
                    self.logger.warning(
                        f"Could not find plugin file for {metadata.name}"
                    )
            except Exception as e:
                self.logger.error(
                    f"Failed to load plugin {metadata.name}: {e}",
                    exc_info=True
                )

        return loaded

    def _find_plugin_file(self, metadata: PluginMetadata) -> Optional[Path]:
        """
        Find the plugin file for given metadata.

        Args:
            metadata: Plugin metadata

        Returns:
            Path to plugin file or None if not found
        """
        for directory in self.plugin_dirs:
            # Look for plugin.py in plugin directory
            plugin_dir = directory / metadata.name
            plugin_file = plugin_dir / "plugin.py"
            if plugin_file.exists():
                return plugin_file

            # Look for {name}.py in plugins directory
            plugin_file = directory / f"{metadata.name}.py"
            if plugin_file.exists():
                return plugin_file

        return None

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self.registry.get(name)

    def get_all_plugins(self) -> Dict[str, Plugin]:
        """
        Get all loaded plugins.

        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        return self.registry.get_all()

    def get_enabled_plugins(self) -> List[Plugin]:
        """
        Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return self.registry.get_enabled()

    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a plugin.

        Args:
            name: Plugin name

        Returns:
            Dictionary with plugin information or None if not found
        """
        plugin = self.registry.get(name)
        if plugin is None:
            return None

        return {
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "author": plugin.metadata.author,
            "description": plugin.metadata.description,
            "state": plugin.state.value,
            "dependencies": plugin.metadata.dependencies,
            "enabled": plugin.config.enabled,
            "priority": plugin.config.priority,
            "error": str(plugin.get_error()) if plugin.get_error() else None,
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins with their information.

        Returns:
            List of plugin information dictionaries
        """
        plugins = []
        for name in self.registry.get_all().keys():
            info = self.get_plugin_info(name)
            if info:
                plugins.append(info)

        # Sort by priority
        plugins.sort(key=lambda p: p["priority"])
        return plugins

    def shutdown(self) -> None:
        """Shutdown the plugin manager and unload all plugins."""
        self.logger.info("Shutting down plugin manager")

        # Disable all enabled plugins
        for plugin in self.registry.get_enabled():
            try:
                self.disable_plugin(plugin.metadata.name)
            except Exception as e:
                self.logger.error(
                    f"Error disabling plugin {plugin.metadata.name}: {e}"
                )

        # Unload all loaded plugins
        for name in list(self.registry.get_all().keys()):
            try:
                self.unload_plugin(name)
            except Exception as e:
                self.logger.error(f"Error unloading plugin {name}: {e}")

        self.logger.info("Plugin manager shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
