# -*- coding: utf8 -*-
from PIL import Image

from core.bot_commands import Command
from core.plugin import Plugin
import logging
import xkcd

logger = logging.getLogger(__name__)
plugin = Plugin("xkcd_comic", "General", "Fetch an xkcd_comic-comic and post it to the room")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("url_only", is_required=False, default_value=False)
    plugin.add_command("xkcd", xkcd_command, "Post the most recent or a specific xkcd_comic-comic")


async def xkcd_command(command: Command):
    """

    :param command:
    :return:
    """

    comic: xkcd.Comic

    if len(command.args) == 0:
        # post most recent xkcd_comic
        comic = xkcd.getLatestComic()

    elif len(command.args) == 1 and command.args[0].isdigit():
        # get a specific comic by id
        comic = xkcd.getComic(command.args[0])

    else:
        await plugin.respond_notice(command, "Too many arguments or malformed id - Usage: `xkcd_comic [id]`")

    image: Image.Image = await plugin.fetch_image_from_url(comic.imageLink)
    alt_text: str = comic.altText
    explanation: str = comic.getExplanation()

    if plugin.read_config("url_only") == False:
        await plugin.send_image(command.client, command.room.room_id, image)
        await plugin.send_message(command.client,
                                  command.room.room_id,
                                  message=f"XKCD {comic.number}: {comic.getTitle()}  \n{alt_text}  \nExplanation: {explanation}")

    else:
        await plugin.send_message(command.client,
                                  command.room.room_id,
                                  message=f"[XKCD {comic.number}]({comic.link}):  {comic.getTitle()}  \n{alt_text}  \nExplanation: {explanation}")

setup()
