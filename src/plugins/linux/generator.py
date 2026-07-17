"""Linux network configuration generator — plugin-package edition.

This module is the authoritative generator used by :class:`LinuxPlugin`.
It can also be invoked stand-alone from the project root::

    python -m src.plugins.linux.generator \\
        -i input/examples/configuration_end-station_Linux.json \\
        -o output/linux

Reads a YANG-modelled JSON input, optionally validates it, and writes:

overlay/
  etc/systemd/network/          ← systemd-networkd back-end
    10-<parent>.link
    20-<parent>.network
    30-<vlan>.netdev  (one per VLAN)
    40-<vlan>.network (one per VLAN)
  usr/lib/network-config/       ← iproute2 back-end
    ip-config.sh
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import stat
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# Template directories (relative to this file)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_SYSTEMD_TEMPLATES = _HERE / "systemd-network-config" / "templates"
_IP_TEMPLATES = _HERE / "ip-network-config" / "templates"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Context helper
# ---------------------------------------------------------------------------

def load_context(json_path: Path) -> dict:
    """Load a JSON file and wrap it under the ``data`` key."""
    with json_path.open() as fh:
        raw = json.load(fh)
    return {"data": raw} if "data" not in raw else raw


def context_from_dict(raw: dict) -> dict:
    """Wrap an in-memory dict under the ``data`` key."""
    return {"data": raw} if "data" not in raw else raw


# ---------------------------------------------------------------------------
# Jinja2 helpers
# ---------------------------------------------------------------------------

def _make_env(template_dir: Path, *, trim_blocks: bool = True, lstrip_blocks: bool = True) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
        trim_blocks=trim_blocks,
        lstrip_blocks=lstrip_blocks,
    )


def _render(env: Environment, template_name: str, **ctx: object) -> str:
    return env.get_template(template_name).render(**ctx)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("  wrote %s", path)


# ---------------------------------------------------------------------------
# systemd-networkd back-end
# ---------------------------------------------------------------------------

def _priority(index: int, base: int = 30) -> str:
    return f"{base + index:02d}"


def generate_systemd(context: dict, overlay_root: Path, input_name: str) -> list[Path]:
    """Render all systemd-networkd unit files into *overlay_root*.

    Returns the list of written file paths.
    """
    env = _make_env(_SYSTEMD_TEMPLATES)
    netd_dir = overlay_root / "etc" / "systemd" / "network"
    interfaces = context["data"]["ietf-interfaces:interfaces"]["interface"]

    written: list[Path] = []
    vlan_idx = 0

    for iface in interfaces:
        is_parent = "ietf-if-extensions:parent-interface" not in iface

        if is_parent and iface.get("type") == "iana-if-type:ethernetCsmacd":
            link_content = _render(env, "parent_interface_name_static.j2", **context)
            _write(link_path := netd_dir / f"10-{iface['name']}.link", link_content)
            written.append(link_path)

            net_content = _render(env, "parent_interface.j2", **context)
            _write(net_path := netd_dir / f"20-{iface['name']}.network", net_content)
            written.append(net_path)

        elif not is_parent and iface.get("type") == "iana-if-type:l2vlan":
            prio_netdev = _priority(vlan_idx, base=30)
            prio_network = _priority(vlan_idx, base=40)

            netdev_content = _render(env, "vlan_netdev.j2", iface=iface, **context)
            _write(netdev_path := netd_dir / f"{prio_netdev}-{iface['name']}.netdev", netdev_content)
            written.append(netdev_path)

            network_content = _render(env, "vlan_network.j2", iface=iface, **context)
            _write(network_path := netd_dir / f"{prio_network}-{iface['name']}.network", network_content)
            written.append(network_path)

            vlan_idx += 1

    return written


# ---------------------------------------------------------------------------
# iproute2 back-end
# ---------------------------------------------------------------------------


def generate_ip(context: dict, overlay_root: Path, input_name: str) -> list[Path]:
    """Render the iproute2 shell script into *overlay_root*.

    Returns the list of written file paths.
    """
    env = _make_env(_IP_TEMPLATES, trim_blocks=False, lstrip_blocks=False)
    script_dir = overlay_root / "usr" / "lib" / "network-config"

    sh_content = _render(env, "ip-config.sh.j2", input_file=input_name, **context)
    sh_path = script_dir / "ip-config.sh"
    _write(sh_path, sh_content)
    sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return [sh_path]


# ---------------------------------------------------------------------------
# Checksum manifest
# ---------------------------------------------------------------------------

def write_manifest(overlay_root: Path) -> Path:
    """Write a SHA-256 manifest of all files under *overlay_root*."""
    manifest_path = overlay_root.parent / "overlay.sha256"
    lines: list[str] = []
    for fpath in sorted(overlay_root.rglob("*")):
        if fpath.is_file():
            digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
            lines.append(f"{digest}  {fpath.relative_to(overlay_root.parent)}\n")
    manifest_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Manifest written to %s", manifest_path)
    return manifest_path


# ---------------------------------------------------------------------------
# CLI entry point (python -m src.plugins.linux.generator)
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    ap = argparse.ArgumentParser(
        description="Generate Linux network configuration from a YANG JSON input file.",
    )
    ap.add_argument("-i", "--input", required=True, metavar="JSON",
                    help="Path to the YANG-modelled JSON input file.")
    ap.add_argument("-o", "--output", default="output/linux", metavar="DIR",
                    help="Output directory (overlay/ subtree written here).")
    ap.add_argument("--skip-yang-validation", action="store_true",
                    help="Skip YANG input validation.")
    ap.add_argument("--no-manifest", action="store_true",
                    help="Skip writing the SHA-256 manifest.")
    args = ap.parse_args(argv)

    json_path = Path(args.input)
    if not json_path.exists():
        logger.error("Input file not found: %s", json_path)
        return 1

    overlay_root = Path(args.output) / "overlay"

    if not args.skip_yang_validation:
        from src.plugins.linux.yang_input_validator import validate_yang  # noqa: PLC0415
        logger.info("Validating %s against YANG models …", json_path)
        validate_yang(json_path, strict=False)
    else:
        logger.info("YANG validation skipped.")

    context = load_context(json_path)
    input_name = json_path.name

    logger.info("Generating systemd-networkd configuration …")
    systemd_files = generate_systemd(context, overlay_root, input_name)

    logger.info("Generating iproute2 configuration …")
    ip_files = generate_ip(context, overlay_root, input_name)

    from src.plugins.linux.output_validator import validate_output  # noqa: PLC0415
    logger.info("Validating generated output …")
    errors = validate_output(overlay_root)
    if errors:
        for err in errors:
            logger.error("Output validation: %s", err)
        return 2

    if not args.no_manifest:
        write_manifest(overlay_root)

    logger.info("Done. %d file(s) written to %s", len(systemd_files) + len(ip_files), overlay_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
