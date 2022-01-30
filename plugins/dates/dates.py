# -*- coding: utf8 -*-
import random

from nio import AsyncClient, RoomMessageText

from core.plugin import Plugin
from typing import Dict, List
import datetime
from shlex import split
import logging
from dateparser import parse
from asyncio import sleep

logger = logging.getLogger(__name__)
plugin = Plugin("dates", "General", "Stores dates and birthdays, posts reminders")

celebratory_emoji: List[str] = [
    "🎉",
    "🎈",
    "🍺",
    "🎂",
    "🍾",
    "🍻",
    "🥂",
    "🍸",
    "🎊",
    "🧁",
    "🥳",
    "🎇",
    "🎆",
    "🍰",
    "🍹",
    "🍷",
    "👯",
    "🎁",
    "💐",
]


def setup():
    plugin.add_command("date", date, "Display the details of the next upcoming date or a specific date")
    plugin.add_command("date_add", date_add, "Add a date or birthday")
    plugin.add_command("date_del", date_del, "Delete a date or birthday", power_level=50)
    plugin.add_command("date_list", date_list, "Display a list of all stored dates")
    plugin.add_command("date_next", date_next, "Display details of the next upcoming date")
    plugin.add_command("date_show", date_show, "Display details of a specific date")
    plugin.add_timer(day_start, frequency="daily")


class StoreDate:
    def __init__(
        self,
        name: str,
        date: datetime.datetime,
        mx_room: str,
        date_type: str = "date",
        description: str = "",
        added_by: str or None = None,
        last_reminded: datetime.datetime or None = None,
    ):
        """
        A date, consisting of a name, a date and the type of date
        :param name: Name of the entry, either arbitrary text or a matrix username
        :param date: The actual date
        :param date_type: the type of date, currently either "date" or "birthday"
        :param description: a description of a date
        :param added_by: name of the person who added the date
        :param last_reminded: date of last posted reminder for the date
        """

        self.name: str = name
        self.date: datetime.datetime = date
        self.date_type: str = date_type
        self.description: str = description
        self.added_by: str or None = added_by
        self.mx_room: str = mx_room
        self.last_reminded: datetime.datetime or None = last_reminded
        self.id: str = generate_date_id(mx_room, name)

    async def is_today(self) -> bool:
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

    async def is_birthday_person(self, room_id: str, plaintext: str or None = "", formatted: str or None = "") -> bool:
        """
        Checks if a given plaintext or formatted text contain a birthday person
        :param room_id:
        :param plaintext:
        :param formatted:
        :return:
        """

        if await self.is_today() and self.date_type == "birthday" and self.mx_room == room_id:
            return (plaintext and self.description.lower() in plaintext.lower()) or (formatted and self.name.lower() in formatted.lower())
        else:
            return False

    async def needs_reminding(self) -> bool:
        """
        Checks if a reminder for a date still has to be posted today
        :return:    True, if date needs reminding (a reminder hasn't been posted yet)
                    False, if date doesn't need reminding (a reminder has already been posted)
        """

        if hasattr(self, "last_reminded") and self.last_reminded:
            return (self.last_reminded.date() < datetime.date.today()) or (
                self.date_type != "birthday" and datetime.datetime.now() > self.date > self.last_reminded
            )
        else:
            return True

    async def set_reminded(self):
        """
        Set the current timestamp as time of last reminder
        :return:
        """

        self.last_reminded = datetime.datetime.now()

    def __str__(self):

        return f"**Name:** {self.name}  \n" f"**Date:** {self.date}  \n" f"**Type:** {self.date_type}  \n" f"**Description:** {self.description}  \n"


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

    return await plugin.respond_notice(
        command,
        "Usage: `date_add <name or username> <date in most common formats> [description]`  \n"
        "Example: `date_add test tomorrow`  \n"
        'Example: `date_add test "in 28 days" "28 days later"`  \n'
        'Example: `date_add new_year 2021-01-01 "A new year"`  \n'
        'Example: `date_add start_of_unixtime "01.01.1970 00:00:00" The dawn of time`  \n'
        "Dates consisting of multiple words must be enclosed in quotes.",
    )


