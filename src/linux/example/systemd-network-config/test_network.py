import unittest

from jinja2 import Environment, FileSystemLoader


class TestNetworkTemplateRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = Environment(loader=FileSystemLoader("templates"))

    def test_template_with_no_interfaces(self):
        # Test rendering with no interfaces
        template = self.env.get_template("vlan_network.j2")
        sample_data = {"ietf-interfaces:interfaces": {"interface": []}}
        # Pass network as None to simulate no interfaces
        rendered = template.render(data=sample_data)
        try:
            self.assertEqual(rendered.strip(), "")  # Expect that nothing will be rendered.
            print("test_template_with_no_interfaces: PASS")
        except AssertionError:
            print("test_template_with_no_interfaces: FAIL")
            raise

    def test_render_vlan_with_full_data(self):
        template = self.env.get_template("vlan_network.j2")
        sample_data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth1.2",
                        "type": "iana-if-type:l2vlan",
                        "enabled": True,
                        "ietf-if-extensions:max-frame-size": 1500,
                        "ietf-if-extensions:parent-interface": "eth1",
                        "ietf-if-extensions:encapsulation": {
                            "ietf-if-vlan-encapsulation:dot1q-vlan": {
                                "outer-tag": {
                                    "tag-type": "ieee802-dot1q-types:c-vlan",
                                    "vlan-id": 2,
                                }
                            }
                        },
                        "ietf-ip:ipv4": {
                            "enabled": True,
                            "address": [{"ip": "10.0.2.16", "prefix-length": 24}],
                        },
                    }
                ]
            }
        }

        #  This block is now inside the method
        rendered = template.render(data=sample_data)
        expected = (
            "\n[Match]\nName=eth1.2\n\n[Network]\nAddress=10.0.2.16/24\n\n[Link]\nMTUBytes=1500"
        )

        try:
            self.assertEqual(rendered.strip(), expected.strip())
            print("test_render_vlan_with_full_data: PASS")
        except AssertionError:
            print("test_render_vlan_with_full_data: FAIL")
            raise

    def test_render_with_parent(self):
        # Test rendering without VLAN
        template = self.env.get_template("parent_interface.j2")
        sample_data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth0",
                        "type": "iana-if-type:ethernetCsmacd",
                        "enabled": True,
                        "ietf-if-extensions:max-frame-size": 1500,
                        "ietf-if-ethernet-like:ethernet-like": {"mac-address": "00-1A-2B-3C-4D-5E"},
                    }
                ]
            }
        }
        rendered = template.render(data=sample_data)
        expected = (
            "\n"
            "[Match]\n"
            "Name=eth0\n"
            "\n"
            "[Link]\n"
            "MACAddress=00:1A:2B:3C:4D:5E\n"
            "MTUBytes=1500\n"
            "\n"
            "[Network]"
        )
        try:
            self.assertEqual(rendered.strip(), expected.strip())
            print("test_render_parent_with_mac: PASS")
        except AssertionError:
            print("test_render_parent_with_mac: FAIL")
            raise

    def test_render_parent_without_mac(self):
        template = self.env.get_template("parent_interface.j2")
        sample_data = {
            "ietf-interfaces:interfaces": {
                "interface": [
                    {
                        "name": "eth0",
                        "type": "iana-if-type:ethernetCsmacd",
                        "ietf-if-extensions:max-frame-size": 1500,
                    }
                ]
            }
        }
        rendered = template.render(data=sample_data)
        expected = "\n[Match]\nName=eth0\n\n[Link]\nMTUBytes=1500\n\n[Network]"
        try:
            self.assertEqual(rendered.strip(), expected.strip())
            print("test_render_parent_without_mac: PASS")
        except AssertionError:
            print("test_render_parent_without_mac: FAIL")
            raise


if __name__ == "__main__":
    unittest.main()
