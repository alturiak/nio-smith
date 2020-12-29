# -*- coding: utf8 -*-
from plugin import Plugin
import requests
import humanize
import datetime

plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """
    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", None, is_required=False)

    plugin.add_command("series", series, "Get a list of currently tracked series", room_id=[plugin.read_config("room_id")])
    plugin.add_command("upcoming", upcoming, "Get a list of upcoming episodes from sonarr's calendar", room_id=[plugin.read_config("room_id")])
    plugin.add_command("today", current_episodes_command, "Get a list of today's episodes", room_id=[plugin.read_config("room_id")])

    # initially post current episodes at the start of the day
    plugin.add_timer(current_episodes_timer, "daily")
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
    Get a list of episodes from the calendar for <limit> days in the future or past
    :param limit: days in the future to fetch calendar entries
    :return: list of episodes (https://github.com/Sonarr/Sonarr/wiki/Calendar)
    """

    if limit < 0:
        start_date = datetime.date.isoformat(datetime.date.today() - datetime.timedelta(days=-limit))
        end_date = datetime.date.isoformat(datetime.date.today())
    else:
        start_date = datetime.date.isoformat(datetime.date.today())
        end_date = datetime.date.isoformat(datetime.date.today() + datetime.timedelta(days=limit+1))
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
    :param command: Command-object
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


async def build_episodes_list(limit: int) -> str:
    """
    Get the list of episodes as defined by limit and nicely format them to a message, displaying episodes and download status
    :param limit: days in the future to fetch calendar entries
    :return: the message listing the episodes, "" if no episodes found
    """

    if episodes := await get_calendar_episodes(limit):
        message: str = ""

        for episode in episodes:
            if episode['hasFile']:
                status_color = "green"
            else:
                status_color = "red"
            message += f"<font color=\"{status_color}\">{str(episode['series']['title'])} " \
                       f"{(str(episode['seasonNumber'])).zfill(2)}x{(str(episode['episodeNumber'])).zfill(2)} " \
                       f"{str(episode['title'])}</font>  \n"

        return message
    else:
        return ""


async def build_today_and_yesterday_list() -> str:
    """
    Get today's and yesterday's episodes and list them in a message, if there are any episodes for today
    :return: the message listign the episodes, "" if no episodes found
    """

    today_episodes: str = await build_episodes_list(0)
    if today_episodes != "":
        yesterday_episodes: str = await build_episodes_list(-1)

        if yesterday_episodes != "":
            return f"**Yesterday's episodes**  \n{yesterday_episodes}  \n  \n" \
                   f"**Today's episodes**  \n{today_episodes}"
        else:
            return f"**Today's episodes**  \n{today_episodes}"
    else:
        return ""


async def current_episodes_command(command):
    """
    Get the list of episodes for the current day and last day and post them to the configured room
    :param command: Command-object
    :return: -
    """

    message: str = await build_today_and_yesterday_list()

    if message != "":
        event_id: str = await plugin.reply(command, message)
        plugin.store_data("today_message", event_id)
    else:
        await plugin.reply_notice(command, "No episodes today, try `upcoming`")


async def current_episodes_timer(client):
    """
    Get the list of episodes for the current day and last day and post them to the configured room
    :param client: nio.AsyncClient
    :return: -
    """

    message: str = await build_today_and_yesterday_list()
    if message != "":
        # store event_id for later editing
        event_id = await plugin.message(client, plugin.read_config("room_id"), message)
        plugin.store_data("today_message", event_id)


async def update_current_episodes(client):
    """
    Check the list of current episodes for successful downloads and update the message accordingly
    :param client: nio.AsyncClient
    :return:
    """

    message: str = await build_today_and_yesterday_list()
    if message != "":
        await plugin.replace(client, plugin.read_config("room_id"), plugin.read_data("today_message"), message)


setup()
