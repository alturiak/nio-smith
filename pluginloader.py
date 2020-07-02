"""
    Imports all plugins from plugins subdirectory

"""

from plugin import Plugin, PluginCommand, PluginHook

from sys import modules
from re import match
from time import time
import operator

from typing import List, Dict, Callable

import logging
logger = logging.getLogger(__name__)

from fuzzywuzzy import fuzz

# import all plugins
try:
    from plugins import *
except ImportError as err:
    logger.critical(f"Error importing plugin: {err.name}, running without plugins.\nConsider removing or repairing the faulty plugin(s).")
    pass


class PluginLoader:

    def __init__(self):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: Dict[str, Plugin] = {}
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.timers: List[Callable] = []

        for key in modules.keys():
            if match("^plugins\.\w*", key):
                # TODO: this needs to catch exceptions
                found_plugin: Plugin = modules[key].plugin
                if isinstance(found_plugin, Plugin):
                    self.__plugin_list[found_plugin.name] = found_plugin

        for plugin in self.__plugin_list.values():
            logger.debug("Reading commands from " + plugin.name)
            logger.debug(self.commands)
            # assemble all valid commands and their respective methods

            self.commands.update(plugin.get_commands())
            self.hooks.update(plugin.get_hooks())
            self.timers.extend(plugin.get_timers())

        logger.debug("Active Commands:")
        logger.debug(self.commands)
        logger.debug("Active Hooks:")
        logger.debug(self.hooks)

    def get_plugins(self) -> Dict[str, Plugin]:

        return self.__plugin_list

    def get_plugin_by_name(self, name: str) -> Plugin or None:

        """Try to find a plugin by the name provided and return it"""

        try:
            return self.get_plugins()[name]
        except KeyError:
            return None

    def get_hooks(self) -> Dict[str, List[PluginHook]]:

        return self.hooks

    def get_commands(self) -> Dict[str, PluginCommand]:

        return self.commands

    def get_timers(self) -> List[Callable]:

        return self.timers

    async def run_command(self, command):

        logger.debug(f"Running Command {command.command} with args {command.args}")

        command_start = command.command.split()[0].lower()
        run_command: str = ""

        if command_start in self.commands.keys():
            run_command = command_start

        # Command not found, try fuzzy matching
        else:
            ratios: Dict[str, int] = {}
            for key in self.commands.keys():
                if fuzz.ratio(command_start, key) > 60:
                    ratios[key] = fuzz.ratio(command_start, key)

            # Sort matching commands by match percentage and get the highest match
            if ratios != {}:
                run_command = sorted(ratios.items(), key=operator.itemgetter(1), reverse=True)[0][0]

        # check if we did actually find a matching command
        if run_command != "":
            if self.commands[run_command].room_id is None or command.room.room_id in self.commands[run_command].room_id:

                # Make sure, exceptions raised by plugins do not kill the bot
                try:
                    await self.commands[run_command].method(command)
                except Exception as err:
                    logger.critical(f"Plugin failed to catch exception caused by {command_start}: {err}")

    async def run_hooks(self, client, event_type: str, room, event):

        if event_type in self.hooks.keys():
            event_hooks: List[PluginHook] = self.hooks[event_type]

            for event_hook in event_hooks:
                if room.room_id is None or room.room_id in event_hook.room_id:
                    # Make sure, exceptions raised by plugins do not kill the bot
                    try:
                        await event_hook.method(client, room.room_id, event)
                    except Exception as err:
                        logger.critical(f"Plugin failed to catch exception caused by hook {event_hook.method} on"
                                        f" {room} for {event}: {err}")

    async def run_timers(self, client, timestamp: float) -> float:

        """Do not run timers more often than every 30s"""
        if time() >= timestamp+30:
            for timer in self.get_timers():
                try:
                    await timer(client)
                except Exception as err:
                    logger.critical(f"Plugin failed to catch exception in {timer}: {err}")
            return time()
        else:
            return timestamp
