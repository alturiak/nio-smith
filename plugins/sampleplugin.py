from plugin import Plugin
from chat_functions import send_text_to_room

import logging
logger = logging.getLogger(__name__)

plugin = Plugin("sampleplugin", "General", "Just a simple sample.")


async def sample_command(command):
    await send_text_to_room(command.client, command.room.room_id, "This is a sample output")


async def sample_store(command):
    """
    Persistently store a message
    :param command:
    :return:
    """

    logger.debug(f"sample_store called with {command.args}")
    if command.args:
        if plugin.store_data("message", command.args):
            await send_text_to_room(command.client, command.room.room_id, f"Message {command.args} stored successfully")
        else:
            await send_text_to_room(command.client, command.room.room_id, "Could not store message")
    else:
        await send_text_to_room(command.client, command.room.room_id, "No message supplied")


async def sample_read(command):
    """
    Read previously stored message
    :param command:
    :return:
    """

    try:
        message: str = plugin.read_data("message")
        await send_text_to_room(command.client, command.room.room_id, f"Message loaded: {message}")
    except ValueError:
        await send_text_to_room(command.client, command.room.room_id, "Message could not be loaded")


async def sample_clear(command):
    """
    Clear a previously stored message
    :param command:
    :return:
    """

    if plugin.clear_data("message"):
        await send_text_to_room(command.client, command.room.room_id, "Message cleared")
    else:
        await send_text_to_room(command.client, command.room.room_id, "Could not clear message as no message was stored")

plugin.add_command("sample", sample_command, "A simple sample command, producing a simple sample output")
plugin.add_command("sample_store", sample_store, "Store a message persistently")
plugin.add_command("sample_read", sample_read, "Read the stored message")
plugin.add_command("sample_clear", sample_clear, "Clear the stored message")
