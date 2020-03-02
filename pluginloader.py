"""
    Imports all plugins from plugins subdirectory

"""
from typing import List
from plugin import Plugin
# import all plugins
from plugins import *
import sys
from re import match


class PluginLoader:

    def __init__(self):
        self.plugin_list: List[Plugin] = []
        for key in sys.modules.keys():
            if match("^plugins\.\w*", key):
                plugin = sys.modules[key]
                self.plugin_list.append(plugin.plugin.get_plugin())

    def get_plugins(self) -> List[Plugin]:

        return self.plugin_list


pl = PluginLoader()
for plugin in pl.get_plugins():
    print(plugin.get_commands())

for plugin in pl.get_plugins():
    print(plugin.get_help_text())
