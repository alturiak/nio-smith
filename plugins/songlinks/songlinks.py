import asyncio
import re
from yarl import URL
from urlextract import URLExtract
import requests
from urllib.parse import quote

from nio import AsyncClient, RoomMessageText
from core.bot_commands import Command
from core.plugin import Plugin
import logging


logger = logging.getLogger(__name__)

plugin = Plugin("songlinks", "General", "Automatically fetches songlinks for music links")


def setup():
    plugin.add_config("room_list", default_value=None, is_required=False)
    plugin.add_config("allowed_domains", default_value=None, is_required=True)
    plugin.add_config("patterns", default_value=None, is_required=True)
    plugin.add_command("songlinks", songlinks_command, "Enable/disable automatic songlinks", room_id=plugin.read_config("room_list"), power_level=50)


async def songlinks_command(command: Command):
    """
    Turn automatic songlinks links on or off
    :param command:
    :return:
    """

    if plugin.has_hook("m.room.message", songlinks_message, room_id_list=[command.room.room_id]):
        # disable songlinks
        plugin.del_hook("m.room.message", songlinks_message, room_id_list=[command.room.room_id])
        await plugin.respond_notice(command, f"Automatic songlinks disabled.")

    else:
        # enable songlinks
        plugin.add_hook("m.room.message", songlinks_message, room_id_list=[command.room.room_id], hook_type="dynamic")
        await plugin.respond_notice(command, f"Automatic songlinks enabled.")


async def songlinks_message(client: AsyncClient, room_id: str, event: RoomMessageText):

    # check message for url
    extractor = URLExtract()
    urls = extractor.find_urls(event.body)
    allowed_domains = plugin.read_config("allowed_domains")
    patterns = plugin.read_config("patterns")

    for url in urls:
        parsed_url = URL(url)
        # check url for supported service
        if parsed_url.scheme == "https" and parsed_url.host in allowed_domains:
            pattern = patterns.get(allowed_domains.get(parsed_url.host))
            compiled_pattern = re.compile(pattern)
            if compiled_pattern.match(parsed_url.path):
                # fetch songlinks-link
                r = requests.get(f"https://api.song.link/v1-alpha.1/links?url={quote(url)}")
                if r.status_code == 200:
                    # post songlinks-link
                    json = r.json()
                    entityId = json.get("entityUniqueId")
                    song_artist = json.get("entitiesByUniqueId").get(entityId).get("artistName")
                    song_name = json.get("entitiesByUniqueId").get(entityId).get("title")
                    song_url = json.get("pageUrl")

                    await plugin.send_notice(client, room_id, f'Songlink: <a href="{song_url}">{song_artist} - {song_name}</a>')
                else:
                    logger.warning(f"song.link error {r.status_code} fetching {url}")


setup()
