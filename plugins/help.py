from plugins.send_typing import send_typing


async def printhelp(command):
    """Show the help text"""
    if not command.args:
        text = "Es gibt nichts zu sehen!"
        await send_text_to_room(command.client, command.room.room_id, text)
        return

    topic = command.args[0]
    if topic == "rules":
        text = "Clantag weg!"
    elif topic == "commands":
        text = ("#### Available commands:  \n"
                "`meter` - accurately measure someones somethingness  \n"
                "`quote` - not implemented yet  \n"
                "`spruch` - famous quotes from even more famous people  \n"
                "`oracle` - predict the inevitable future  "
                )
    else:
        text = "Unknown help topic!"
    await send_typing(command.client, command.room.room_id, text, notice=False)
