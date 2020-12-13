"""
    Imports all plugins from plugins subdirectory

"""

from plugin import Plugin, PluginCommand, PluginHook

from sys import modules
from re import match
from time import time
import operator
import pickle
import datetime
from typing import List, Dict, Callable, Tuple

import logging
logger = logging.getLogger(__name__)

from fuzzywuzzy import fuzz


# import all plugins
try:
    from plugins import *
except ImportError as err:
    logger.critical(f"Error importing plugin: {err.name}: {err}")
except KeyError as err:
    logger.critical(f"Error importing plugin: {err}")

# global variable to store last timer execution timestamp
last_timers_execution: Dict[str, datetime.datetime]


class PluginLoader:

    def __init__(self):
        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: Dict[str, Plugin] = {}
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.timers: List[Tuple[str, Callable, str or datetime.timedelta or None]] = []

        for key in modules.keys():
            if match("^plugins\.\w*", key):
                # TODO: this needs to catch exceptions
                found_plugin: Plugin = modules[key].plugin
                if isinstance(found_plugin, Plugin):
                    self.__plugin_list[found_plugin.name] = found_plugin

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

            """assemble all timers and their respective methods"""
            self.timers.extend(plugin.get_timers())

            """load the plugin's saved data"""
            plugin.plugin_data = plugin.load_data()

            """Display details about the loaded plugins, this does nothing else"""
            logger.info(f"Loaded plugin {plugin.name}:")
            if plugin.get_commands() != {}:
                logger.info(f"  Commands: {', '.join([*plugin.get_commands().keys()])}")
            if plugin.get_hooks() != {}:
                logger.info(f"  Hooks:    {', '.join([*plugin.get_hooks().keys()])}")
            if plugin.get_timers():
                timers: List[str] = []
                for name, timer, frequency in plugin.get_timers():
                    timers.append(name)
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

    def get_timers(self) -> List[Tuple[str, Callable, str or datetime.timedelta or None]]:

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

        global last_timers_execution

        """Do not run timers more often than every 30s"""
        if time() >= timestamp+30:

            timer: Callable
            frequency = datetime.timedelta or str or None
            timers_triggered: bool = False

            for name, timer, frequency in self.get_timers():

                should_trigger: bool = False

                # run perpetual timers without storing last execution time
                if frequency is None:
                    should_trigger = True

                # get last execution time and run timer if necessary
                else:
                    # get last execution time for the method
                    last_execution: datetime.datetime
                    if not (last_execution := last_timers_execution.get(name)):
                        last_execution = datetime.datetime(year=1970, month=1, day=1, hour=0, minute=0)

                    # hardcoded intervals
                    if isinstance(frequency, str):
                        last_execution_day: datetime.date = last_execution.date()
                        last_execution_hour: int = last_execution.time().hour
                        current_day: datetime.date = datetime.datetime.today()
                        current_hour: int = datetime.datetime.now().hour

                        if frequency == "weekly":
                            # last_execution is either in smaller weeknumber in same year or higher weeknumber in smaller year
                            if (last_execution_day.isocalendar()[1] < current_day.isocalendar()[1] and last_execution_day.year == current_day.year) or\
                                    (last_execution_day.isocalendar()[1] > current_day.isocalendar()[1] and last_execution_day.year < current_day.year):
                                should_trigger = True

                        elif frequency == "daily":
                            if last_execution_day.day < current_day.day and last_execution_day.year <= current_day.year:
                                should_trigger = True

                        elif frequency == "hourly":
                            if (last_execution_hour < current_hour and last_execution_day.day <= current_day.day) or\
                                    (last_execution_day.day < current_day.day):
                                should_trigger = True

                    # timedelta intervals
                    elif isinstance(frequency, datetime.timedelta):
                        if datetime.datetime.now() - last_execution > frequency:
                            should_trigger = True

                    else:
                        logger.error(f"Invalid frequency specification for {timer}: {frequency}")

                if should_trigger:
                    try:
                        logger.info(f"Triggering timer {name} at {datetime.datetime.now()}")
                        await timer(client)
                        timers_triggered = True
                        last_timers_execution[name] = datetime.datetime.now()
                    except Exception as err:
                        logger.critical(f"Plugin failed to catch exception in {timer}: {err}")

            if timers_triggered:
                # write timers to file
                try:
                    pickle.dump(last_timers_execution, open(filepath, "wb"))
                except IOError as err:
                    logger.error(f"Error writing last timers execution to {filepath}: {err}")

            return time()
        else:
            return timestamp

    async def load_timers(self, filepath: str):
        """
        Load all timers' last execution time from file
        :param filepath: path to the file containing the dict
        :return:
        """

        global last_timers_execution

        try:
            last_timers_execution = pickle.load(open(filepath, "rb"))
        except FileNotFoundError as err:
            last_timers_execution = {}
            logger.warning(f"Failed loading last timers execution from {filepath}: {err}")
