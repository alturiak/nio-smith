from plugin import Plugin

plugin = Plugin("cash-up", "General", "A very simple cash-up plugin to share expenses in a group")


def setup():
    # first command will be called when plugin name is called
    plugin.add_command("cash-up-help", help, "cash up help info text")
    plugin.add_command("cash-up-echo", echo, "cash up test echo command")


async def help(command):
    """Echo back the command's arguments"""
    response = "this is some basic help text for the cash-up plugin"
    await plugin.reply(command, response)

async def echo(command):
    """Echo back the command's arguments"""
    response = " ".join(command.args)
    await plugin.reply(command, response)

setup()
