from src.sdk.base_plugin import BasePlugin
from src.sdk.render_template import render_template
import os


class SwitchPlugin(BasePlugin):
    name = "switch"
    capabilities = ["vlan", "routes"]

    def generate(self, config, output_dir):
        base_path = os.path.dirname(__file__)
        template_path = os.path.join(base_path, "templates")

        render_template(
            template_path,
            "interfaces.j2",
            config,
            f"{output_dir}/switch.conf",
        )
