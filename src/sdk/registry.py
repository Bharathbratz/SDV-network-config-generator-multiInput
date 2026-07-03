"""Plugin registry and loading strategy.

The registry attempts to load plugins from Python entry points first. If no
entry-point plugins are successfully loaded, it falls back to importing known
built-in plugins defined in ``PLUGIN_SPECS``.
"""

from importlib import import_module
from importlib.metadata import entry_points


class PluginRegistry:
    """Load, store, and resolve plugin instances by name."""

    # Built-in plugin fallback map: (registry name, module path, class name)
    PLUGIN_SPECS = [
        ("android", "src.plugins.android.plugin", "AndroidPlugin"),
        ("linux",   "src.plugins.linux.plugin",   "LinuxPlugin"),
        ("mcu",     "src.plugins.mcu.plugin",     "MCUPlugin"),
        ("qnx",     "src.plugins.qnx.plugin",     "QNXPlugin"),
        ("switch",  "src.plugins.switch.plugin",  "SwitchPlugin"),
    ]

    def __init__(self):
        """Initialize an empty in-memory plugin registry."""
        self.plugins = {}

    def load_plugins(self):
        """Load plugins from entry points, then fallback to built-ins if needed."""
        # Entry points allow external packages to register plugins dynamically.
        for plugin in entry_points(group="sdn.plugins"):
            try:
                # ``plugin.load()`` returns the plugin class; ``()`` instantiates it.
                self.plugins[plugin.name] = plugin.load()()
            except Exception as e:
                print(f"Failed to load {plugin.name}: {e}")

        if not self.plugins:
            self._load_plugins_fallback()

    def _load_plugins_fallback(self):
        """Load built-in plugins when entry-point discovery yields no usable plugins."""
        for name, module_path, class_name in self.PLUGIN_SPECS:
            try:
                module = import_module(module_path)
                # Import class symbol by name and register an instantiated plugin.
                self.plugins[name] = getattr(module, class_name)()
            except Exception as e:
                print(f"Failed to load {name}: {e}")

        # No plugins available means generation cannot continue safely.
        if not self.plugins:
            raise RuntimeError("No plugins could be loaded. Please check your plugin configurations.")

    def get(self, name):
        """Return a plugin instance by registry name.

        Raises:
            ValueError: If the requested plugin does not exist.
        """
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not found")
        return self.plugins[name]

    def list_plugins(self):
        """List currently loaded plugin names."""
        return list(self.plugins.keys())


# Module-level singleton used by orchestrator services.
registry = PluginRegistry()
registry.load_plugins()