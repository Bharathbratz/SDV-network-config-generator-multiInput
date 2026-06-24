import ipaddress


def validate_against_yang(config):

    if "interfaces" not in config:
        raise ValueError("Missing interfaces section")

    validate_interfaces(config["interfaces"])
    validate_routes(config.get("routes", []))

    print("✅ Validation passed (including VLAN, TSN, IP, routes)")


def validate_interfaces(interfaces):

    for iface in interfaces:

        if "name" not in iface:
            raise ValueError("Interface name missing")

        if "ip" not in iface:
            raise ValueError(f"Missing IP for {iface['name']}")

        if "netmask" not in iface:
            raise ValueError(f"Missing netmask for {iface['name']}")

        # IP validation
        try:
            ipaddress.ip_address(iface["ip"])
        except ValueError:
            raise ValueError(f"Invalid IP: {iface['ip']}")

        # VLAN validation
        vlan_id = iface.get("vlan_id")
        if vlan_id is not None and not (1 <= vlan_id <= 4094):
            raise ValueError(f"Invalid VLAN ID {vlan_id}")

        # TSN validation
        tsn = iface.get("tsn")
        if tsn:
            validate_tsn(tsn, iface["name"])


def validate_tsn(tsn, iface_name):

    if not (0 < tsn.get("bandwidth", 0) <= 100):
        raise ValueError(f"Invalid TSN bandwidth for {iface_name}")

    if not (0 <= tsn.get("priority", -1) <= 7):
        raise ValueError(f"Invalid TSN priority for {iface_name}")


def validate_routes(routes):

    for route in routes:

        if "destination" not in route:
            raise ValueError("Route destination missing")

        if "gateway" not in route:
            raise ValueError("Route gateway missing")

        try:
            ipaddress.ip_address(route["gateway"])
        except ValueError:
            raise ValueError(f"Invalid gateway {route['gateway']}")