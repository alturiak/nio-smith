from core.plugin import Plugin
import random
import os.path


async def spruch(command):
    with open(os.path.join(os.path.dirname(__file__), "spruchdb.txt")) as spruchdb:
        sprueche = spruchdb.readlines()

    message = random.choice(sprueche)
    await plugin.respond_message(command, message, delay=200)


plugin = Plugin("spruch", "General", "Plugin to provide a simple, randomized !spruch")
plugin.add_command("spruch", spruch, "famous quotes from even more famous people")
