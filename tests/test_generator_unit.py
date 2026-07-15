"""Unit tests for generation orchestration.

The goal is to validate orchestration boundaries independently of plugin
implementations by patching parser, validator, and registry collaborators.
"""

from pathlib import Path

import pytest

import src.core.generator as generator
from src.core.parser import ParsedConfig


class DummyPlugin:
    """Simple test plugin that records generation calls."""

    def __init__(self) -> None:
        self.calls = []

    def generate(self, model: dict, output_dir: str) -> None:
        self.calls.append((model, output_dir))


class DummyRegistry:
    """Test registry with deterministic plugin lookup behavior."""

    def __init__(self, plugin_names: list[str]) -> None:
        self._plugins = {name: DummyPlugin() for name in plugin_names}

    def list_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def get(self, name: str) -> DummyPlugin:
        return self._plugins[name]


def test_validate_input_file_rejects_missing_path(tmp_path: Path) -> None:
    """Missing input files should fail early before orchestration starts."""
    with pytest.raises(ValueError, match="input file does not exist"):
        generator._validate_input_file(str(tmp_path / "missing.json"))


def test_validate_output_dir_rejects_file_path(tmp_path: Path) -> None:
    """Output path must be a directory and not an existing file."""
    file_path = tmp_path / "output.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="output must be a directory path"):
        generator._validate_output_dir(str(file_path))


def test_parse_and_validate_wraps_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parser-level filesystem errors should be translated to ValueError."""

    def _raise_os_error(_path: str) -> ParsedConfig:
        raise OSError("simulated read failure")

    monkeypatch.setattr(generator, "parse_json", _raise_os_error)

    with pytest.raises(ValueError, match="failed to read input file"):
        generator._parse_and_validate("input.json")


def test_generate_sdn_config_single_target_invokes_selected_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Single-target generation should parse/validate once and run one plugin."""
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")

    parsed = ParsedConfig(
        model={"interfaces": [], "routes": [], "dns_servers": []},
        source_format="ietf",
        source_config={},
    )
    test_registry = DummyRegistry(["linux", "android"])

    monkeypatch.setattr(generator, "parse_json", lambda _p: parsed)
    monkeypatch.setattr(generator, "validate_json", lambda _p: None)
    monkeypatch.setattr(generator, "registry", test_registry)

    result = generator.generate_sdn_config(
        str(input_file), str(tmp_path / "out"), "linux"
    )

    assert result == "linux"
    assert len(test_registry.get("linux").calls) == 1
    assert len(test_registry.get("android").calls) == 0


def test_generate_sdn_config_all_invokes_each_plugin_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """all target should fan out to every loaded plugin with one parsed model."""
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")

    parsed = ParsedConfig(
        model={"interfaces": [], "routes": [], "dns_servers": []},
        source_format="ietf",
        source_config={},
    )
    test_registry = DummyRegistry(["switch", "linux", "android"])

    monkeypatch.setattr(generator, "parse_json", lambda _p: parsed)
    monkeypatch.setattr(generator, "validate_json", lambda _p: None)
    monkeypatch.setattr(generator, "registry", test_registry)

    result = generator.generate_sdn_config(str(input_file), str(tmp_path / "out"), "all")

    assert result == "all"
    for name in test_registry.list_plugins():
        assert len(test_registry.get(name).calls) == 1


def test_generate_with_plugin_translates_filesystem_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plugin filesystem failures should be wrapped in actionable ValueError."""

    class FailingPlugin:
        def generate(self, _model: dict, _output_dir: str) -> None:
            raise PermissionError("write denied")

    class LocalRegistry:
        def get(self, _name: str) -> FailingPlugin:
            return FailingPlugin()

    monkeypatch.setattr(generator, "registry", LocalRegistry())

    with pytest.raises(ValueError, match="filesystem error while generating"):
        generator._generate_with_plugin({}, str(tmp_path), "linux")
