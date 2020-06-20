# -*- coding: utf8 -*-
__description__ = "Pick a random item from a given list of items. The trigger is 'pick'."
__version__ = "1.0"
__author__ = "Dingo"

from plugin import Plugin
import re
import random
from chat_functions import send_typing


async def pick(command):

    message = " ".join(command.args)
    message = message.replace(" and say:", ":")
    try:
        pickstring, saystring = re.split(r": ", message, 1)
    except ValueError:
        pickstring = message
        saystring = None

    prepicks = [x.strip() for x in pickstring.split(",")]
    picks = []
    re_range = re.compile(r"^(-?\d+)\.\.(-?\d+)(;\d+)?$")
    for pick in prepicks:
        rangecheck = re_range.search(pick)
        if rangecheck:
            try:
                if rangecheck.group(1).startswith("0") or rangecheck.group(1).startswith("-0"):
                    fill_string = "%%0%ii" % len(rangecheck.group(1))
                else:
                    fill_string = "%i"
                start = int(rangecheck.group(1))
                stop = int(rangecheck.group(2))
                if rangecheck.group(3):
                    step = int(rangecheck.group(3)[1:])
                else:
                    step = 1
            except ValueError:
                picks.append(pick)
                continue
            if start > stop or abs((stop - start) / step) > 1024:
                picks.append(pick)
            else:
                picks.extend(fill_string % i for i in range(start, stop + 1, step))
        else:
            picks.append(pick)

    absurdity = random.randint(1, 100)
    if absurdity > 80:
        texts = (
            "The sources from beyond the grave say: %s",
            "Our computer simulation predicts %s! No warranty expressed or implied.",
            "Don't you worry about %s, let me worry about blank.",
            "%s? %S?? You're not looking at the big picture!",
            "Give me %s or give me death!",
            "Amy! I mean: %s!",
            "Once again, the conservative, sandwich-heavy %s pays off for the hungry investor.",
            "%s: style and comfort for the discriminating crotch.",
            "%s sounds interesting! No, that other word. Tedious!",
            "Good man. Nixon's pro-war and pro-%s.",
            "Doug & Carrie, Doug & Carrie, Doug & Carrie, Doug & Carrie! %s! %s! %s! %s!",
            "%u, %s is make-believe, like elves, gremlins, and eskimos.",
            "Weaseling out of %s is important to learn. It's what separates us from the animals ... except the weasel.",
            "Is %s too violent for children? Most people would say, 'No, of course not. Don't be ridiculous.' But one woman says, 'Yes.' %u.",
            "The dark side clouds everything. Impossible to see the future is... But I'm sure %s is in it!",
            "I spent 90% of my money on women and %s. The rest I wasted.",
            "As God once put it: let there be %s!",
            "%u, today is your day, %s is waiting, so get on your way.",
            "I've got four words for you: I! LOVE! THIS! %S! YEEEEEEEEEEEAAAS!!!",
            "Remember, a Jedi's strength flows from the Force. But beware. Anger, fear, %s. The dark side they are.",
            "Choose %s! Respect my authoritah!!",
            "%s: it's a privilege, not a right.",
            "Fear leads to Anger. Anger leads to Hate. Hate leads to %s.",
            "Drugs are for losers, and %s is for losers with big weird eyebrows.",
            "I heard %s makes you stupid. | <%u> No, I'm... doesn't!",
            "%s. Hell, it's about time!",
        )
    else:
        texts = (
            "The computer simulation recommends %s.",
            "Result: %s",
            "The answer is %s.",
            "Optimal choice: %s",
        )
    if saystring:
        if any(mark in saystring for mark in ("%s", "%S", "%n", "%N")):
            text = saystring
        else:
            text = "%s " + saystring
    else:
        if len(picks) == 1 and picks[0].lower() in ("flower", "nose", "fight", "a fight", "pocket", "lock"):
            onlypick = picks[0].lower()
            if onlypick == "flower":
                text = "%u picks a flower. As its sweet smell fills the channel, all chatter get +3 for saving throws on net splits."
            elif onlypick == "nose":
                text = "Eeeew! %u, do that somewhere private!"
            elif onlypick in ("fight", "a fight"):
                text = "%u starts a brawl in another channel. Only the quick reaction of fellow %c chatters saves the weakling from a gruesome fate."
            elif onlypick == "pocket":
                text = "Despite being amazingly clumsy, %u manages to pick the pocket of an innocent bystander. A used handkerchief is the reward."
            elif onlypick == "lock":
                text = "Lockpick required."
        else:
            text = random.choice(texts)
    chosen = random.choice(picks)
    if picks != [""]:
        msg = text
        # msg = msg.replace("%u", event.user)
        # msg = msg.replace("%c", str(event.channel))
        msg = msg.replace("%S", "**" + chosen.upper() + "**")
        msg = msg.replace("%s", "**" + chosen + "**")
        msg = msg.replace("%N", chosen.upper())
        msg = msg.replace("%n", chosen)
    else:
        return None

    await send_typing(command.client, command.room.room_id, msg)

plugin = Plugin("pick", "General", "Plugin to provide a simple, randomized !pick")
plugin.add_command("pick", pick, "aids you in those really important life decisions")

plugin = Plugin("pick", "General", "Plugin to provide a simple, randomized !pick")
plugin.add_command("pick", pick, "aids you in those really important life decisions")

plugin = Plugin("pick", "General", "Plugin to provide a simple, randomized !pick")
plugin.add_command("pick", pick, "aids you in those really important life decisions")

plugin = Plugin("pick", "General", "Plugin to provide a simple, randomized !pick")
plugin.add_command("pick", pick, "aids you in those really important life decisions")
