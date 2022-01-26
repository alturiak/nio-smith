import copy

from nio import UnknownEvent, RoomMessageText

from core.chat_functions import send_text_to_room
from core.plugin import Plugin, PluginCommand, PluginHook
from core.timer import Timer
from core.config import Config
from sys import modules
from re import match
from time import time
import operator
from typing import List, Dict
import glob
from os.path import basename, isfile, isdir
import importlib
from fuzzywuzzy import fuzz
import logging
import traceback

logger = logging.getLogger(__name__)


class PluginLoader:

    def __init__(self, config, plugins_dir: str = "plugins"):
        """
        Handles importing and running plugins
        :param config (Config): Bot configuration parameters
        :param plugins_dir: (str) Directory containing the plugins
        """

        self.config: Config = config
        # import all plugins
        module_all = glob.glob(f"{plugins_dir}/*")
        module_all.sort()
        module_dirs: List[str] = [basename(d) for d in module_all if isdir(d) and not d.endswith('__pycache__')]
        module_files: List[str] = [basename(f)[:-3] for f in module_all if isfile(f) and f.endswith('.py') and not f.endswith('__init__.py')]

        if self.config.plugins_allowlist:
            logger.info(f"Plugin allowlist: {self.config.plugins_allowlist}")
        if self.config.plugins_denylist:
            logger.info(f"Plugin denylist: {self.config.plugins_denylist}")

        for module in module_dirs:
            if self.is_allowed_plugin(module):
                try:
                    globals()[module] = importlib.import_module(f"plugins.{module}.{module}")
                except ModuleNotFoundError:
                    logger.error(f"Error importing {module}. Please check requirements: {traceback.format_exc(limit=1)}")
                except KeyError:
                    logger.error(f"Error importing {module} due to missing configuration items. Skipping.")
                except Exception:
                    logger.error(f"Error importing {module} due to the following error: {traceback.format_exc(limit=1)}.\nSkipping.")
            else:
                logger.info(f"Skipping plugin {module} as it hasn't been allowed by configuration.")
        for module in module_files:
            if self.is_allowed_plugin(module):
                try:
                    logger.warning(f"DEPRECATION WARNING: Single-file plugin {module} detected. This will not be loaded from 0.2.0 onwards.")
                    globals()[module] = importlib.import_module(f"plugins.{module}")
                except ModuleNotFoundError:
                    logger.error(f"Error importing {module}. Please check requirements: {traceback.format_exc(limit=1)}")
                except KeyError:
                    logger.error(f"Error importing {module} due to missing configuration items. Skipping.")
                except Exception:
                    logger.error(f"Error importing {module} due to the following error: {traceback.format_exc(limit=1)}.\nSkipping.")
            else:
                logger.info(f"Skipping plugin {module} as it hasn't been allowed by configuration.")

        # get all loaded plugins from sys.modules and make them available as plugin_list
        self.__plugin_list: Dict[str, Plugin] = {}

        for key in modules.keys():
            if match(r"^plugins\.\w*(\.\w*)?", key):
                if hasattr(modules[key], "plugin") and isinstance(modules[key].plugin, Plugin):
                    self.__plugin_list[modules[key].plugin.name] = modules[key].plugin

        for plugin in self.__plugin_list.values():
            """Display details about the loaded plugins, this does nothing else"""
            logger.info(f"Loaded plugin {plugin.name}:")
            if plugin._get_commands() != {}:
                logger.info(f"  Commands: {', '.join([*plugin._get_commands().keys()])}")
            if plugin._get_hooks() != {}:
                logger.info(f"  Hooks:    {', '.join([*plugin._get_hooks().keys()])}")
            if plugin._get_timers():
                timers: List[str] = []
                for timer in plugin._get_timers():
                    timers.append(f"{timer.name} ({timer.frequency})")
                logger.info(f"  Timers:   {', '.join(timers)}")

    def is_allowed_plugin(self, plugin: str):
        """
        Check if a given plugin is allowed to be loaded
        :param plugin: (str) Name of the plugin to check
        :return:    True, if plugin may be loaded
                    False, otherwise
        """

        if plugin not in self.config.plugins_denylist:
            return not self.config.plugins_allowlist or plugin in self.config.plugins_allowlist

    async def load_plugin_data(self):

        for plugin in self.__plugin_list.values():
            plugin.plugin_data = await plugin._load_data_from_file()

    async def load_plugin_state(self):
        """
        Load the plugin state (dynamic commands, dynamic hooks, timers)
        :return:
        """

        for plugin in self.get_plugins().values():
            plugin._load_state()

    def get_plugins(self) -> Dict[str, Plugin]:

        return self.__plugin_list

    def get_plugin_by_name(self, name: str) -> Plugin or None:

        """Try to find a plugin by the name provided and return it"""

        try:
            return self.get_plugins()[name]
        except KeyError:
            return None

    def get_hooks(self) -> Dict[str, List[PluginHook]]:
        """
        Get all hooks currently registered by all plugins
        :return: Dict of event_type and list of PluginHooks for the event_type
        """

        all_plugin_hooks: Dict[str, List[PluginHook]] = {}
        plugin: Plugin

        for plugin in self.get_plugins().values():
            for event_type, current_plugin_hooks in plugin._get_hooks().items():
                if event_type in all_plugin_hooks.keys():
                    for plugin_hook in current_plugin_hooks:
                        all_plugin_hooks[event_type].append(plugin_hook)
                else:
                    all_plugin_hooks[event_type] = copy.deepcopy(current_plugin_hooks)

        return all_plugin_hooks

    def get_commands(self) -> Dict[str, PluginCommand]:
        """
        Get all commands curently registered by all plugins
        :return: Dict of command-string and the corresponding PluginCommand
        """

        plugin_commands: Dict[str, PluginCommand] = {}
        plugin: Plugin

        for plugin in self.get_plugins().values():
            plugin_commands.update(plugin._get_commands())

        return plugin_commands

    def get_timers(self) -> List[Timer]:
        """
        Return a list of all active timers of all plugins
        :return:
        """

        all_plugin_timers: List[Timer] = []
        plugin: Plugin

        for plugin in self.get_plugins().values():
            all_plugin_timers += plugin._get_timers()

        return all_plugin_timers

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

        if command_start in self.get_commands().keys():
            run_command = command_start

        # Command not found, try fuzzy matching
        else:
            ratios: Dict[str, int] = {}
            for key in self.get_commands().keys():
                if fuzz.ratio(command_start, key) > 60:
                    ratios[key] = fuzz.ratio(command_start, key)

            # Sort matching commands by match percentage and get the highest match
            if ratios != {}:
                run_command = sorted(ratios.items(), key=operator.itemgetter(1), reverse=True)[0][0]

        # check if we did actually find a matching command
        if run_command != "":
            if self.get_commands()[run_command].room_id is None or command.room.room_id in self.get_commands()[run_command].room_id:

                # check if the user's power_level matches the command's requirement
                if command.room.power_levels.get_user_level(command.event.sender) >= self.get_commands()[run_command].power_level:

                    # Make sure, exceptions raised by plugins do not kill the bot
                    try:
                        await self.get_commands()[run_command].method(command)
                    except Exception:
                        logger.critical(f"Plugin failed to catch exception caused by {command_start}:")
                        traceback.print_exc()
                    return 0
                else:
                    await send_text_to_room(command.client, command.room.room_id, f"Required power level for command {command.command} not met")
                    return 2
            else:
                return 1

    async def run_hooks(self, client, event_type: str, room, event: UnknownEvent or RoomMessageText):
        """
        Run all applicable hooks for the event_type
        :param client:
        :param event_type:
        :param room:
        :param event:
        :return:
        """

        if event_type in self.get_hooks().keys():

            plugin_hooks: List[PluginHook] = self.get_hooks()[event_type]
            plugin_hook: PluginHook

            for plugin_hook in plugin_hooks:
                if (not plugin_hook.room_id_list or room.room_id in plugin_hook.room_id_list) and \
                        (not plugin_hook.event_ids or event.source['content']['m.relates_to']['event_id'] in plugin_hook.event_ids):
                    # plugin_hook is valid for room of the current event and
                    # event relates to a specified event_id

                    # Make sure, exceptions raised by plugins do not kill the bot
                    try:
                        await plugin_hook.method(client, room.room_id, event)
                    except Exception as err:
                        logger.critical(f"Plugin failed to catch exception caused by hook {plugin_hook.method} on {room} for {event}:")
                        traceback.print_exc()

    async def run_timers(self, client, timestamp: float) -> float:
        """
        Checks all timers if their execution is due and executes them
        :param client:
        :param timestamp: timestamp of last execution to make sure we're not running more than once every 30s
        :return:
        """

        """Do not run timers more often than every 30s"""
        if time() >= timestamp+30:

            timer: Timer
            affected_plugins: List[str] = []

            # check all timers for execution
            for timer in self.get_timers():
                try:
                    if await timer.trigger(client):
                        logger.debug(f"Timer {timer.name} triggered")
                        affected_plugins.append(timer.name.split(".")[0])
                except Exception:
                    logger.critical(f"Plugin failed to catch exception caused by timer {timer.name}:")
                    traceback.print_exc()

            # save state of a plugin if it's timer has triggered
            if affected_plugins:
                plugin: Plugin
                for plugin in self.get_plugins().values():
                    if plugin.name in affected_plugins:
                        plugin._save_state()

            return time()
        else:
            return timestamp

