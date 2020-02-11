# import plugins
# TODO: this should at some point feature dynamic imports
# https://www.bnmetrics.com/blog/dynamic-import-in-python3
import plugins.echo
import plugins.help
import plugins.meter
import plugins.oracle
import plugins.spruch
import plugins.roll
import plugins.pick
import plugins.sabnzbdapi


class Command(object):
    def __init__(self, client, store, config, command, room, event):
        """A command made by a user

        Args:
            client (nio.AsyncClient): The client to communicate to matrix with

            store (Storage): Bot storage

            config (Config): Bot configuration parameters

            command (str): The command and arguments

            room (nio.rooms.MatrixRoom): The room the command was sent in

            event (nio.events.room_events.RoomMessageText): The event describing the command
        """
        self.client = client
        self.store = store
        self.config = config
        self.command = command
        self.room = room
        self.event = event
        self.args = self.command.split()[1:]

    async def process(self):
        """Process the command"""

        """general commands"""
        if self.command.startswith("echo"):
            await plugins.echo.echo(self)
        elif self.command.startswith("help"):
            await plugins.help.printhelp(self)
        elif self.command.startswith("meter"):
            await plugins.meter.meter(self)
        elif self.command.startswith("oracle"):
            await plugins.oracle.oracle(self)
        elif self.command.startswith("pick"):
            await plugins.pick.pick(self)
        elif self.command.startswith("roll"):
            await plugins.roll.roll(self)
        elif self.command.startswith("spruch"):
            await plugins.spruch.spruch(self)
        else:
            """room-specific commands"""
            if self.room.room_id == plugins.sabnzbdapi.room_id:
                if self.command.startswith("last"):
                    await plugins.sabnzbdapi.last(self)
                elif self.command.startswith("resume"):
                    await plugins.sabnzbdapi.resume(self)
                elif self.command.startswith("delete"):
                    await plugins.sabnzbdapi.delete(self)
                elif self.command.startswith("purge"):
                    await plugins.sabnzbdapi.purge(self)
