import os.path
from os import remove
import pickle
from typing import List, Any, Dict, Callable
import yaml
from errors import ConfigError
import logging
logger = logging.getLogger(__name__)


class Plugin:

    def __init__(self, name: str, category: str, description: str):
        """
        commands (list[tuple]): list of commands in the form of (trigger: str, method: str, helptext: str)

        """
        self.category: str = category
        self.name: str = name
        self.description: str = description
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.timers: List[Callable] = []
        self.rooms: List[str] = []

        self.plugin_data_filename: str = f"plugins/{self.name}.pickle"
        self.plugin_data: Dict[str, Any] = self.__load_data()

        self.config_items: Dict[str, Any] = {}
        self.configuration: Dict[str, Any] = {}

    def is_valid_for_room(self, room_id: str) -> bool:

        if self.rooms == [] or room_id in self.rooms:
            return True
        else:
            return False

    def get_help_text(self):
        # TODO: change to use of self.help_texts
        """
        Extract helptexts from commands

        :return:
        list[dict]: {command: helptext}
        """

        commandhelp: List[Dict] = []
        for command in self.commands:
            commandhelp.append({command[0]: command[2]})

        return commandhelp

    def add_command(self, command: str, method: Callable, help_text: str, room_id: List[str] = None):

        plugin_command = PluginCommand(command, method, help_text, room_id)
        if command not in self.commands.keys():
            self.commands[command] = plugin_command
            self.help_texts[command] = help_text
            # Add rooms from command to the rooms the plugin is valid for
            if room_id:
                for room in room_id:
                    if room not in self.rooms:
                        self.rooms.append(room)
            logger.debug(f"Added command {command} to rooms {room_id}")
        else:
            logger.error(f"Error adding command {command} - command already exists")

    def get_commands(self):
        """
        Extract called methods from commands

        :return:
        dict: {command: method}
        """

        return self.commands

    def add_hook(self, event_type: str, method: Callable, room_id: List[str] = None):

        plugin_hook = PluginHook(event_type, method, room_id)
        if event_type not in self.hooks.keys():
            self.hooks[event_type] = [plugin_hook]
            logger.debug(f"Added hook for {event_type} to rooms {room_id}")
        else:
            self.hooks[event_type].append(plugin_hook)

    def get_hooks(self):

        return self.hooks

    def add_timer(self, method: Callable):

        self.timers.append(method)

    def get_timers(self) -> List[Callable]:

        return self.timers

    def store_data(self, name: str, data: Any) -> bool:
        """
        Store data in plugins/<pluginname>.pickle
        :param name: Name of the data to store, used as a reference to retrieve it later
        :param data: data to be stored
        :return:    True, if data was successfully stored
                    False, if data could not be stored
        """

        self.plugin_data[name] = data
        return self.__save_data()

    def read_data(self, name: str) -> Any:
        """
        Read data from self.plugin_data
        :param name: Name of the data to be retrieved
        :return: the previously stored data
        """

        if name in self.plugin_data:
            return self.plugin_data[name]
        else:
            raise ValueError

    def clear_data(self, name: str) -> bool:
        """
        Clear a specific field in self.plugin_data
        :param name: name of the field to be cleared
        :return:    True, if successfully cleared
                    False, if name not contained in self.plugin_data or data could not be saved to disk
        """

        if name in self.plugin_data:
            del self.plugin_data[name]
            return self.__save_data()
        else:
            return False

    def __load_data(self) -> Any:
        """
        Load plugin_data from file
        :return: Data read from file to be loaded into self.plugin_data
        """

        try:
            return pickle.load(open(self.plugin_data_filename, "rb"))
        except FileNotFoundError:
            logger.debug(f"File {self.plugin_data_filename} not found, plugin_data will be empty")
            return {}
        except Exception as err:
            logger.critical(f"Could not load plugin_data from {self.plugin_data_filename}: {err}")
            return {}

    def __save_data(self) -> bool:
        """
        Save modified plugin_data to disk
        :return:
        """

        if self.plugin_data != {}:
            """there is actual data to save"""
            try:
                pickle.dump(self.plugin_data, (open(self.plugin_data_filename, "wb")))
                return True
            except Exception as err:
                logger.critical(f"Could not write plugin_data to {self.plugin_data_filename}: {err}")
                return False
        else:
            """no data to save, remove file"""
            if os.path.isfile(self.plugin_data_filename):
                try:
                    remove(self.plugin_data_filename)
                    return True
                except Exception as err:
                    logger.critical(f"Could not remove file {self.plugin_data_filename}: {err}")
                    return False

    def add_config_items(self, config_items: Dict[str, Any]):
        """Add config items (and their default value) to get from a configuration file"""

        self.config_items = config_items

    def _get_cfg(self, filepath: str, path: List[str], default: Any = None, required: bool = True) -> Any:
        """Get a config option from a path and option name, specifying whether it is
        required.

        Raises:
            ConfigError: If required is specified and the object is not found
                (and there is no default value provided), this error will be raised
        """
        # Sift through the the config until we reach our option
        with open(filepath) as file_stream:
            config = yaml.safe_load(file_stream.read())
        for name in path:
            config = config.get(name)

            # If at any point we don't get our expected option...
            if config is None:
                # Raise an error if it was required
                if required or not default:
                    raise ConfigError(f"Config option {'.'.join(path)} is required")

                # or return the default value
                return default

        # We found the option. Return it
        return config

    def read_config(self):
        configfile = os.path.join(os.path.dirname(__file__), os.path.basename(__file__)[:-3] + ".yaml")
        configuration: dict = {}
        for value in self.config_items:
            configuration[value] = self._get_cfg(configfile, [value], required=True)
            

class PluginCommand:

    def __init__(self, command: str, method: Callable, help_text: str, room_id: List[str]):
        self.command: str = command
        self.method: Callable = method
        self.help_text: str = help_text
        self.room_id: List[str] = room_id


class PluginHook:

    def __init__(self, event_type: str, method: Callable, room_id: List[str]):
        self.event_type: str = event_type
        self.method: Callable = method
        self.room_id: List[str] = room_id
