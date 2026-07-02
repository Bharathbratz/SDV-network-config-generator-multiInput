import json
import ipaddress
from src.core.validator import validate_normalized, validate_against_yang


def _prefix_to_netmask(prefix_length: int) -> str:
    """Convert CIDR prefix length to dotted-decimal subnet mask."""
    if prefix_length == 0:
        return "0.0.0.0"
    bits = (0xFFFFFFFF >> (32 - prefix_length)) << (32 - prefix_length)
    return (f"{(bits >> 24) & 0xFF}.{(bits >> 16) & 0xFF}."
            f"{(bits >> 8) & 0xFF}.{bits & 0xFF}")


def normalize_ietf(raw: dict) -> dict:
    """Normalize IETF-namespaced JSON (RFC 8343/8349/7317) into the internal
    SDV network model consumed by all plugins.

    Input keys handled:
      ietf-interfaces:interfaces  → interfaces[]
      ietf-routing:routing        → routes[]
      ietf-system:system          → hostname, dns_servers[]
    """
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

    model = {
        "hostname": hostname,
        "interfaces": interfaces,
        "routes": routes,
        "dns_servers": dns_servers,
    }

    validate_normalized(model)
    return model


def parse_json_data(data: dict) -> dict:
    """Parse from an already-loaded dict. Auto-detects IETF vs legacy format."""
    if "ietf-interfaces:interfaces" in data:
        return normalize_ietf(data)
    # Legacy flat format
    config = data.get("network-config", data)
    validate_against_yang(config)
    return config


def parse_json(file_path: str) -> dict:
    """Parse a configuration JSON file. Auto-detects IETF vs legacy format."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return parse_json_data(data)


