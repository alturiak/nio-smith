# -*- coding: utf8 -*-
from __future__ import annotations
import datetime
from dateutil.parser import isoparse
import logging
from typing import Dict, List

import requests
from humanize import naturalsize
from nio import AsyncClient
from requests import Response

from core.bot_commands import Command
from core.plugin import Plugin

logger = logging.getLogger(__name__)
plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")

suppressed_series_attributes: List[str] = ['lastInfoSync', 'previousAiring']
suppressed_season_attributes: List[str] = []


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", is_required=True)
    plugin.add_config("series_tracking", is_required=False, default_value=True)

    plugin.add_command("series", print_series, "Get a list of currently tracked series", room_id=[plugin.read_config("room_id")])
    plugin.add_command("episodes", current_episodes, "Post a new message that is tracking episodes", room_id=[plugin.read_config("room_id")])

    # initially post current episodes at the start of the week
    plugin.add_timer(current_episodes, frequency="weekly")
    # check for updates to the episodes' status and update the message accordingly
    plugin.add_timer(update_current_episodes, frequency=datetime.timedelta(minutes=5))
    # check for changes to currently tracked series
    plugin.add_timer(check_series_changes, frequency="hourly")


class Season:
    def __init__(self, season_dict: Dict):
        self.seasonNumber: int = season_dict['seasonNumber']
        self.monitored: bool = season_dict['monitored']
        # self.previousAiring: datetime.datetime = datetime.datetime.fromisoformat(season_dict['statistics']['previousAiring'][:-1])
        self.episodeFileCount: int = season_dict['statistics']['episodeFileCount']
        self.episodeCount: int = season_dict['statistics']['episodeCount']
        self.totalEpisodeCount: int = season_dict['statistics']['totalEpisodeCount']
        self.sizeOnDisk: str = naturalsize(season_dict['statistics']['sizeOnDisk'])
        self.percentOfEpisodes: float = season_dict['statistics']['percentOfEpisodes']

    def __str__(self):
        return f"{self.seasonNumber}"

    async def get(self, attribute: str) -> any:
        """
        Get the current value of an attribute
        :param attribute:
        :return:
        """

        if attribute in self.__dict__.keys():
            return self.__dict__.get(attribute)
        else:
            return None

    async def compare(self, other_season: Season) -> List[str] or None:
        """
        Compare two seasons for differences in relevant attributes. Returns a list of attributes in which the compared seasons differ
        :param other_season:
        :return:
        """

        changed_attributes: List[str] = []

        for key in self.__dict__.keys():
            if key not in suppressed_season_attributes:
                if self.__dict__.get(key) != other_season.__dict__.get(key):
                    changed_attributes.append(key)

        if changed_attributes:
            return changed_attributes
        else:
            return None


class Series:
    def __init__(self, series_dict: Dict):
        self.title: str = series_dict['title']
        self.alternateTitles: List[Dict] = series_dict['alternateTitles']
        self.sortTitle: str = series_dict['sortTitle']
        self.seasonCount: int = series_dict['seasonCount']
        self.totalEpisodeCount: int = series_dict['totalEpisodeCount']
        self.episodeCount: int = series_dict['episodeCount']
        self.episodeFileCount: int = series_dict['episodeFileCount']
        self.sizeOnDisk: str = naturalsize(series_dict['sizeOnDisk'])
        self.status: str = series_dict['status']
        self.overview: str = series_dict['overview']
        try:
            self.previousAiring: datetime.datetime = isoparse(series_dict['previousAiring'])
        except KeyError:
            self.previousAiring: None = None
        self.network: str = series_dict['network']
        self.airTime: str = series_dict['airTime']
        self.images: List[Dict] = series_dict['images']
        self.year: datetime.date.year = series_dict['year']
        self.path: str = series_dict['path']
        self.profileId: int = series_dict['profileId']
        self.languageProfileId: int = series_dict['languageProfileId']
        self.seasonFolder: bool = series_dict['seasonFolder']
        self.monitored: bool = series_dict['monitored']
        self.useSceneNumbering: bool = series_dict['useSceneNumbering']
        self.runtime: int = series_dict['runtime']
        self.tvdbId: int = series_dict['tvdbId']
        self.tvRageId: int = series_dict['tvRageId']
        self.tvMazeId: int = series_dict['tvMazeId']
        self.firstAired: datetime.datetime = isoparse(series_dict['firstAired'])
        self.lastInfoSync: datetime.datetime = isoparse(series_dict['lastInfoSync'])
        self.seriesType: str = series_dict['seriesType']
        self.cleanTitle: str = series_dict['cleanTitle']
        self.imdbId: str = series_dict['imdbId']
        self.titleSlug: str = series_dict['titleSlug']
        try:
            self.certification: str = series_dict['certification']
        except KeyError:
            self.certification: None = None
        self.genres: List[str] = series_dict['genres']
        self.tags: List[int] = series_dict['tags']
        self.added: datetime.datetime = isoparse(series_dict['added'])
        self.ratings: Dict[str, any] = series_dict['ratings']
        self.qualityProfileId: int = series_dict['qualityProfileId']
        self.id: int = series_dict['id']

        self.seasons: List[Season] = [Season(x) for x in series_dict['seasons']]

    async def get(self, attribute: str) -> any:
        """
        Get the current value of an attribute
        :param attribute:
        :return:
        """

        if attribute in self.__dict__.keys():
            return self.__dict__.get(attribute)
        else:
            return None

    async def compare(self, other_series: Series) -> List[str] or None:
        """
        Compare two series for differences in relevant attributes. Returns a list of attributes in which the compared seasons differ
        :param other_series:
        :return:
        """

        changed_attributes: List[str] = []

        for key in self.__dict__.keys():
            if key == "seasons":
                season: Season
                other_season: Season
                for season in self.seasons:
                    for other_season in other_series.seasons:
                        if not await season.compare(other_season):
                            break
                    else:
                        if key not in changed_attributes:
                            changed_attributes.append(key)
                            break

            elif key not in suppressed_series_attributes:
                if self.__dict__.get(key) != other_series.__dict__.get(key):
                    if key not in changed_attributes:
                        changed_attributes.append(key)
        if changed_attributes:
            return changed_attributes
        else:
            return None


