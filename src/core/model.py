class Interface:
    def __init__(self, name, vlan_id, ip, netmask):
        self.name = name
        self.vlan_id = vlan_id
        self.ip = ip
        self.netmask = netmask

class Route:
    def __init__(self, destination, gateway):
        self.destination = destination
        self.gateway = gateway