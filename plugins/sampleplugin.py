from plugin import Plugin

import logging
logger = logging.getLogger(__name__)

plugin = Plugin("sampleplugin", "General", "Just a simple sample.")


class Sample:
    def __init__(self, message: str):
        self.message = message


async def sample_command(command):
    await plugin.reply(command, "This is a sample output")


async def sample_store(command):
    """
    Persistently store a message
    :param command:
    :return:
    """

    if command.args:
        logger.debug(f"sample_store called with {command.args}")
        message: str = " ".join(command.args)
        sample: Sample = Sample(message)
        if plugin.store_data("sample", sample):
            await plugin.reply_notice(command, f"Message \"{message}\" stored successfully")
        else:
            await plugin.reply_notice(command, "Could not store message")
    else:
        await plugin.reply_notice(command, "No message supplied")


async def sample_read(command):
    """
    Read previously stored message
    :param command:
    :return:
    """

    try:
        sample: Sample = plugin.read_data("sample")
        await plugin.reply(command, f"Message: {sample.message}", 200)
    except KeyError:
        await plugin.reply_notice(command, "Message could not be loaded")


async def sample_clear(command):
    """
    Clear a previously stored message
    :param command:
    :return:
    """

    if plugin.clear_data("sample"):
        await plugin.reply_notice(command, "Message cleared")
    else:
        await plugin.reply_notice(command, "Could not clear message as no message was stored")

plugin.add_command("sample", sample_command, "A simple sample command, producing a simple sample output")
plugin.add_command("sample_store", sample_store, "Store a message persistently")
plugin.add_command("sample_read", sample_read, "Read the stored message")
plugin.add_command("sample_clear", sample_clear, "Clear the stored message")
