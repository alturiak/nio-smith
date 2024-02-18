# -*- coding: utf8 -*-
from __future__ import annotations
import datetime
from dateutil.parser import isoparse
import logging
from typing import Dict, List, Tuple

import requests
from humanize import naturalsize
from nio import AsyncClient

from core.bot_commands import Command
from core.plugin import Plugin

logger = logging.getLogger(__name__)
plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")

suppressed_series_attributes: List[str] = [
    "lastInfoSync",
    "previousAiring",
    "episodeCount",
    "episodeFileCount",
    "sizeOnDisk",
    "runtime",
    "tag_ids",
    "qualityprofile_id",
    "images",
    "genres",
    "totalEpisodeCount",
]
suppressed_season_attributes: List[str] = ["percentOfEpisodes", "episodeFileCount", "totalEpisodeCount"]
debug: bool = False


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", is_required=True)
    plugin.add_config("series_tracking", is_required=False, default_value=True)

    plugin.add_command(
        "series",
        print_series,
        "Get a list of currently tracked series",
        room_id=[plugin.read_config("room_id")],
    )
    plugin.add_command(
        "episodes",
        current_episodes,
        "Post a new message that is tracking episodes",
        room_id=[plugin.read_config("room_id")],
    )

    # initially post current episodes at the start of the week
    plugin.add_timer(current_episodes, frequency="weekly")
    # check for updates to the episodes' status and update the message accordingly
    plugin.add_timer(update_current_episodes, frequency=datetime.timedelta(minutes=5))
    # check for changes to currently tracked series
    plugin.add_timer(check_series_changes, frequency="daily")


class QualityProfile:
    def __init__(self, qualityprofile_id: int, name: str):
        self.qualityprofile_id: int = qualityprofile_id
        self.name: str = name

    def __str__(self):
        return self.name

    def __ne__(self, other: QualityProfile) -> bool:
        return self.qualityprofile_id != other.qualityprofile_id


class Tag:
    def __init__(self, tag_id: int, label: str):
        self.tag_id: int = tag_id
        self.label: str = label

    def __str__(self):
        return self.label

    def __ne__(self, other: Tag) -> bool:
        return self.tag_id != other.tag_id


class Season:
    def __init__(self, season_dict: Dict):
        self.seasonNumber: int = season_dict.get("seasonNumber")
        self.monitored: bool = season_dict.get("monitored")
        self.previousAiring: datetime.datetime or None = None
        if season_dict.get("statistics").get("nextAiring"):
            self.nextAiring = isoparse(season_dict.get("statistics").get("nextAiring"))
        self.previousAiring: datetime.datetime or None = None
        if season_dict.get("statistics").get("previousAiring"):
            self.nextAiring = isoparse(season_dict.get("statistics").get("previousAiring"))
        self.episodeFileCount: int = season_dict.get("statistics").get("episodeFileCount")
        self.episodeCount: int = season_dict.get("statistics").get("episodeCount")
        self.totalEpisodeCount: int = season_dict.get("statistics").get("totalEpisodeCount")
        self.sizeOnDisk: int = season_dict.get("statistics").get("sizeOnDisk")
        self.releaseGroups: List[str] = season_dict.get("statistics").get("releaseGroups")
        self.percentOfEpisodes: float = season_dict.get("statistics").get("percentOfEpisodes")
        self.images: List[str] = season_dict.get("images")

    def __str__(self):
        return f"{self.seasonNumber}"

    def __ne__(self, other_season) -> bool:
        if self.list_diffs(other_season):
            return True
        else:
            return False

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

    def list_diffs(self, new_season: Season) -> List[str]:
        """
        Compare two seasons for differences in relevant attributes. Returns a list of attributes in which the compared seasons differ
        :param new_season:
        :return:
        """

        changed_attributes: List[str] = []

        for key in self.__dict__.keys():
            if key not in suppressed_season_attributes:
                if self.__dict__.get(key) != new_season.__dict__.get(key):
                    changed_attributes.append(key)

        return changed_attributes

    async def print_diff(self, new_season: Season) -> str:
        """

        :param new_season:
        :return:
        """

        change_message: str = ""
        changed_season_attributes: List[str] = self.list_diffs(new_season)
        for changed_season_attribute in changed_season_attributes:
            change_message += await print_diff(
                changed_season_attribute,
                await self.get(changed_season_attribute),
                await new_season.get(changed_season_attribute),
            )

        return change_message


