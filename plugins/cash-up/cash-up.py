from types import AsyncGeneratorType
from core.plugin import Plugin
import logging



logger = logging.getLogger(__name__)
plugin = Plugin("cash-up", "General", "A very simple cash-up plugin to share expenses in a group")


def setup():
    # first command will be called when plugin name is called
    plugin.add_command("cash-up-help", help, "cash up help info text")
    plugin.add_command("cash-up-register", register, "Resets existing room DB and initializes all group members for sharing expenses. Usage `chash-up-register <user-name1> [<user1-percentage>], <user-name2> [<user2-percentage>], ...` [optional]")
    # cash-up-new-expense / cash-up-np Andra 5€

class Group:
    def __init__(self, room_id: str, payments):
        self.room_id = room_id
        self.payments = payments


    def reset_all_payments(self):
        # für alle payments
        # payment["expenses"] = 0


    def increase_expense(self, uid, new_expense):
        # find payment with uid
        # payment["expenses"] += new_expense



class Persistent_groups:
    def __init__(self):
        self.groups_per_room = []
    
    def create_new_group(self, new_group: Group):
        self.groups_per_room.append()

    def find_group(self, room_id):
        print()

    def update_group(self, room_id): # needed?
        print()
    
    def delete_group(self, room_id):
        print()

    def load(self):
        print("implement load from db file")
    
    def save(self):
        print("implement save to file")


async def help(command):
    """Echo back the command's arguments"""
    response = "this is some basic help text for the cash-up plugin"
    await plugin.reply(command, response)

async def register(command):
    """Register a set of people as a new group to share expenses"""
    if command.args:
        logger.debug(f"cash-up-register called with {command.args}")
        # cash-up-register called with ['Marius', '0,7;', 'Andrea', '0,3;']
        # db key: command.room.room_id

        # message: str = " ".join(command.args)
        # sample: Sample = Sample(message)
        # if await plugin.store_data("sample", sample):
        #     await plugin.reply_notice(command, f"Message \"{message}\" stored successfully")
        # else:
        #     await plugin.reply_notice(command, "Could not store message")
    else:
        await plugin.reply_notice(command, "No users provided for registration. You need to register at least two users: `chash-up-register <user-name1> [<user1-percentage>], <user-name2> [<user2-percentage>], ...` [optional]")
    response = "register response"
    await plugin.reply(command, response)

setup()
