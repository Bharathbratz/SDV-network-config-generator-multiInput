"""Unit tests for parser behavior and format normalization boundaries.

These tests validate parser-only concerns:
- source-format detection
- RFC/IETF normalization into internal model
- legacy payload mapping path
- file read integration for parse_json
"""

import json
from pathlib import Path

from src.core.parser import (
    ParsedConfig,
    _parse_json_data,
    _prefix_to_netmask,
    parse_json,
)


def test_prefix_to_netmask_common_values() -> None:
    """CIDR prefixes should map to expected dotted-decimal netmasks."""
    assert _prefix_to_netmask(0) == "0.0.0.0"
    assert _prefix_to_netmask(24) == "255.255.255.0"
    assert _prefix_to_netmask(32) == "255.255.255.255"


def test_parse_json_data_detects_ietf_and_normalizes() -> None:
    """IETF payloads should produce normalized ParsedConfig with ietf marker."""
    ietf_payload = {
        "ietf-interfaces:interfaces": {
            "interface": [
                {
                    "name": "eth0",
                    "type": "iana-if-type:ethernetCsmacd",
                    "enabled": True,
                    "ietf-if-ethernet-like:ethernet-like": {
                        "mac-address": "00:11:22:33:44:55"
                    },
                },
                {
                    "name": "eth0.10",
                    "type": "iana-if-type:l2vlan",
                    "enabled": True,
                    "ietf-if-extensions:parent-interface": "eth0",
                    "ietf-if-extensions:encapsulation": {
                        "ietf-if-vlan-encapsulation:dot1q-vlan": {
                            "outer-tag": {"vlan-id": 10}
                        }
                    },
                    "ietf-ip:ipv4": {
                        "address": [{"ip": "192.168.10.2", "prefix-length": 24}]
                    },
                },
            ]
        },
        "ietf-routing:routing": {
            "control-plane-protocols": {
                "control-plane-protocol": [
                    {
                        "static-routes": {
                            "ietf-ipv4-unicast-routing:ipv4": {
                                "route": [
                                    {
                                        "destination-prefix": "0.0.0.0/0",
                                        "next-hop": {
                                            "next-hop-address": "192.168.10.1"
                                        },
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        },
        "ietf-system:system": {
            "hostname": "node-a",
            "dns-resolver": {
                "server": [{"udp-and-tcp": {"address": "8.8.8.8"}}]
            },
        },
    }

    parsed = _parse_json_data(ietf_payload)

    assert isinstance(parsed, ParsedConfig)
    assert parsed.source_format == "ietf"
    assert parsed.model["hostname"] == "node-a"
    assert parsed.model["dns_servers"] == ["8.8.8.8"]
    assert len(parsed.model["interfaces"]) == 2
    assert parsed.model["interfaces"][1]["vlan_id"] == 10
    assert parsed.model["interfaces"][1]["netmask"] == "255.255.255.0"
    assert parsed.model["routes"][0]["gateway"] == "192.168.10.1"


def test_parse_json_data_detects_legacy_and_maps() -> None:
    """Legacy payloads should map via mapper and preserve source config metadata."""
    legacy_payload = {
        "network-config": {
            "interfaces": [
                {
                    "name": "eth1",
                    "ip": "10.0.0.2",
                    "netmask": "255.255.255.0",
                    "vlan_id": 200,
                }
            ],
            "routes": [{"destination": "0.0.0.0/0", "gateway": "10.0.0.1"}],
        }
    }

    parsed = _parse_json_data(legacy_payload)

    assert parsed.source_format == "legacy"
    assert parsed.source_config["interfaces"][0]["name"] == "eth1"
    assert parsed.model["interfaces"][0]["vlan"] == 200
    assert parsed.model["routes"][0]["gateway"] == "10.0.0.1"


def test_parse_json_reads_file_and_returns_parsed_config(tmp_path: Path) -> None:
    """parse_json should load JSON from disk and route through parser pipeline."""
    payload = {
        "network-config": {
            "interfaces": [
                {
                    "name": "eth2",
                    "ip": "172.16.1.10",
                    "netmask": "255.255.255.0",
                }
            ]
        }
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")

    parsed = parse_json(str(input_file))

    assert parsed.source_format == "legacy"
    assert parsed.model["interfaces"][0]["name"] == "eth2"
