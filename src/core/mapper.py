"""Mapping utilities for converting legacy config payloads to internal model."""


def map_data(data: dict) -> dict:
    """Map legacy network configuration shape into plugin-ready model.

    Args:
        data: Legacy config dictionary (typically ``network-config`` payload).

    Returns:
        Internal model dictionary used by plugin templates.
    """
    return {
        "interfaces": [
            {
                "name": i["name"],
                "ip": i["ip"],
                "netmask": i["netmask"],
                # Legacy input uses vlan_id; internal model exposes this as vlan.
                "vlan": i.get("vlan_id"),
                "tsn": i.get("tsn")
            }
            for i in data.get("interfaces", [])
        ],
        "routes": data.get("routes", [])
    }