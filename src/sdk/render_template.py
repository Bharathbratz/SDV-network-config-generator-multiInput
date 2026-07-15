"""Jinja2 template rendering utilities used by plugin implementations."""

import os
from jinja2 import Environment, FileSystemLoader

# Cache Jinja environments per template directory to avoid re-initialization.
_env_cache = {}


def get_env(template_path: str) -> Environment:
    """Return a cached Jinja2 environment for a template directory."""
    if template_path not in _env_cache:
        _env_cache[template_path] = Environment(
            loader=FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _env_cache[template_path]


def render_template(
    template_path: str,
    template_name: str,
    context: dict,
    output_file: str,
) -> None:
    """Render one template with context and write it to a file.

    Args:
        template_path: Directory containing the template file.
        template_name: Template filename to load from ``template_path``.
        context: Data model provided to template rendering.
        output_file: Absolute or relative path of generated output file.
    """

    env = get_env(template_path)

    template = env.get_template(template_name)

    rendered_output = template.render(context)

    # Ensure output folder exists before writing generated artifact.
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_output)

    print(f"Generated: {output_file}")
