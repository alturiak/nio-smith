# -*- coding: utf8 -*-
from plugin import Plugin
import requests
import humanize

plugin = Plugin("sonarr", "TV-Shows", "Provides commands to query sonarr's API")


def setup():
    plugin.add_config("api_base", is_required=True)
    plugin.add_config("api_key", is_required=True)
    plugin.add_config("room_id", None, is_required=False)
    plugin.add_command("series", series, "Get a list of currently tracked series", room_id=[plugin.read_config("room_id")])


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

setup()
