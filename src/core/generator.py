"""Core generation service.

This module contains orchestration logic used by the CLI layer:
- validate incoming paths and plugin identifiers
- delegate JSON parsing/normalization to parser
- dispatch config generation to the selected plugin
"""

import os

from src.core.parser import parse_json
from src.core.validator import validate_json
from src.sdk.registry import registry


def _validate_input_file(input_path: str) -> str:
    """Validate and normalize an input file path.

    Args:
        input_path: Path provided by the caller.

    Returns:
        The validated input path.

    Raises:
        ValueError: If the path does not exist, is not a file, or is unreadable.
    """
    if not os.path.exists(input_path):
        raise ValueError(f"input file does not exist: {input_path}")
    if not os.path.isfile(input_path):
        raise ValueError(f"input path is not a file: {input_path}")
    if not os.access(input_path, os.R_OK):
        raise ValueError(f"input file is not readable: {input_path}")
    return input_path


def _validate_output_dir(output_path: str) -> str:
    """Validate and prepare an output directory path.

    Args:
        output_path: Output path provided by the caller.

    Returns:
        The validated output directory path.

    Raises:
        ValueError: If the path exists but is not a directory.
    """
    if os.path.exists(output_path) and not os.path.isdir(output_path):
        raise ValueError("output must be a directory path (not a file)")

    # Idempotent: creates the directory only when needed.
    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as exc:
        raise ValueError(
            f"cannot create or access output directory '{output_path}': {exc}"
        ) from exc
    return output_path


def _resolve_plugin_name(plugin_name: str) -> str:
    """Resolve and validate a plugin name against the current registry.

    Matching is case-insensitive, but the returned value uses the canonical
    key stored in the registry.

    Args:
        plugin_name: Plugin key passed by the caller.

    Returns:
        Canonical plugin key as registered in the plugin registry.

    Raises:
        ValueError: If no registered plugin matches the provided name.
    """
    available = registry.list_plugins()
    by_lower = {name.lower(): name for name in available}
    selected = by_lower.get(plugin_name.lower())
    if selected is None:
        allowed = ", ".join(sorted(available))
        raise ValueError(f"invalid plugin '{plugin_name}'. Choose one of: {allowed}")
    return selected


def _parse_and_validate(input_file: str) -> dict:
    """Parse and validate one input file exactly once.

    Args:
        input_file: Validated path to the input JSON file.

    Returns:
        Plugin-ready internal model.
    """
    # Parser returns parsed metadata and plugin-ready model.
    try:
        parsed = parse_json(input_file)
    except OSError as exc:
        raise ValueError(f"failed to read input file '{input_file}': {exc}") from exc

    # Validator owns domain/schema checks through a single API.
    validate_json(parsed)

    return parsed.model


def _generate_with_plugin(model: dict, output_dir: str, plugin_name: str) -> None:
    """Generate outputs for one selected plugin using an already-validated model.

    Args:
        model: Parsed and validated internal model.
        output_dir: Validated output directory.
        plugin_name: Canonical plugin key.

    Returns:
        None. Side effect is generated config files on disk.
    """

    plugin = registry.get(plugin_name)
    plugin_output_dir = os.path.join(output_dir, plugin_name)
    try:
        # Plugins write one or more files under their own subdirectory.
        os.makedirs(plugin_output_dir, exist_ok=True)
        plugin.generate(model, plugin_output_dir)
    except OSError as exc:
        raise ValueError(
            f"filesystem error while generating '{plugin_name}' output in '{plugin_output_dir}': {exc}"
        ) from exc


def generate_sdn_config(input_path: str, output_path: str, os_target: str) -> str:
    """Public service entrypoint for SDN config generation.

    This function is intentionally called by the CLI layer so that `main.py`
    stays as argument parsing only.

    Args:
        input_path: Raw input file path from CLI.
        output_path: Raw output directory path from CLI.
        os_target: Plugin key from CLI `--os` flag.

    Returns:
        Canonical plugin name that generated the output.
    """
    input_file = _validate_input_file(input_path)
    output_dir = _validate_output_dir(output_path)
    model = _parse_and_validate(input_file)

    if os_target.lower() == "all":
        plugin_names = sorted(registry.list_plugins())
    else:
        plugin_names = [_resolve_plugin_name(os_target)]

    for plugin_name in plugin_names:
        _generate_with_plugin(model, output_dir, plugin_name)

    return "all" if os_target.lower() == "all" else plugin_names[0]
