# -*- coding: utf8 -*-
from plugin import Plugin
from typing import Dict, List
import dateparser
import datetime
from shlex import split

plugin = Plugin("dates", "General", "Stores dates and birthdays, posts reminders")


def setup():
    plugin.add_command("date_add", date_add, "Add a date or birthday")
    plugin.add_command("date_del", date_del, "Delete a date or birthday", power_level=50)
    plugin.add_command("date_show", date_show, "Display details of a specific date")
    plugin.add_timer(current_dates, frequency="daily")


class StoreDate:

    def __init__(self,
                 name: str,
                 date: datetime.datetime,
                 mx_room: str,
                 date_type: str = "date",
                 description: str = "",
                 added_by: str or None = None):
        """
        A date, consisting of a name, a date and the type of date
        :param name: Name of the entry, either arbitrary text or a matrix username
        :param date: The actual date
        :param date_type: the type of date, currently either "date" or "birthday"
        :param description: a description of a date
        """

        self.name: str = name
        self.date: datetime.datetime = date
        self.date_type: str = date_type
        self.description: str = description
        self.added_by: str or None = added_by
        self.mx_room: str = mx_room
        self.id: str = generate_date_id(mx_room, name)

    def is_today(self) -> bool:
        """
        Check if the date is happening today
        :return:
        """

        if self.date_type == "date":
            today = datetime.date.today()
            midnight = datetime.datetime.combine(today, datetime.datetime.min.time())
            tomorrow = datetime.datetime.combine(today, datetime.datetime.max.time())

            return midnight < self.date < tomorrow

        elif self.date_type == "birthday":
            return self.date.day == datetime.datetime.today().day and self.date.month == datetime.datetime.today().month


def generate_date_id(mx_room: str, name: str) -> str:
    """
    Generate a date-id from room-name and date-name
    :param mx_room: matrix room id
    :param name: name of the date
    :return: a combination of room-id and name
    """

    return f"{mx_room}::{name}"


async def reply_usage_message(command) -> str:
    """
    Reply with a detailed usage message
    :param command:
    :return:
    """

    return await plugin.reply_notice(command, "Usage: `date_add <name or username> <date in most common formats> [description]`  \n"
                                              "Example: `date_add test tomorrow`  \n"
                                              "Example: `date_add test \"in 28 days\" \"28 days later\"`  \n"
                                              "Example: `date_add new_year 2021-01-01 \"A new year\"`  \n"
                                              "Example: `date_add start_of_unixtime \"01.01.1970 00:00:00\" The dawn of time`  \n"
                                              "Dates consisting of multiple words must be enclosed in quotes.")


async def date_add(command):
    """
    Adds a date or a birthday to the database
    :param command: (Command) the command issued to the bot
    :return:
    """

    if len(command.args) < 2:
        await reply_usage_message(command)
        return

    name: str = command.args[0]
    # split remaining args by quoted substrings

    try:
        args: List[str] = split(" ".join(command.args[1:]))
    except Exception:
        await reply_usage_message(command)
        return

    date: datetime.datetime or None = dateparser.parse(args[0])

    if len(args) > 1:
        description: str = " ".join(args[1:])
    else:
        description: str = ""

    if date is None:
        await plugin.reply_notice(command, "Invalid date. Usage: `date_add <name or username> <date>")
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "❌")
        return

    dates: Dict[str, StoreDate] = plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if await plugin.is_user_in_room(command.client, command.room.room_id, name, strictness="strict"):
        # add a birthday
        store_date: StoreDate = StoreDate(await plugin.get_mx_user_id(command.client, command.room.room_id, name),
                                          date,
                                          command.room.room_id,
                                          date_type="birthday",
                                          description=name)

        if store_date.id in dates.keys():
            await plugin.reply_notice(command, f"Birthday for {await plugin.get_mx_user_id(command.client, command.room.room_id, name)} already stored as "
                                               f"{dates[store_date.id].date}, overwriting.")

        dates[store_date.id] = store_date
        plugin.store_data("stored_dates", dates)
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "✅")

    else:
        # add a date
        store_date: StoreDate = StoreDate(name,
                                          date,
                                          command.room.room_id,
                                          description=description)

        if store_date.id in dates.keys():
            await plugin.reply_notice(command, f"Error: date {name} already exists:  \n"
                                               f"Date: {dates[store_date.id].date}  \n"
                                               f"Description: {dates[store_date.id].description}")
        else:
            dates[store_date.id] = store_date
            plugin.store_data("stored_dates", dates)
            await plugin.react(command.client, command.room.room_id, command.event.event_id, "✅")


