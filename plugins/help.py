from chat_functions import send_typing
import plugins.sabnzbdapi


async def printhelp(command):
    """Show the help text"""
    text = (
        "#### Available commands:  \n"
        "`echo` - make someone agree with you for once  \n"
        "`meter` - accurately measure someones somethingness  \n"
        "`oracle` - predict the inevitable future  \n"
        "`pick` - aids you in those really important life decisions  \n"
        "`roll` - the dive giveth and the dive taketh away  \n"
        "`spruch` - famous quotes from even more famous people  \n"
        )
    if command.room.room_id == plugins.sabnzbdapi.room_id:
        text = text + (
            "`last [n]` - get last n history items  \n"
            "`resume <nzo_id>` - resume paused download  \n"
            "`delete <nzo_id>` - remove download from queue  \n"
            "`purge` - clear entire queue  \n"
        )

    await send_typing(command.client, command.room.room_id, text)
