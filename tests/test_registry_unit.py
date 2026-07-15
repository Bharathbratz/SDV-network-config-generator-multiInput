"""Unit tests for plugin registry loading strategy.

These tests isolate registry behavior by patching entry-point discovery and
fallback imports.
"""

import types

import pytest

import src.sdk.registry as registry_module
from src.sdk.registry import PluginRegistry


class FakeEntryPoint:
    """Minimal entry-point stub compatible with PluginRegistry.load_plugins."""

    def __init__(self, name: str, plugin_cls):
        self.name = name
        self._plugin_cls = plugin_cls

    def load(self):
        return self._plugin_cls


def test_load_plugins_prefers_entry_points(monkeypatch: pytest.MonkeyPatch) -> None:
    """When entry points are available, registry should load from them."""

    class EPPlugin:
        pass

    monkeypatch.setattr(
        registry_module,
        "entry_points",
        lambda group: [FakeEntryPoint("ep-linux", EPPlugin)] if group == "sdn.plugins" else [],
    )

    reg = PluginRegistry()
    reg.load_plugins()

    assert reg.list_plugins() == ["ep-linux"]
    assert isinstance(reg.get("ep-linux"), EPPlugin)


def test_load_plugins_uses_fallback_when_entry_points_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback imports should populate built-in plugins when no entry points exist."""
    monkeypatch.setattr(registry_module, "entry_points", lambda group: [])

    class LinuxPlugin:
        pass

    fake_module = types.SimpleNamespace(LinuxPlugin=LinuxPlugin)

    def fake_import_module(module_path: str):
        if module_path == "src.plugins.linux.plugin":
            return fake_module
        raise ImportError("missing module in test")

    monkeypatch.setattr(registry_module, "import_module", fake_import_module)

    reg = PluginRegistry()
    reg.PLUGIN_SPECS = [("linux", "src.plugins.linux.plugin", "LinuxPlugin")]
    reg.load_plugins()

    assert reg.list_plugins() == ["linux"]
    assert isinstance(reg.get("linux"), LinuxPlugin)


def test_load_plugins_raises_when_all_sources_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registry should raise RuntimeError if neither entry points nor fallback load."""
    monkeypatch.setattr(registry_module, "entry_points", lambda group: [])
    monkeypatch.setattr(registry_module, "import_module", lambda _path: (_ for _ in ()).throw(ImportError("nope")))

    reg = PluginRegistry()
    reg.PLUGIN_SPECS = [("linux", "src.plugins.linux.plugin", "LinuxPlugin")]

    with pytest.raises(RuntimeError, match="No plugins could be loaded"):
        reg.load_plugins()


def test_get_unknown_plugin_raises_value_error() -> None:
    """Unknown plugin names should produce a stable ValueError."""
    reg = PluginRegistry()

    with pytest.raises(ValueError, match="not found"):
        reg.get("does-not-exist")
