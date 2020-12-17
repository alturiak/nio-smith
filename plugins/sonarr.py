# -*- coding: utf8 -*-
from plugin import Plugin
import requests
import humanize
import datetime

plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")


def setup():
    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", None, is_required=False)
    plugin.add_command("series", series, "Get a list of currently tracked series", room_id=[plugin.read_config("room_id")])
    plugin.add_command("upcoming", upcoming, "Get a list of upcoming episodes from sonarr's calendar", room_id=[plugin.read_config("room_id")])
    plugin.add_command("today", today, "Get a list of today's episodes", room_id=[plugin.read_config("room_id")])
    plugin.add_timer(episodes_today, "daily")
    plugin.add_timer(update_episodes_today, frequency=datetime.timedelta(minutes=5))


async def series(command):

    api_path = "/series"
    api_parameters = {"apikey": plugin.read_config("api_key")}

    shows = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)

    if shows.status_code == 200:
        message = "<table><tr>"
        cols = ["Title", "Seasons", "Episodes on Disk", "Size", "Status", "Rating"]
        for col in cols:
            message = message + f"<td><b>{col}</b></td>"
        message = message + "</tr>"
        sorted_shows = sorted(shows.json(), key=lambda i: i['title'])
        for show in sorted_shows:
            cols = [f"<a href=\"https://www.imdb.com/title/{show['imdbId']}\">{show['title']}</a>",
                    f"{str(show['seasonCount'])}",
                    f"{str(show['episodeCount'])}",
                    f"{str(humanize.naturalsize(show['sizeOnDisk']))}",
                    f"{str(show['status'])}",
                    f"{str(show['ratings']['value'])}"]
            message = message + "<tr>"
            for col in cols:
                message = message + "<td>" + col + "</td>"
            message = message + "</tr>"
        message = message + "</table>"
        await plugin.reply(command, message)

    else:
        await plugin.reply_notice(command, f"Response Code: {str(shows.status_code)}")


async def get_calendar_episodes(limit: int) -> list or None:
    """
    Get a list of episodes from the calendar for <limit> days in the future
    :param limit: days in the future to fetch calendar entries
    :return: list of episodes (https://github.com/Sonarr/Sonarr/wiki/Calendar)
    """
    start_date = datetime.date.isoformat(datetime.date.today())
    end_date = datetime.date.isoformat(datetime.date.today() + datetime.timedelta(days=limit))
    api_path = "/calendar"
    api_parameters = {"apikey": plugin.read_config("api_key"),
                      "start": start_date,
                      "end": end_date
                      }

    response: requests.Response = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)

    if response.status_code == 200:
        return sorted(response.json(), key=lambda i: i['airDateUtc'])
    else:
        return None


async def upcoming(command):
    """
    Get the list of episodes for the next seven days and post them to the room
    :param command:
    :return: -
    """

    if episodes := await get_calendar_episodes(7):
        message: str = ""
        for episode in episodes:
            message += f"{str(episode['airDateUtc'])} {str(episode['series']['title'])} {str(episode['seasonNumber'])}x{str(episode['episodeNumber'])} " \
                       f"{str(episode['title'])}  \n"

        if message != "":
            message = f"**Upcoming episodes in the next 7 days:**  \n{message}"
            await plugin.reply(command, message)

    else:
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "❌")


async def build_episodes_today() -> str:
    """
    Get the list of today's episodes and nicely format them to a message, displaying episodes and download status
    :return: (str) the message listing the episodes
    """

    if episodes := await get_calendar_episodes(1):
        message: str = ""
        for episode in episodes:
            if episode['hasFile']:
                message += f"<font color=\"green\">"
            else:
                message += f"<font color=\"red\">"
            message += f"{str(episode['series']['title'])} {str(episode['seasonNumber'])}x{str(episode['episodeNumber'])} {str(episode['title'])}</font>  \n"

        if message != "":
            return f"**Episodes expected today:**  \n{message}"
        else:
            return ""


async def episodes_today(client):
    """
    Get the list of episodes for the current day and post them to the configured room
    :param client:
    :return: -
    """

    message: str = await build_episodes_today()
    if message != "":
        # store message-id and message for editing the message later
        event_id = await plugin.message(client, plugin.read_config("room_id"), message)
        plugin.store_data("today_message", (event_id, message))


async def update_episodes_today(client):
    """
    Check the list of current episodes for successful downloads and update the message accordingly
    :param client:
    :return:
    """

    message: str = await build_episodes_today()

    if message != "" and message != plugin.read_data("today_message")[1]:
        # store message-id and message for editing the message later
        await plugin.replace(client, plugin.read_config("room_id"), plugin.read_data("today_message")[0], message)
        plugin.store_data("today_message", (plugin.read_data("today_message")[0], message))


async def today(command):
    """
    Get the list of episodes for the current day and post them to the configured room
    :param command:
    :return: -
    """

    message: str = await build_episodes_today()

    if message != "":
        event_id: str = await plugin.reply(command, message)
        plugin.store_data("today_message", (event_id, message))


setup()
