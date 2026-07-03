"""Focused CLI negative-path tests for error translation behavior."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from src.main import main


def test_invalid_os_returns_click_error(tmp_path: Path) -> None:
    """Invalid --os should fail with a clean, actionable message."""
    runner = CliRunner()
    input_file = Path("input/configuration_end-station_Linux.json")

    result = runner.invoke(
        main,
        [
            "--input",
            str(input_file),
            "--output",
            str(tmp_path),
            "--os",
            "invalid",
        ],
    )

    assert result.exit_code == 1
    assert "Error: invalid plugin 'invalid'." in result.output


def test_malformed_json_returns_click_error(tmp_path: Path) -> None:
    """Malformed JSON should fail without traceback and include parser detail."""
    runner = CliRunner()
    bad_json = tmp_path / "malformed.json"
    bad_json.write_text('{"interfaces": [ {"name": "eth0"} ]', encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "--input",
            str(bad_json),
            "--output",
            str(tmp_path / "out"),
            "--os",
            "linux",
        ],
    )

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Expecting" in result.output


def test_permission_denied_is_translated_to_click_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filesystem permission failures should be translated into Click-style errors."""
    runner = CliRunner()
    input_file = Path("input/configuration_end-station_Linux.json")

    import src.core.generator as generator

    real_makedirs = generator.os.makedirs

    def fake_makedirs(path: str, exist_ok: bool = False) -> None:
        path_str = str(path)
        if path_str.endswith("/linux"):
            raise PermissionError("permission denied in test")
        real_makedirs(path, exist_ok=exist_ok)

    monkeypatch.setattr(generator.os, "makedirs", fake_makedirs)

    result = runner.invoke(
        main,
        [
            "--input",
            str(input_file),
            "--output",
            str(tmp_path / "no_write"),
            "--os",
            "linux",
        ],
    )

    assert result.exit_code == 1
    assert "Error: filesystem error while generating 'linux' output" in result.output
    assert "permission denied in test" in result.output
