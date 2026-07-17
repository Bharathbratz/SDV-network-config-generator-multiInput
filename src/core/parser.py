"""JSON parsing and normalization for SDN config generation.

This module is responsible for:
- reading input JSON files
- detecting supported source formats
- converting payloads into a plugin-ready internal model

Validation is intentionally handled by the validator service.
"""

import json
from dataclasses import dataclass

from src.core.mapper import map_data


@dataclass(frozen=True)
class ParsedConfig:
    """Immutable parser result consumed by orchestrator and validator.

    Attributes:
        model: Plugin-ready internal model.
        source_format: Input format identifier ("ietf" or "legacy").
        source_config: Source-shaped config used by validator.
    """

    model: dict
    source_format: str
    source_config: dict


def _prefix_to_netmask(prefix_length: int) -> str:
    """Convert a CIDR prefix length into dotted-decimal netmask."""
    if prefix_length == 0:
        return "0.0.0.0"
    bits = (0xFFFFFFFF >> (32 - prefix_length)) << (32 - prefix_length)
    return (f"{(bits >> 24) & 0xFF}.{(bits >> 16) & 0xFF}."
            f"{(bits >> 8) & 0xFF}.{bits & 0xFF}")


def _normalize_ietf(raw: dict) -> dict:
    """Normalize IETF-namespaced JSON (RFC 8343/8349/7317) into the internal
    SDV network model consumed by all plugins.

    Input keys handled:
      ietf-interfaces:interfaces  → interfaces[]
      ietf-routing:routing        → routes[]
      ietf-system:system          → hostname, dns_servers[]
    """
    # Output model sections consumed directly by plugin templates.
    interfaces = []
    routes = []
    dns_servers = []
    hostname = ""

    # ── Interfaces ───────────────────────────────────────────────────────────
    for iface in raw.get("ietf-interfaces:interfaces", {}).get("interface", []):
        name = iface["name"]
        iface_type = iface.get("type", "")
        enabled = iface.get("enabled", True)
        max_frame_size = iface.get("ietf-if-extensions:max-frame-size")

        if "ethernetCsmacd" in iface_type:
            # Physical Ethernet interface
            eth = iface.get("ietf-if-ethernet-like:ethernet-like", {})
            interfaces.append({
                "name": name,
                "type": "ethernet",
                "enabled": enabled,
                "mac_address": eth.get("mac-address"),
                "max_frame_size": max_frame_size,
            })

        elif "l2vlan" in iface_type:
            # IEEE 802.1Q VLAN sub-interface
            outer_tag = (
                iface.get("ietf-if-extensions:encapsulation", {})
                     .get("ietf-if-vlan-encapsulation:dot1q-vlan", {})
                     .get("outer-tag", {})
            )
            vlan_id = outer_tag.get("vlan-id")
            parent = iface.get("ietf-if-extensions:parent-interface")

            addrs = iface.get("ietf-ip:ipv4", {}).get("address", [])
            ip = netmask = None
            prefix_length = None
            if addrs:
                ip = addrs[0].get("ip")
                prefix_length = addrs[0].get("prefix-length")
                if prefix_length is not None:
                    netmask = _prefix_to_netmask(prefix_length)

            interfaces.append({
                "name": name,
                "type": "vlan",
                "enabled": enabled,
                "parent": parent,
                "vlan_id": vlan_id,
                "ip": ip,
                "prefix_length": prefix_length,
                "netmask": netmask,
                "max_frame_size": max_frame_size,
            })

    # ── Static routes ────────────────────────────────────────────────────────
    protocols = (
        raw.get("ietf-routing:routing", {})
           .get("control-plane-protocols", {})
           .get("control-plane-protocol", [])
    )
    for proto in protocols:
        for r in (proto.get("static-routes", {})
                       .get("ietf-ipv4-unicast-routing:ipv4", {})
                       .get("route", [])):
            routes.append({
                "destination": r["destination-prefix"],
                "gateway": r["next-hop"]["next-hop-address"],
            })

    # ── System / DNS ─────────────────────────────────────────────────────────
    system = raw.get("ietf-system:system", {})
    hostname = system.get("hostname", "")
    for srv in system.get("dns-resolver", {}).get("server", []):
        addr = srv.get("udp-and-tcp", {}).get("address")
        if addr:
            dns_servers.append(addr)

    # Canonical internal model used by all plugin generators.
    model = {
        "hostname": hostname,
        "interfaces": interfaces,
        "routes": routes,
        "dns_servers": dns_servers,
    }

    return model


def _parse_json_data(data: dict) -> ParsedConfig:
    """Parse an in-memory JSON object and detect supported source format.

    Returns:
        ParsedConfig with both plugin-ready model and source-shape metadata.
    """
    if "ietf-interfaces:interfaces" in data:
        # IETF/RFC namespaced payload -> normalize into internal model.
        model = _normalize_ietf(data)
        # Preserve the original IETF JSON so plugins that work directly with
        # the IETF data model (e.g. LinuxPlugin) can retrieve it without
        # re-parsing the file.
        model["_raw_ietf"] = data
        return ParsedConfig(model=model, source_format="ietf", source_config=data)

    # Legacy flat format
    config = data.get("network-config", data)
    model = map_data(config)
    return ParsedConfig(model=model, source_format="legacy", source_config=config)


def parse_json(file_path: str) -> ParsedConfig:
    """Read and parse one configuration JSON file.

    Args:
        file_path: Absolute or relative path to an input JSON file.

    Returns:
        ParsedConfig containing model + source metadata for validator routing.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _parse_json_data(data)
