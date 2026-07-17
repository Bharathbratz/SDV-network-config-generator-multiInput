"""Output validation for generated network configuration files.

Checks that the generated systemd unit files and ip-config shell script are
structurally correct before deployment.  Validation is deliberately
conservative: it checks structure and required fields rather than executing
anything.

Two back-ends are validated:

* **systemd-networkd** — `.link`, `.netdev`, `.network` INI files:
  required sections and keys present, no obviously broken syntax.
* **iproute2** — `ip-config.sh`:
  POSIX ``sh -n`` syntax check (no execution).
"""

from __future__ import annotations

import configparser
import io
import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_INI_SECTION_RE = re.compile(r"^\s*\[(\w[\w\s]*)\]")


def _parse_ini(path: Path) -> configparser.ConfigParser:
    """Parse *path* as a systemd-style INI file.

    systemd allows duplicate keys in a section; ``configparser`` does not.
    We use ``OPTIONXFORM`` identity (case-preserving) and ``strict=False``
    to handle duplicate keys gracefully.
    """
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str  # type: ignore[method-assign]  # preserve case
    cp.read_string(path.read_text(encoding="utf-8"))
    return cp


def _sections(path: Path) -> set[str]:
    cp = _parse_ini(path)
    return set(cp.sections())


def _has_key(cp: configparser.ConfigParser, section: str, key: str) -> bool:
    return cp.has_option(section, key)


# ---------------------------------------------------------------------------
# Per-file validators
# ---------------------------------------------------------------------------

def _validate_link_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        cp = _parse_ini(path)
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: cannot parse INI – {exc}"]

    if "Match" not in cp.sections():
        errors.append(f"{path}: missing [Match] section")
    if "Link" not in cp.sections():
        errors.append(f"{path}: missing [Link] section")
    else:
        if not _has_key(cp, "Link", "Name"):
            errors.append(f"{path}: [Link] missing 'Name'")
    return errors


def _validate_netdev_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        cp = _parse_ini(path)
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: cannot parse INI – {exc}"]

    if "NetDev" not in cp.sections():
        errors.append(f"{path}: missing [NetDev] section")
    else:
        if not _has_key(cp, "NetDev", "Name"):
            errors.append(f"{path}: [NetDev] missing 'Name'")
        kind = cp.get("NetDev", "Kind", fallback="")
        if kind == "vlan" and "VLAN" not in cp.sections():
            errors.append(f"{path}: Kind=vlan but [VLAN] section missing")
    return errors


def _validate_network_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        cp = _parse_ini(path)
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: cannot parse INI – {exc}"]

    if "Match" not in cp.sections():
        errors.append(f"{path}: missing [Match] section")
    else:
        if not _has_key(cp, "Match", "Name"):
            errors.append(f"{path}: [Match] missing 'Name'")
    return errors


def _validate_sh_script(path: Path) -> list[str]:
    """Run ``sh -n`` (syntax-only) on the script."""
    errors: list[str] = []
    try:
        result = subprocess.run(
            ["sh", "-n", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            errors.append(
                f"{path}: sh -n syntax check failed: {result.stderr.strip()}"
            )
    except FileNotFoundError:
        logger.warning("sh not found – skipping shell syntax check for %s", path)
    except subprocess.TimeoutExpired:
        errors.append(f"{path}: sh -n timed out")
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def validate_output(overlay_root: Path) -> list[str]:
    """Validate all generated files under *overlay_root*.

    Returns a (possibly empty) list of error strings.  An empty list means
    all checks passed.
    """
    errors: list[str] = []
    overlay_root = Path(overlay_root)

    if not overlay_root.exists():
        return [f"Output directory does not exist: {overlay_root}"]

    netd_dir = overlay_root / "etc" / "systemd" / "network"
    sh_path = overlay_root / "usr" / "lib" / "network-config" / "ip-config.sh"

    # Presence checks
    for expected in (netd_dir, sh_path):
        if not expected.exists():
            errors.append(f"Expected file/directory not found: {expected}")

    # systemd unit files
    if netd_dir.exists():
        for f in sorted(netd_dir.iterdir()):
            if f.suffix == ".link":
                errors.extend(_validate_link_file(f))
            elif f.suffix == ".netdev":
                errors.extend(_validate_netdev_file(f))
            elif f.suffix == ".network":
                errors.extend(_validate_network_file(f))

    # Shell script
    if sh_path.exists():
        errors.extend(_validate_sh_script(sh_path))

    if not errors:
        logger.info("Output validation passed for %s", overlay_root)
    else:
        for err in errors:
            logger.error(err)

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Validate generated overlay files.")
    ap.add_argument("overlay_dir", help="Path to the overlay root directory.")
    args = ap.parse_args()

    errs = validate_output(Path(args.overlay_dir))
    if errs:
        sys.exit(1)
    print("All checks passed.")
