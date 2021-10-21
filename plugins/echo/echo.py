from core.plugin import Plugin

plugin = Plugin("echo", "General", "A very simple Echo plugin")


def setup():
    plugin.add_command("echo", echo, "make someone agree with you for once")


async def echo(command):
    """Echo back the command's arguments"""
    response = " ".join(command.args)
    await plugin.respond_message(command, response)

setup()
