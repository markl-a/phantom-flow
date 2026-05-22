"""
Demonstration of the AI Automation Framework Plugin System.

This example shows how to:
1. Create a plugin manager
2. Load plugins from files
3. Enable/disable plugins
4. Handle plugin dependencies
5. Configure plugins
6. Use plugin functionality
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_automation_framework.core.plugins import (
    PluginManager,
    PluginMetadata,
    PluginConfig,
    PluginState,
    PluginError,
    PluginLoadError
)


def main():
    """Run the plugin system demonstration."""
    print("=" * 60)
    print("AI Automation Framework - Plugin System Demo")
    print("=" * 60)

    # 1. Create Plugin Manager
    print("\n1. Creating Plugin Manager...")
    manager = PluginManager(
        plugin_dirs=[Path(__file__).parent / "plugins"],
        auto_discover=True  # Automatically discover and load plugins
    )
    print("✓ Plugin Manager created")

    # 2. List discovered plugins
    print("\n2. Discovered Plugins:")
    plugins = manager.list_plugins()
    for plugin_info in plugins:
        print(f"   - {plugin_info['name']} v{plugin_info['version']}")
        print(f"     State: {plugin_info['state']}")
        print(f"     Author: {plugin_info['author']}")
        print(f"     Description: {plugin_info['description']}")
        print()

    # 3. Get a specific plugin
    print("\n3. Getting ExamplePlugin...")
    example_plugin = manager.get_plugin("example_plugin")
    if example_plugin:
        print(f"✓ Found plugin: {example_plugin}")
        print(f"  State: {example_plugin.state.value}")
    else:
        print("✗ ExamplePlugin not found. Make sure it's loaded.")
        print("  This is expected if auto-discovery didn't find it.")

    # 4. Load a plugin manually (if not auto-loaded)
    if example_plugin is None:
        print("\n4. Loading plugin manually...")
        try:
            metadata = PluginMetadata(
                name="example_plugin",
                version="1.0.0",
                author="AI Automation Framework Team",
                description="Example plugin for demonstration",
                dependencies=[],
                entry_point="Plugin"
            )
            config = PluginConfig(
                enabled=True,
                priority=100,
                settings={"message": "Hello from manual load!"}
            )

            plugin_file = Path(__file__).parent / "plugins" / "example_plugin.py"
            if plugin_file.exists():
                example_plugin = manager.load_plugin(
                    metadata,
                    file_path=plugin_file,
                    config=config
                )
                print(f"✓ Plugin loaded: {example_plugin.metadata.name}")
            else:
                print(f"✗ Plugin file not found: {plugin_file}")
        except PluginLoadError as e:
            print(f"✗ Failed to load plugin: {e}")

    # 5. Work with the plugin
    if example_plugin:
        print("\n5. Working with the plugin...")
        print(f"   Current state: {example_plugin.state.value}")

        # Enable if not already enabled
        if example_plugin.state != PluginState.ENABLED:
            try:
                manager.enable_plugin("example_plugin")
                print("   ✓ Plugin enabled")
            except PluginError as e:
                print(f"   ✗ Failed to enable plugin: {e}")

        # Call plugin method (if enabled)
        if example_plugin.state == PluginState.ENABLED:
            try:
                result = example_plugin.do_something()
                print(f"   Plugin response: {result}")
            except Exception as e:
                print(f"   ✗ Error calling plugin method: {e}")

        # Update configuration
        print("\n6. Updating plugin configuration...")
        new_config = PluginConfig(
            enabled=True,
            priority=50,
            settings={"message": "Updated configuration!"}
        )
        try:
            manager.configure_plugin("example_plugin", new_config)
            print("   ✓ Configuration updated")
        except Exception as e:
            print(f"   ✗ Failed to update configuration: {e}")

        # Disable plugin
        print("\n7. Disabling plugin...")
        try:
            manager.disable_plugin("example_plugin")
            print(f"   ✓ Plugin disabled. State: {example_plugin.state.value}")
        except PluginError as e:
            print(f"   ✗ Failed to disable plugin: {e}")

        # Re-enable plugin
        print("\n8. Re-enabling plugin...")
        try:
            manager.enable_plugin("example_plugin")
            print(f"   ✓ Plugin enabled. State: {example_plugin.state.value}")
        except PluginError as e:
            print(f"   ✗ Failed to enable plugin: {e}")

    # 9. Show all enabled plugins
    print("\n9. All Enabled Plugins:")
    enabled = manager.get_enabled_plugins()
    for plugin in enabled:
        print(f"   - {plugin.metadata.name} (priority: {plugin.config.priority})")

    # 10. Shutdown (cleanup)
    print("\n10. Shutting down Plugin Manager...")
    manager.shutdown()
    print("✓ Plugin Manager shutdown complete")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
