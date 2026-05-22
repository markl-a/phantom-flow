"""Base plugin that provides common utilities for other plugins."""

from ai_automation_framework.core.plugins import Plugin, PluginMetadata, PluginConfig


class BasePlugin(Plugin):
    """
    Base plugin that provides common utilities.

    Other plugins can depend on this plugin to use shared functionality.
    """

    def __init__(self, metadata: PluginMetadata, config: PluginConfig = None):
        """Initialize the base plugin."""
        super().__init__(metadata, config)
        self._utilities = {}

    def on_load(self) -> None:
        """Load base utilities."""
        self.logger.info("Loading BasePlugin utilities...")
        self._utilities = {
            "version": "1.0.0",
            "timestamp": None
        }
        self.logger.info("BasePlugin loaded")

    def on_unload(self) -> None:
        """Cleanup base utilities."""
        self.logger.info("Unloading BasePlugin...")
        self._utilities.clear()
        self.logger.info("BasePlugin unloaded")

    def on_enable(self) -> None:
        """Enable base utilities."""
        self.logger.info("Enabling BasePlugin...")
        import time
        self._utilities["timestamp"] = time.time()
        self.logger.info("BasePlugin enabled")

    def on_disable(self) -> None:
        """Disable base utilities."""
        self.logger.info("Disabling BasePlugin...")
        self._utilities["timestamp"] = None
        self.logger.info("BasePlugin disabled")

    def get_utility_info(self) -> dict:
        """
        Get utility information.

        Returns:
            Dictionary with utility information
        """
        return self._utilities.copy()

    def format_message(self, message: str) -> str:
        """
        Format a message with plugin branding.

        Args:
            message: Message to format

        Returns:
            Formatted message
        """
        return f"[BasePlugin] {message}"


# Entry point
Plugin = BasePlugin
