from plugin import Plugin, PluginCommand
from chat_functions import send_text_to_room
from re import match

from typing import List, Tuple, Dict


def build_sorted_text_output(headline: str, content: List[Tuple[str, str, int]]) -> str:

    """
    Takes a headline and a list of items and their respective descriptions,
    sorts it and returns a nicely readable output
    """

    content.sort()
    output: str = f"{headline}  \n\n"
    for (item, description, power_level) in content:
        if power_level != 0:
            output = f"{output}`{item}`: {description} (PL: {power_level})  \n"
        else:
            output = f"{output}`{item}`: {description}  \n"

    return output


async def print_help(command):
    """Show the help text"""

    help_text: str = ""
    current_room_id: str = command.room.room_id

    if len(command.args) == 0:
        """print loaded plugins"""

        loaded_plugin: Plugin
        plugin_texts: List[Tuple[str, str, int]] = []

        # Load names and descriptions of all loaded plugins
        for loaded_plugin in command.plugin_loader.get_plugins().values():
            if not loaded_plugin.rooms or current_room_id in loaded_plugin.rooms:
                plugin_texts.append((loaded_plugin.name, loaded_plugin.description, 0))

        headline: str = f"**Available Plugins in this room**  \nuse `help <pluginname>` to get detailed help"
        help_text = build_sorted_text_output(headline, plugin_texts)

    elif len(command.args) == 1 and match("[A-z]*", command.args[0]):

        """print plugin-specific commands"""
        try:
            requested_plugin: Plugin
            if requested_plugin := command.plugin_loader.get_plugin_by_name(command.args[0]):
                if requested_plugin.is_valid_for_room(command.room.room_id):
                    plugin_command_name: str
                    plugin_command: PluginCommand
                    command_texts: List[Tuple[str, str, int]] = []

                    # Iterate through all commands of requested plugin and add descriptions
                    for (plugin_command_name, plugin_command) in requested_plugin.get_commands().items():
                        command_texts.append((plugin_command_name, plugin_command.help_text, plugin_command.power_level))

                    headline: str = f"**Plugin {requested_plugin.name}**"
                    help_text = build_sorted_text_output(headline, command_texts)

                else:
                    # Plugin is not valid for the room
                    raise ValueError

            else:
                # Plugin does not exist
                raise ValueError

        except ValueError:
            help_text = "Plugin not active (in this room), try `help`"

    else:
        # too many arguments or invalid plugin-name
        help_text = "try `help` ;-)"

    await send_text_to_room(command.client, current_room_id, help_text)


plugin = Plugin("help", "General", "Provide helpful help")
plugin.add_command("help", print_help, "Display list of all available commands")
