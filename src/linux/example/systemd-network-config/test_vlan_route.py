#!/usr/bin/env python3
"""Test the test_render_vlan_with_route function."""

from jinja2 import Environment, FileSystemLoader
import sys

def test_render_vlan_with_route():
    """Test VLAN interface rendering with route information."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('vlan_network.j2')
    
    sample_data = {
        'ietf-interfaces:interfaces': {
            'interface': [
                {
                    'name': 'eth1.10',
                    'type': 'iana-if-type:l2vlan',
                    'enabled': True,
                    'ietf-if-extensions:max-frame-size': 1500,
                    'ietf-if-extensions:parent-interface': 'eth1',
                    'ietf-if-extensions:encapsulation': {
                        'ietf-if-vlan-encapsulation:dot1q-vlan': {
                            'outer-tag': {
                                'tag-type': 'ieee802-dot1q-types:c-vlan',
                                'vlan-id': 10
                            }
                        }
                    },
                    'ietf-ip:ipv4': {
                        'enabled': True,
                        'address': [
                            {
                                'ip': '172.16.10.11',
                                'prefix-length': 24
                            }
                        ]
                    }
                }
            ]
        },
        'ietf-routing:routing': {
            'control-plane-protocols': {
                'control-plane-protocol': [
                    {
                        'name': 'default',
                        'type': 'ietf-routing:static',
                        'static-routes': {
                            'ietf-ipv4-unicast-routing:ipv4': {
                                'route': [
                                    {
                                        'destination-prefix': '0.0.0.0/0',
                                        'next-hop': {
                                            'next-hop-address': '172.16.10.254',
                                            'outgoing-interface': 'eth1.10'
                                        }
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }
    
    rendered = template.render(data=sample_data)
    expected = (
        "\n"
        "[Match]\n"
        "Name=eth1.10\n"
        "\n"
        "[Network]\n"
        "Address=172.16.10.11/24\n"
        "\n"
        "[Link]\n"
        "MTUBytes=1500\n"
        "\n"
        "[Route]\n"
        "Gateway=172.16.10.254\n"
        "Destination=0.0.0.0/0"
    )
    
    print("=" * 60)
    print("TEST: test_render_vlan_with_route")
    print("=" * 60)
    print("\nExpected output:")
    print("-" * 60)
    print(expected)
    print("-" * 60)
    print("\nActual rendered output:")
    print("-" * 60)
    print(rendered)
    print("-" * 60)
    
    if rendered.strip() == expected.strip():
        print("\n✓ TEST PASSED")
        return True
    else:
        print("\n✗ TEST FAILED")
        print("\nExpected (repr):")
        print(repr(expected.strip()))
        print("\nGot (repr):")
        print(repr(rendered.strip()))
        
        # Show differences
        exp_lines = expected.strip().split('\n')
        got_lines = rendered.strip().split('\n')
        
        print("\nLine-by-line comparison:")
        max_lines = max(len(exp_lines), len(got_lines))
        for i in range(max_lines):
            exp_line = exp_lines[i] if i < len(exp_lines) else "<missing>"
            got_line = got_lines[i] if i < len(got_lines) else "<missing>"
            
            match = "✓" if exp_line == got_line else "✗"
            print(f"{match} Line {i+1}:")
            print(f"  Expected: {repr(exp_line)}")
            print(f"  Got:      {repr(got_line)}")
        
        return False

if __name__ == '__main__':
    try:
        result = test_render_vlan_with_route()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
