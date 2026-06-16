def map_interfaces(data):
    interfaces = []
    for iface in data["interfaces"]:
        interfaces.append({
            "name": iface["name"],
            "vlan": iface.get("vlan_id"),
            "ip": iface.get("ip"),
            "netmask": iface.get("netmask")
        })
    return interfaces


def map_routes(data):
    return data.get("routes", [])