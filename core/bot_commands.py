import re
from typing import List

from nio import AsyncClient, MatrixRoom, RoomMessageText


def _parse_args(input: str) -> List[str]:
    """splits arguments at spaces but keeps the argument as one if its encapsulated by quotes"""
    args_list = []
    for args in re.split(r'(["].+?["])', " ".join(input.split()[1:])):
        if re.match(r'["]', args):
            args_list.append(args.strip('"'))
        else:
            args_list.extend(args.split())
    return args_list


class Command(object):
    def __init__(self, client, store, config, command, room, event, plugin_loader):
        """A command made by a user

        Args:
            client (nio.AsyncClient): The client to communicate to matrix with

            store (Storage): Bot storage

            config (Config): Bot configuration parameters

            command (str): The command and arguments

            room (nio.rooms.MatrixRoom): The room the command was sent in

            event (nio.events.room_events.RoomMessageText): The event describing the command
        """
        self.client: AsyncClient = client
        self.store = store
        self.config = config
        self.command = command
        self.room: MatrixRoom = room
        self.event: RoomMessageText = event
        self.args = _parse_args(self.command)
        self.plugin_loader = plugin_loader
