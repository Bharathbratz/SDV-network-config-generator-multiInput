import glob
import json
import os
import click
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.parser import normalize_ietf, parse_json_data
from src.core.mapper import map_data
from src.sdk.registry import registry

# Maps lowercase keyword in filename → registered plugin name
_FILENAME_TO_PLUGIN = {
    "android": "android",
    "linux":   "linux",
    "mcu":     "mcu",
    "qnx":     "qnx",
    "switch":  "switch",
}


def _detect_plugin(filename: str) -> str | None:
    """Derive the target plugin from a configuration_end-station_<OS>.json filename."""
    base = os.path.basename(filename).lower()
    for keyword, plugin_name in _FILENAME_TO_PLUGIN.items():
        if keyword in base:
            return plugin_name
    return None


def _process_file(input_file: str, output_dir: str, plugin_name: str = None) -> str:
    """Parse one input file (auto-detect format) and run the matching plugin."""
    with open(input_file, "r") as f:
        raw = json.load(f)

    if plugin_name is None:
        plugin_name = _detect_plugin(input_file)

    if plugin_name is None:
        raise ValueError(
            f"Cannot determine target plugin for '{os.path.basename(input_file)}'. "
            "Name must contain one of: android, linux, mcu, qnx, switch"
        )

    if "ietf-interfaces:interfaces" in raw:
        # IETF YANG-compliant format → normalise directly
        config = normalize_ietf(raw)
    else:
        # Legacy flat format → validate then map to internal model
        config = map_data(parse_json_data(raw))

    plugin = registry.get(plugin_name)
    plugin.generate(config, f"{output_dir}/{plugin_name}")
    return plugin_name


@click.command()
@click.option(
    "--input", "input_path", required=True,
    help="Input JSON file OR directory containing configuration_end-station_*.json files",
)
@click.option("--output", required=True, help="Output base directory")
@click.option(
    "--os", "os_target", default="all",
    help="Target OS plugin name (used only when --input is a single file)",
)
def main(input_path, output, os_target):

    print("Available plugins:", registry.list_plugins())

    if os.path.isdir(input_path):
        # ── Directory mode: discover all per-ECU config files ────────────────
        pattern = os.path.join(input_path, "configuration_end-station_*.json")
        files = sorted(glob.glob(pattern))

        if not files:
            print(f"❌ No configuration_end-station_*.json files found in '{input_path}'")
            raise SystemExit(1)

        print(f"\n📂 Discovered {len(files)} input file(s):")
        for f in files:
            print(f"   {os.path.basename(f)}  →  plugin: {_detect_plugin(f) or '?'}")
        print()

        results, errors = [], []
        with ThreadPoolExecutor(max_workers=min(4, len(files))) as executor:
            futures = {executor.submit(_process_file, f, output): f for f in files}
            for future in as_completed(futures):
                src_file = futures[future]
                try:
                    name = future.result()
                    results.append(name)
                    print(f"✅ Completed: {name}  ({os.path.basename(src_file)})")
                except Exception as exc:
                    errors.append((src_file, exc))
                    print(f"❌ Failed [{os.path.basename(src_file)}]: {exc}")

        print(f"\n✅ Generated {len(results)} config(s) → {output}")
        if errors:
            raise SystemExit(1)

    else:
        # ── Single-file mode ─────────────────────────────────────────────────
        plugin_name = None if os_target == "all" else os_target
        name = _process_file(input_path, output, plugin_name)
        print(f"✅ Config generation completed for: {name}")


if __name__ == "__main__":
    main()