import click
from parser import parse_json
from generator import generate_qnx_config

@click.command()
@click.option('--input', required=True, help='Input JSON file')
@click.option('--output', required=True, help='Output directory')
def main(input, output):
    config = parse_json(input)
    generate_qnx_config(config, output)
    print("✅ QNX config generated successfully")

if __name__ == "__main__":
    main()