from src.sdk.base_plugin import BasePlugin
from src.sdk.render_template import render_template
import os


class MCUPlugin(BasePlugin):
    name = "mcu"
    capabilities = ["vlan"]

    def generate(self, config, output_dir):
        base_path = os.path.dirname(__file__)
        template_path = os.path.join(base_path, "templates")

        render_template(
            template_path,
            "network_config.j2",
            config,
            f"{output_dir}/network_config.h",
        )
