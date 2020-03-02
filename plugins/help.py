from chat_functions import send_typing
import plugins.sabnzbdapi
import plugins.sonarrapi

# we might need this later
# self.pl = PluginLoader()
# self.commands = Dict[str, List[Dict]]

# assemble all valid commands and their respective methods
# for plugin in self.pl.get_plugins():
#    for plugin_command in plugin.get_commands():
#        self.commands[plugin.category].append(plugin_command)


async def printhelp(command):
    """Show the help text"""
    text = (
        "#### Available commands:  \n"
        "**general**  \n"
        "`echo` - make someone agree with you for once  \n"
        "`meter` - accurately measure someones somethingness  \n"
        "`oracle` - predict the inevitable future  \n"
        "`pick` - aids you in those really important life decisions  \n"
        "`roll` - the dice giveth and the dice taketh away  \n"
        "`spruch` - famous quotes from even more famous people  \n"
        "`translate [[bi] source_lang... dest_lang]` - translate text from one or more source_lang to dest_lang  \n"
        )
    if command.room.room_id == plugins.sabnzbdapi.room_id:
        text = text + (
            "  \n"
            "**sabnzbd**  \n"
            "`last [n]` - get last n history items  \n"
            "`resume <nzo_id>` - resume paused download  \n"
            "`delete <nzo_id>` - remove download from queue  \n"
            "`purge` - clear entire queue  \n"
        )
    if command.room.room_id == plugins.sonarrapi.room_id:
        text = text + (
            "  \n"
            "**sonarr**  \n"
            "`series` - display currently tracked series  \n"
        )

    await send_typing(command.client, command.room.room_id, text)
