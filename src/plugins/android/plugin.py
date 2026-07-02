from src.sdk.base_plugin import BasePlugin
from src.sdk.render_template import render_template
import os


class AndroidPlugin(BasePlugin):

    def generate(self, config, output_dir):
        base_path = os.path.dirname(__file__)
        template_path = os.path.join(base_path, "templates")

        render_template(
            template_path,
            "network.j2",
            config,
            f"{output_dir}/interfaces.conf"
        )
