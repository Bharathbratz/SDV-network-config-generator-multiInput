"""Tests for the systemd-networkd Jinja2 templates.

Covers:
* parent_interface_name_static.j2  → .link
* parent_interface.j2              → .network (parent)
* vlan_netdev.j2                   → .netdev
* vlan_network.j2                  → .network (VLAN)
"""

from __future__ import annotations

import pytest
from jinja2 import Environment


# ---------------------------------------------------------------------------
# parent_interface_name_static.j2  (.link file)
# ---------------------------------------------------------------------------

class TestLinkTemplate:
    """Tests for parent_interface_name_static.j2."""

    def test_renders_match_and_link_sections(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "[Match]" in out
        assert "[Link]" in out

    def test_link_name_set(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "Name=eth1" in out

    def test_mtu_bytes_set(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "MTUBytes=1500" in out

    def test_no_vlan_in_link_file(self, systemd_env: Environment, single_vlan_iface: dict):
        """VLAN interfaces must not produce a .link entry."""
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        out = tmpl.render(data=single_vlan_iface)
        # Only one [Match] block (for the parent), not for the VLAN
        assert out.count("[Match]") == 1
        assert "eth1.2" not in out

    def test_no_output_for_empty_interfaces(self, systemd_env: Environment):
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        data = {"ietf-interfaces:interfaces": {"interface": []}}
        out = tmpl.render(data=data)
        assert out.strip() == ""

    def test_fzcu_mpu_link_file(self, systemd_env: Environment, fzcu_mpu_data: dict):
        tmpl = systemd_env.get_template("parent_interface_name_static.j2")
        out = tmpl.render(data=fzcu_mpu_data)
        assert "Name=eth1" in out
        assert "MTUBytes=1500" in out


# ---------------------------------------------------------------------------
# parent_interface.j2  (.network file for parent)
# ---------------------------------------------------------------------------

class TestParentInterfaceTemplate:
    """Tests for parent_interface.j2."""

    def test_match_section_present(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "[Match]" in out
        assert "Name=eth1" in out

    def test_link_section_with_mac_and_mtu(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "[Link]" in out
        assert "MACAddress=F2:00:00:00:00:10" in out
        assert "MTUBytes=1500" in out

    def test_mac_dash_replaced_with_colon(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "-" not in out.split("MACAddress=")[1].split("\n")[0]

    def test_network_section_lists_vlans(self, systemd_env: Environment, single_vlan_iface: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=single_vlan_iface)
        assert "[Network]" in out
        assert "VLAN=eth1.2" in out

    def test_no_vlan_in_network_section_when_none(self, systemd_env: Environment, single_parent_iface: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=single_parent_iface)
        assert "VLAN=" not in out

    def test_fzcu_mpu_parent_lists_all_vlans(self, systemd_env: Environment, fzcu_mpu_data: dict):
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=fzcu_mpu_data)
        assert "VLAN=eth1.2049" in out
        assert "VLAN=eth1.10" in out
        assert "VLAN=eth1.201" in out

    def test_parent_without_mac(self, systemd_env: Environment):
        data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth0",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                    }
                ]
            }
        }
        tmpl = systemd_env.get_template("parent_interface.j2")
        out = tmpl.render(data=data)
        assert "MACAddress=" not in out
        assert "[Match]" in out


# ---------------------------------------------------------------------------
# vlan_netdev.j2  (.netdev file)
# ---------------------------------------------------------------------------

class TestVlanNetdevTemplate:
    """Tests for vlan_netdev.j2."""

    def _vlan_iface(self, name: str = "eth1.2", vlan_id: int = 2) -> dict:
        return {
            "name": name,
            "type": "iana-if-type:l2vlan",
            "enabled": True,
            "ietf-if-extensions:parent-interface": "eth1",
            "ietf-if-extensions:max-frame-size": 1500,
            "ietf-if-extensions:encapsulation": {
                "ietf-if-vlan-encapsulation:dot1q-vlan": {
                    "outer-tag": {
                        "tag-type": "ieee802-dot1q-types:c-vlan",
                        "vlan-id": vlan_id,
                    }
                }
            },
            "ietf-ip:ipv4": {
                "enabled": True,
                "address": [{"ip": "10.0.2.16", "prefix-length": 24}],
            },
        }

    def test_netdev_section_present(self, systemd_env: Environment):
        iface = self._vlan_iface()
        data = {"ietf-interfaces:interfaces": {"interface": [iface]}}
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "[NetDev]" in out

    def test_kind_is_vlan(self, systemd_env: Environment):
        iface = self._vlan_iface()
        data = {"ietf-interfaces:interfaces": {"interface": [iface]}}
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "Kind=vlan" in out

    def test_vlan_id_rendered(self, systemd_env: Environment):
        iface = self._vlan_iface(vlan_id=2049)
        data = {"ietf-interfaces:interfaces": {"interface": [iface]}}
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "Id=2049" in out

    def test_name_rendered(self, systemd_env: Environment):
        iface = self._vlan_iface(name="eth1.201", vlan_id=201)
        data = {"ietf-interfaces:interfaces": {"interface": [iface]}}
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "Name=eth1.201" in out

    def test_no_output_for_parent_iface(self, systemd_env: Environment, single_parent_iface: dict):
        """A parent interface must not produce any .netdev output."""
        parent = single_parent_iface["ietf-interfaces:interfaces"]["interface"][0]
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        out = tmpl.render(iface=parent, data=single_parent_iface)
        assert out.strip() == ""

    def test_fzcu_mpu_all_vlans(self, systemd_env: Environment, fzcu_mpu_data: dict):
        tmpl = systemd_env.get_template("vlan_netdev.j2")
        interfaces = fzcu_mpu_data["ietf-interfaces:interfaces"]["interface"]
        vlan_ifaces = [i for i in interfaces if i.get("type") == "iana-if-type:l2vlan"]
        assert len(vlan_ifaces) == 3

        expected_ids = {2049, 10, 201}
        for iface in vlan_ifaces:
            out = tmpl.render(iface=iface, data=fzcu_mpu_data)
            vlan_id = iface["ietf-if-extensions:encapsulation"][
                "ietf-if-vlan-encapsulation:dot1q-vlan"
            ]["outer-tag"]["vlan-id"]
            assert f"Id={vlan_id}" in out
            expected_ids.discard(vlan_id)
        assert expected_ids == set(), f"Missing VLAN IDs: {expected_ids}"


# ---------------------------------------------------------------------------
# vlan_network.j2  (.network file for VLAN)
# ---------------------------------------------------------------------------

class TestVlanNetworkTemplate:
    """Tests for vlan_network.j2."""

    def _minimal_vlan_data(
        self,
        name: str = "eth1.10",
        ip: str = "172.16.10.11",
        prefix: int = 24,
        vlan_id: int = 10,
    ) -> tuple[dict, dict]:
        iface = {
            "name": name,
            "type": "iana-if-type:l2vlan",
            "enabled": True,
            "ietf-if-extensions:max-frame-size": 1500,
            "ietf-if-extensions:parent-interface": "eth1",
            "ietf-if-extensions:encapsulation": {
                "ietf-if-vlan-encapsulation:dot1q-vlan": {
                    "outer-tag": {
                        "tag-type": "ieee802-dot1q-types:c-vlan",
                        "vlan-id": vlan_id,
                    }
                }
            },
            "ietf-ip:ipv4": {
                "enabled": True,
                "address": [{"ip": ip, "prefix-length": prefix}],
            },
        }
        data = {"ietf-interfaces:interfaces": {"interface": [iface]}}
        return iface, data

    def test_match_section(self, systemd_env: Environment):
        iface, data = self._minimal_vlan_data()
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "[Match]" in out
        assert "Name=eth1.10" in out

    def test_address_rendered(self, systemd_env: Environment):
        iface, data = self._minimal_vlan_data(ip="172.16.10.11", prefix=24)
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "Address=172.16.10.11/24" in out

    def test_mtu_in_link_section(self, systemd_env: Environment):
        iface, data = self._minimal_vlan_data()
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "[Link]" in out
        assert "MTUBytes=1500" in out

    def test_no_output_for_parent_iface(self, systemd_env: Environment, single_parent_iface: dict):
        parent = single_parent_iface["ietf-interfaces:interfaces"]["interface"][0]
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=parent, data=single_parent_iface)
        assert out.strip() == ""

    def test_route_rendered_when_outgoing_interface_matches(self, systemd_env: Environment):
        iface, data = self._minimal_vlan_data(name="eth1.10")
        data["ietf-routing:routing"] = {
            "control-plane-protocols": {
                "control-plane-protocol": [
                    {
                        "name": "default",
                        "type": "ietf-routing:static",
                        "static-routes": {
                            "ietf-ipv4-unicast-routing:ipv4": {
                                "route": [
                                    {
                                        "destination-prefix": "0.0.0.0/0",
                                        "next-hop": {
                                            "next-hop-address": "172.16.10.254",
                                            "outgoing-interface": "eth1.10",
                                        },
                                    }
                                ]
                            }
                        },
                    }
                ]
            }
        }
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "[Route]" in out
        assert "Gateway=172.16.10.254" in out
        assert "Destination=0.0.0.0/0" in out

    def test_route_not_rendered_for_wrong_interface(self, systemd_env: Environment):
        iface, data = self._minimal_vlan_data(name="eth1.10")
        data["ietf-routing:routing"] = {
            "control-plane-protocols": {
                "control-plane-protocol": [
                    {
                        "name": "default",
                        "type": "ietf-routing:static",
                        "static-routes": {
                            "ietf-ipv4-unicast-routing:ipv4": {
                                "route": [
                                    {
                                        "destination-prefix": "0.0.0.0/0",
                                        "next-hop": {
                                            "next-hop-address": "172.24.1.254",
                                            "outgoing-interface": "eth1.2049",  # different iface
                                        },
                                    }
                                ]
                            }
                        },
                    }
                ]
            }
        }
        tmpl = systemd_env.get_template("vlan_network.j2")
        out = tmpl.render(iface=iface, data=data)
        assert "[Route]" not in out

    def test_fzcu_mpu_vlan10_has_default_route(self, systemd_env: Environment, fzcu_mpu_data: dict):
        tmpl = systemd_env.get_template("vlan_network.j2")
        interfaces = fzcu_mpu_data["ietf-interfaces:interfaces"]["interface"]
        vlan10 = next(i for i in interfaces if i["name"] == "eth1.10")
        out = tmpl.render(iface=vlan10, data=fzcu_mpu_data)
        assert "Address=172.16.10.11/24" in out

    def test_fzcu_mpu_vlan2049_address(self, systemd_env: Environment, fzcu_mpu_data: dict):
        tmpl = systemd_env.get_template("vlan_network.j2")
        interfaces = fzcu_mpu_data["ietf-interfaces:interfaces"]["interface"]
        vlan2049 = next(i for i in interfaces if i["name"] == "eth1.2049")
        out = tmpl.render(iface=vlan2049, data=fzcu_mpu_data)
        assert "Address=172.24.1.11/24" in out
