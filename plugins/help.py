from plugin import Plugin, PluginCommand
from chat_functions import send_text_to_room
from typing import List
from re import match


async def print_help(command):
    """Show the help text"""

    text: str = ""
    loaded_plugin: Plugin
    text_plugin_list: str = ""
    room_id: str = command.room.room_id

    if len(command.args) == 0:

        """print loaded plugins"""
        for loaded_plugin in command.plugin_loader.get_plugins().values():
            if not loaded_plugin.rooms or room_id in loaded_plugin.rooms:
                text_plugin_list = text_plugin_list + "`" + loaded_plugin.name + "`" + " " + loaded_plugin.description + "  \n"

        text = "**Available Plugins in this room**  \nuse `help <pluginname>` to get detailed help  \n" + text_plugin_list

    elif len(command.args) == 1 and match("[A-z]*", command.args[0]):

        """print plugin-specific commands"""
        try:
            command_rooms: List[str] = command.plugin_loader.get_plugins()[command.args[0]].rooms
            if not command_rooms or room_id in command_rooms:
                loaded_command_name: str
                loaded_command: PluginCommand
                for loaded_command_name, loaded_command in command.plugin_loader.get_plugins()[command.args[0]].get_commands().items():
                    text = text + "`" + loaded_command_name + "`" + "    " + loaded_command.help_text + "  \n"

                text = "**Plugin " + command.args[0] + "**  \n" + text
            else:
                raise ValueError

        except ValueError:
            text = "Plugin not active (in this room), try `help`"

    else:
        text = "try `help` ;-)"
    await send_text_to_room(command.client, room_id, text)


plugin = Plugin("help", "General", "Provide helpful help")
plugin.add_command("help", print_help, "Display list of all available commands")