class Series:
    def __init__(self, series_dict: Dict, tags: Dict[int, Tag], qualityprofiles: Dict[int, QualityProfile]):
        self.id: int = series_dict.get("id")
        self.title: str = series_dict.get("title")
        self.alternateTitles: List[Dict] or None = series_dict.get("alternateTitles")
        self.sortTitle: str or None = series_dict.get("sortTitle")
        self.status: str = series_dict.get("status")
        self.ended: bool = series_dict.get("ended")
        self.profileName: str = series_dict.get("profileName")
        self.overview: str = series_dict.get("overview")
        self.nextAiring: datetime.datetime or None
        if series_dict.get("nextAiring"):
            self.nextAiring = isoparse(series_dict.get("nextAiring"))
        self.previousAiring: datetime.datetime or None = None
        if series_dict.get("previousAiring"):
            self.previousAiring = isoparse(series_dict.get("previousAiring"))
        self.network: str = series_dict.get("network")
        self.airTime: str or None = series_dict.get("airTime")
        self.images: List[Dict] = series_dict.get("images")
        self.seasonCount: int or None = series_dict.get("seasonCount")
        self.totalEpisodeCount: int or None = series_dict.get("totalEpisodeCount")
        self.originalLanguage = series_dict.get("originalLanguage")
        self.remotePoster = series_dict.get("remotePoster")
        self.seasons: List[Season] = [Season(x) for x in series_dict["seasons"]]
        self.year: datetime.date.year = series_dict.get("year")
        self.path: str = series_dict.get("path")
        self.qualityprofile_id = series_dict.get("qualityProfileId")
        self.qualityProfile: QualityProfile = qualityprofiles[self.qualityprofile_id]
        self.seasonFolder: bool = series_dict.get("seasonFolder")
        self.monitored: bool = series_dict.get("monitored")
        self.monitorNewItems: str = series_dict.get("monitorNewItems")
        self.useSceneNumbering: bool = series_dict.get("useSceneNumbering")
        self.runtime: int = series_dict.get("runtime")
        self.tvdbId: int = series_dict.get("tvdbId")
        self.tvRageId: int = series_dict.get("tvRageId")
        self.tvMazeId: int = series_dict.get("tvMazeId")
        self.firstAired: datetime.datetime or None = None
        if series_dict.get("firstAired"):
            self.firstAired = isoparse(series_dict.get("firstAired"))
        self.lastAired: datetime.datetime or None = None
        if series_dict.get("lastAired"):
            self.lastAired = isoparse(series_dict.get("lastAired"))
        self.seriesType: str = series_dict.get("seriesType")
        self.cleanTitle: str = series_dict.get("cleanTitle")
        self.imdbId: str = series_dict.get("imdbId")
        self.titleSlug: str = series_dict.get("titleSlug")
        self.rootFolderPath: str = series_dict.get("rootFolderPath")
        self.folder: str = series_dict.get("folder")
        self.certification: str or None = series_dict.get("certification")
        self.genres: List[str] = series_dict.get("genres")
        self.tag_ids: List[int] = series_dict["tags"]
        self.tags: List[Tag] = []
        for tag_id in self.tag_ids:
            self.tags.append(tags[tag_id])
        self.added: datetime.datetime = isoparse(series_dict.get("added"))
        self.addOptions: List[any] or None = series_dict.get("addOptions")
        self.ratings: Dict[str, any] = series_dict.get("ratings")
        self.seasonCount: int = series_dict.get("statistics").get("seasonCount")
        self.episodeFileCount: int = series_dict.get("statistics").get("episodeFileCount")
        self.episodeCount: int = series_dict.get("statistics").get("episodeCount")
        self.totalEpisodeCount: int = series_dict.get("statistics").get("totalEpisodeCount")
        self.sizeOnDisk: int = series_dict.get("statistics").get("sizeOnDisk")
        self.releaseGroups: List[str] = series_dict.get("statistics").get("releaseGroups")

    def __str__(self):
        return self.title

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

    async def list_diffs(self, new_series: Series) -> List[str]:
        """
        Compare two series for differences in relevant attributes. Returns a list of attributes in which the compared seasons differ
        :param new_series:
        :return:
        """

        changed_attributes: List[str] = []

        for key in self.__dict__.keys():
            if key not in suppressed_series_attributes and key not in changed_attributes:
                if isinstance(self.__dict__.get(key), list) and key in [
                    "seasons",
                    "tags",
                ]:
                    if len(self.__dict__.get(key)) != len(new_series.__dict__.get(key)):
                        changed_attributes.append(key)
                    else:
                        i = 0
                        while i < len(self.__dict__.get(key)):
                            if self.__dict__.get(key)[i] != new_series.__dict__.get(key)[i]:
                                changed_attributes.append(key)
                                break
                            i += 1

                elif self.__dict__.get(key) != new_series.__dict__.get(key):
                    changed_attributes.append(key)

        return changed_attributes

    async def print_diff(self, new_series: Series) -> str:
        """

        :param new_series:
        :return:
        """

        change_message: str = ""
        changed_attributes: List[str] or None = await self.list_diffs(new_series)
        if changed_attributes:
            # change to existing series detected
            changed_attribute: str
            for changed_attribute in changed_attributes:
                if changed_attribute == "seasons":
                    i: int = 0
                    while i < len(self.seasons) and i < len(new_series.seasons):
                        season_change: str = await self.seasons[i].print_diff(new_series.seasons[i])
                        if season_change:
                            change_message += f"<li>Season {new_series.seasons[i]}:<ul>{season_change}</ul></li>"
                        i += 1

                elif changed_attribute == "tags":
                    old_tags: List[str] = [x.label for x in self.tags]
                    new_tags: List[str] = [x.label for x in new_series.tags]
                    change_message += await print_diff("Tags", old_tags, new_tags)

                # list changed series attributes
                else:
                    change_message += await print_diff(
                        changed_attribute,
                        await self.get(changed_attribute),
                        await new_series.get(changed_attribute),
                    )
        return change_message


