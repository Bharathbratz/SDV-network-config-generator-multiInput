def map_data(data):
    return {
        "interfaces": [
            {
                "name": i["name"],
                "ip": i["ip"],
                "netmask": i["netmask"],
                "vlan": i.get("vlan_id"),
                "tsn": i.get("tsn")
            }
            for i in data.get("interfaces", [])
        ],
        "routes": data.get("routes", [])
    }