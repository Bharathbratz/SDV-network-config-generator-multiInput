from src.sdk.base_plugin import BasePlugin
from src.sdk.render_template import render_template
import os


class AndroidPlugin(BasePlugin):

    def generate(self, config, output_dir):

        render_template(
            "src/plugins/android/templates",  
            "network.j2",                      
            config,
            f"{output_dir}/interfaces.conf"
        )
