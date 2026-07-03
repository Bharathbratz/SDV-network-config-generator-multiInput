"""Core in-memory data models used across parsing and generation layers."""


class Interface:
    """Represents one network interface in the internal configuration model."""

    def __init__(self, name: str, vlan_id: int | None, ip: str, netmask: str):
        """Create an interface model.

        Args:
            name: Interface name (for example, eth0.100).
            vlan_id: Optional VLAN ID associated with the interface.
            ip: IPv4 address assigned to the interface.
            netmask: IPv4 netmask in dotted-decimal notation.
        """
        self.name = name
        self.vlan_id = vlan_id
        self.ip = ip
        self.netmask = netmask


class Route:
    """Represents one static route entry in the internal model."""

    def __init__(self, destination: str, gateway: str):
        """Create a route model.

        Args:
            destination: Destination CIDR/prefix for the route.
            gateway: Next-hop gateway IPv4 address.
        """
        self.destination = destination
        self.gateway = gateway