from chat_functions import send_typing
from plugin import Plugin
import random


async def meter(command):
    try:
        nick = command.args[0]
        condition = " ".join(command.args[1:])
        if not condition:
            chosen = "Syntax: `!meter <target> <condition>`"
        else:
            dash_condition = condition.replace(" ", "-")
            meters = (
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font "
                                 "color=\"#006400\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font "
                                 "color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font "
                                 "color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font "
                                 "color=\"#A9A9A9\">&#x2588;</font> <font color=\"#A9A9A9\">0</font>/10 " + nick + " "
                                                                                                                   "is <font color=\"red\">never</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">1</font>/10 " + condition + " is just <font color=\"red\">barely</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">2</font>/10 " + condition + " is <font color=\"red\">kinda</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">3</font>/10 " + condition + " is a <font color=\"red\">bit</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">4</font>/10 " + nick + " is <font color=\"red\">sorta</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">5</font>/10 " + nick + " is <font color=\"red\">basic average</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">6</font>/10 " + nick + " is " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">7</font>/10 " + nick + " is <font color=\"red\">fairly</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">8</font>/10 " + nick + " is <font color=\"red\">pretty darn</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">9</font>/10 " + nick + " is <font color=\"red\">extremely</font> " + condition,
                dash_condition + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">10</font>/10 " + nick + " is the " + condition + "est of all! " + nick + " scores a <font color=\"red\">perfect</font> 10 on the " + dash_condition + "-o-meter!! I bow to " + nick + "'s " + condition + "ness....",
            )
            chosen = random.choice(meters)

    except (ValueError, IndexError):
        chosen = "Syntax: `!meter <target> <condition>`"

    await send_typing(command.client, command.room.room_id, chosen)

plugin = Plugin("meter", "General", "Plugin to provide a simple, randomized !meter")
plugin.add_command("meter", meter, "accurately measure someones somethingness")
