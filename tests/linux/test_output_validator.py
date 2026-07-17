"""Tests for the output validator module."""

from __future__ import annotations

import configparser
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

from src.plugins.linux.output_validator import (
    validate_output,
    _validate_link_file,
    _validate_netdev_file,
    _validate_network_file,
    _validate_sh_script,
)


# ---------------------------------------------------------------------------
# Unit tests for individual validators
# ---------------------------------------------------------------------------

class TestLinkFileValidator:
    def test_valid_link_file(self, tmp_path: Path):
        f = tmp_path / "10-eth1.link"
        f.write_text(
            "[Match]\nOriginalName=pfe0\nType=ether\n\n[Link]\nName=eth1\nMTUBytes=1500\n"
        )
        assert _validate_link_file(f) == []

    def test_missing_match_section(self, tmp_path: Path):
        f = tmp_path / "bad.link"
        f.write_text("[Link]\nName=eth1\n")
        errs = _validate_link_file(f)
        assert any("Match" in e for e in errs)

    def test_missing_link_section(self, tmp_path: Path):
        f = tmp_path / "bad.link"
        f.write_text("[Match]\nOriginalName=pfe0\n")
        errs = _validate_link_file(f)
        assert any("Link" in e for e in errs)

    def test_missing_name_in_link(self, tmp_path: Path):
        f = tmp_path / "bad.link"
        f.write_text("[Match]\nOriginalName=pfe0\n\n[Link]\nMTUBytes=1500\n")
        errs = _validate_link_file(f)
        assert any("Name" in e for e in errs)


class TestNetdevFileValidator:
    def test_valid_netdev_file(self, tmp_path: Path):
        f = tmp_path / "30-eth1.10.netdev"
        f.write_text("[NetDev]\nName=eth1.10\nKind=vlan\n\n[VLAN]\nId=10\n")
        assert _validate_netdev_file(f) == []

    def test_missing_netdev_section(self, tmp_path: Path):
        f = tmp_path / "bad.netdev"
        f.write_text("[VLAN]\nId=10\n")
        errs = _validate_netdev_file(f)
        assert any("NetDev" in e for e in errs)

    def test_vlan_kind_without_vlan_section(self, tmp_path: Path):
        f = tmp_path / "bad.netdev"
        f.write_text("[NetDev]\nName=eth1.10\nKind=vlan\n")
        errs = _validate_netdev_file(f)
        assert any("[VLAN]" in e for e in errs)


class TestNetworkFileValidator:
    def test_valid_network_file(self, tmp_path: Path):
        f = tmp_path / "20-eth1.network"
        f.write_text("[Match]\nName=eth1\n\n[Network]\nVLAN=eth1.10\n")
        assert _validate_network_file(f) == []

    def test_missing_match_section(self, tmp_path: Path):
        f = tmp_path / "bad.network"
        f.write_text("[Network]\nVLAN=eth1.10\n")
        errs = _validate_network_file(f)
        assert any("Match" in e for e in errs)

    def test_missing_name_in_match(self, tmp_path: Path):
        f = tmp_path / "bad.network"
        f.write_text("[Match]\nType=ether\n\n[Network]\nVLAN=eth1.10\n")
        errs = _validate_network_file(f)
        assert any("Name" in e for e in errs)


class TestShScriptValidator:
    def test_valid_script(self, tmp_path: Path):
        f = tmp_path / "ip-config.sh"
        f.write_text("#!/bin/sh\nset -eu\nip link set dev eth1 up\n")
        assert _validate_sh_script(f) == []

    def test_invalid_script_syntax(self, tmp_path: Path):
        f = tmp_path / "ip-config.sh"
        f.write_text("#!/bin/sh\nset -eu\nif then done\n")
        errs = _validate_sh_script(f)
        assert len(errs) > 0


# ---------------------------------------------------------------------------
# Integration: validate_output on a complete overlay tree
# ---------------------------------------------------------------------------

class TestValidateOutput:
    def test_empty_dir_fails(self, tmp_path: Path):
        errs = validate_output(tmp_path / "overlay")
        assert len(errs) > 0

    def test_complete_overlay_passes(self, tmp_path: Path):
        """Build a minimal but complete overlay tree and expect no errors."""
        overlay = tmp_path / "overlay"

        netd = overlay / "etc" / "systemd" / "network"
        netd.mkdir(parents=True)

        (netd / "10-eth1.link").write_text(
            "[Match]\nOriginalName=pfe0\nType=ether\n\n[Link]\nName=eth1\nMTUBytes=1500\n"
        )
        (netd / "20-eth1.network").write_text(
            "[Match]\nName=eth1\n\n[Link]\nMACAddress=F2:00:00:00:00:10\nMTUBytes=1500\n\n[Network]\nVLAN=eth1.2\n"
        )
        (netd / "30-eth1.2.netdev").write_text(
            "[NetDev]\nName=eth1.2\nKind=vlan\n\n[VLAN]\nId=2\n"
        )
        (netd / "40-eth1.2.network").write_text(
            "[Match]\nName=eth1.2\n\n[Network]\nAddress=10.0.2.16/24\n\n[Link]\nMTUBytes=1500\n"
        )

        script_dir = overlay / "usr" / "lib" / "network-config"
        script_dir.mkdir(parents=True)
        sh = script_dir / "ip-config.sh"
        sh.write_text("#!/bin/sh\nset -eu\nip link set dev eth1 up\n")

        errs = validate_output(overlay)
        assert errs == [], f"Unexpected errors: {errs}"
