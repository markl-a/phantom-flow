"""
Test plugin dependency resolution.

This script demonstrates how the plugin system handles dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_automation_framework.core.plugins import PluginManager, PluginState


def main():
    """Test plugin dependency resolution."""
    print("=" * 60)
    print("Testing Plugin Dependency Resolution")
    print("=" * 60)

    # Create plugin manager without auto-discovery first
    print("\n1. Creating Plugin Manager...")
    manager = PluginManager(
        plugin_dirs=[Path(__file__).parent / "plugins"],
        auto_discover=False
    )

    # Manually discover plugins with broader pattern
    print("   Discovering plugins with pattern '*.yaml'...")
    from ai_automation_framework.core.plugins import PluginLoader
    loader = PluginLoader()
    metadata_list = loader.discover_plugins(
        Path(__file__).parent / "plugins",
        pattern="*.yaml"
    )
    print(f"   Found {len(metadata_list)} plugin(s)")

    # Resolve dependencies and load
    from ai_automation_framework.core.plugins import DependencyResolver
    resolver = DependencyResolver()
    ordered_metadata = resolver.resolve(metadata_list)
    print(f"   Load order: {[m.name for m in ordered_metadata]}")

    # Load plugins in dependency order
    for metadata in ordered_metadata:
        plugin_file = Path(__file__).parent / "plugins" / f"{metadata.name}.py"
        if plugin_file.exists():
            manager.load_plugin(metadata, file_path=plugin_file)

    # List all plugins
    print("\n2. Discovered Plugins:")
    plugins = manager.list_plugins()
    for plugin_info in plugins:
        deps = ", ".join(plugin_info["dependencies"]) if plugin_info["dependencies"] else "none"
        print(f"   - {plugin_info['name']}")
        print(f"     Dependencies: {deps}")
        print(f"     State: {plugin_info['state']}")
        print(f"     Priority: {plugin_info['priority']}")
        print()

    # Verify load order
    print("\n3. Verifying Dependency Resolution:")
    base_plugin = manager.get_plugin("base_plugin")
    dependent_plugin = manager.get_plugin("dependent_plugin")

    if base_plugin and dependent_plugin:
        print(f"   ✓ Base plugin state: {base_plugin.state.value}")
        print(f"   ✓ Dependent plugin state: {dependent_plugin.state.value}")

        # Connect dependent plugin to base plugin
        if base_plugin.state == PluginState.ENABLED:
            dependent_plugin.set_base_plugin(base_plugin)
            print("   ✓ Connected dependent plugin to base plugin")

            # Test using base plugin from dependent plugin
            if dependent_plugin.state == PluginState.ENABLED:
                result = dependent_plugin.process_with_base("Hello World")
                print(f"   ✓ Processed message: {result}")
    else:
        print("   ✗ Plugins not loaded")

    # Test disabling base plugin (should fail if dependent is enabled)
    print("\n4. Testing Dependency Protection:")
    try:
        manager.disable_plugin("base_plugin")
        print("   ✗ Base plugin was disabled (this shouldn't happen!)")
    except Exception as e:
        print(f"   ✓ Correctly prevented disabling base plugin: {e}")

    # Disable dependent first, then base
    print("\n5. Proper Shutdown Order:")
    try:
        manager.disable_plugin("dependent_plugin")
        print("   ✓ Disabled dependent plugin")

        manager.disable_plugin("base_plugin")
        print("   ✓ Disabled base plugin")
    except Exception as e:
        print(f"   ✗ Error during shutdown: {e}")

    # Show final states
    print("\n6. Final Plugin States:")
    for name, plugin in manager.get_all_plugins().items():
        print(f"   - {name}: {plugin.state.value}")

    # Cleanup
    print("\n7. Shutting down...")
    manager.shutdown()
    print("   ✓ Shutdown complete")

    print("\n" + "=" * 60)
    print("Dependency Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
