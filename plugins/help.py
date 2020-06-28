from plugin import Plugin, PluginCommand
from chat_functions import send_text_to_room
from re import match

from typing import List, Tuple, Dict


def build_sorted_text_output(headline: str, content: List[Tuple[str, str]]) -> str:

    """
    Takes a headline and a list of items and their respective descriptions,
    sorts it and returns a nicely readable output
    """

    content.sort()
    output: str = f"{headline}  \n\n"
    for (item, description) in content:
        output = f"{output}`{item}`: {description}  \n"

    return output


async def print_help(command):
    """Show the help text"""

    help_text: str = ""
    current_room_id: str = command.room.room_id

    if len(command.args) == 0:
        """print loaded plugins"""

        loaded_plugin: Plugin
        plugin_texts: List[Tuple[str, str]] = []

        # Load names and descriptions of all loaded plugins
        for loaded_plugin in command.plugin_loader.get_plugins().values():
            if not loaded_plugin.rooms or current_room_id in loaded_plugin.rooms:
                plugin_texts.append((loaded_plugin.name, loaded_plugin.description))

        headline: str = f"**Available Plugins in this room**  \nuse `help <pluginname>` to get detailed help"
        help_text = build_sorted_text_output(headline, plugin_texts)

    elif len(command.args) == 1 and match("[A-z]*", command.args[0]):

        """print plugin-specific commands"""
        try:
            available_plugins: Dict[str, Plugin] = command.plugin_loader.get_plugins()
            requested_plugin_name: str = command.args[0]
            
            # check if requested plugin is actually available
            if requested_plugin_name in available_plugins.keys():
                requested_plugin: Plugin = available_plugins[requested_plugin_name]

                # get all rooms the plugin has commands for
                plugin_rooms: List[str] = requested_plugin.rooms

                # check if plugin is global or is valid for the current room
                if not plugin_rooms or current_room_id in plugin_rooms:
                    plugin_command_name: str
                    plugin_command: PluginCommand
                    command_texts: List[Tuple[str, str]] = []

                    # Iterate through all commands of requested plugin and add descriptions
                    for (plugin_command_name, plugin_command) in requested_plugin.get_commands().items():
                        command_texts.append((plugin_command_name, plugin_command.help_text))

                    headline: str = f"**Plugin {requested_plugin_name}**"
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
