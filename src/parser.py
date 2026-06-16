import json

import ipaddress

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
        if "vlan_id" in iface:
            if not (1 <= iface["vlan_id"] <= 4094):
                raise ValueError("Invalid VLAN ID")
            

    print(f"Processing interface: {iface['name']}")


    for iface in cfg["interfaces"]:
        if "name" not in iface:
            raise ValueError("Interface name missing")
        if "ip" not in iface:
            raise ValueError("IP missing")
        validate_ip(iface["ip"])
        if "netmask" not in iface:
            raise ValueError("Netmask missing")

    print("✅ Basic validation passed")


def parse_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    validate_basic(data)

    return data["network-config"]
