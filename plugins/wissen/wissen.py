# -*- coding: utf8 -*-
import logging
import random
import os.path

from core.bot_commands import Command
from core.plugin import Plugin

logger = logging.getLogger(__name__)
plugin = Plugin("wissen", "Fun", "Post a random or specific entry of the database of useless knowledge.")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_command("wissen", wissen, "Post a random or specific entry of the database of useless knowledge.")


async def wissen(command: Command):
    """
    Post a random or specific entry of the database of useless knowledge
    :param command:
    :return:
    """

    with open(os.path.join(os.path.dirname(__file__), "wissen.txt")) as wissendb:
        wissen = wissendb.readlines()
    wissenanzahl = len(wissen)

    if len(command.args) == 1 and str(command.args[0]).isdigit():
        handle: int = command.args[0]

    elif len(command.args) == 0:
        handle: int = 0

    else:
        await plugin.respond_notice(command, "Usage: `wissen [index]`")
        return

    try:
        wissenindex = int(handle)
        if wissenindex < 1 or wissenindex > wissenanzahl:
            raise IndexError
        chosen = wissen[wissenindex - 1]
    except (ValueError, IndexError):
        chosen = random.choice(wissen)
        wissenindex = wissen.index(chosen) + 1
    ausgabe = "%s (%s/%s)" % (chosen.strip(), wissenindex, wissenanzahl)

    await plugin.respond_notice(command, ausgabe)


setup()
