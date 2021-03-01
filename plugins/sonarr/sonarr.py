# -*- coding: utf8 -*-
from typing import Dict, List

import urllib3
from nio import AsyncClient

from core.bot_commands import Command
from plugin import Plugin
import datetime
import logging
import requests
from humanize import naturalsize

logger = logging.getLogger(__name__)
plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """
    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", is_required=True)

    plugin.add_command("series", series, "Get a list of currently tracked series", room_id=[plugin.read_config("room_id")])
    plugin.add_command("episodes", current_episodes, "Post a new message that is tracking episodes", room_id=[plugin.read_config("room_id")])

    # initially post current episodes at the start of the week
    plugin.add_timer(current_episodes, frequency="weekly")
    # check for updates to the episodes' status and update the message accordingly
    plugin.add_timer(update_current_episodes, frequency=datetime.timedelta(minutes=5))


async def series(command):
    """
    Retrieves all currently tracked series from sonarr and puts out a table with the following details:
    Title, Seasons, Episodes on Disk, Size, Status, Rating
    :param command: Command-object
    :return:
    """

    api_path = "/series"
    api_parameters = {"apikey": plugin.read_config("api_key")}

    try:
        shows = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)
    except (TimeoutError, ConnectionRefusedError, urllib3.exceptions.NewConnectionError):
        return

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
                    f"{str(naturalsize(show['sizeOnDisk']))}",
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


async def current_week_dates() -> (str, str):
    """
    Return start date of current week and start date of next week to allow for retrieving episodes for the current week
    :return: start date and end date of the current week
    """

    weekday: int = datetime.date.today().weekday()
    week_start: str = datetime.date.isoformat(datetime.date.today() - datetime.timedelta(days=weekday))
    week_end: str = datetime.date.isoformat(datetime.date.today() + datetime.timedelta(days=7-weekday))

    return week_start, week_end


async def get_calendar_episodes(start_date: str, end_date: str) -> list or None:
    """
    Get a list of episodes from the calendar between start_date and end_date
    :param start_date: start_date to get episodes for in datetime.date.isoformat
    :param end_date: end_date to get episodes for in datetime.date.isoformat
    :return: list of episodes (https://github.com/Sonarr/Sonarr/wiki/Calendar), sorted by airdate
    """

    api_path = "/calendar"
    api_parameters = {"apikey": plugin.read_config("api_key"),
                      "start": start_date,
                      "end": end_date
                      }
    try:
        response: requests.Response = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)
    except (TimeoutError, ConnectionRefusedError, urllib3.exceptions.NewConnectionError):
        return

    if response.status_code == 200:
        return sorted(response.json(), key=lambda i: i['airDateUtc'])
    else:
        return None


async def compose_upcoming(start_date: str, end_date: str) -> str:
    """
    Get the list of episodes between start_date and end_date and format them as a list, grouped by day, highlighting current day and file-status of episodes
    :param start_date: start_date to get episodes for in datetime.date.isoformat
    :param end_date: end_date to get episodes for in datetime.date.isoformat
    :return: formatted message
    """

    message: str = "#### Episodes expected this week  \n"

    if episodes := await get_calendar_episodes(start_date, end_date):

        episodes_by_day: Dict[str, List[any]] = {}

        for episode in episodes:

            day: str = datetime.datetime.fromisoformat(episode['airDateUtc'].rstrip('Z')).strftime('%A')
            if day not in episodes_by_day.keys():
                episodes_by_day[day] = [episode]
            else:
                episodes_by_day.get(day).append(episode)

        for day, episode_list in episodes_by_day.items():
            if day == datetime.datetime.today().strftime('%A'):
                message += f"**<font color=\"orange\">{day}</font>**  \n"
            else:
                message += f"**{day}**  \n"

            for episode in episode_list:

                format_begin: str = ""
                format_end: str = ""

                if episode['hasFile']:
                    format_begin = "<font color=\"green\">"
                    format_end = "</font>"
                elif datetime.datetime.fromisoformat(episode['airDateUtc'].rstrip('Z')) < datetime.datetime.now():
                    # airdate is in the past, mark file missing
                    format_begin = "<font color=\"red\">"
                    format_end = "</font>"

                message += f"{format_begin}{str(episode['series']['title'])} " \
                           f"S{str(episode['seasonNumber']).zfill(2)}E{str(episode['episodeNumber']).zfill(2)} " \
                           f"{str(episode['title'])}{format_end}  \n"
    return message


async def current_episodes(command_client: Command or AsyncClient):
    """
    Get the list of episodes for the current week and post them to the configured room
    :param command_client: Command or AsyncClient, depending on whether the method has been called by a command or a timer
    :return: -
    """

    if isinstance(command_client, AsyncClient):
        client = command_client
    else:
        client = command_client.client

    (week_start, week_end) = await current_week_dates()
    message: str = await compose_upcoming(week_start, week_end)

    if message != "":
        # store event_id for later editing
        event_id = await plugin.message(client, plugin.read_config("room_id"), message)
        await plugin.store_data("today_message", event_id)
        await plugin.store_data("today_message_text", message)


async def update_current_episodes(client):
    """
    update the message posted by current_episodes to reflect current status of episodes
    :param client: nio.AsyncClient
    :return:
    """

    (week_start, week_end) = await current_week_dates()
    message: str = await compose_upcoming(week_start, week_end)

    if message != "" and message != await plugin.read_data("today_message_text"):
        message_id: str or None = await plugin.replace(client, plugin.read_config("room_id"), await plugin.read_data("today_message"), message)
        if not message_id:
            await current_episodes(client)
        else:
            await plugin.store_data("today_message_text", message)


setup()
