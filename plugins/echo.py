from chat_functions import send_text_to_room

async def echo(command):
    """Echo back the command's arguments"""
    response = " ".join(command.args)
    await send_text_to_room(command.client, command.room.room_id, response)
