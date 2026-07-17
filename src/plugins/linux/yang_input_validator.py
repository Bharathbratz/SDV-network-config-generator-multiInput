"""YANG validation of JSON input files.

Delegates to the project-canonical validator in
``yang_sdv/utils/yang_validator.py``, which uses the ``yangson`` library and
the YANG library bundled at ``yang_sdv/yang/yl.json``.

Validation is intentionally kept as a *best-effort* check: if ``yangson`` is
not installed the function logs a warning and returns ``True`` so the rest of
the pipeline is not blocked.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Repository root — used to make yang_sdv importable regardless of CWD.
# File is at: src/plugins/linux/yang_input_validator.py  (3 levels up = repo root)
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_yang_sdv_on_path() -> None:
    """Insert the repo root into sys.path so yang_sdv is importable."""
    repo_str = str(_REPO_ROOT)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def validate_yang(json_path: Path | str, *, strict: bool = False) -> bool:
    """Validate *json_path* against the bundled YANG models.

    Delegates to :func:`yang_sdv.utils.yang_validator.validate_file`, the
    project-canonical implementation.  The YANG library and module search path
    are resolved from ``yang_sdv/yang/`` inside that module so they are always
    consistent.

    Parameters
    ----------
    json_path:
        Path to the JSON instance document.
    strict:
        When ``True`` raise :exc:`ValueError` on validation failure instead of
        returning ``False``.

    Returns
    -------
    bool
        ``True`` if the document is valid (or if ``yangson`` is unavailable),
        ``False`` on validation failure (only when *strict* is ``False``).
    """
    _ensure_yang_sdv_on_path()

    try:
        from yang_sdv.utils.yang_validator import validate_file  # noqa: PLC0415
    except ImportError as exc:
        logger.warning(
            "Cannot import yang_sdv validator (%s) – skipping YANG validation. "
            "Run: pip install yangson",
            exc,
        )
        return True

    return validate_file(Path(json_path), strict=strict)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    ap = argparse.ArgumentParser(description="Validate a JSON file against YANG models.")
    ap.add_argument("json_file", help="Path to the JSON instance file.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 on validation failure.",
    )
    args = ap.parse_args()

    ok = validate_yang(args.json_file, strict=args.strict)
    if ok:
        print("YANG validation passed")
    else:
        print("YANG validation failed")
        sys.exit(1)

        sys.exit(1)
    print("Validation OK.")
