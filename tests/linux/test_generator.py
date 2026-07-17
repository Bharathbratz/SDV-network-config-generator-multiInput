"""Integration tests for the Linux network config generator.

Tests the full pipeline:
  JSON input → YANG validation → Jinja2 rendering → output validation → overlay tree
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

from src.plugins.linux.generator import generate_ip, generate_systemd, load_context
from src.plugins.linux.output_validator import validate_output


@pytest.fixture
def overlay_dir(tmp_path: Path) -> Path:
    return tmp_path / "overlay"


@pytest.fixture
def linux_context() -> dict:
    path = _REPO_ROOT / "input" / "examples" / "configuration_end-station_Linux.json"
    return load_context(path)


# ---------------------------------------------------------------------------
# generate_systemd
# ---------------------------------------------------------------------------

class TestGenerateSystemd:
    def test_creates_link_file(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        link_files = list(netd.glob("*.link"))
        assert len(link_files) == 1
        assert "eth1" in link_files[0].name

    def test_creates_parent_network_file(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        # Parent file: name ends in '-<iface>.network' with no VLAN digit after the dot
        import re
        network_files = [f for f in netd.glob("*.network") if not re.search(r'eth1\.\d', f.name)]
        assert len(network_files) == 1

    def test_creates_three_netdev_files(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        netdev_files = list(netd.glob("*.netdev"))
        assert len(netdev_files) == 3

    def test_creates_three_vlan_network_files(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        import re
        vlan_network_files = [f for f in netd.glob("*.network") if re.search(r'eth1\.\d', f.name)]
        assert len(vlan_network_files) == 3

    def test_link_file_content(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        link_file = next(netd.glob("*.link"))
        content = link_file.read_text()
        assert "[Match]" in content
        assert "[Link]" in content
        assert "Name=eth1" in content

    def test_netdev_vlan2049_content(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        netdev = next(f for f in netd.glob("*.netdev") if "2049" in f.name)
        content = netdev.read_text()
        assert "Kind=vlan" in content
        assert "Id=2049" in content

    def test_parent_network_has_vlan_entries(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        netd = overlay_dir / "etc" / "systemd" / "network"
        import re
        parent_net = next(f for f in netd.glob("*.network") if not re.search(r'eth1\.\d', f.name))
        content = parent_net.read_text()
        assert "VLAN=eth1.2049" in content
        assert "VLAN=eth1.10" in content
        assert "VLAN=eth1.201" in content


# ---------------------------------------------------------------------------
# generate_ip
# ---------------------------------------------------------------------------

class TestGenerateIp:
    def test_creates_ip_config_sh(self, overlay_dir: Path, linux_context: dict):
        generate_ip(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        sh = overlay_dir / "usr" / "lib" / "network-config" / "ip-config.sh"
        assert sh.exists()

    def test_script_is_executable(self, overlay_dir: Path, linux_context: dict):
        generate_ip(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        sh = overlay_dir / "usr" / "lib" / "network-config" / "ip-config.sh"
        assert sh.stat().st_mode & 0o111, "ip-config.sh must be executable"

    def test_script_contains_all_vlans(self, overlay_dir: Path, linux_context: dict):
        generate_ip(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        sh = overlay_dir / "usr" / "lib" / "network-config" / "ip-config.sh"
        content = sh.read_text()
        assert "eth1.2049" in content
        assert "eth1.10" in content
        assert "eth1.201" in content


# ---------------------------------------------------------------------------
# Full pipeline + output validation
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_output_validation_passes(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        generate_ip(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        errors = validate_output(overlay_dir)
        assert errors == [], f"Output validation errors: {errors}"

    def test_overlay_tree_structure(self, overlay_dir: Path, linux_context: dict):
        generate_systemd(linux_context, overlay_dir, "configuration_end-station_Linux.json")
        generate_ip(linux_context, overlay_dir, "configuration_end-station_Linux.json")

        expected_dirs = [
            overlay_dir / "etc" / "systemd" / "network",
            overlay_dir / "usr" / "lib" / "network-config",
        ]
        for d in expected_dirs:
            assert d.is_dir(), f"Expected directory not found: {d}"

    def test_generator_cli_runs(self, tmp_path: Path):
        from src.plugins.linux.generator import main  # noqa: PLC0415

        out_base = tmp_path / "out"
        result = main([
            "-i", str(_REPO_ROOT / "input" / "examples" / "configuration_end-station_Linux.json"),
            "-o", str(out_base),
            "--skip-yang-validation",
        ])
        assert result == 0
        overlay = out_base / "overlay"
        assert (overlay / "etc" / "systemd" / "network").exists()
        assert (overlay / "usr" / "lib" / "network-config" / "ip-config.sh").exists()

    def test_manifest_written(self, tmp_path: Path):
        from src.plugins.linux.generator import main  # noqa: PLC0415

        out_base = tmp_path / "out"
        main([
            "-i", str(_REPO_ROOT / "input" / "examples" / "configuration_end-station_Linux.json"),
            "-o", str(out_base),
            "--skip-yang-validation",
        ])
        manifest = out_base / "overlay.sha256"
        assert manifest.exists()
        content = manifest.read_text()
        assert "ip-config.sh" in content