async def date(command):
    """
    Display the next or a specific date
    :param command:
    :return:
    """

    if len(command.args) == 0:
        await date_next(command)

    elif len(command.args) == 1:
        await date_show(command)

    else:
        await plugin.respond_notice(command, "Usage: `date [name or username]`")


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

    date: datetime.datetime or None = parse(args[0])

    if len(args) > 1:
        description: str = " ".join(args[1:])
    else:
        description: str = ""

    if date is None:
        await plugin.respond_notice(
            command,
            "Invalid date. Usage: `date_add <name or username> <date> [description]`",
        )
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "❌")
        return

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if await plugin.is_user_in_room(command.client, command.room.room_id, name, strictness="strict"):
        # add a birthday
        store_date: StoreDate = StoreDate(
            await plugin.get_mx_user_id(command.client, command.room.room_id, name),
            date,
            command.room.room_id,
            date_type="birthday",
            description=name,
        )

        if store_date.id in dates.keys():
            await plugin.respond_notice(
                command,
                f"Birthday for {await plugin.get_mx_user_id(command.client, command.room.room_id, name)} already stored as "
                f"{dates[store_date.id].date}, overwriting.",
            )

        dates[store_date.id] = store_date
        await plugin.store_data("stored_dates", dates)
        # if date is today, start a timer to post a reminder
        if await store_date.is_today() and not plugin.has_timer_for_method(post_reminders):
            plugin.add_timer(post_reminders, timer_type="dynamic")

        plugin.add_hook(
            "m.room.message",
            birthday_tada,
            room_id_list=[command.room.room_id],
            hook_type="dynamic",
        )
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "✅")

    else:
        # add a date
        store_date: StoreDate = StoreDate(name, date, command.room.room_id, description=description)

        if store_date.id in dates.keys():
            await plugin.respond_notice(
                command,
                f"Error: date {name} already exists:  \n" f"Date: {dates[store_date.id].date}  \n" f"Description: {dates[store_date.id].description}",
            )
        else:
            dates[store_date.id] = store_date
            await plugin.store_data("stored_dates", dates)
            # if date is today, start a timer to post a reminder
            if store_date.date.date() == datetime.date.today() and not plugin.has_timer_for_method(post_reminders):
                plugin.add_timer(post_reminders, timer_type="dynamic")
            await plugin.respond_notice(command, f"Date {store_date.name} added for {store_date.date}.")
            await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "✅")


async def date_del(command):
    """
    Delete a date
    :param command:
    :return:
    """

    if len(command.args) != 1:
        await plugin.respond_notice(command, "Usage: `date_del <name or username>`")
        return

    name: str = command.args[0]
    if await plugin.is_user_in_room(command.client, command.room.room_id, name):
        name = await plugin.get_mx_user_id(command.client, command.room.room_id, name)

    date_id: str = generate_date_id(command.room.room_id, name)

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if date_id in dates.keys():
        del dates[date_id]
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "✅")
    else:
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "❌")
    await plugin.store_data("stored_dates", dates)


async def date_show(command):
    """
    Display a specific date
    :param command:
    :return:
    """

    if len(command.args) != 1:
        await plugin.respond_notice(command, "Usage: `date_show <name or username>`")
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "❌")
        return

    name: str = command.args[0]
    if await plugin.is_user_in_room(command.client, command.room.room_id, name):
        name: str = await plugin.get_mx_user_id(command.client, command.room.room_id, name)

    date_id: str = generate_date_id(command.room.room_id, name)
    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")

    if dates is None:
        dates: Dict[str, StoreDate] = {}

    if date_id in dates.keys():
        store_date: StoreDate = dates[date_id]
        await plugin.respond_message(command, f"{store_date}")
    else:
        await plugin.respond_notice(command, f"Error: date {name} not found.")


async def date_next(command):
    """
    Display the next, upcoming date
    :param command:
    :return:
    """

    if len(command.args) > 0:
        await plugin.respond_notice(command, "Usage: `date_next`")
        return

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    sorted_dates: List[StoreDate] = sorted(dates.values(), key=lambda x: x.date)

    date: StoreDate
    for date in sorted_dates:
        # iterate through the sorted dates until we find the first upcoming date
        if date.mx_room and date.mx_room == command.room.room_id and date.date > datetime.datetime.now():
            await plugin.respond_message(command, f"{date}")
            return

    else:
        await plugin.respond_notice(command, f"No upcoming dates for this room.")


async def date_list(command):
    """
    Display a list of all dates
    :param command:
    :return:
    """

    if len(command.args) > 0:
        await plugin.respond_notice(command, "Usage: `date_list`")
        return

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    sorted_dates: List[StoreDate] = sorted(dates.values(), key=lambda x: x.date)

    date: StoreDate
    date_list: str = ""

    for date in sorted_dates:
        if date.mx_room and date.mx_room == command.room.room_id and date.date_type == "date":
            date_list += f"{date.date} - {date.name} - {date.description}  \n"

    if date_list:
        await plugin.respond_message(command, f"**All stored dates for this room**  \n" f"{date_list}")
    else:
        await plugin.send_reaction(command.client, command.room.room_id, command.event.event_id, "❌")


