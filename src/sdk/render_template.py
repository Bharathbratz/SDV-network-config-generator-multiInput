import os
from jinja2 import Environment, FileSystemLoader

_env_cache = {}


def get_env(template_path):
    if template_path not in _env_cache:
        _env_cache[template_path] = Environment(
            loader=FileSystemLoader(template_path),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _env_cache[template_path]


def render_template(template_path, template_name, context, output_file):

    env = get_env(template_path)

    template = env.get_template(template_name)

    rendered_output = template.render(context)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        f.write(rendered_output)

    print(f"Generated: {output_file}")
