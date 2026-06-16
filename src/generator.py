import os
from qnx_mapper import map_interfaces, map_routes

def generate_qnx_config(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    interfaces = map_interfaces(data)
    routes = map_routes(data)

    # Generate interface config
    with open(f"{output_dir}/interfaces.conf", "w") as f:
        for iface in interfaces:
            f.write(f"ifconfig {iface['name']} {iface['ip']} "
                    f"netmask {iface['netmask']}\n")

            if iface["vlan"]:
                f.write(f"vlan create {iface['vlan']} {iface['name']}\n")

    # Generate routing config
    with open(f"{output_dir}/routes.conf", "w") as f:
        for route in routes:
            f.write(f"route add {route['destination']} {route['gateway']}\n")