import os.path
from modulefinder import Module
from typing import List, Any, Dict, Coroutine
import nio
import yaml

from errors import ConfigError


def _get_cfg(
        filepath: str,
        path: List[str],
        default: Any = None,
        required: bool = True,
) -> Any:
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


class Plugin:

    def __init__(self, name, category, description):
        """
        commands (list[tuple]): list of commands in the form of (trigger: str, method: str, helptext: str)

        """
        self.category: str = category
        self.name: str = name
        self.description: str = description
        # Hooks
        # Dict of Rooms, each value being a Dict of events and coroutines being called by the event.
        # self.hooks: { nio.rooms.MatrixRoom: { event_type: [ Coroutine, ... ] } }
        self.commands: Dict[nio.rooms.MatrixRoom, Dict[str, List[Coroutine]]] = {}
        self.hooks: Dict[nio.rooms.MatrixRoom, Dict[str, List[Coroutine]]] = {}
        self.help_texts: Dict[nio.rooms.MatrixRoom, Dict[str, str]] = {}
        self.configitems: List[str] = []
        self.configuration: Dict[str, str] = {}

    def get_plugin(self):
        return self

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

    def add_command(self, command, method, helptext, room_list=[]):

        if room_list:
            for room in room_list:
                try:
                    self.commands[room][command].append(method)
                except KeyError:
                    if room in self.commands.keys():
                        print("Added command " + command + " for room " + room)
                        self.commands[room][command] = [method]
                    else:
                        print("Set commands for room " + room + " to " + command)
                        self.commands[room] = {}
                        self.commands[room][command] = [method]
                # self.help_texts[room][command] = helptext
        else:
            any_room = nio.rooms.MatrixRoom("any", "undef")
            if any_room in self.commands.keys():
                print("Added global command " + command)
                self.commands[any_room][command].append(method)
            else:
                print("Set global commands to " + command)
                self.commands[any_room] = {}
                self.commands[any_room][command] = [method]
            if any_room in self.help_texts.keys():
                print("Added global helptext " + command + ", " + helptext)
                self.help_texts[any_room][command] = helptext

    def get_commands(self):
        """
        Extract called methods from commands

        :return:
        dict: {command: method}
        """

        # commandmethods: Dict = {}
        # for command in self.commands:
        #    commandmethods[command[0]] = command[1]
        #
        # return commandmethods

        return self.commands

    def add_hook(self, event_type, method, room_list=[]):

        if room_list:
            for room in room_list:
                self.hooks[room][event_type].append(method)
        else:
            self.hooks[nio.rooms.MatrixRoom("any", "undef")][event_type].append(method)

    def get_hooks(self):

        # try:
        #    command = self.hooks[room_id][event_type]
        #    return command
        # except ValueError:
        #    return None

        return self.hooks

    def read_config(self) -> dict:
        configfile = os.path.join(os.path.dirname(__file__), os.path.basename(__file__)[:-3] + ".yaml")
        configuration: dict = {}
        for value in self.configitems:
            configuration[value] = _get_cfg(configfile, [value], required=True)