class SeriesList:
    def __init__(
        self,
        series_json: List[Dict[str, any]],
        tags_json: List[Dict[str, any]],
            qualityprofiles_json: List[Dict[str, any]],
    ):
        """

        :param series_json:
        """

        self.series: Dict[str, Series] = {}
        tags: Dict[int, Tag] = {}
        tag_json: Dict[str, any]
        for tag_json in tags_json:
            tags[tag_json.get("id")] = Tag(tag_json.get("id"), tag_json.get("label"))

        qualityprofiles: Dict[int, QualityProfile] = {}
        qualityprofile_json: Dict[str, any]
        for qualityprofile_json in qualityprofiles_json:
            qualityprofiles[qualityprofile_json.get("id")] = QualityProfile(qualityprofile_json.get("id"),
                                                                            qualityprofile_json.get("name"))

        series: Series
        for show_json in series_json:
            series = Series(show_json, tags, qualityprofiles)
            self.series[series.titleSlug] = series

    def find_series_by_titleslug(self, titleSlug: str) -> Series or None:
        """

        :param titleSlug:
        :return:
        """

        try:
            return self.series[titleSlug]
        except KeyError:
            return None

    def find_series_by_seriesId(self, seriesId: int) -> Series or None:
        """

        :param seriesId:
        :return:
        """

        show: Series
        for show in self.series.values():
            if show.id == seriesId:
                return show
        else:
            return None

    async def list_diffs(self, new_series_list: SeriesList) -> Tuple[List[Series], List[Series], List[Series]] or None:
        """

        :param new_series_list:
        :return:
        """

        added_series: List[Series] = []
        removed_series: List[Series] = []
        changed_series: List[Series] = []

        series: Series
        for series in new_series_list.series.values():
            if series.titleSlug not in self.series.keys():
                added_series.append(series)

        for series in self.series.values():
            if series.titleSlug not in new_series_list.series.keys():
                removed_series.append(series)
            elif await series.list_diffs(new_series_list.series.get(series.titleSlug)):
                changed_series.append(series)

        if added_series or removed_series or changed_series:
            return (added_series, removed_series, changed_series)
        else:
            return None

    async def print_diff(self, new_series_list: SeriesList) -> str:
        """

        :param new_series_list:
        :return:
        """

        change_message: str = ""

        if await self.list_diffs(new_series_list):
            added_series: List[Series]
            removed_series: List[Series]
            changed_series: List[Series]
            (added_series, removed_series, changed_series) = await self.list_diffs(new_series_list)

            series: Series
            for series in added_series:
                change_message += f'<li>Added <a href="https://www.imdb.com/title/{series.imdbId}">{series.title}</a></li>'

            for series in removed_series:
                change_message += f'<li>Removed <a href="https://www.imdb.com/title/{series.imdbId}">{series.title}</a></li>'

            for series in changed_series:
                change_message += f'<li>Changed <a href="https://www.imdb.com/title/{series.imdbId}">{series.title}</a>:<ul>'
                change_message += await series.print_diff(new_series_list.series.get(series.titleSlug))
                change_message += "</ul></li>"
            change_message = f"<ul>{change_message}</ul>"

        return change_message

    async def print_html_table(self) -> str:
        """

        :return:
        """
        pass


