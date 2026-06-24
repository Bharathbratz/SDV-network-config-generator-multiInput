import click
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.parser import parse_json
from src.core.mapper import map_data
from src.sdk.registry import registry


def run_all_plugins_parallel(mapped, output):

    def run_plugin(name):
        plugin = registry.get(name)
        plugin.generate(mapped, f"{output}/{name}")
        return name

    plugins = registry.list_plugins()

    if not plugins:
        print("❌ No plugins loaded.")
        return

    with ThreadPoolExecutor(max_workers=min(4, len(plugins))) as executor:
        futures = [
            executor.submit(run_plugin, name)
            for name in plugins
        ]

        for future in as_completed(futures):
            print(f"✅ Completed plugin: {future.result()}")


@click.command()
@click.option('--input', required=True)
@click.option('--output', required=True)
@click.option('--os', default="all")
def main(input, output, os):

    print("Available plugins:", registry.list_plugins())

    config = parse_json(input)
    mapped = map_data(config)

    if os == "all":
        run_all_plugins_parallel(mapped, output)
    else:
        plugin = registry.get(os)
        plugin.generate(mapped, output)

    print(f"✅ Config generation completed for: {os}")


if __name__ == "__main__":
    main()