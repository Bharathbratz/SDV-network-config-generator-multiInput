#!/usr/bin/env python3
from importlib.metadata import entry_points

print("All entry point groups:", list(entry_points().keys()))
sdn_eps = entry_points(group='sdn.plugins')
print(f"SDN plugins found: {len(list(sdn_eps))}")
for ep in sdn_eps:
    print(f"  - {ep.name}: {ep.value}")

# Try direct import
print("\nTrying direct imports:")
try:
    from plugins.qnx.plugin import QNXPlugin
    print("  ✓ QNXPlugin imported successfully")
except Exception as e:
    print(f"  ✗ QNXPlugin import failed: {e}")

try:
    from plugins.android.plugin import AndroidPlugin
    print("  ✓ AndroidPlugin imported successfully")
except Exception as e:
    print(f"  ✗ AndroidPlugin import failed: {e}")

try:
    from plugins.linux.plugin import LinuxPlugin
    print("  ✓ LinuxPlugin imported successfully")
except Exception as e:
    print(f"  ✗ LinuxPlugin import failed: {e}")
