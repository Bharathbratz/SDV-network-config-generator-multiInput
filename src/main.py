"""CLI entrypoint for SDN config generation.

This module intentionally contains only argument parsing and error translation.
All orchestration and business logic are delegated to the core generator service.
"""

import click

from src.core.generator import generate_sdn_config


@click.command()
@click.option(
    "--input",
    "input_path",
    required=True,
    type=str,
    help="Path to one input JSON file",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=str,
    help="Path to output directory",
)
@click.option(
    "--os",
    "os_target",
    required=True,
    type=str,
    help="Plugin key to use from registry",
)
def main(input_path: str, output_path: str, os_target: str):
    """Run config generation from CLI-provided arguments."""
    try:
        name = generate_sdn_config(input_path, output_path, os_target)
    except (ValueError, OSError) as exc:
        # Convert service-layer validation errors into Click-formatted CLI errors.
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Config generation completed for plugin: {name}")


if __name__ == "__main__":
    main()