from chat_functions import send_typing
from plugin import Plugin


async def echo(command):
    """Echo back the command's arguments"""
    response = " ".join(command.args)
    await send_typing(command.client, command.room.room_id, response)


plugin = Plugin("echo", "General", "A very simple Echo plugin")
plugin.add_command("echo", echo, "make someone agree with you for once", room_id=["!iAxDarGKqYCIKvNSgu:pack.rocks", "!WLzPcYhULnmsuPwZSN:pack.rocks"])
plugin.add_command("echo2", echo, "make someone agree with you for once - again", room_id=["!iAxDarGKqYCIKvNSgu:pack.rocks", "!WLzPcYhULnmsuPwZSN:pack.rocks"])
