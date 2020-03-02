"""
    Imports all plugins from plugins subdirectory

"""
from typing import List
from plugin import Plugin
# import all plugins
from plugins import *
from sys import modules
from re import match


class PluginLoader:

    def __init__(self):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: List[Plugin] = []
        for key in modules.keys():
            if match("^plugins\.\w*", key):
                # this needs to catch exceptions
                found_plugin = modules[key].plugin.get_plugin()
                if isinstance(found_plugin, Plugin):
                    self.__plugin_list.append(found_plugin)

    def get_plugins(self) -> List[Plugin]:

        return self.__plugin_list
