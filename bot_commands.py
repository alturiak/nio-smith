from chat_functions import send_text_to_room


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
        if self.command.startswith("echo"):
            await self._echo()
        elif self.command.startswith("help"):
            await self._show_help()
        elif self.command.startswith("meter"):
            await self._meter()
        else:
            await self._unknown_command()

    async def _echo(self):
        """Echo back the command's arguments"""
        response = " ".join(self.args)
        await send_text_to_room(self.client, self.room.room_id, response)

    async def _show_help(self):
        """Show the help text"""
        if not self.args:
            text = "Es gibt nichts zu sehen!"
            await send_text_to_room(self.client, self.room.room_id, text)
            return

        topic = self.args[0]
        if topic == "rules":
            text = "Clantag weg!"
        elif topic == "commands":
            text = ("#### Available commands:  \n"
                    "`meter` - work in progress  \n"
                    "`quote` - not implemented yet  \n"
                    "`spruch` - not implemented yet  \n"
                    "`oracle` - not implemented yet  "
                    )
        else:
            text = "Unknown help topic!"
        await send_text_to_room(self.client, self.room.room_id, text)

    async def _meter(self):
        import random

        try:
            nick = self.args[0]
            meter_string = self.args[1]
            meter = " ".join(meter_string.split())
            dash_meter = "-".join(meter_string.split())
            meters = (
                dash_meter + "-o-Meter \x0314\u2590\x02\x033\u2588\u2588\u2588\u2588\x037\u2588\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03140\x03/10 " + nick + " is <span style=\"color:red\">never</span> " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\x033\u2588\u2588\u2588\x037\u2588\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03091\x03/10 " + nick + " is just \x034barely\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\x033\u2588\u2588\x037\u2588\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03092\x03/10 " + nick + " is \x034kinda\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\x033\u2588\x037\u2588\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03093\x03/10 " + nick + " is a \x034bit\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x037\u2588\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03094\x03/10 " + nick + " is \x034sorta\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\x037\u2588\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03085\x03/10 " + nick + " is \x034basic average\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\u2588\x037\u2588\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03086\x03/10 " + nick + " is \x0304" + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\u2588\u2588\x037\x035\u2588\u2588\u2588\x02\x0314\u258C\x03 \x03087\x03/10 " + nick + " is \x034fairly\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\u2588\u2588\x037\x034\u2588\x035\u2588\u2588\x02\x0314\u258C\x03 \x03048\x03/10 " + nick + " is \x034pretty darn\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\u2588\u2588\x037\x034\u2588\u2588\x035\u2588\x02\x0314\u258C\x03 \x03049\x03/10 " + nick + " is \x034extremely\x03 " + meter,
                dash_meter + "-o-Meter \x0314\u2590\x02\x039\u2588\u2588\u2588\u2588\x038\u2588\u2588\u2588\x037\x034\u2588\u2588\u2588\x02\x0314\u258C\x03 \x030410\x03/10 " + nick + " is the " + meter + "est of all! " + nick + " scores a \x034perfect\x03 10 on the " + dash_meter + "-o-meter!! I bow to " + nick + "'s " + meter + "ness....",
            )
            chosen = random.choice(meters)
        except ValueError:
            chosen = "Syntax: !meter <target> <condition>"
        await send_text_to_room(self.client, self.room.room_id, chosen)

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            f"Unknown command '{self.command}'. Try the 'help' command for more information.",
        )