async def day_start(client):
    """
    Setup at the start of the day, clearing any expired timers and set up new ones if required
    :param client:
    :return:
    """

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    await plugin.clear_data("last_tada")
    # remove in_day_reminder if there are no events today
    plugin.del_timer(post_reminders)
    plugin.del_hook("m.room.message", birthday_tada)

    dates_today: bool = False
    birthdays_today: bool = False
    birthday_rooms_today: List[str] = []

    for store_date in dates.values():
        if await store_date.is_today():
            dates_today = True
            if store_date.date_type == "birthday":
                birthdays_today = True
                if store_date.mx_room not in birthday_rooms_today:
                    birthday_rooms_today.append(store_date.mx_room)

    if dates_today:
        if not plugin.has_timer_for_method(post_reminders):
            plugin.add_timer(post_reminders, timer_type="dynamic")

        if birthdays_today:
            plugin.add_hook(
                "m.room.message",
                birthday_tada,
                room_id_list=birthday_rooms_today,
                hook_type="dynamic",
            )


async def post_reminders(client):
    """
    Display dates for the current day at the start of each day
    :param client:
    :return:
    """

    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    if dates is None:
        dates: Dict[str, StoreDate] = {}

    store_date: StoreDate
    for store_date in dates.values():
        if await store_date.is_today() and await store_date.needs_reminding():
            if store_date.date_type == "birthday":
                user_link: str = await plugin.link_user(client, store_date.mx_room, store_date.description)
                message_id: str = await plugin.send_message(
                    client,
                    store_date.mx_room,
                    f"🎉 @room, it's {user_link}'s birthday! 🎉  \n",
                )

                # post 3 to 6 random emoji
                emoji_list: List[str] = random.sample(celebratory_emoji, random.randint(3, 6))
                emoji: str
                for emoji in emoji_list:
                    await plugin.send_reaction(client, store_date.mx_room, message_id, emoji)
                # sleep for 15 seconds to avoid being ratelimited if there's multiple birthdays
                await sleep(15)

            elif store_date.date_type == "date":
                if datetime.datetime.now() < store_date.date:
                    # date is in the future, post start of day reminder
                    await plugin.send_message(
                        client,
                        store_date.mx_room,
                        f"**Reminder:** {store_date.name} is today!  \n" f"**Date:** {store_date.date}  \n" f"**Description:** {store_date.description}",
                    )
                else:
                    # date is in the past, post alert
                    await plugin.send_message(
                        client,
                        store_date.mx_room,
                        f"**{store_date.name}** ({store_date.description}) is **now**!  \n",
                    )

            await store_date.set_reminded()
            await plugin.store_data("stored_dates", dates)


async def birthday_tada(client: AsyncClient, room_id: str, event: RoomMessageText):
    """
    Post a :tada: message when birthday person posts a message
    or someone mentions birthday person, not more than once every hour.
    :param client:
    :param room_id:
    :param event:
    :return:
    """

    # check if at least one hour has passed since last tada in the current room
    last_tada_dict: Dict[str, datetime.datetime] or None = await plugin.read_data("last_tada")
    if last_tada_dict is not None:
        last_tada: datetime.datetime or None = last_tada_dict.get(room_id)
        if last_tada is not None and last_tada > datetime.datetime.now() - datetime.timedelta(hours=1):
            return
    else:
        last_tada_dict: Dict[str, datetime.datetime] = {}

    # check if there are actual dates stored
    dates: Dict[str, StoreDate] = await plugin.read_data("stored_dates")
    if dates is None:
        return

    store_date: StoreDate
    for store_date in dates.values():

        if await store_date.is_birthday_person(room_id, formatted=event.sender) or await store_date.is_birthday_person(
            room_id, plaintext=event.body, formatted=event.formatted_body
        ):
            # sender is birthday person or birthday person is mentioned
            reactions: List[str] = ["🎉", "❄", "🎆"]
            await plugin.send_message(client, room_id, random.choice(reactions), markdown_convert=False)
            last_tada_dict[room_id] = datetime.datetime.now()
            await plugin.store_data("last_tada", last_tada_dict)
            break


setup()
