from typing import Dict, List
from pluginloader import PluginLoader
from plugin import Plugin
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

        self.pl = PluginLoader()
        # dictionary of commands and the method to call for each command
        self.commands: Dict[str, str] = {}

        # assemble all valid commands and their respective methods
        for plugin in self.pl.get_plugins():
            plugin_commands = plugin.get_commands()
            self.commands = {**self.commands, **plugin_commands}

    async def process(self):

        commandstart = self.command.split()[0].lower()

        # we might still need this later
        # commands = commands_general
        # if self.room.room_id in commands_rooms:
        #    commands = {**commands, **commands_rooms[self.room.room_id]}

        print(self.commands)
        print(commandstart)
        print(type(self.commands[commandstart]))

        try:
            # is this a secure thing to do in python?
            await self.commands[commandstart](self)

        # command could not be found, try fuzzy matching with scores > 60% and use the best match
        except KeyError:
            ratios = {}
            for key in self.commands.keys():
                if fuzz.ratio(commandstart, key) > 60:
                    ratios[key] = fuzz.ratio(commandstart, key)
            try:
                if ratios:
                    await self.commands[max(ratios.items(), key=operator.itemgetter(1))[0]](self)
            except KeyError:
                pass
