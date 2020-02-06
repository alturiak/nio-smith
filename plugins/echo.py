from plugins.send_typing import send_typing


async def echo(command):
    """Echo back the command's arguments"""
    response = " ".join(command.args)
    await send_typing(command.client, command.room.room_id, response)
