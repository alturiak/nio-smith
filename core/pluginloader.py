"""
    Imports all plugins from plugins subdirectory

"""

from plugin import Plugin, PluginCommand, PluginHook
from core.timer import Timer
from sys import modules
from re import match
from time import time
import operator
import pickle
from typing import List, Dict
import glob
from os.path import dirname, basename, isfile, join, isdir
import importlib
from fuzzywuzzy import fuzz
import logging
logger = logging.getLogger(__name__)

# import all plugins
module_all = glob.glob("plugins/*")
module_dirs: List[str] = [basename(d) for d in module_all if isdir(d) and not d.endswith('__pycache__')]
module_files: List[str] = [basename(f)[:-3] for f in module_all if isfile(f) and f.endswith('.py') and not f.endswith('__init__.py')]

for module in module_dirs:
    globals()[module] = importlib.import_module(f"plugins.{module}.{module}")
for module in module_files:
    globals()[module] = importlib.import_module(f"plugins.{module}")


class PluginLoader:

    def __init__(self, timers_filepath: str):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: Dict[str, Plugin] = {}
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}

        """load stored timers"""
        self.timers_filepath: str = timers_filepath
        self.timers: List[Timer] = []
        stored_timers: List[Timer] = self.__load_timers()

        for key in modules.keys():
            if match(r"^plugins\.\w*(\.\w*)?", key):
                if hasattr(modules[key], "plugin") and isinstance(modules[key].plugin, Plugin):
                    self.__plugin_list[modules[key].plugin.name] = modules[key].plugin

        for plugin in self.__plugin_list.values():

            """assemble all valid commands and their respective methods"""
            self.commands.update(plugin.get_commands())

            """assemble all hooks and their respective methods"""
            event_type: str
            plugin_hooks: List[PluginHook]
            plugin_hook: PluginHook
            for event_type, plugin_hooks in plugin.get_hooks().items():
                if event_type in self.hooks.keys():
                    for plugin_hook in plugin_hooks:
                        self.hooks[event_type].append(plugin_hook)
                else:
                    self.hooks[event_type] = plugin_hooks

            """
            check if a timer of the same name exists already,
            overwrite method if needed, keep last_execution from stored timer
            non-existing timers will be added as is
            """
            new_timer: Timer
            stored_timer: Timer

            for new_timer in plugin.get_timers():
                for stored_timer in stored_timers:
                    if stored_timer.name == new_timer.name:
                        logger.debug(f"Updated existing timer {stored_timer.name} {stored_timer.last_execution}")
                        self.timers.append(Timer(new_timer.name, new_timer.method, new_timer.frequency, stored_timer.last_execution))
                        break
                else:
                    # timer not found in stored timers
                    self.timers.append(new_timer)
                    logger.debug(f"Added new timer: {new_timer.name}")

            """load the plugin's saved data"""
            plugin.plugin_data = plugin._load_data_from_file()

            """Display details about the loaded plugins, this does nothing else"""
            logger.info(f"Loaded plugin {plugin.name}:")
            if plugin.get_commands() != {}:
                logger.info(f"  Commands: {', '.join([*plugin.get_commands().keys()])}")
            if plugin.get_hooks() != {}:
                logger.info(f"  Hooks:    {', '.join([*plugin.get_hooks().keys()])}")
            if plugin.get_timers():
                timers: List[str] = []
                for timer in plugin.get_timers():
                    timers.append(timer.name)
                logger.info(f"  Timers:   {', '.join(timers)}")

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

    def get_timers(self) -> List[Timer]:

        return self.timers

    async def run_command(self, command) -> int:
        """

        :param command:
        :return:    0 if command was found and executed successfully
                    1 if command was not found (or not valid for room)
                    2 if command was found, but required power_level was not met
        """

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

                # check if the user's power_level matches the command's requirement
                if command.room.power_levels.get_user_level(command.event.sender) >= self.commands[run_command].power_level:

                    # Make sure, exceptions raised by plugins do not kill the bot
                    try:
                        await self.commands[run_command].method(command)
                    except Exception as err:
                        logger.critical(f"Plugin failed to catch exception caused by {command_start}: {err}")
                    return 0
                else:
                    return 2
            else:
                return 1

    async def run_hooks(self, client, event_type: str, room, event):

        if event_type in self.hooks.keys():
            event_hooks: List[PluginHook] = self.hooks[event_type]

            event_hook: PluginHook
            for event_hook in event_hooks:
                if event_hook.room_id is None or room.room_id in event_hook.room_id:
                    # Make sure, exceptions raised by plugins do not kill the bot
                    try:
                        await event_hook.method(client, room.room_id, event)
                    except Exception as err:
                        logger.critical(f"Plugin failed to catch exception caused by hook {event_hook.method} on {room} for {event}: {err}")

    async def run_timers(self, client, timestamp: float, filepath: str) -> float:

        """
        Checks all timers if their execution is due and executes them
        :param client:
        :param timestamp: timestamp of last execution to make sure we're not running more than once every 30s
        :param filepath: path to the file to store all timers' last execution dates for persistence
        :return:
        """

        """Do not run timers more often than every 30s"""
        if time() >= timestamp+30:

            timer: Timer
            timers_triggered: bool = False

            # check all timers for execution
            for timer in self.get_timers():
                try:
                    if await timer.trigger(client):
                        logger.debug(f"Timer {timer.name} triggered")
                        timers_triggered = True
                except Exception as err:
                    logger.critical(f"Plugin failed to catch exception caused by timer {timer.name}: {err}")

            if timers_triggered:
                # write all timers to file
                try:
                    pickle.dump(self.get_timers(), open(filepath, "wb"))
                except IOError as err:
                    logger.error(f"Error writing last timers execution to {filepath}: {err}")

            return time()
        else:
            return timestamp

    def __load_timers(self) -> List[Timer]:
        """
        Load all timers' last execution time from file
        :return:
        """

        try:
            return pickle.load(open(self.timers_filepath, "rb"))
        except (FileNotFoundError, AttributeError) as err:
            # TODO: this (AttributeError) resets the stored last execution times for ALL timers of the plugin if the method of a stored timer has been renamed
            logger.warning(f"Failed loading last timers execution from {self.timers_filepath}: {err}")
            return []
