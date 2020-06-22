from plugin import Plugin
from chat_functions import send_typing
import random
import os.path


async def spruch(command):
    with open(os.path.join(os.path.dirname(__file__), "spruchdb.txt")) as spruchdb:
        sprueche = spruchdb.readlines()

    message = random.choice(sprueche)
    await send_typing(command.client, command.room.room_id, message)

plugin = Plugin("spruch", "General", "Plugin to provide a simple, randomized !spruch")
plugin.add_command("spruch", spruch, "famous quotes from even more famous people")
