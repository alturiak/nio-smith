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
import plugins.translate
from fuzzywuzzy import fuzz
import operator


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

        commands_general = {
            "echo": plugins.echo.echo,
            "help": plugins.help.printhelp,
            "meter": plugins.meter.meter,
            "oracle": plugins.oracle.oracle,
            "pick": plugins.pick.pick,
            "roll": plugins.roll.roll,
            "sach": plugins.translate.switch,
            "spruch": plugins.spruch.spruch,
            "translate": plugins.translate.switch,
        }

        commands_rooms = {
            plugins.sabnzbdapi.room_id: {
                "last": plugins.sabnzbdapi.last,
                "resume": plugins.sabnzbdapi.resume,
                "delete": plugins.sabnzbdapi.delete,
                "purge": plugins.sabnzbdapi.purge,
            }
        }

        commandstart = self.command.split()[0].lower()
        commands = commands_general
        if self.room.room_id in commands_rooms:
            commands = {**commands, **commands_rooms[self.room.room_id]}

        try:
            # is this a secure thing to do in python?
            await commands[commandstart](self)
        except KeyError:
            ratios = {}
            for key in commands.keys():
                if fuzz.ratio(commandstart, key) > 60:
                    ratios[key] = fuzz.ratio(commandstart, key)
            try:
                if ratios:
                    await commands[max(ratios.items(), key=operator.itemgetter(1))[0]](self)
            except KeyError:
                pass
