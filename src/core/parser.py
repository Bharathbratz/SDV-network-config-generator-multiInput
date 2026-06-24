import json
import ipaddress
from src.core.validator import validate_against_yang

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise ValueError(f"Invalid IP address: {ip}")

def validate_basic(data):
    if "network-config" not in data:
        raise ValueError("Missing 'network-config'")

    cfg = data["network-config"]

    if "interfaces" not in cfg:
        raise ValueError("Missing interfaces")

    for iface in cfg["interfaces"]:

        # Required fields
        if "name" not in iface:
            raise ValueError("Interface name missing")
        if "ip" not in iface:
            raise ValueError(f"IP missing for {iface['name']}")
        if "netmask" not in iface:
            raise ValueError(f"Netmask missing for {iface['name']}")

        # ✅ VLAN validation
        vlan_id = iface.get("vlan_id")
        if vlan_id is not None:
            if not (1 <= vlan_id <= 4094):
                raise ValueError(
                    f"Invalid VLAN ID {vlan_id} for {iface['name']} (valid range 1–4094)"
                )
        # ✅ TSN Validation
        tsn = iface.get("tsn")
        if tsn:
            if "bandwidth" not in tsn or not (0 < tsn["bandwidth"] <= 100):
                raise ValueError("Invalid TSN bandwidth (1–100)")
            if "priority" not in tsn or not (0 <= tsn["priority"] <= 7):
                raise ValueError("Invalid TSN priority (0–7)")

    print("✅ Validation passed (including VLAN range)")
    print("✅ Validation passed for  TSN)")

def parse_json_data(data: dict) -> dict:
    """
    Parse JSON from already loaded data (UI use case)
    """

    config = data.get("network-config", data)

    validate_against_yang(config)

    return config


def parse_json(file_path: str) -> dict:
    """Parse configuration JSON from file path and validate it."""
    with open(file_path, "r") as f:
        data = json.load(f)

    return parse_json_data(data)