async def print_diff(name: str, old_value: int or str, new_value: int or str) -> str:
    """

    :param name:
    :param old_value:
    :param new_value:
    :return:
    """

    sign: str = "➡"
    # make sure, old_value and new_value are not bool and are int or float
    if not (isinstance(old_value, bool) or isinstance(new_value, bool)) and (isinstance(old_value, (int, float)) and isinstance(new_value, (int, float))):
        if new_value > old_value:
            sign: str = "📈"
        elif old_value > new_value:
            sign: str = "📉"

    if name == "sizeOnDisk":
        old_value = naturalsize(old_value, binary=True)
        new_value = naturalsize(new_value, binary=True)

    return f"<li>{name}: {old_value} {sign} {new_value}</li>"


async def fetch_sonarr_api(api_path: str) -> List[str] or None:
    """

    :param api_path:
    :return:
    """
    api_parameters = {"apikey": plugin.read_config("api_key")}

    try:
        response: requests.Response = requests.get(plugin.read_config("api_base") + f"/{api_path}", params=api_parameters)
    except requests.exceptions.ConnectionError as err:
        logger.warning(f"Connection to sonarr failed: {err}")
        return None

    if response.status_code == 200:
        return response.json()
    else:
        return None


async def fetch_sonarr_data() -> Dict[str, List[Dict[str, any]]] or None:
    """
    Retrieve currently tracked series and other required data from sonarr
    :return: (str) sorted JSON of currently tracked series
    """

    series_json: List[Dict[str, any]] = sorted(await fetch_sonarr_api("series"), key=lambda i: i["sortTitle"])
    tags_json: List[Dict[str, any]] = await fetch_sonarr_api("tag")
    qualityprofiles_json: List[Dict[str, any]] = await fetch_sonarr_api("qualityprofile")

    if series_json and tags_json and qualityprofiles_json:
        return {
            "series_json": series_json,
            "tags_json": tags_json,
            "qualityprofiles_json": qualityprofiles_json,
        }
    else:
        return None


async def check_series_changes(client):
    """

    :param client:
    :return:
    """

    stored_series_json: List[Dict[str, any]] = await plugin.read_data("stored_shows")
    stored_tags_json: List[Dict[str, any]] = await plugin.read_data("stored_tags")
    stored_qualityprofiles_json: List[Dict[str, any]] = await plugin.read_data("stored_qualityprofiles")
    tracked_data: Dict[str, List[Dict[str, any]]] = await fetch_sonarr_data()

    if not stored_series_json or not stored_qualityprofiles_json:
        await plugin.store_data("stored_shows", tracked_data.get("series_json"))
        await plugin.store_data("stored_tags", tracked_data.get("tags_json"))
        await plugin.store_data("stored_qualityprofiles", tracked_data.get("qualityprofiles_json"))

    elif tracked_data:
        tracked_series: SeriesList = SeriesList(
            tracked_data.get("series_json"),
            tracked_data.get("tags_json"),
            tracked_data.get("qualityprofiles_json"),
        )
        stored_series: SeriesList = SeriesList(stored_series_json, stored_tags_json, stored_qualityprofiles_json)

        if await stored_series.list_diffs(tracked_series):
            change_message: str = f"{await stored_series.print_diff(tracked_series)}"
            if not debug:
                await plugin.send_notice(client, plugin.read_config("room_id"), change_message)
            else:
                print(change_message)

            await plugin.store_data("stored_shows", tracked_data.get("series_json"))
            await plugin.store_data("stored_tags", tracked_data.get("tags_json"))
            await plugin.store_data("stored_qualityprofiles", tracked_data.get("qualityprofiles_json"))


