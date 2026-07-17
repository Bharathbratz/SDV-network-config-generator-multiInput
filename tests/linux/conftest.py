"""Shared pytest fixtures for the linux network config test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_LINUX = _REPO_ROOT / "src" / "plugins" / "linux"
_SYSTEMD_TEMPLATES = _SRC_LINUX / "systemd-network-config" / "templates"
_IP_TEMPLATES = _SRC_LINUX / "ip-network-config" / "templates"
_INPUT_DIR = _REPO_ROOT / "input"


# ---------------------------------------------------------------------------
# Jinja2 environments
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def systemd_env() -> Environment:
    """Jinja2 environment loaded from the systemd-networkd templates."""
    return Environment(
        loader=FileSystemLoader(str(_SYSTEMD_TEMPLATES)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


@pytest.fixture(scope="session")
def ip_env() -> Environment:
    """Jinja2 environment loaded from the ip-config templates."""
    return Environment(
        loader=FileSystemLoader(str(_IP_TEMPLATES)),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )


# ---------------------------------------------------------------------------
# Minimal data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def single_parent_iface() -> dict:
    """Minimal data with one physical interface."""
    return {
        "ietf-interfaces:interfaces": {
            "interface": [
                {
                    "name": "eth1",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "ietf-if-extensions:max-frame-size": 1500,
                    "ietf-if-ethernet-like:ethernet-like": {
                        "mac-address": "F2-00-00-00-00-10",
                    },
                }
            ]
        }
    }


@pytest.fixture
def single_vlan_iface() -> dict:
    """Minimal data with one physical + one VLAN interface."""
    return {
        "ietf-interfaces:interfaces": {
            "interface": [
                {
                    "name": "eth1",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "ietf-if-extensions:max-frame-size": 1500,
                    "ietf-if-ethernet-like:ethernet-like": {
                        "mac-address": "F2-00-00-00-00-10",
                    },
                },
                {
                    "name": "eth1.2",
                    "type": "iana-if-type:l2vlan",
                    "enabled": True,
                    "ietf-if-extensions:max-frame-size": 1500,
                    "ietf-if-extensions:parent-interface": "eth1",
                    "ietf-if-extensions:encapsulation": {
                        "ietf-if-vlan-encapsulation:dot1q-vlan": {
                            "outer-tag": {
                                "tag-type": "ieee802-dot1q-types:c-vlan",
                                "vlan-id": 2,
                            }
                        }
                    },
                    "ietf-ip:ipv4": {
                        "enabled": True,
                        "address": [{"ip": "10.0.2.16", "prefix-length": 24}],
                    },
                },
            ]
        }
    }


@pytest.fixture
def fzcu_mpu_data() -> dict:
    """Full FZCU_MPU configuration loaded from the canonical Linux example."""
    import json  # noqa: PLC0415

    path = _INPUT_DIR / "examples" / "configuration_end-station_Linux.json"
    with path.open() as fh:
        return json.load(fh)
