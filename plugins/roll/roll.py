# -*- coding: utf8 -*-
__description__ = "Roll one or more dice. The trigger is 'roll'."
__version__ = "1.1"
__author__ = "Dingo"

from plugin import Plugin
import random
from core.chat_functions import send_typing


async def roll(command):

    if not command.args:
        await send_typing(command.client, command.room.room_id, "No argument given.")
        return None
    try:
        number, rest = command.args[0].lower().split("d", 1)
        if number.strip() == "":
            number = 1
        else:
            number = abs(int(number.strip()))

        if rest.strip().startswith("0"):
            lowest_value = 0
        else:
            lowest_value = 1

        if "+" in rest:
            sides, modifier = rest.split("+", 1)
            if sides.strip() == "":
                sides = 6
            else:
                sides = abs(int(sides.strip()))
            modifier = int(modifier.strip())
        elif "-" in rest:
            sides, modifier = rest.split("-", 1)
            if sides.strip() == "":
                sides = 6
            else:
                sides = abs(int(sides.strip()))
            modifier = - int(modifier.strip())
        else:
            if rest.strip() == "":
                sides = 6
            else:
                sides = abs(int(rest.strip()))
            modifier = 0

    except ValueError:
        await send_typing(command.client, command.room.room_id, "Malformed argument! Use 1d6, 3d10 etc.")
        return None
    if number == 0 or sides == 0:
        await send_typing(command.client, command.room.room_id, "Number of dice or sides per die are zero! Please use only nonzero numbers.")
        return None
    random.seed()
    roll_list = []
    if number > 100000:
        await send_typing(command.client, command.room.room_id, "Number of dice too large! Try a more reasonable number. (5 digits are fine)")
        return None
    for _ in range(number):
        roll_list.append(random.randint(lowest_value, sides))
    if len(roll_list) > 50:
        result_list = "  <detailed list too large>"
    else:
        result_list = "  (" + " + ".join([str(x) for x in roll_list]) + ")"
    if len(result_list) > 200:
        result_list = "  <detailed list too large>"
    if len(roll_list) == 1:
        result_list = ""

    await send_typing(command.client, command.room.room_id, "**Result:** " + str(sum(roll_list) + modifier) + result_list)

plugin = Plugin("roll", "General", "Plugin to provide a simple, randomized !roll of dice")
plugin.add_command("roll", roll, "the dice giveth and the dice taketh away")
