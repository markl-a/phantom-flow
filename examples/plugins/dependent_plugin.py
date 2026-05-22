"""Plugin that depends on base_plugin to demonstrate dependency resolution."""

from ai_automation_framework.core.plugins import (
    Plugin,
    PluginMetadata,
    PluginConfig,
    PluginError
)


class DependentPlugin(Plugin):
    """
    Plugin that depends on BasePlugin.

    Demonstrates how plugins can use functionality from other plugins.
    """

    def __init__(self, metadata: PluginMetadata, config: PluginConfig = None):
        """Initialize the dependent plugin."""
        super().__init__(metadata, config)
        self._base_plugin = None

    def on_load(self) -> None:
        """Load the plugin."""
        self.logger.info("Loading DependentPlugin...")
        self.logger.info("DependentPlugin loaded")

    def on_unload(self) -> None:
        """Unload the plugin."""
        self.logger.info("Unloading DependentPlugin...")
        self._base_plugin = None
        self.logger.info("DependentPlugin unloaded")

    def on_enable(self) -> None:
        """Enable the plugin and connect to base plugin."""
        self.logger.info("Enabling DependentPlugin...")

        # Get reference to base plugin (from plugin manager if available)
        # In a real implementation, you would pass the manager reference
        # or use a service locator pattern
        self.logger.info("DependentPlugin enabled")

    def on_disable(self) -> None:
        """Disable the plugin."""
        self.logger.info("Disabling DependentPlugin...")
        self._base_plugin = None
        self.logger.info("DependentPlugin disabled")

    def set_base_plugin(self, base_plugin: Plugin) -> None:
        """
        Set the base plugin reference.

        Args:
            base_plugin: Instance of BasePlugin
        """
        self._base_plugin = base_plugin
        self.logger.info("Connected to BasePlugin")

    def process_with_base(self, message: str) -> str:
        """
        Process a message using base plugin utilities.

        Args:
            message: Message to process

        Returns:
            Processed message

        Raises:
            PluginError: If base plugin is not available
        """
        if self._base_plugin is None:
            raise PluginError("BasePlugin not connected")

        # Use base plugin functionality
        formatted = self._base_plugin.format_message(message)
        info = self._base_plugin.get_utility_info()

        return f"{formatted} (Base version: {info['version']})"


# Entry point
Plugin = DependentPlugin
