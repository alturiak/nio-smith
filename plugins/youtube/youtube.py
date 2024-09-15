from typing import Dict

import requests
from nio import AsyncClient, RoomMessageText
from urlextract import URLExtract

from core.bot_commands import Command
from core.plugin import Plugin
import logging
import re
from urllib import parse
from yarl import URL
from datetime import datetime, timedelta
from humanize import naturaldate, intword, precisedelta


logger = logging.getLogger(__name__)
plugin = Plugin(
    "youtube",
    "Lookup",
    "Watches for youtube links and posts video title, description, thumbnail and other various details",
)


def setup():
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_list", default_value=None, is_required=False)
    plugin.add_config("enable_dislikes", default_value=True, is_required=True)
    plugin.add_command("youtube", youtube_command, "Enable/disable automatic youtube link preview")


def parse_duration(iso_duration):
    """Parses an ISO 8601 duration string into a datetime.timedelta instance.
    Args:
        iso_duration: an ISO 8601 duration string.
    Returns:
        a datetime.timedelta instance
    """
    m = re.match(r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:.\d+)?)S)?$", iso_duration)
    if m is None:
        raise ValueError("invalid ISO 8601 duration string")

    days = 0
    hours = 0
    minutes = 0
    seconds = 0.0

    # Years and months are not being utilized here, as there is not enough
    # information provided to determine which year and which month.
    # Python's time_delta class stores durations as days, seconds and
    # microseconds internally, and therefore we'd have to
    # convert parsed years and months to specific number of days.

    if m[3]:
        days = int(m[3])
    if m[4]:
        hours = int(m[4])
    if m[5]:
        minutes = int(m[5])
    if m[6]:
        seconds = float(m[6])

    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


async def youtube_command(command: Command):
    """
    Turn automatic youtube previews on or off
    :param command:
    :return:
    """

    if plugin.has_hook("m.room.message", youtube_message, room_id_list=[command.room.room_id]):
        # disable youtube previews
        plugin.del_hook("m.room.message", youtube_message, room_id_list=[command.room.room_id])
        await plugin.respond_notice(command, f"Automatic youtube previews disabled.")

    else:
        # enable youtube previews
        plugin.add_hook("m.room.message", youtube_message, room_id_list=[command.room.room_id], hook_type="dynamic")
        await plugin.respond_notice(command, f"Automatic youtube previews enabled.")


async def youtube_message(client: AsyncClient, room_id: str, event: RoomMessageText):

    parts: str = "snippet,contentDetails,statistics"
    # The part parameter identifies groups of properties that should be returned for a resource.
    fields: str = "items(snippet(title,publishedAt,thumbnails,channelTitle),contentDetails(duration),statistics(viewCount,likeCount))"
    # The fields parameter filters the API response to only return specific properties within the requested resource parts.

    # strip body of replied-to text from the message
    line: str
    actual_message: str = "\n".join([line for line in event.body.split("\n") if not line.startswith("> ")])

    extractor = URLExtract()
    urls = extractor.find_urls(actual_message)

    for url in urls:
        parsed_url = URL(url)

        if parsed_url.scheme == "https" and parsed_url.host in ["www.youtube.com", "youtube.com"]:
            url_data = parse.urlparse(url)
            query = parse.parse_qs(url_data.query)
            video_id = query["v"][0]

        elif parsed_url.host == "youtu.be":
            url_data = parse.urlparse(url)
            video_id = url_data.path[1:]

        else:
            return

        youtube_error = False
        youtube_response: requests.Response = requests.Response()

        try:
            youtube_response: requests.Response = requests.get(
                f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={plugin.read_config("api_key")}&fields={fields}&part={parts}'
            )

        except requests.exceptions.ConnectionError as err:
            logger.warning(f"Connection to youtube-API failed: {err}")

        if youtube_response.status_code == 200:
            response_json: Dict[str, any] = youtube_response.json()
            video = response_json.get("items")[0]
            video_title: str = video.get("snippet").get("title")
            try:
                video_thumbnail: str = video.get("snippet").get("thumbnails").get("standard").get("url")
            except AttributeError:
                video_thumbnail: str = ""
            video_date: str = video.get("snippet").get("publishedAt")
            video_date_dt = datetime.fromisoformat(video_date)
            channel_title: str = video.get("snippet").get("channelTitle")
            video_duration: timedelta = parse_duration(video.get("contentDetails").get("duration"))
            youtube_views: int = int(video.get("statistics").get("viewCount"))
            youtube_likes: int = int(video.get("statistics").get("likeCount"))

        else:
            logger.warning(f"Error in youtube API response: {youtube_response.status_code}")
            youtube_error = True

        if plugin.read_config("enable_dislikes"):
            youtube_dislike_error = False
            youtube_dislike_response: requests.Response = requests.Response()

            try:
                youtube_dislike_response: requests.Response = requests.get(f"https://returnyoutubedislikeapi.com/Votes?videoId={video_id}")
            except requests.exceptions.ConnectionError as err:
                logger.warning(f"Connection to youtube-dislike-API failed: {err}")

            if youtube_dislike_response.status_code == 200:
                response_json: Dict[str, any] = youtube_dislike_response.json()
                youtube_dislike_likes: int = response_json.get("likes")
                youtube_dislike_rawlikes: int = response_json.get("rawLikes")
                youtube_dislike_dislikes: int = response_json.get("dislikes")
                try:
                    sample_size: float = youtube_dislike_rawlikes / youtube_dislike_likes * 100
                except ZeroDivisionError:
                    youtube_dislike_error = True

            else:
                logger.warning(f"Error in youtube-dislike API response: {youtube_dislike_response.status_code}")
                youtube_dislike_error = True

        if not youtube_error:
            if video_thumbnail != "":
                link: str = f'<a href="{video_thumbnail}">-</a>'
            else:
                link: str = "-"
            message: str = (
                f'{channel_title} {link} **{video_title}**  \n📅 {naturaldate(video_date_dt)} | ⌛ {precisedelta(video_duration, minimum_unit="minutes", format="%0.0f")} | 👀 {intword(youtube_views)} | 👍 {intword(youtube_likes)}'
            )

            if plugin.read_config("enable_dislikes") and not youtube_dislike_error:
                message += f' | 👎 ~{intword(youtube_dislike_dislikes)} (🧪 {"{:.0f}".format(sample_size)}%)'
            await plugin.send_notice(client, room_id, message)


setup()
