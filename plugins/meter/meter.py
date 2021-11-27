from typing import Dict, List
from core.plugin import Plugin
import random


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


def build_block(color: str, inactive: bool = False) -> str:

    block: str = ""

    if not inactive:
        block = "&#x2593;"
    else:
        block = "&#x2592;"

    return f"<font color=\"{color}\">{block}</font>"


def build_gauge(level: int) -> str:

    left_frame: str = f"<font color=\"#A9A9A9\">&#x2590;</font>"
    right_frame: str = f"<font color=\"#A9A9A9\">&#x258C;</font>"

    gauge: str = left_frame
    for i in range(1, 11):
        if i <= level:
            # add active block
            gauge = gauge + build_block(get_level_color(i))
        else:
            # add inactive block
            gauge = gauge + build_block(get_level_color(i, True), True)
    gauge += right_frame

    return gauge


def get_comment(level: int, nick: str, condition: str) -> str:

    comments: Dict[int, str] = {
        0: f"<font color=\"red\">never</font> {condition}",
        1: f"just <font color =\"red\">barely</font> {condition}",
        2: f"<font color =\"red\">kinda</font> {condition}",
        3: f"a <font color=\"red\">bit</font> {condition}",
        4: f"<font color=\"red\">sorta</font> {condition}",
        5: f"<font color=\"red\">basic average</font> {condition}",
        6: condition,
        7: f"<font color=\"red\">fairly</font> {condition}",
        8: f"<font color=\"red\">pretty darn</font> {condition}",
        9: f"<font color=\"red\">extremely</font> {condition}",
        10: f"the {condition}est of all! {nick} scores a <font color=\"red\">perfect</font> 10 on the {condition.replace(' ', '-')}-o-meter!! I bow to {nick}'s"
            f" {condition}ness...",
    }

    return comments[level]


def display_level(level: int) -> str:

    if level > 0:
        return f"<font color =\"{get_level_color(level)}\">{str(level)}</font>/10"
    else:
        return f"{str(level)}/10"


async def meter(command):

    try:
        # try to build a userlink, if possible
        nick: str = await plugin.link_user(command.client, command.room.room_id, command.args[0])
        condition: str = " ".join(command.args[1:])

        if not condition:
            raise IndexError
        else:
            level: int = random.randint(0, 10)
            text: str = f"{condition.replace(' ', '-')}-o-Meter {build_gauge(level)} {display_level(level)} {nick} is " \
                        f"{get_comment(level, nick, condition)}"
            await plugin.respond_message(command, text, delay=200)

    except (ValueError, IndexError):

        await plugin.respond_notice(command, "Usage: `meter <target> <condition>`")


plugin = Plugin("meter", "General", "Plugin to provide a simple, randomized !meter")
plugin.add_command("meter", meter, "accurately measure someones somethingness")
