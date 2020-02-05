from chat_functions import send_text_to_room
import random


async def meter(command):

    # do not enable for rooms with irc-bridge
    if command.room.room_id not in ["!hIWWJKHWQMUcrVPRqW:pack.rocks", "!MhEYjKIkPbppBXWEdQ:pack.rocks"]:
        try:
            nick = command.args[0]
            meter_string = command.args[1]
            meter = " ".join(meter_string.split())
            dash_meter = "-".join(meter_string.split())
            meters = (
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#A9A9A9\">0</font>/10 " + nick + " is <font color=\"red\">never</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">1</font>/10 " + nick + " is just <font color=\"red\">barely</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">2</font>/10 " + nick + " is <font color=\"red\">kinda</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">3</font>/10 " + nick + " is a <font color=\"red\">bit</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">4</font>/10 " + nick + " is <font color=\"red\">sorta</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;</font><font color=\"#604000\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">5</font>/10 " + nick + " is <font color=\"red\">basic average</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;</font><font color=\"#604000\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">6</font>/10 " + nick + " is " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">7</font>/10 " + nick + " is <font color=\"red\">fairly</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">8</font>/10 " + nick + " is <font color=\"red\">pretty darn</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">9</font>/10 " + nick + " is <font color=\"red\">extremely</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">10</font>/10 " + nick + " is the " + meter + "est of all! " + nick + " scores a <font color=\"red\">perfect</font> 10 on the " + dash_meter + "-o-meter!! I bow to " + nick + "'s " + meter + "ness....",
            )
            chosen = random.choice(meters)
        except ValueError:
            chosen = "Syntax: !meter <target> <condition>"
        await send_text_to_room(command.client, command.room.room_id, chosen, notice=False)
        print("Plugin meter called on " + command.room.room_id)