async def get_series_json() -> List[str] or None:
    """
    Retrieve currently tracked series from sonarr
    :return: (str) sorted JSON of currently tracked series
    """

    api_path = "/series"
    api_parameters = {"apikey": plugin.read_config("api_key")}

    try:
        shows: Response = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)
    except requests.exceptions.ConnectionError as err:
        logger.warning(f"Connection to sonarr failed: {err}")
        return

    if shows.status_code == 200:
        sorted_shows = sorted(shows.json(), key=lambda i: i['sortTitle'])
        return sorted_shows
    else:
        return None


async def check_series_changes(client):
    """

    :param client:
    :return:
    """

    change_message: str = ""

    tracked_series_json: List[Dict[str, any]] or None = await get_series_json()
    tracked_series_dict: Dict[str, Series] = {}
    stored_series_json: List[Dict[str, any]] = await plugin.read_data("stored_shows")
    stored_series_dict: Dict[str, Series] = {}

    if not stored_series_json:
        await plugin.store_data("stored_shows", tracked_series_json)
        return

    elif tracked_series_json:
        series_json: Dict[str, any]
        series: Series
        for series_json in tracked_series_json:
            series = Series(series_json)
            tracked_series_dict[series.titleSlug] = series

        for series_json in stored_series_json:
            series = Series(series_json)
            stored_series_dict[series.titleSlug] = series

        # tracked series retrieved and stored series present, check for differences
        for series in tracked_series_dict.values():
            if series.titleSlug not in stored_series_dict.keys():
                # tracked series not in stored series
                change_message += f"<li>Added <a href=\"https://www.imdb.com/title/{series.imdbId}\">{series.title}</a></li>  \n"

            else:
                stored_series: Series = stored_series_dict[series.titleSlug]
                changed_attributes: List[str] or None = await series.compare(stored_series)
                if changed_attributes:
                    # change to existing series detected
                    change_message += f"<li>Changed <a href=\"https://www.imdb.com/title/{series.imdbId}\">{series.title}</a>:  \n<ul>  \n"
                    changed_attribute: str
                    for changed_attribute in changed_attributes:

                        # check for changes in season and list each season's changes individually
                        # TODO: Refactoring
                        if changed_attribute == "seasons":
                            if len(stored_series.seasons) != len(series.seasons):
                                change_message += f"<li>Seasons: {len(stored_series.seasons)} ➡ {len(series.seasons)}"
                            else:
                                tracked_season: Season
                                stored_season: Season
                                i: int = 0
                                while i < len(series.seasons):
                                    tracked_season = series.seasons[i]
                                    stored_season = stored_series.seasons[i]
                                    changed_season_attributes: List[str] or None = await tracked_season.compare(stored_season)
                                    if changed_season_attributes:
                                        change_message += f"<li>Season {tracked_season}:<ul>"
                                        changed_season_attribute: str
                                        for changed_season_attribute in changed_season_attributes:
                                            change_message += f"<li>{changed_season_attribute}: {await stored_season.get(changed_season_attribute)} ➡️ " \
                                                              f"{await tracked_season.get(changed_season_attribute)}</li>\n"

                                        change_message += f"</ul></li>"
                                    i += 1

                        # list changed series attributes
                        else:
                            change_message += f"<li>{changed_attribute}: {await stored_series.get(changed_attribute)} ➡️ " \
                                              f"{await series.get(changed_attribute)}</li>\n"
                    change_message += "</ul></li>"

        for series in stored_series_dict.values():
            if series.titleSlug not in tracked_series_dict.keys():
                # stored series not in tracked series
                change_message += f"<li>Removed <a href=\"https://www.imdb.com/title/{series.imdbId}\">{series.title}</a><li>  \n"

        if change_message:
            change_message = f"**Changes to tracked series:**  \n<ul>{change_message}</ul>"
            await plugin.send_notice(client, plugin.read_config("room_id"), change_message)
            await plugin.store_data("stored_shows", tracked_series_json)


async def print_series(command):
    """
    Retrieves all currently tracked series from sonarr and puts out a table with the following details:
    Title, Seasons, Episodes on Disk, Size, Status, Rating
    :param command: Command-object
    :return:
    """

    shows: List[str] or None = await get_series_json()

    if shows:
        message = "<table><tr>"
        cols = ["Title", "Seasons", "Episodes on Disk", "Size", "Status", "Rating"]
        for col in cols:
            message = message + f"<td><b>{col}</b></td>"
        message = message + "</tr>"
        for show in shows:
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
        await plugin.respond_message(command, message)

    else:
        await plugin.respond_notice(command, f"Error retrieving series.")


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
    except requests.exceptions.ConnectionError as err:
        logger.warning(f"Connection to sonarr failed: {err}")
        return None

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
        event_id = await plugin.send_message(client, plugin.read_config("room_id"), message)
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
        message_id: str or None = await plugin.replace_message(client, plugin.read_config("room_id"), await plugin.read_data("today_message"), message)
        if not message_id:
            await current_episodes(client)
        else:
            await plugin.store_data("today_message_text", message)


setup()
