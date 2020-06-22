"""
    Imports all plugins from plugins subdirectory

"""
import operator
from typing import List, Dict, Callable

import nio
from fuzzywuzzy import fuzz

from plugin import Plugin
# import all plugins
from plugins import *
from sys import modules
from re import match
import logging
from plugincommand import PluginCommand
from pluginhook import PluginHook
import operator
logger = logging.getLogger(__name__)


class PluginLoader:

    def __init__(self):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: List[Plugin] = []
        # Commands: Dict of room-ids, each containing a list of dicts with command and coroutine
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        for key in modules.keys():
            if match("^plugins\.\w*", key):
                # TODO: this needs to catch exceptions
                found_plugin = modules[key].plugin.get_plugin()
                if isinstance(found_plugin, Plugin):
                    self.__plugin_list.append(found_plugin)

        for plugin in self.__plugin_list:
            logger.debug("Reading commands from " + plugin.name)
            logger.debug(self.commands)
            # assemble all valid commands and their respective methods

            self.commands.update(plugin.get_commands())
            self.hooks.update(plugin.get_hooks())

        logger.debug("Active Commands:")
        logger.debug(self.commands)
        logger.debug("Active Hooks:")
        logger.debug(self.hooks)

    def get_plugins(self) -> List[Plugin]:

        return self.__plugin_list

    def get_hooks(self) -> Dict[str, List[PluginHook]]:

        return self.hooks

    def get_commands(self) -> Dict[str, PluginCommand]:

        return self.commands

    async def run_command(self, command):

        logger.debug(f"Running Command {command.command} with args {command.args}")

        command_start = command.command.split()[0].lower()

        if command_start in self.commands.keys():
            if self.commands[command_start].room_id is None or command.room.room_id in self.commands[command_start].room_id:
                await self.commands[command_start].method(command)

        # Command not found, try fuzzy matching
        else:
            ratios: Dict[str, int] = {}
            for key in self.commands.keys():
                if fuzz.ratio(command_start, key) > 60:
                    ratios[key] = fuzz.ratio(command_start, key)

            # Sort matching commands by match percentage
            # ratios is a list, there is probably a less ugly way to do this
            ratios: List[Dict[str, int]] = sorted(ratios.items(), key=operator.itemgetter(1), reverse=True)
            for candidate in ratios:
                candidate_command = candidate[0]
                if self.commands[candidate_command].room_id is None or command.room.room_id in self.commands[candidate_command].room_id:
                    await self.commands[candidate_command].method(command)

    def run_hooks(self, event_type, event):

        # run room-specific hooks
        try:
            for hook in self.hooks[event.room][event_type]:
                hook(self)
        except KeyError:
            pass

        # run global hooks
        try:
            for hook in self.hooks["global"][event_type]:
                hook(self)
        except KeyError:
            pass
