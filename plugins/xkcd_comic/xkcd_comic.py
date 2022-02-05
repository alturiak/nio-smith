# -*- coding: utf8 -*-
import datetime
from typing import List

from PIL import Image
from nio import AsyncClient, UnknownEvent

from core.bot_commands import Command
from core.plugin import Plugin
import logging
import xkcd

logger = logging.getLogger(__name__)
plugin = Plugin("xkcd_comic", "General", "Fetch an xkcd-comic and post it to the room")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("url_only", is_required=False, default_value=False)
    plugin.add_config("room_list", is_required=False, default_value=[])
    plugin.add_command("xkcd", xkcd_command, "Post the most recent or a specific xkcd-comic")
    plugin.add_timer(xkcd_check, datetime.timedelta(hours=1))


async def format_message(comic: xkcd.Comic, link_comic: bool = False) -> str:
    """
    Format a message posting xkcd Comic number, title, alt-text and link to the explanation
    :param comic: the xkcd.Comic Object
    :param link_comic: whether to include the link to the comic in the message
    :return:
    """

    message: str = f"xkcd {comic.number}:  {comic.getTitle()}  \n{comic.altText}  \nExplanation: {comic.getExplanation()}"

    if link_comic:
        message = message.replace(f"xkcd {comic.number}", f"[xkcd {comic.number}]({comic.link})")

    return message


async def get_comic(comic_id: int or None = None) -> xkcd.Comic or None:
    """
    Retrieve the most recent or a specified xkcd-Comic
    :return:    xkcd.Comic if successfully retrieved,
                None otherwise
    """

    comic: xkcd.Comic
    try:
        if comic_id is None:
            return xkcd.getLatestComic()
        else:
            return xkcd.getComic(comic_id)
    except:
        return None


async def post_xkcd(client: AsyncClient, room_id: str, comic: xkcd.Comic):
    """
    Post an xkcd-comic to a room
    :param client:
    :param room_id:
    :param comic:
    :return:
    """

    if plugin.read_config("url_only") == False:
        image: Image.Image = await plugin.fetch_image_from_url(comic.imageLink)
        if image is not None:
            await plugin.send_image(client, room_id, image)
            await plugin.send_message(client, room_id, await format_message(comic))
        else:
            # error retrieving the actual image, fall back to posting the url
            await plugin.send_message(client, room_id, await format_message(comic, link_comic=True))

    else:
        await plugin.send_message(client, room_id, await format_message(comic, link_comic=True))


async def xkcd_command(command: Command):
    """
    Parse !xkcd-command and post comic to room if successfully fetched
    :param command:
    :return:
    """

    comic: xkcd.Comic

    if len(command.args) == 0:
        # post most recent xkcd_comic
        comic = await get_comic()

    elif len(command.args) == 1 and command.args[0].isdigit():
        # get a specific comic by id
        comic = await get_comic(command.args[0])

    else:
        await plugin.respond_notice(command, "Too many arguments or malformed id - Usage: `xkcd [id]`")
        return

    if comic is None:
        await plugin.respond_notice(command, "Error fetching comic.")
    else:
        await post_xkcd(command.client, command.room.room_id, comic)


async def xkcd_react(client: AsyncClient, room_id: str, event: UnknownEvent):
    """
    Triggered by a 👀-reaction to an xkcd_check message, posts the most recent xkcd-Comic
    :param client:
    :param room_id: (str) the room-id, the reaction has been received on
    :param event: the event of the reaction (not used)
    :return:
    """

    if plugin.has_hook("m.reaction", xkcd_react, [room_id]):
        comic: xkcd.Comic = await get_comic()
        if comic is not None:
            await post_xkcd(client, room_id, comic)
        plugin.del_hook("m.reaction", xkcd_react, [room_id])


async def xkcd_check(client):
    """
    Check for a new xkcd comic and post a message about its availability if room_list is specified.
    :param client:
    :return:
    """

    room_list: List[str] = plugin.read_config("room_list")
    if room_list:
        known_recent: int = await plugin.read_data("known_recent")
        if known_recent is None:
            known_recent = 0

        try:
            comic: xkcd.Comic = xkcd.getLatestComic()
        except:
            logger.warning(f"Unable to get latest xkcd-Comic.")
            return

        if comic.number > known_recent:
            plugin.del_hook("m.reaction", xkcd_react)
            message_ids: List[str] = []
            for room_id in room_list:
                message_id: str or None = await plugin.send_notice(
                    client,
                    room_id,
                    f"New xkcd-Comic: [{comic.title} ({comic.number})]({comic.link}). " f"`!xkcd` or 👀 to display.",
                )
                await plugin.send_reaction(client, room_id, message_id, "👀")
                message_ids.append(message_id)

            if message_ids:
                plugin.add_hook(
                    "m.reaction",
                    xkcd_react,
                    room_list,
                    message_ids,
                    hook_type="dynamic",
                )
            await plugin.store_data("known_recent", comic.number)


setup()