async def date_del(command):
    """
    Delete a date
    :param command:
    :return:
    """

    if len(command.args) != 1:
        await plugin.reply_notice(command, "Usage: `date_del <name or username>`")
        return

    name: str = command.args[0]
    if await plugin.is_user_in_room(command.client, command.room.room_id, name):
        name = await plugin.get_mx_user_id(command.client, command.room.room_id, name)

    date_id: str = generate_date_id(command.room.room_id, name)

    dates: Dict[str, StoreDate] = plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if date_id in dates.keys():
        del(dates[date_id])
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "✅")
    else:
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "❌")
    plugin.store_data("stored_dates", dates)


async def date_show(command):
    """
    Display a specific date
    :param command:
    :return:
    """

    if len(command.args) != 1:
        await plugin.reply_notice(command, "Usage: `date_show <name or username>`")
        await plugin.react(command.client, command.room.room_id, command.event.event_id, "❌")
        return

    name: str = command.args[0]
    if await plugin.is_user_in_room(command.client, command.room.room_id, name):
        name: str = await plugin.get_mx_user_id(command.client, command.room.room_id, name)

    date_id: str = generate_date_id(command.room.room_id, name)
    dates: Dict[str, StoreDate] = plugin.read_data("stored_dates")

    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if date_id in dates.keys():
        store_date: StoreDate = dates[date_id]
        await plugin.reply(command, f"Name: {store_date.name}  \n"
                                    f"Date: {store_date.date}  \n"
                                    f"Type: {store_date.date_type}  \n"
                                    f"Description: {store_date.description}  \n")
    else:
        await plugin.reply_notice(command, f"Error: date {name} not found.")


async def current_dates(client):
    """
    Display dates for the current day at the start of each day
    :param client:
    :return:
    """

    dates: Dict[str, StoreDate] = plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    store_date: StoreDate

    for store_date in dates.values():
        if store_date.is_today():
            if store_date.date_type == "birthday":
                user_link: str or None
                if (user_link := await plugin.link_user(client, store_date.mx_room, store_date.description)) is not None:
                    react_to: str = await plugin.message(client, store_date.mx_room, f"🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉  \n"
                                                                                     f"Everyone, it's {user_link}'s birthday!  \n"
                                                                                     f"This calls for a celebration in @room  \n"
                                                                                     f"🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉  \n")
                    await plugin.react(client, store_date.mx_room, react_to, "🎁")
                    await plugin.react(client, store_date.mx_room, react_to, "🍻")
                    await plugin.react(client, store_date.mx_room, react_to, "🥂")
                    await plugin.react(client, store_date.mx_room, react_to, "✨")
                    await plugin.react(client, store_date.mx_room, react_to, "🎈")
                    await plugin.react(client, store_date.mx_room, react_to, "🎊")

                else:
                    await plugin.message(client, store_date.mx_room, f"🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉  \n"
                                                                     f"Everyone, it's {store_date.description}'s birthday!  \n"
                                                                     f"This calls for a celebration in @room  \n"
                                                                     f"🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉  \n")

            elif store_date.date_type == "date:":
                await plugin.message(client, store_date.mx_room, f"Reminder: {store_date.name} is today!  \n"
                                                                 f"Date: {store_date.date}  \n"
                                                                 f"Description: {store_date.description}")

setup()
