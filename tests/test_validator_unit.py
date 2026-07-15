"""Unit tests for semantic validation rules.

These tests validate the validator boundary in isolation from parser and CLI.
"""

import pytest

from src.core.parser import ParsedConfig
from src.core.validator import validate_json


def test_validate_json_accepts_valid_ietf_normalized_model() -> None:
    """A valid normalized IETF model should pass without raising."""
    parsed = ParsedConfig(
        model={
            "interfaces": [
                {"name": "eth0", "type": "ethernet", "enabled": True},
                {
                    "name": "eth0.10",
                    "type": "vlan",
                    "enabled": True,
                    "vlan_id": 10,
                    "ip": "192.168.1.2",
                },
            ],
            "routes": [{"destination": "0.0.0.0/0", "gateway": "192.168.1.1"}],
            "dns_servers": ["1.1.1.1", "8.8.8.8"],
        },
        source_format="ietf",
        source_config={},
    )

    validate_json(parsed)


def test_validate_json_rejects_invalid_ietf_vlan_id() -> None:
    """Out-of-range VLAN IDs should fail for normalized IETF model."""
    parsed = ParsedConfig(
        model={
            "interfaces": [
                {"name": "eth0.9999", "type": "vlan", "vlan_id": 5000, "ip": "10.1.1.2"}
            ],
            "routes": [],
            "dns_servers": [],
        },
        source_format="ietf",
        source_config={},
    )

    with pytest.raises(ValueError, match="Invalid VLAN ID"):
        validate_json(parsed)


def test_validate_json_rejects_invalid_ietf_gateway() -> None:
    """Invalid route gateways should fail normalized validation."""
    parsed = ParsedConfig(
        model={
            "interfaces": [{"name": "eth0", "type": "ethernet"}],
            "routes": [{"destination": "0.0.0.0/0", "gateway": "not-an-ip"}],
            "dns_servers": [],
        },
        source_format="ietf",
        source_config={},
    )

    with pytest.raises(ValueError, match="Invalid gateway"):
        validate_json(parsed)


def test_validate_json_accepts_valid_legacy_config() -> None:
    """A valid legacy payload should pass through legacy path checks."""
    parsed = ParsedConfig(
        model={},
        source_format="legacy",
        source_config={
            "interfaces": [
                {
                    "name": "eth1",
                    "ip": "10.0.0.2",
                    "netmask": "255.255.255.0",
                    "tsn": {"bandwidth": 50, "priority": 3},
                }
            ],
            "routes": [{"destination": "0.0.0.0/0", "gateway": "10.0.0.1"}],
        },
    )

    validate_json(parsed)


def test_validate_json_rejects_legacy_without_interfaces() -> None:
    """Legacy payload must contain interfaces section."""
    parsed = ParsedConfig(model={}, source_format="legacy", source_config={"routes": []})

    with pytest.raises(ValueError, match="Missing interfaces section"):
        validate_json(parsed)


def test_validate_json_rejects_unknown_source_format() -> None:
    """Unexpected parser format identifiers must fail fast."""
    parsed = ParsedConfig(model={}, source_format="unknown", source_config={})

    with pytest.raises(ValueError, match="Unsupported source format"):
        validate_json(parsed)
