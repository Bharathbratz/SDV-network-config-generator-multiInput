from src.sdk.base_plugin import BasePlugin
from src.sdk.render_template import render_template
import os

class QNXPlugin(BasePlugin):

    def generate(self, config, output_dir):

        render_template(
            "src/plugins/qnx/templates",
            "interfaces.j2",
            {"interfaces": config["interfaces"]},
            f"{output_dir}/interfaces.conf"
        )

        render_template(
            "src/plugins/qnx/templates",
            "routes.j2",
            {"routes": config["routes"]},
            f"{output_dir}/routes.conf"
        )
