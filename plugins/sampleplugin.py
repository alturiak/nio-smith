from plugin import Plugin
from chat_functions import send_text_to_room

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot_commands import Command


async def sample_command(command: Command):
    await send_text_to_room(command.client, command.room.room_id, "This is a sample output")

plugin = Plugin("Sample", "General", "Just a simple sample.")
plugin.add_command("sample", sample_command, "A simple sample command, producing a simple sample output")
