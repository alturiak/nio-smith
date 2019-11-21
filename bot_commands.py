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
#        else:
#            await self._unknown_command()

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
                    "`meter` - accurately measure someones somethingness  \n"
                    "`quote` - not implemented yet  \n"
                    "`spruch` - not implemented yet  \n"
                    "`oracle` - not implemented yet  "
                    )
        else:
            text = "Unknown help topic!"
        await send_text_to_room(self.client, self.room.room_id, text, notice=False)

    async def _meter(self):
        import random

        try:
            nick = self.args[0]
            meter_string = self.args[1]
            meter = " ".join(meter_string.split())
            dash_meter = "-".join(meter_string.split())
            meters = (
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#A9A9A9\">0</font>/10 " + nick + " is <font color=\"red\">never</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">1/</font>10 " + nick + " is just <font color=\"red\">barely</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">2/</font>/10 " + nick + " is <font color=\"red\">kinda</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#006400\">&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">3/</font>/10 " + nick + " is a <font color=\"red\">bit</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"#7FFF00\">4/</font>/10 " + nick + " is <font color=\"red\">sorta</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;</font><font color=\"#FF8C00\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">5</font>/10 " + nick + " is <font color=\"red\">basic average</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;</font><font color=\"#FF8C00\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">6</font>/10 " + nick + " is " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"yellow\">7</font>/10 " + nick + " is <font color=\"red\">fairly</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;</font><font color=\"#8B0000\">&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">8</font>/10 " + nick + " is <font color=\"red\">pretty darn</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;</font><font color=\"#8B0000\">&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">9</font>/10 " + nick + " is <font color=\"red\">extremely</font> " + meter,
                dash_meter + "-o-Meter <font color=\"#A9A9A9\">&#x2588;</font><font color=\"#7FFF00\">&#x2588;&#x2588;&#x2588;&#x2588;</font><font color=\"#FFFF00\">&#x2588;&#x2588;&#x2588;</font><font color=\"#FF0000\">&#x2588;&#x2588;&#x2588;</font><font color=\"#A9A9A9\">&#x2588;</font> <font color=\"red\">10</font>/10 " + nick + " is the " + meter + "est of all! " + nick + " scores a <font color=\"red\">perfect</font> 10 on the " + dash_meter + "-o-meter!! I bow to " + nick + "'s " + meter + "ness....",
            )
            chosen = random.choice(meters)
        except ValueError:
            chosen = "Syntax: !meter <target> <condition>"
        # await send_text_to_room(self.client, self.room.room_id, chosen)
        await send_text_to_room(self.client, self.room.room_id, chosen, notice=False)

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            f"Unknown command '{self.command}'. Try the 'help' command for more information.",
        )
