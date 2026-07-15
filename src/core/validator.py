import ipaddress

from src.core.parser import ParsedConfig


def validate_json(parsed: ParsedConfig) -> None:
    """Validate parsed JSON data using a single orchestrator-facing API."""
    if parsed.source_format == "ietf":
        _validate_normalized(parsed.model)
        return

    if parsed.source_format == "legacy":
        _validate_against_yang(parsed.source_config)
        return

    raise ValueError(f"Unsupported source format: {parsed.source_format}")


def _validate_normalized(model: dict):
    """Validate the normalized internal SDV network model (IETF-derived).

    Called after normalize_ietf() to assert YANG-model constraints before
    passing data to any plugin generator.
    """
    interfaces = model.get("interfaces", [])
    routes = model.get("routes", [])
    dns_servers = model.get("dns_servers", [])

    for iface in interfaces:
        if "name" not in iface:
            raise ValueError("Interface is missing a name")

        iface_type = iface.get("type")
        if iface_type not in ("ethernet", "vlan"):
            raise ValueError(
                f"Unknown interface type '{iface_type}' for '{iface['name']}' "
                "(expected 'ethernet' or 'vlan')"
            )

        if iface_type == "vlan":
            vlan_id = iface.get("vlan_id")
            if vlan_id is not None and not (1 <= vlan_id <= 4094):
                raise ValueError(
                    f"Invalid VLAN ID {vlan_id} for '{iface['name']}' (range 1–4094)"
                )
            ip = iface.get("ip")
            if ip:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    raise ValueError(
                        f"Invalid IP address '{ip}' for interface '{iface['name']}'"
                    )

    for route in routes:
        if "destination" not in route:
            raise ValueError("Route entry is missing 'destination'")
        if "gateway" not in route:
            raise ValueError("Route entry is missing 'gateway'")
        try:
            ipaddress.ip_address(route["gateway"])
        except ValueError:
            raise ValueError(f"Invalid gateway address '{route['gateway']}'")

    for addr in dns_servers:
        try:
            ipaddress.ip_address(addr)
        except ValueError:
            raise ValueError(f"Invalid DNS server address '{addr}'")

    print("✅ YANG validation passed (interfaces, routes, DNS)")


def _validate_against_yang(config):
    """Validate legacy flat-format config against YANG model constraints."""
    if "interfaces" not in config:
        raise ValueError("Missing interfaces section")

    _validate_interfaces(config["interfaces"])
    _validate_routes(config.get("routes", []))
    print("✅ Validation passed (including VLAN, TSN, IP, routes)")


def _validate_interfaces(interfaces):

    for iface in interfaces:

        if "name" not in iface:
            raise ValueError("Interface name missing")

        if "ip" not in iface:
            raise ValueError(f"Missing IP for {iface['name']}")

        if "netmask" not in iface:
            raise ValueError(f"Missing netmask for {iface['name']}")

        try:
            ipaddress.ip_address(iface["ip"])
        except ValueError:
            raise ValueError(f"Invalid IP: {iface['ip']}")

        vlan_id = iface.get("vlan_id")
        if vlan_id is not None and not (1 <= vlan_id <= 4094):
            raise ValueError(f"Invalid VLAN ID {vlan_id}")

        tsn = iface.get("tsn")
        if tsn:
            _validate_tsn(tsn, iface["name"])


def _validate_tsn(tsn, iface_name):

    if not (0 < tsn.get("bandwidth", 0) <= 100):
        raise ValueError(f"Invalid TSN bandwidth for {iface_name}")

    if not (0 <= tsn.get("priority", -1) <= 7):
        raise ValueError(f"Invalid TSN priority for {iface_name}")


def _validate_routes(routes):

    for route in routes:

        if "destination" not in route:
            raise ValueError("Route destination missing")

        if "gateway" not in route:
            raise ValueError("Route gateway missing")

        try:
            ipaddress.ip_address(route["gateway"])
        except ValueError:
            raise ValueError(f"Invalid gateway {route['gateway']}")

