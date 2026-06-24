from importlib.metadata import entry_points

class PluginRegistry:
    def __init__(self):
        self.plugins = {}

    def load_plugins(self):
        """Load plugins via entry_points with automatic fallback to manual imports"""
        try:
            # Try loading via entry_points (standard method)
            eps = list(entry_points(group="sdn.plugins"))
            
            if len(eps) > 0:
                # Entry points found, use them
                for ep in eps:
                    try:
                        plugin_class = ep.load()
                        plugin_instance = plugin_class()
                        self.plugins[ep.name] = plugin_instance
                    except Exception as e:
                        print(f"✗ Failed to load {ep.name}: {e}")
            else:
                # No entry points found, use fallback
                self._load_plugins_fallback()
        except Exception as e:
            # Exception occurred, use fallback
            self._load_plugins_fallback()

    def _load_plugins_fallback(self):
        """Fallback: manually import plugins if entry_points fails"""
        plugin_specs = [
            ("qnx", "src.plugins.qnx.plugin", "QNXPlugin"),
            ("android", "src.plugins.android.plugin", "AndroidPlugin"),
            ("linux", "src.plugins.linux.plugin", "LinuxPlugin"),
        ]
        
        for name, module_name, class_name in plugin_specs:
            try:
                module = __import__(module_name, fromlist=[class_name])
                plugin_class = getattr(module, class_name)
                plugin_instance = plugin_class()
                self.plugins[name] = plugin_instance
            except Exception as e:
                print(f"✗ Failed to load {name}: {e}")

    def get(self, name):
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not found")
        return self.plugins[name]

    def list_plugins(self):
        return list(self.plugins.keys())


# ✅ Instantiate and auto-load
registry = PluginRegistry()
registry.load_plugins()