async def print_series(command):
    """
    Retrieves all currently tracked series from sonarr and puts out a table with the following details:
    Title, Seasons, Episodes on Disk, Size, Status, Rating
    :param command: Command-object
    :return:
    """

    shows: List[str] or None = (await fetch_sonarr_data())["series_json"]

    if shows:
        message = "<table><tr>"
        cols = ["Title", "Seasons", "Episodes on Disk", "Size", "Status", "Rating"]
        for col in cols:
            message = message + f"<td><b>{col}</b></td>"
        message = message + "</tr>"
        for show in shows:
            cols = [
                f"<a href=\"https://www.imdb.com/title/{show['imdbId']}\">{show['title']}</a>",
                f"{str(show['seasonCount'])}",
                f"{str(show['episodeCount'])}",
                f"{str(naturalsize(show['sizeOnDisk'], binary=True))}",
                f"{str(show['status'])}",
                f"{str(show['ratings']['value'])}",
            ]
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
    week_end: str = datetime.date.isoformat(datetime.date.today() + datetime.timedelta(days=7 - weekday))

    return week_start, week_end


async def get_calendar_episodes(start_date: str, end_date: str) -> list or None:
    """
    Get a list of episodes from the calendar between start_date and end_date
    :param start_date: start_date to get episodes for in datetime.date.isoformat
    :param end_date: end_date to get episodes for in datetime.date.isoformat
    :return: list of episodes (https://github.com/Sonarr/Sonarr/wiki/Calendar), sorted by airdate
    """

    api_path = "/calendar"
    api_parameters = {
        "apikey": plugin.read_config("api_key"),
        "start": start_date,
        "end": end_date,
    }
    try:
        response: requests.Response = requests.get(plugin.read_config("api_base") + api_path, params=api_parameters)
    except requests.exceptions.ConnectionError as err:
        logger.warning(f"Connection to sonarr failed: {err}")
        return None

    if response.status_code == 200:
        return sorted(response.json(), key=lambda i: i["airDateUtc"])
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

    tracked_data: Dict[str, List[Dict[str, any]]] = await fetch_sonarr_data()
    if (episodes := await get_calendar_episodes(start_date, end_date)) and (tracked_data := await fetch_sonarr_data()):
        tracked_series: SeriesList = SeriesList(
            tracked_data.get("series_json"),
            tracked_data.get("tags_json"),
            tracked_data.get("qualityprofiles_json")
        )

        episodes_by_day: Dict[str, List[any]] = {}

        for episode in episodes:

            day: str = datetime.datetime.fromisoformat(episode["airDateUtc"].rstrip("Z")).strftime("%A")
            if day not in episodes_by_day.keys():
                episodes_by_day[day] = [episode]
            else:
                episodes_by_day.get(day).append(episode)

        for day, episode_list in episodes_by_day.items():
            if day == datetime.datetime.today().strftime("%A"):
                message += f'**<font color="orange">{day}</font>**  \n'
            else:
                message += f"**{day}**  \n"

            for episode in episode_list:

                format_begin: str = ""
                format_end: str = ""

                if episode["hasFile"]:
                    format_begin = '<font color="green">✅ '
                    format_end = "</font>"
                elif datetime.datetime.fromisoformat(episode["airDateUtc"].rstrip("Z")) < datetime.datetime.now():
                    # airdate is in the past, mark file missing
                    format_begin = '<font color="red">❌ '
                    format_end = "</font>"
                else:
                    format_begin = '⌛️'

                message += (
                    f"{format_begin}{str(tracked_series.find_series_by_seriesId(episode['seriesId']))} "
                    f"S{str(episode['seasonNumber']).zfill(2)}E{str(episode['episodeNumber']).zfill(2)} "
                    f"{str(episode['title'])}{format_end}  \n"
                )
    else:
        message += f"such empty, much nothing.  \nvery sad."
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
        event_id = await plugin.send_notice(client, plugin.read_config("room_id"), message)
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
        message_id: str or None = await plugin.replace_notice(
            client,
            plugin.read_config("room_id"),
            await plugin.read_data("today_message"),
            message,
        )
        if not message_id:
            await current_episodes(client)
        else:
            await plugin.store_data("today_message_text", message)


setup()
