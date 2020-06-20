"""
    Imports all plugins from plugins subdirectory

"""
import operator
from typing import List, Dict, Coroutine

import nio
from fuzzywuzzy import fuzz

from plugin import Plugin
# import all plugins
from plugins import *
from sys import modules
from re import match


class PluginLoader:

    def __init__(self):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: List[Plugin] = []
        self.commands: Dict[nio.rooms.MatrixRoom, Dict[str, List[Coroutine]]] = {}
        self.hooks: Dict[nio.rooms.MatrixRoom, Dict[str, List[Coroutine]]] = {}
        for key in modules.keys():
            if match("^plugins\.\w*", key):
                # this needs to catch exceptions
                found_plugin = modules[key].plugin.get_plugin()
                if isinstance(found_plugin, Plugin):
                    self.__plugin_list.append(found_plugin)

        for plugin in self.__plugin_list:
            # assemble all valid commands and their respective methods
            plugin_commands = plugin.get_commands()
            self.commands = {**self.commands, **plugin_commands}

            # assemble all hooks and their respective methods
            plugin_hooks = plugin.get_hooks()
            self.hooks = {**self.hooks, **plugin_hooks}

        print("Active Commands:")
        print(self.commands)
        print("Active Hooks:")
        print(self.hooks)

    def get_plugins(self) -> List[Plugin]:

        return self.__plugin_list

    def get_hooks(self) -> Dict[nio.rooms.MatrixRoom, Dict[str, List[Coroutine]]]:

        return self.hooks

    def get_commands(self) -> Dict[str, Coroutine]:

        return self.commands

    def run_command(self, command):

        # TODO: clean this mess up
        command_start = command.command.split()[0].lower()

        # run room-specific commands
        try:
            # is this a secure thing to do in python?
            self.commands[command.room][command_start](self)

        # command could not be found, try fuzzy matching with scores > 60% and use the best match
        except KeyError:
            ratios = {}
            if command.room in self.commands.keys():
                for key in self.commands[command.room].keys():
                    if fuzz.ratio(command_start, key) > 60:
                        ratios[key] = fuzz.ratio(command_start, key)
                try:
                    if ratios and command.room in self.commands.keys():
                        self.commands[command.room][max(ratios.items(), key=operator.itemgetter(1))[0]](self)
                except KeyError:
                    pass

        # run global commands
        try:
            # is this a secure thing to do in python?
            self.commands[nio.rooms.MatrixRoom("any", "undef")][command_start](self)

        # command could not be found, try fuzzy matching with scores > 60% and use the best match
        except KeyError:
            ratios = {}
            if nio.rooms.MatrixRoom("any", "undef") in self.commands.keys():
                for key in self.commands[nio.rooms.MatrixRoom("any", "undef")].keys():
                    if fuzz.ratio(command_start, key) > 60:
                        ratios[key] = fuzz.ratio(command_start, key)
                try:
                    if ratios:
                        self.commands[nio.rooms.MatrixRoom("any", "undef")][max(ratios.items(), key=operator.itemgetter(1))[
                            0]](self)
                except KeyError:
                    pass

    def run_hooks(self, event_type, event):

        # run room-specific hooks
        try:
            for hook in self.hooks[event.room][event_type]:
                hook(self)
        except KeyError:
            pass

        # run global hooks
        try:
            for hook in self.hooks[nio.rooms.MatrixRoom("any", "undef")][event_type]:
                hook(self)
        except KeyError:
            pass
