import os.path
from modulefinder import Module
from typing import List, Any, Dict

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
        self.commands: List[List[str, str, str]] = []
        self.configitems: List[str] = []
        self.configuration: Dict[str, str] = {}

    def get_plugin(self):
        return self

    def get_help_text(self):
        """
        Extract helptexts from commands

        :return:
        list[dict]: {command: helptext}
        """

        commandhelp: List[Dict] = []
        for command in self.commands:
            commandhelp.append({command[0]: command[2]})

        return commandhelp

    def add_command(self, command, method, helptext):
        self.commands.append([command, method, helptext])

    def get_commands(self):
        """
        Extract called methods from commands

        :return:
        list[dict]: {command: method}
        """

        commandmethods: list[dict] = []
        for command in self.commands:
            commandmethods.append({command[0]: command[1]})

        return commandmethods

    def read_config(self) -> dict:
        configfile = os.path.join(os.path.dirname(__file__), os.path.basename(__file__)[:-3] + ".yaml")
        configuration: dict = {}
        for value in self.configitems:
            configuration[value] = _get_cfg(configfile, [value], required=True)
