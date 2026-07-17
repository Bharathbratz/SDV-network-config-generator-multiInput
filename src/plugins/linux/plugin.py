"""Linux network configuration plugin.

Produces a rootfs-overlay directory tree containing:

* ``etc/systemd/network/``   — systemd-networkd unit files
* ``usr/lib/network-config/`` — iproute2 ``ip-config.sh`` shell script
* ``overlay.sha256``          — SHA-256 integrity manifest

The overlay tree is placed under ``<output_dir>/overlay/`` so that multiple
plugins can coexist inside the shared output directory.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.sdk.base_plugin import BasePlugin
from src.plugins.linux.generator import (
    context_from_dict,
    generate_ip,
    generate_systemd,
    write_manifest,
)
from src.plugins.linux.output_validator import validate_output
from src.plugins.linux.yang_input_validator import validate_yang

logger = logging.getLogger(__name__)


class LinuxPlugin(BasePlugin):
    """Generate systemd-networkd and iproute2 network configuration."""

    capabilities = ["vlan", "routes", "systemd-networkd", "iproute2"]

    def generate(self, config: dict, output_dir: str) -> None:
        """Generate Linux network configuration artefacts.

        Parameters
        ----------
        config:
            Plugin-ready internal model produced by the core parser.
            When the input was IETF-namespaced JSON, the original document is
            available under ``config['_raw_ietf']`` and used directly so that
            the full IETF data model is available to the Jinja2 templates.
        output_dir:
            Target directory.  The overlay tree is written to
            ``<output_dir>/overlay/``.
        """
        overlay_root = Path(output_dir) / "overlay"

        # Prefer the preserved raw IETF JSON; fall back to the normalised model
        # for backwards-compatibility with non-IETF inputs.
        raw_ietf = config.get("_raw_ietf", config)

        # Remove internal bookkeeping key before passing to templates.
        raw_ietf.pop("_raw_ietf", None)

        context = context_from_dict(raw_ietf)

        # ------------------------------------------------------------------
        # YANG input validation (best-effort; does not abort on failure)
        # ------------------------------------------------------------------
        # The YANG validator needs a file path; if the raw data was embedded
        # by the parser we validate in-memory by writing a temp file.
        import json, tempfile, os  # noqa: E401, PLC0415
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(raw_ietf, tmp)
            tmp_path = tmp.name
        try:
            validate_yang(Path(tmp_path), strict=False)
        finally:
            os.unlink(tmp_path)

        # ------------------------------------------------------------------
        # Determine a descriptive label for generated file headers
        # ------------------------------------------------------------------
        hostname = raw_ietf.get("ietf-system:system", {}).get("hostname", "unknown")
        input_name = hostname

        # ------------------------------------------------------------------
        # Render templates
        # ------------------------------------------------------------------
        logger.info("[linux] Generating systemd-networkd configuration …")
        systemd_files = generate_systemd(context, overlay_root, input_name)

        logger.info("[linux] Generating iproute2 configuration …")
        ip_files = generate_ip(context, overlay_root, input_name)

        # ------------------------------------------------------------------
        # Output validation
        # ------------------------------------------------------------------
        errors = validate_output(overlay_root)
        if errors:
            for err in errors:
                logger.error("[linux] Output validation: %s", err)
        else:
            logger.info("[linux] Output validation passed.")

        # ------------------------------------------------------------------
        # SHA-256 manifest
        # ------------------------------------------------------------------
        write_manifest(overlay_root)

        logger.info(
            "[linux] Done. %d file(s) written to %s",
            len(systemd_files) + len(ip_files),
            overlay_root,
        )
