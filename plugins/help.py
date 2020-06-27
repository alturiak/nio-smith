from plugin import Plugin, PluginCommand
from chat_functions import send_text_to_room
from typing import List


async def printhelp(command):
    """Show the help text"""

    text: str = ""
    loaded_plugin: Plugin
    loaded_plugins_names: List[str] = []
    text_plugin_list: str = ""

    for loaded_plugin in command.plugin_loader.get_plugins():
        loaded_plugins_names.append(loaded_plugin.name)
        text_plugin_list = text_plugin_list + "`" + loaded_plugin.name + "`" + " " + loaded_plugin.description + "  \n"

    if len(command.args) == 0:
        # Print loaded plugins
        loaded_plugins: List[Plugin] = []
        for loaded_plugin in command.plugin_loader.get_plugins():
            loaded_plugins.append(loaded_plugin)

        text = "**Available Plugins**  \n" + "use `help <pluginname>` to get detailed help  \n" + text_plugin_list

    elif len(command.args) == 1:
        try:
            loaded_plugin_pos: int = loaded_plugins_names.index(command.args[0])
            loaded_command_name: str
            loaded_command: PluginCommand
            for loaded_command_name, loaded_command in command.plugin_loader.get_plugins()[
                loaded_plugin_pos].get_commands().items():
                text = text + "`" + loaded_command_name + "`" + "    " + loaded_command.help_text + "  \n"

            text = "**Plugin " + loaded_plugins_names[loaded_plugin_pos] + "**  \n" + text

        except ValueError:
            text = "Plugin not found, try `help`"

    else:
        text = "try `help` ;-)"
    await send_text_to_room(command.client, command.room.room_id, text)


plugin = Plugin("help", "General", "Provide helpful help")
plugin.add_command("help", printhelp, "Display list of all available commands")
