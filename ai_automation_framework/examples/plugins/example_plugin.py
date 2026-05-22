"""Example plugin demonstrating the plugin system."""

from ai_automation_framework.core.plugins import (
    Plugin,
    PluginMetadata,
    PluginConfig,
    PluginLoadError,
    PluginError
)


class ExamplePlugin(Plugin):
    """
    Example plugin that demonstrates the plugin lifecycle hooks.

    This plugin shows how to implement:
    - Lifecycle hooks (on_load, on_unload, on_enable, on_disable)
    - Configuration handling
    - Error handling
    """

    def __init__(self, metadata: PluginMetadata, config: PluginConfig = None):
        """Initialize the example plugin."""
        super().__init__(metadata, config)
        self._resource = None
        self.logger.info("ExamplePlugin instance created")

    def on_load(self) -> None:
        """
        Called when plugin is loaded.

        Initialize resources that don't depend on other plugins.
        """
        self.logger.info("Loading ExamplePlugin...")

        try:
            # Initialize your resources here
            self._resource = "Initialized resource"
            self.logger.info("ExamplePlugin loaded successfully")

        except Exception as e:
            raise PluginLoadError(f"Failed to load ExamplePlugin: {e}") from e

    def on_unload(self) -> None:
        """
        Called when plugin is unloaded.

        Clean up resources allocated in on_load.
        """
        self.logger.info("Unloading ExamplePlugin...")

        # Clean up resources
        self._resource = None
        self.logger.info("ExamplePlugin unloaded successfully")

    def on_enable(self) -> None:
        """
        Called when plugin is enabled.

        Start providing plugin functionality.
        """
        self.logger.info("Enabling ExamplePlugin...")

        if self._resource is None:
            raise PluginError("Cannot enable: plugin not properly loaded")

        # Start your plugin services
        self.logger.info("ExamplePlugin enabled and ready")

    def on_disable(self) -> None:
        """
        Called when plugin is disabled.

        Stop providing plugin functionality but keep resources.
        """
        self.logger.info("Disabling ExamplePlugin...")

        # Stop your plugin services
        self.logger.info("ExamplePlugin disabled")

    def on_config_change(self, new_config: PluginConfig) -> None:
        """
        Handle configuration changes.

        Args:
            new_config: New plugin configuration
        """
        self.logger.info(f"Configuration changed: {new_config.settings}")
        super().on_config_change(new_config)

        # React to configuration changes
        # For example, adjust behavior based on new settings

    def do_something(self) -> str:
        """
        Example method that plugin consumers can call.

        Returns:
            A message string
        """
        return f"ExamplePlugin says: {self._resource}"


# This is the entry point that will be loaded
Plugin = ExamplePlugin
