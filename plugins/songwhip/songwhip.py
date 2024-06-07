import asyncio
import re
from yarl import URL
from urlextract import URLExtract
import requests
from typing import Optional, Dict, List, Any, Pattern

from nio import AsyncClient, RoomMessageText
from core.bot_commands import Command
from core.plugin import Plugin
import logging


logger = logging.getLogger(__name__)

plugin = Plugin("songwhip", "General", "Automatically fetches songwhip-links for music links")


def setup():
    plugin.add_config("room_list", default_value=None, is_required=False)
    plugin.add_config("allowed_domains", default_value=None, is_required=True)
    plugin.add_config("patterns", default_value=None, is_required=True)
    plugin.add_command("songwhip", songwhip_command, "Enable/disable automatic songwhip links", room_id=plugin.read_config("room_list"), power_level=50)


async def songwhip_command(command: Command):
    """
    Turn automatic songwhip links on or off
    :param command:
    :return:
    """

    if plugin.has_hook("m.room.message", songwhip_message, room_id_list=[command.room.room_id]):
        # disable songwhip
        plugin.del_hook("m.room.message", songwhip_message, room_id_list=[command.room.room_id])
        await plugin.respond_notice(command, f"Automatic songwhip links disabled.")

    else:
        # enable songwhip
        plugin.add_hook("m.room.message", songwhip_message, room_id_list=[command.room.room_id], hook_type="dynamic")
        await plugin.respond_notice(command, f"Automatic songwhip links enabled.")


async def songwhip_message(client: AsyncClient, room_id: str, event: RoomMessageText):

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
                # fetch songwhip-link
                r = requests.post("https://songwhip.com/api/songwhip/create", json={"country": "N/A", "url": url})
                if r.status_code == 200:
                    # post songwhip-link
                    json = r.json()
                    song_artists: List[str] = []
                    for song_artist in json.get("data").get("item").get("artists"):
                        song_artists.append(song_artist.get("name"))
                    song_name = json.get("data").get("item").get("name")
                    song_path = json.get("data").get("item").get("path")

                    await plugin.send_notice(
                        client, room_id, f'Songwhip: <a href="https://songwhip.com/{song_path}">{",".join(song_artists)} - {song_name}</a>'
                    )


setup()
