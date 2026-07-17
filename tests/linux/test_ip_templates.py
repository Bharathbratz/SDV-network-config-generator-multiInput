"""Tests for the iproute2 ip-config.sh.j2 template."""

from __future__ import annotations

import pytest
from jinja2 import Environment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_ip(ip_env: Environment, data: dict, input_file: str = "configuration_end-station_Linux.json") -> str:
    tmpl = ip_env.get_template("ip-config.sh.j2")
    return tmpl.render(data=data, input_file=input_file)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIpConfigTemplate:
    """Tests for ip-config.sh.j2."""

    def test_shebang_and_errexit(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert out.startswith("#!/bin/sh")
        assert "set -eu" in out

    def test_parent_interface_brought_up(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "ip link set dev eth1" in out

    def test_mac_address_set_with_colons(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        # FZCU_MPU MAC is E4:D3:AA:96:FF:01 (colons, not dashes)
        assert "E4:D3:AA:96:FF:01" in out
        assert "E4-D3-AA-96-FF-01" not in out

    def test_vlan_link_add_commands(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "ip link add" in out
        assert "type vlan id" in out

    def test_all_vlans_present(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "eth1.2049" in out
        assert "eth1.10" in out
        assert "eth1.201" in out

    def test_ip_addr_add_commands(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "ip addr add 172.24.1.11/24 dev eth1.2049" in out
        assert "ip addr add 172.16.10.11/24 dev eth1.10" in out
        assert "ip addr add 172.16.201.11/24 dev eth1.201" in out

    def test_ip_addr_add_is_idempotent(self, ip_env: Environment, fzcu_mpu_data: dict):
        """Each ip addr add must be guarded by a grep check."""
        out = _render_ip(ip_env, fzcu_mpu_data)
        # Every 'ip addr add' line should be preceded by a 'grep -q' guard
        lines = out.splitlines()
        for i, line in enumerate(lines):
            if "ip addr add" in line and "ip addr add" in line:
                # Look back up to 3 lines for the guard
                context = "\n".join(lines[max(0, i - 3) : i])
                assert "grep -q" in context, (
                    f"ip addr add at line {i} is not guarded by grep: {line!r}"
                )

    def test_static_routes_rendered(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "ip route replace" in out
        assert "172.16.10.254" in out
        assert "172.24.1.254" in out

    def test_default_route_as_default_keyword(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "ip route replace default" in out

    def test_vlan_parent_env_var_used(self, ip_env: Environment, fzcu_mpu_data: dict):
        out = _render_ip(ip_env, fzcu_mpu_data)
        assert "VLAN_PARENT" in out

    def test_minimal_no_routes(self, ip_env: Environment):
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth1",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                    }
                ]
            }
        }
        out = _render_ip(ip_env, data)
        assert "ip route replace" not in out
        assert "ip link set dev eth1" in out

    def test_disabled_interface_not_configured(self, ip_env: Environment):
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth1",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": False,
                    }
                ]
            }
        }
        out = _render_ip(ip_env, data)
        assert "ip link set dev eth1" not in out

    def test_mtu_set_on_parent(self, ip_env: Environment):
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth1",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                        "ietf-if-extensions:max-frame-size": 9000,
                    }
                ]
            }
        }
        out = _render_ip(ip_env, data)
        assert "mtu 9000" in out

    def test_mtu_set_on_vlan(self, ip_env: Environment):
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth1",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                    },
                    {
                        "name": "eth1.100",
                        "type": "iana-if-type:l2vlan",
                        "enabled": True,
                        "ietf-if-extensions:parent-interface": "eth1",
                        "ietf-if-extensions:max-frame-size": 1500,
                        "ietf-if-extensions:encapsulation": {
                            "ietf-if-vlan-encapsulation:dot1q-vlan": {
                                "outer-tag": {
                                    "tag-type": "ieee802-dot1q-types:c-vlan",
                                    "vlan-id": 100,
                                }
                            }
                        },
                    },
                ]
            }
        }
        out = _render_ip(ip_env, data)
        assert "mtu 1500" in out
