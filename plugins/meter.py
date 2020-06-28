from chat_functions import send_typing, send_text_to_room
from plugin import Plugin
import random

from typing import Dict, List, TYPE_CHECKING
if TYPE_CHECKING:
    from bot_commands import Command


def get_level_color(level: int, inactive: bool = False) -> str:

    # active and inactive color values for each value
    colors: Dict[int, List[str]] = {
        0: ["", ""],
        1: ["#7FFF00", "#006400"],
        2: ["#7FFF00", "#006400"],
        3: ["#7FFF00", "#006400"],
        4: ["#7FFF00", "#006400"],
        5: ["#FFFF00", "#604000"],
        6: ["#FFFF00", "#604000"],
        7: ["#FFFF00", "#604000"],
        8: ["#FF0000", "#8B0000"],
        9: ["#FF0000", "#8B0000"],
        10: ["#FF0000", "#8B0000"]
    }

    return colors[level][inactive]


def get_comment(level: int, nick: str, condition: str) -> str:

    comments: Dict[int, str] = {
        0: "<font color=\"red\">never</font> " + condition,
        1: "just <font color =\"red\">barely</font> " + condition,
        2: "<font color =\"red\">kinda</font> " + condition,
        3: "a <font color=\"red\">bit</font> " + condition,
        4: "<font color=\"red\">sorta</font> " + condition,
        5: "<font color=\"red\">basic average</font> " + condition,
        6: condition,
        7: "<font color=\"red\">fairly</font> " + condition,
        8: "<font color=\"red\">pretty darn</font> " + condition,
        9: "<font color=\"red\">extremely</font> " + condition,
        10: "the " + condition + "est of all! " + nick + " scores a <font color=\"red\">perfect</font> 10 on "
            "the " + condition.replace(" ", "-") + "-o-meter!! I bow to " + nick + "'s " + condition + "ness...",
    }

    return comments[level]


def build_block(color: str) -> str:

    return "<font color=\"" + color + "\">&#x2588;</font>"


def build_gauge(level: int) -> str:
    frame: str = build_block("#A9A9A9")
    gauge: str = frame
    for i in range(1, 11):
        if i <= level:
            # add active block
            gauge = gauge + build_block(get_level_color(i))
        else:
            # add inactive block
            gauge = gauge + build_block(get_level_color(i, True))

    gauge = gauge + frame
    return gauge


async def meter(command: Command):

    try:
        nick = command.args[0]
        condition = " ".join(command.args[1:])
        if not condition:
            raise IndexError
        else:
            level: int = random.randint(0, 10)
            text: str = condition.replace(" ", "-") + "-o-Meter " + build_gauge(level) + " <font color=\"" + \
                get_level_color(level) + "\">" + str(level) + "</font>/10 " + nick + " is " + \
                get_comment(level, nick, condition)
            await send_typing(command.client, command.room.room_id, text)

    except (ValueError, IndexError):

        await send_text_to_room(command.client, command.room.room_id, "Usage: `meter <target> <condition>`")


plugin = Plugin("meter", "General", "Plugin to provide a simple, randomized !meter")
plugin.add_command("meter", meter, "accurately measure someones somethingness")
