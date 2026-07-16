import unittest
from jinja2 import Environment, FileSystemLoader

class TestNetdevTemplateRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = Environment(loader=FileSystemLoader('templates'))

    def test_template_with_no_interfaces(self):
        # Test rendering with no interfaces
        template = self.env.get_template('vlan_netdev.j2')
        sample_data = {
            'ietf-interfaces:interfaces': {
                'interface': []
            }
        }
        # Pass netdev as None to simulate no interfaces
        rendered = template.render(data=sample_data)
        try:
            self.assertEqual(rendered.strip(), '')  # Expect that nothing will be rendered.
            print("test_template_with_no_interfaces: PASS")
        except AssertionError:
            print("test_template_with_no_interfaces: FAIL")
            raise

    def test_render_with_vlan(self):
        template = self.env.get_template('vlan_netdev.j2')
        sample_data = {
            'ietf-interfaces:interfaces': {
                'interface': [
                    {
                        'name': 'eth1.2',
                        'type': 'iana-if-type:l2vlan',
                        'enabled': True,
                        'ietf-if-extensions:max-frame-size': 1500,
                        'ietf-if-extensions:parent-interface': 'eth1',
                        'ietf-if-extensions:encapsulation': {
                            'ietf-if-vlan-encapsulation:dot1q-vlan': {
                                'outer-tag': {
                                    'tag-type': 'ieee802-dot1q-types:c-vlan',
                                    'vlan-id': 2
                                }
                            }
                        },
                        'ietf-ip:ipv4': {
                            'enabled': True,
                            'address': [
                                {
                                    'ip': '10.0.2.16',
                                    'prefix-length': 24
                                }
                            ]
                        }
                    }
                ]
            }
        }

        rendered = template.render(data=sample_data)
        expected = (
            "[NetDev]\n"
            "Name=eth1.2\n"
            "\n"
            "Kind=vlan\n"
            "\n"
            "[VLAN]\n"
            "Id=2\n"
            "\n"
        )

        try:
            self.assertEqual(rendered.strip(), expected.strip())
            print("test_render_with_Vlan: PASS")
        except AssertionError:
            print("test_render_with_vlan: FAIL")
            raise


if __name__ == '__main__':
    unittest.main()
