import io
import os.path
from os import remove, path
import pickle
from typing import List, Any, Dict, Callable, Union, Hashable, Tuple
import datetime

import requests
import yaml
from core.chat_functions import (
    send_text_to_room,
    send_reaction,
    send_replace,
    send_image,
)
from asyncio import sleep
import logging
from nio import (
    AsyncClient,
    JoinedMembersResponse,
    RoomMember,
    RoomSendResponse,
    RoomSendError,
    MatrixRoom,
)
from core.timer import Timer
from fuzzywuzzy import fuzz
import copy
import jsonpickle
import markdown
from PIL import Image

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, name: str, category: str, description: str):
        """
        commands (list[tuple]): list of commands in the form of (trigger: str, method: str, helptext: str)

        """
        self.category: str = category
        self.name: str = name
        self.description: str = description
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.timers: List[Timer] = []
        self.rooms: List[str] = []
        self.client: AsyncClient or None = None
        if path.isdir(f"plugins/{self.name}"):
            self.is_directory_based: bool = True
            self.basepath: str = f"plugins/{self.name}/{self.name}"
        else:
            self.is_directory_based: bool = False
            self.basepath: str = f"plugins/{self.name}"

        self.plugin_data_filename: str = f"{self.basepath}.pkl"
        self.plugin_dataj_filename: str = f"{self.basepath}.json"
        self.plugin_state_filename: str = f"{self.basepath}_state.json"
        self.config_items_filename: str = f"{self.basepath}.yaml"

        self.plugin_data: Dict[str, Any] = {}
        self.config_items: Dict[str, Any] = {}
        self.configuration: Union[Dict[Hashable, Any], list, None] = self.__load_config()
        logger.debug(f"{self.name}: Configuration loaded from file: {self.configuration}")

        self.add_config("doc_url", is_required=False)
        self.doc_url: str = self.read_config("doc_url")

    def _is_valid_for_room(self, room_id: str) -> bool:
        """
        Determine if at least one of the plugin's commands is allowed to be used in the given room
        :param room_id: room_id to check for
        :return:    True, if the plugin is allowed for the room
                    False, otherwise
        """

        if not self.rooms:
            return True
        else:
            command: PluginCommand
            for command in self.commands.values():
                if not command.room_id or command.room_id and room_id in command.room_id:
                    return True
            return False

    def _get_help_text(self):
        """
        Extract helptexts from commands

        :return:
        List[dict]: {command: helptext}
        """

        command_help: List[Dict] = []
        for command in self.commands:
            command_help.append({command[0]: command[2]})

        return command_help

    def add_command(self, command: str, method: Callable, help_text: str, room_id: List[str] = None, power_level: int = 0, command_type: str = "static"):
        """
        Adds a new command
        :param command: the actual name of the command, e.g. !help
        :param method: the method to be called when the command is received
        :param help_text: the command's helptext, e.g. as displayed by !help
        :param power_level: an optional matrix room power_level needed for users to be able to execute the command (defaults to 0, all users may execute the command)
        :param room_id: an optional room_id-list the command will be added on (defaults to none, command will be active on all rooms)
        :param command_type: the optional type of the command, currently "static" (default) or "dynamic"
        :return:
        """

        plugin_command = PluginCommand(command, method, help_text, power_level=power_level, room_id=room_id, command_type=command_type)
        if command not in self.commands.keys():
            self.commands[command] = plugin_command
            self.help_texts[command] = help_text
            # Add rooms from command to the rooms the plugin is valid for
            if room_id:
                for room in room_id:
                    if room not in self.rooms:
                        self.rooms.append(room)
            logger.debug(f"Added command {command} to rooms {room_id}")

            if command_type == "dynamic":
                self._save_state()
        else:
            logger.error(f"Error adding command {command} - command already exists")

    def del_command(self, command: str) -> bool:
        """
        Removes an active command if it's of type dynamic
        :param command: the actual name of the command
        :return:    True, if the command has been found and removed,
                    False, otherwise
        """

        command: str
        if command in self.commands.keys():
            if self.commands.get(command).command_type == "dynamic":
                del self.commands[command]
                self._save_state()
                return True
            else:
                logger.warning(f"Plugin {self.name} tried to remove static command {command}.")

        else:
            return False

    def _get_commands(self):
        """
        Extract called methods from commands

        :return:
        dict: {command: method}
        """

        return self.commands

    def add_hook(
        self,
        event_type: str,
        method: Callable,
        room_id_list: List[str] or None = None,
        event_ids: List[str] or None = None,
        hook_type: str = "static",
    ):
        """
        Hook into events defined by event_type with `method`.
        Will overwrite existing hooks with the same event_type and method.
        :param event_type: event-type to hook into, currently "m.reaction" and "m.room.message"
        :param method: method to be called when an event is received
        :param room_id_list: optional list of room_ids the hook is active on
        :param event_ids: optional list of event-ids, the hook is applicable for, currently only useful for "m.reaction"-hooks
        :param hook_type: the optional type of the hook, currently "static" (default) or "dynamic"
        :return:
        """

        if not self.has_hook(event_type, method, room_id_list=room_id_list):
            # a hook doesn't already exist for the same event_type, method and room_id_list

            if event_type not in self.hooks.keys():
                # no hooks for event_type, add an event_type and hook
                self.hooks[event_type] = [
                    PluginHook(event_type, method, room_id_list=copy.deepcopy(room_id_list), event_ids=copy.deepcopy(event_ids), hook_type=hook_type)
                ]

            else:
                hook: PluginHook
                for hook in self.hooks[event_type]:
                    if hook.method == method:
                        # hook exists for same event_type and method, adjust rooms if required
                        if room_id_list:
                            hook.room_id_list.extend(x for x in room_id_list if x not in hook.room_id_list)
                        break
                else:
                    # no hook for the given method, append a new hook
                    self.hooks[event_type].append(
                        PluginHook(
                            event_type,
                            method,
                            room_id_list=room_id_list,
                            event_ids=event_ids,
                            hook_type=hook_type,
                        )
                    )

            if hook_type == "dynamic":
                self._save_state()
            logger.debug(f"Added hook for event {event_type}, method {method} to rooms {room_id_list}")

    def _get_hooks(self):

        return self.hooks

    def del_hook(self, event_type: str, method: Callable, room_id_list: List[str] or None = None) -> bool:
        """
        Remove an active hook for the given event_type and method and an optional list of rooms
        :param event_type: event_type: event-type to hook into, currently "m.reaction" and "m.room.message"
        :param method: method to be called when an event is received
        :param room_id_list: list of room_ids to remove the hook from
        :return:    True, if hook for given event_type and method has been found and removed
                    False, otherwise
        """

        if self.has_hook(event_type, method, room_id_list=room_id_list):
            # there actually is a matching hook

            hook_removed: bool = False
            hooks = self.hooks
            hook: PluginHook
            for hook in hooks.get(event_type):
                if hook.method == method:
                    # hook exists for same event_type and method, adjust rooms if required
                    if hook.hook_type == "dynamic":
                        if not room_id_list or all(elem in room_id_list for elem in hook.room_id_list):
                            # completely remove the hook as no rooms have been supplied or all room_ids of the hook are to be removed
                            self.hooks[event_type].remove(hook)
                            hook_removed = True
                        else:
                            if not hook.room_id_list:
                                # hook is valid for all rooms, we can not remove a specific room
                                logger.error(f"Plugin {self.name} tried to remove a global hook for a specific room - this is not possible")
                            else:
                                # hook is valid for specific rooms, remove the given rooms from the hook
                                for room_id in room_id_list:
                                    if room_id in hook.room_id_list:
                                        hook.room_id_list.remove(room_id)

                                hook_removed = True

                    else:
                        logger.warning(f"Plugin {self.name} tried to remove static hook for {event_type}.")

            if hook_removed:
                self._save_state()
                logger.debug(f"Removed hook for event {event_type}, method {method}")
                return True

        else:
            return False

    def has_hook(self, event_type: str, method: Callable, room_id_list: List[str] or None = None) -> bool:
        """
        Check a hook exists for a given event_type, method and ALL given room_ids
        :param event_type: event_type: event-type to hook into, currently "m.reaction" and "m.room.message"
        :param method: method to be called when an event is received
        :param room_id_list: list of room_ids to remove the hook from
        :return:    True, if there are any timers for the given method
                    False, otherwise
        """

        plugin_hooks = self._get_hooks()
        plugin_hook: PluginHook

        if event_type in plugin_hooks.keys():
            for plugin_hook in plugin_hooks.get(event_type):
                if plugin_hook.method == method:
                    # found matching method, check rooms
                    if not plugin_hook.room_id_list:
                        # hook is valid for all rooms, we don't need to check supplied rooms
                        return True
                    else:
                        # hook has specified rooms, check if all of given room_id_list are contained
                        if not room_id_list or all(elem in plugin_hook.room_id_list for elem in room_id_list):
                            return True
                        else:
                            # hook is not valid for all given room-ids
                            return False
        else:
            return False

    def add_timer(
        self,
        method: Callable,
        frequency: str or datetime.timedelta or None = None,
        timer_type: str = "static",
    ):
        """

        :param method: the method to be called when the timer trigger
        :param frequency: frequency in which the timer should trigger
                can be:
                - datetime.timedelta: to specify timeperiods between triggers or
                - str:
                    - "weekly": run once a week roughly at Monday, 00:00
                    - "daily": run once a day roughly at midnight
                    - "hourly": run once an hour roughly at :00
                - None: triggers about every thirty seconds
        :param timer_type:
        :return:
        """

        self.timers.append(
            Timer(
                f"{self.name}.{method.__name__}",
                method,
                frequency=frequency,
                timer_type=timer_type,
            )
        )
        if timer_type == "dynamic":
            self._save_state()

    def _get_timers(self) -> List[Timer]:

        return self.timers

    def has_timer_for_method(self, method: Callable) -> bool:
        """
        Check if timers exist for a given method
        :param method: Callable to check for
        :return:    True, if there are any timers for the given method
                    False, otherwise
        """

        timer: Timer
        timers = self._get_timers()
        for timer in timers:
            if timer.method == method:
                return True
        return False

    def del_timer(self, method: Callable) -> bool:
        """
        Remove an existing timer, if it is of timer_type dynamic
        :param method:
        :return:
        """

        timer: Timer
        timers = self._get_timers()
        for timer in timers:
            if timer.method == method:
                if timer.timer_type == "dynamic":
                    self._get_timers().remove(timer)
                    self._save_state()
                    return True
                else:
                    logger.warning(f"Plugin {self.name} tried to remove static timer {timer.name}.")

        return False

    async def store_data(self, name: str, data: Any) -> bool:
        """
        Store data in plugins/<pluginname>.dill
        :param name: Name of the data to store, used as a reference to retrieve it later
        :param data: data to be stored
        :return:    True, if data was successfully stored
                    False, if data could not be stored
        """

        if data != self.plugin_data.get(name):
            self.plugin_data[name] = data
            return await self.__save_data_to_file()
        else:
            return True

    async def read_data(self, name: str) -> Any:
        """
        Read data from self.plugin_data
        :param name: Name of the data to be retrieved
        :return: the previously stored data
        """

        if name in self.plugin_data:
            return copy.deepcopy(self.plugin_data[name])
        else:
            return None

    async def clear_data(self, name: str) -> bool:
        """
        Clear a specific field in self.plugin_data
        :param name: name of the field to be cleared
        :return:    True, if successfully cleared
                    False, if name not contained in self.plugin_data or data could not be saved to disk
        """

        if name in self.plugin_data:
            del self.plugin_data[name]
            return await self.__save_data_to_file()
        else:
            return False

    async def backup_data(self) -> bool:
        """
        Create a backup file of the data currently stored by the plugin. This is not executed automatically and needs to be called by the plugin,
        preferably before executing potentially destructive operations
        :return:    True, if backup file was created successfully
                    False, otherwise
        """

        if self.plugin_data != {}:
            return await self.__save_data_to_json_file(
                self.plugin_data,
                f"{self.plugin_dataj_filename}.bak.{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
            )
        else:
            return False

    async def __load_pickle_data_from_file(self, filename: str) -> Dict[str, Any]:
        """
        Load data from a pickle-file
        :param filename: filename to load data from
        :return: loaded data
        """

        file = open(filename, "rb")
        data = pickle.load(file)
        file.close()
        return data

    async def __load_json_data_from_file(self, filename: str, convert: bool = False) -> Dict[str, Any]:
        """
        Load data from a json-file
        :param filename: filename to load data from
        :param convert: If data needs to be converted from single-file to directory-based
        :return: loaded data
        """

        file = open(filename, "r")
        json_data: str = file.read()
        if convert and f'"py/object": "plugins.{self.name}.{self.name}.' not in json_data:
            json_data = json_data.replace(
                f'"py/object": "plugins.{self.name}.',
                f'"py/object": "plugins.{self.name}.{self.name}.',
            )
        data = jsonpickle.decode(json_data)

        return data

    async def _load_data_from_file(self) -> Dict[str, Any]:
        """
        Load plugin_data from file
        :return: Data read from file to be loaded into self.plugin_data
        """

        plugin_data_from_json: Dict[str, Any] = {}
        plugin_data_from_pickle: Dict[str, Any] = {}
        abandoned_data: bool = False

        try:
            if os.path.isfile(self.plugin_dataj_filename):
                # local json data found, convert if needed
                plugin_data_from_json = await self.__load_json_data_from_file(self.plugin_dataj_filename, self.is_directory_based)
                if os.path.isfile(self.plugin_data_filename):
                    logger.warning(
                        f"Data for {self.name} read from {self.plugin_dataj_filename}, but {self.plugin_data_filename} still exists. After "
                        f"verifying, that {self.name} is running correctly, please remove {self.plugin_data_filename}"
                    )

            elif os.path.isfile(self.plugin_data_filename):
                # local pickle-data found
                logger.warning(f"Reading data for {self.name} from pickle. This should only happen once. Data will be stored in new format.")
                plugin_data_from_pickle = await self.__load_pickle_data_from_file(self.plugin_data_filename)

            else:
                # no local data found, check for abandoned data
                if self.is_directory_based:
                    abandoned_json_file: str = f"plugins/{self.name}.json"
                    if os.path.isfile(abandoned_json_file):
                        abandoned_data = True
                        logger.warning(f"Loading abandoned data for {self.name} from {abandoned_json_file}. This should only happen once.")
                        plugin_data_from_json = await self.__load_json_data_from_file(abandoned_json_file, convert=True)

        except Exception as err:
            logger.critical(f"Could not load plugin_data for {self.name}: {err}")
            return {}

        if abandoned_data:
            if "abandoned_json_file" in locals() and os.path.isfile(abandoned_json_file):
                logger.warning(f"You may remove {abandoned_json_file} now, it is no longer being used.")
            await self.__save_data_to_json_file(plugin_data_from_json, self.plugin_dataj_filename)

        if plugin_data_from_pickle != {} and not os.path.isfile(self.plugin_dataj_filename):
            logger.warning(f"Converting data for {self.name} to {self.plugin_dataj_filename}. This should only happen once.")
            if os.path.isfile(self.plugin_data_filename):
                logger.warning(f"You may remove {self.plugin_data_filename} now, it is no longer being used.")

        if plugin_data_from_pickle != {}:
            return plugin_data_from_pickle
        elif plugin_data_from_json != {}:
            return plugin_data_from_json
        else:
            return {}

    async def __save_data_to_pickle_file(self, data: Dict[str, Any], filename: str):
        """
        Save data to a pickle-file
        :param data: data to save
        :param filename: filename to save the data to
        :return:    True, if data stored successfully
                    False, otherwise
        """
        try:
            pickle.dump(data, open(filename, "wb"))
            return True
        except Exception as err:
            logger.critical(f"Could not write plugin_data to {self.plugin_data_filename}: {err}")
            return False

    async def __save_data_to_json_file(self, data: Dict[str, Any], filename: str):
        """
        Save data to a json file
        :param data: data to save
        :param filename: filename to save the data to
        :return:    True, if data stored successfully
                    False, otherwise
        """

        try:
            json_data = jsonpickle.encode(data)
            file = open(filename, "w")
            file.write(json_data)
            file.close()
            return True
        except Exception as err:
            logger.critical(f"Could not write plugin_data to {self.plugin_data_filename}: {err}")
            return False

    async def __save_data_to_file(self) -> bool:
        """
        Save modified plugin_data to disk
        :return:    True, if data stored successfully
                    False, otherwise
        """

        if self.plugin_data != {}:
            """there is actual data to save"""
            return await self.__save_data_to_json_file(self.plugin_data, self.plugin_dataj_filename)

        else:
            logger.debug("No data to save, remove datafiles")
            """no data to save, remove file"""
            if os.path.isfile(self.plugin_data_filename):
                try:
                    remove(self.plugin_data_filename)
                    return True
                except Exception as err:
                    logger.critical(f"Could not remove file {self.plugin_data_filename}: {err}")
                    return False

            if os.path.isfile(self.plugin_dataj_filename):
                try:
                    remove(self.plugin_dataj_filename)
                    return True
                except Exception as err:
                    logger.critical(f"Could not remove file {self.plugin_dataj_filename}: {err}")
                    return False

    async def __expandable_message_body(self, header: str, body: str) -> str:
        """
        Generate HTML-code for an expandable message body, used e.g. by
        - send_expandable_message
        - respond_expandable_message
        - send_expandable_notice
        - respond_expandable_notice
        :param header: the part of the message that is always displayed
        :param body: the part of the message that is only displayed after expanding it
        :return: expandable message
        """

        markdown_header: str = markdown.markdown(header)
        markdown_body: str = markdown.markdown(body)
        return f"<details><summary>{markdown_header}</summary><br>{markdown_body}</details>"

    async def send_message(
        self,
        client,
        room_id,
        message: str,
        expanded_message: str = "",
        delay: int = 0,
        markdown_convert: bool = True,
    ) -> str or None:
        """
        Send a message to a room, usually utilized by plugins to respond to commands
        :param client: AsyncClient used to send the message
        :param room_id: room_id to send to message to
        :param message: the actual message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :param delay: optional delay with typing notification, 1..1000ms
        :param markdown_convert: optional flag if content should be converted to markdown, defaults to True
        :return: the event_id of the sent message or None in case of an error
        """

        if delay > 0:
            if delay > 1000:
                delay = 1000

            await client.room_typing(room_id, timeout=delay)
            await sleep(float(delay / 1000))
            await client.room_typing(room_id, typing_state=False)

        if expanded_message:
            message = await self.__expandable_message_body(message, expanded_message)
        event_response: RoomSendResponse or RoomSendError = await send_text_to_room(client, room_id, message, notice=False, markdown_convert=markdown_convert)

        if isinstance(event_response, RoomSendResponse):
            return event_response.event_id
        else:
            logger.warning(f"Error sending {message} to {room_id}: {event_response}")
            return None

    async def respond_message(
        self,
        command,
        message: str,
        expanded_message: str = "",
        delay: int = 0,
        markdown_convert: bool = True,
    ) -> str or None:
        """
        Simplified version of self.send_message() to reply to commands
        :param command: the command object passed by the message we're responding to
        :param message: the actual message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :param delay: optional delay with typing notification, 1..1000ms
        :param markdown_convert: optional flag if content should be converted to markdown, defaults to True
        :return: the event_id of the sent message or None in case of an error
        """

        return await self.send_message(
            command.client,
            command.room.room_id,
            message,
            expanded_message=expanded_message,
            delay=delay,
            markdown_convert=markdown_convert,
        )

    async def message(self, client, room_id, message: str, delay: int = 0) -> str or None:
        """
        ** DEPRECATED ** Alias for send_message
        """
        logger.warning(f"Deprecated function 'message' used - use 'send_message' instead")
        return await self.send_message(client, room_id, message, delay=delay)

    async def reply(self, command, message: str, delay: int = 0) -> str or None:
        """
        ** DEPRECATED ** Alias for respond
        """
        logger.warning(f"Deprecated function 'reply' used - use 'respond_message' instead")
        return await self.respond_message(command, message, delay=delay)

    async def send_notice(
        self,
        client,
        room_id: str,
        message: str,
        expanded_message: str = "",
        markdown_convert: bool = True,
    ) -> str or None:
        """
        Send a notice to a room, usually utilized by plugins to post errors, help texts or other messages not warranting pinging users
        :param client: AsyncClient used to send the message
        :param room_id: room_id to send to message to
        :param message: the actual message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :param markdown_convert: optional flag if content should be converted to markdown, defaults to True
        :return: the event_id of the sent message or None in case of an error
        """

        if expanded_message:
            message = await self.__expandable_message_body(message, expanded_message)
        event_response: RoomSendResponse or RoomSendError = await send_text_to_room(client, room_id, message, notice=True, markdown_convert=markdown_convert)

        if isinstance(event_response, RoomSendResponse):
            return event_response.event_id
        else:
            logger.warning(f"Error sending {message} to {room_id}: {event_response}")
            return None

    async def respond_notice(
        self,
        command,
        message: str,
        expanded_message: str = "",
        markdown_convert: bool = True,
    ) -> str or None:
        """
        Simplified version of self.notice() to reply to commands
        :param command: the command object passed by the message we're responding to
        :param message: the actual message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :param markdown_convert: optional flag if content should be converted to markdown, defaults to True
        :return: the event_id of the sent message or None in case of an error
        """

        return await self.send_notice(
            command.client,
            command.room.room_id,
            message,
            expanded_message=expanded_message,
            markdown_convert=markdown_convert,
        )

    async def notice(self, client, room_id: str, message: str) -> str or None:
        """
        ** DEPRECATED ** Alias for send_notice
        """
        logger.warning(f"Deprecated function 'notice' used - use 'send_notice' instead")
        return await self.send_notice(client, room_id, message)

    async def reply_notice(self, command, message: str) -> str or None:
        """
        ** DEPRECATED ** Alias for respond_notice
        """
        logger.warning(f"Deprecated function 'reply_notice' used - use 'respond_notice' instead")
        return await self.respond_notice(command, message)

    async def replace_notice(
        self,
        client: AsyncClient,
        room_id: str,
        event_id: str,
        message: str,
        expanded_message: str = "",
    ) -> str or None:
        """
        Edits an event. send_replace() will check if the new content actually differs before really sending the replacement
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id of the original event
        :param event_id: (str) event_id to edit
        :param message: (str) the new message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :return:    (str) the event-id of the new room-event, if the original event has been replaced or
                    None, if the event has not been edited
        """

        if expanded_message:
            message = await self.__expandable_message_body(message, expanded_message)
        return await send_replace(client, room_id, event_id, message, message_type="m.notice")

    async def send_reaction(self, client, room_id: str, event_id: str, reaction: str):
        """
        React to a specific event
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id to send the reaction to (is this actually being used?)
        :param event_id: (str) event_id to react to
        :param reaction: (str) the reaction to send
        :return:
        """

        await send_reaction(client, room_id, event_id, reaction)

    async def react(self, client, room_id: str, event_id: str, reaction: str):
        """
        ** DEPRECATED ** Alias for send_redaction
        """
        logger.warning(f"Deprecated function 'react' used - use 'send_reaction' instead")
        await self.send_reaction(client, room_id, event_id, reaction)

    async def replace_message(
        self,
        client: AsyncClient,
        room_id: str,
        event_id: str,
        message: str,
        expanded_message: str = "",
    ) -> str or None:
        """
        Edits an event. send_replace() will check if the new content actualy differs before really sending the replacement
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id of the original event
        :param event_id: (str) event_id to edit
        :param message: (str) the new message
        :param expanded_message: an optional part of the message only visible after expanding the message (at least on Element Web)
        :return:    (str) the event-id of the new room-event, if the original event has been replaced or
                    None, if the event has not been edited
        """

        if expanded_message:
            message = await self.__expandable_message_body(message, expanded_message)
        return await send_replace(client, room_id, event_id, message, message_type="m.text")

    async def replace(self, client: AsyncClient, room_id: str, event_id: str, message: str) -> str or None:
        """
        ** DEPRECATED ** Alias for replace_message
        """
        logger.warning(f"Deprecated function 'replace' used - use 'replace_message' instead")
        return await self.replace_message(client, room_id, event_id, message)

    async def redact_message(self, client: AsyncClient, room_id: str, event_id: str, reason: str = ""):
        """
        Redact an event
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id to send the redaction to
        :param event_id: (str) event_id to redact
        :param reason: (str) optional reason for the redaction
        :return:
        """

        await client.room_redact(room_id, event_id, reason)

    async def message_redact(self, client: AsyncClient, room_id: str, event_id: str, reason: str = ""):
        """
        ** DEPRECATED ** Alias for redact_message
        """
        logger.warning(f"Deprecated function 'message_redact' used - use 'redact_message' instead")
        return await self.redact_message(client, room_id, event_id, reason)

    async def message_delete(self, client: AsyncClient, room_id: str, event_id: str, reason: str = ""):
        """
        ** DEPRECATED ** Alias for redact_message
        """
        logger.warning(f"Deprecated function 'message_delete' used - use 'redact_message' instead")
        await self.redact_message(client, room_id, event_id, reason)

    async def send_image(self, client: AsyncClient, room_id: str, image: Image):
        """
        Posts an image to the given room
        :param client:
        :param room_id:
        :param image:
        :return:
        """

        if image is not None:
            event_response: RoomSendResponse or RoomSendError = await send_image(client, room_id, image)

            if isinstance(event_response, RoomSendResponse):
                return event_response.event_id
            else:
                return None
        else:
            logger.warning(f"send_image called without valid image")
            return None

    async def is_user_in_room(
        self,
        client: AsyncClient,
        room_id: str,
        display_name: str,
        strictness: str = "loose",
        fuzziness: int = 75,
    ) -> RoomMember or None:
        """
        Try to determine if a diven displayname is currently a member of the room
        :param client: AsyncClient
        :param room_id: id of the room to check for a user
        :param display_name: displayname of the user
        :param strictness: how strict to match the nickname
                            strict: exact match
                            loose: case-insensitive match (default)
                            fuzzy: fuzzy matching
        :param fuzziness: if strictness == fuzzy, fuzziness determines the required percentage for a match
        :return:    RoomMember matching the displayname if found,
                    None otherwise
        """

        room_members: JoinedMembersResponse = await client.joined_members(room_id)
        room_member: RoomMember

        if strictness == "strict" or strictness == "loose":
            for room_member in room_members.members:

                if strictness == "strict":
                    if room_member.display_name == display_name:
                        return room_member

                else:
                    """loose matching"""
                    if room_member.display_name.lower() == display_name.lower():
                        return room_member
            else:
                return None

        else:
            """attempt fuzzy matching"""
            ratios: Dict[int, RoomMember] = {}
            for room_member in room_members.members:
                score: int = 0
                if room_member.display_name and (score := fuzz.ratio(display_name.lower(), room_member.display_name.lower())) >= fuzziness:
                    ratios[score] = room_member

            if ratios != {}:
                return ratios[max(ratios.keys())]
            else:
                return None

    async def is_user_id_in_room(self, client: AsyncClient, room_id: str, user_id: str) -> RoomMember or None:
        """
        Try to determine if a diven displayname is currently a member of the room
        :param client: AsyncClient
        :param room_id: id of the room to check for a user
        :param user_id: id of the user to check for
        :return:    RoomMember matching the user_id if found,
                    None otherwise
        """

        room_members: JoinedMembersResponse = await client.joined_members(room_id)
        room_member: RoomMember

        for room_member in room_members.members:
            if room_member.user_id == user_id:
                return room_member

        return None

    async def link_user(
        self,
        client: AsyncClient,
        room_id: str,
        display_name: str,
        strictness: str = "loose",
        fuzziness: int = 75,
    ) -> str:
        """
        Given a displayname and a command, returns a userlink
        :param client: AsyncClient
        :param room_id: id of the room
        :param display_name: displayname of the user
        :param strictness: how strict to match the nickname
                            strict: exact match
                            loose: case-insensitive match (default)
                            fuzzy: fuzzy matching
        :param fuzziness: if strictness == fuzzy, fuzziness determines the required percentage for a match
        :return:    string with the userlink-html-code if found,
                    given display_name otherwise
        """

        user: RoomMember
        if user := await self.is_user_in_room(client, room_id, display_name, strictness=strictness, fuzziness=fuzziness):
            return f'<a href="https://matrix.to/#/{user.user_id}">{user.display_name}</a>'
        else:
            return display_name

    async def link_user_by_id(self, client: AsyncClient, room_id: str, user_id: str) -> str:
        """
        Given a user_id, returns a userlink if the user has been found. Returns the unchanged user_id otherwise.
        :param client:
        :param room_id:
        :param user_id:
        :return:
        """

        user: RoomMember
        if user := await self.is_user_id_in_room(client, room_id, user_id):
            return f'<a href="https://matrix.to/#/{user.user_id}">{user.display_name}</a>'
        else:
            return user_id

    async def get_mx_user_id(
        self,
        client: AsyncClient,
        room_id: str,
        display_name: str,
        strictness="loose",
        fuzziness: int = 75,
    ) -> str or None:
        """
        Given a displayname and a command, returns a mx user id
        :param client:
        :param room_id:
        :param display_name: displayname of the user
        :param strictness: how strict to match the nickname
                            strict: exact match
                            loose: case-insensitive match (default)
                            fuzzy: fuzzy matching
        :param fuzziness: if strictness == fuzzy, fuzziness determines the required percentage for a match
        :return:    string with the user_id if found
                    None otherwise
        """

        user: RoomMember
        if user := await self.is_user_in_room(client, room_id, display_name, strictness=strictness, fuzziness=fuzziness):
            return user.user_id
        else:
            return None

    def add_config(self, config_item: str, default_value: Any = None, is_required: bool = False) -> bool:
        """
        Add a config value to be searched for in the plugin-specific configuration file upon loading, raise KeyError exception if required config_item can't be
        found
        :param config_item: the name of the configuration Item
        :param default_value: The value to use if the item is not specified in the configuration
        :param is_required: specify whether the configuration has to be present in the config-file for successful loading
        :return:    True, if the config_item is stored and not a duplicate
                    False, if the config_item already exists
        """

        if config_item in self.config_items.keys():
            logger.warning(f"{self.name}: Configuration item {config_item} has been defined already, new value not loaded.")
            return False
        else:
            # check for the value in configuration file and apply it if found
            if self.configuration and config_item in self.configuration.keys():
                logger.debug(f"{self.name}: add_config: Applying {config_item} from config-file. Value: {self.configuration.get(config_item)}")
                self.config_items[config_item] = self.configuration.get(config_item)
            # otherwise, apply default
            elif default_value is not None:
                logger.debug(f"{self.name}: add_config: {config_item} not found, setting to default-value {default_value}")
                self.config_items[config_item] = default_value

            # if no value and no default, but item is not required, set it to None
            elif not is_required:
                logger.debug(f"{self.name}: add_config: {config_item} not found, no default and not required, setting to None.")
                self.config_items[config_item] = None

            # no value, no default, and item is required
            else:
                err_str: str = f"Required configuration item {config_item} for plugin {self.name} could not be found"
                logger.warning(err_str)
                raise KeyError(err_str)

        return True

    def read_config(self, config_item: str) -> Any:
        """
        Read and return a specific value from the configuration
        If the actual value hasn't been read from the configuration, return the default value
        :param config_item: the name of the configuration item to look for
        :return:    The value of the requested config_item
                    None, if the value could not be found or does not have a default value defined
        """

        try:
            return copy.deepcopy(self.config_items[config_item])
        except KeyError:
            return None

    def __load_config(self) -> Union[Dict[Hashable, Any], list, None] or None:
        """
        Load the plugins configuration from a .yaml-file. The filename needs to match the plugins name
        e.g. the configuration for sample has to be provided in sample.yaml
        :return:    result of yaml.safe_load, if the config file has been successfully read
                    None, if there was an error reading the configuration
        """

        if path.exists(self.config_items_filename):
            try:
                with open(self.config_items_filename) as file_stream:
                    return yaml.safe_load(file_stream.read())
            except OSError as err:
                logger.info(f"Error loading {self.config_items_filename}: {format(err)}")
                return None
        else:
            return None

    def _save_state(self) -> bool:
        """
        Save dynamic commands, dynamic hooks and all timers to state file
        :return:
        """

        dynamic_commands: Dict[str, PluginCommand] = {}
        dynamic_hooks: Dict[str, List[PluginHook]] = {}

        command: PluginCommand
        for name, command in self._get_commands().items():
            if command.command_type == "dynamic":
                dynamic_commands[name] = command

        hooks_list: List[PluginHook]
        for event_type, hooks_list in self._get_hooks().items():
            hook: PluginHook
            for hook in hooks_list:
                if hook.hook_type == "dynamic":
                    if event_type in dynamic_hooks.keys():
                        dynamic_hooks.get(event_type).append(hook)
                    else:
                        dynamic_hooks[event_type] = [hook]

        plugin_state: Tuple[Dict, Dict, List] = (
            dynamic_commands,
            dynamic_hooks,
            self._get_timers(),
        )

        if plugin_state != ({}, {}, []):
            # we have an actual state to save
            try:
                json_data = jsonpickle.encode(plugin_state)
                file = open(self.plugin_state_filename, "w")
                file.write(json_data)
                file.close()
                return True
            except Exception as err:
                logger.critical(f"Could not write plugin_state to {self.plugin_state_filename}: {err}")
                return False
        else:
            # state is empty, remove file if it exists
            if os.path.isfile(self.plugin_state_filename):
                try:
                    remove(self.plugin_state_filename)
                    return True
                except Exception as err:
                    logger.critical(f"Could not remove file {self.plugin_state_filename}: {err}")
                    return False

    def _load_state(self):
        """
        Load dynamic commands, dynamic hooks and all timers from state file
        :return:
        """

        try:
            file = open(self.plugin_state_filename, "r")
            json_data: str = file.read()
            file.close()
        except Exception as err:
            logger.debug(f"Could not load plugin_state from {self.plugin_state_filename}: {err}")
            return

        dynamic_commands: Dict[str, PluginCommand]
        dynamic_hooks: Dict[str, PluginHook]
        timers: List[Timer]
        (dynamic_commands, dynamic_hooks, timers) = jsonpickle.decode(json_data)

        # add dynamic commands
        self.commands.update(dynamic_commands)

        # add dynamic hooks
        event: str
        hooks_list: List[PluginHook]
        for event, hooks_list in dynamic_hooks.items():
            if self.hooks.get(event):
                self._get_hooks()[event] += hooks_list
            else:
                self.hooks[event] = hooks_list

        # add last execution for static timers and all dynamic timers
        state_timer: Timer
        static_timer: Timer
        for state_timer in timers:
            for static_timer in self._get_timers():
                if static_timer.name == state_timer.name:
                    # update last execution from state, keep everything else
                    static_timer.last_execution = state_timer.last_execution
                    break

            else:
                # state_timer not found in static_timers, add if dynamic
                if state_timer.timer_type == "dynamic":
                    self.timers.append(state_timer)

    async def fetch_image_from_url(self, url: str) -> Image or None:
        """
        Try to get an image from the given url
        :param url: a url to an image
        :return:    Image-Object if successfully retrieved,
                    None otherwise
        """

        try:
            response = requests.get(url)
            image_bytes = io.BytesIO(response.content)
            return Image.open(image_bytes)
        except:
            return None

    async def get_rooms_for_server(self, client: AsyncClient, server_name: str) -> List[str]:
        """
        Get a list of rooms the bot shares with users of the given server
        :param client:
        :param server_name:
        :return:
        """

        room_list: Dict[str, MatrixRoom] = client.rooms
        shared_rooms: List[str] = []

        room: MatrixRoom
        for room in room_list.values():
            user_id: str
            for user_id in room.users:
                if server_name == user_id.split(":")[1] and room not in shared_rooms:
                    shared_rooms.append(room.room_id)

        return shared_rooms

    async def get_connected_servers(self, client: AsyncClient, room_id_list: List[str]) -> List[str]:
        """
        Get a list of connected servers for a list of rooms. Returns all connected servers if room_id_list is empty.
        :param room_id_list:
        :param client:
        :return:
        """

        connected_servers: List[str] = []

        if not room_id_list:
            room_id_list = list(client.rooms.keys())

        room_id: str
        for room_id in room_id_list:
            user_id: str
            for user_id in client.rooms[room_id].users:
                server_name: str = user_id.split(":")[1]
                if server_name not in connected_servers:
                    connected_servers.append(server_name)

        connected_servers.sort()
        return connected_servers

    async def get_users_on_servers(self, client: AsyncClient, home_servers: List[str], room_id_list: List[str]) -> Dict[str, List[str]]:
        """
        Get a list of users on a specific homeserver in a list of rooms. Returns all known users if room_id_list is empty.
        :param home_servers: the homeservers to test for
        :param client:
        :param room_id_list: List of rooms to check users in.
        :return:
        """

        home_server_users: Dict[str, List[str]] = {}
        if not room_id_list:
            room_id_list = list(client.rooms.keys())

        room_id: str
        for room_id in room_id_list:
            user_id: str
            for user_id in client.rooms[room_id].users:
                user_server_name: str = user_id.split(":")[1]
                if user_server_name in home_servers:
                    if user_server_name in home_server_users.keys():
                        if user_id not in home_server_users[user_server_name]:
                            home_server_users[user_server_name].append(user_id)
                    else:
                        home_server_users[user_server_name] = [user_id]

        return home_server_users

    def _set_client(self, client) -> None:
        """
        Set the bot's client instance
        :param client:
        :return:
        """
        self.client = client

    async def get_client(self) -> AsyncClient:
        """
        Get the bot's client instance
        :return:
        """

        return self.client


class PluginCommand:
    def __init__(
            self,
            command: str,
            method: Callable,
            help_text: str,
            power_level,
            room_id: List[str],
        command_type: str = "static",
    ):
        """
        Initialise a PluginCommand
        :param command: the actual command used to call the Command, e.g. "help"
        :param method: the method that's being called by the command
        :param help_text: the help_text displayed for the command
        :param power_level: an optional required power_level to execute the command
        :param room_id: an optional list of room_ids the command will be active on
        :param command_type: the optional type of the command, currently "static" (default) or "dynamic"
        """

        self.command: str = command
        self.method: Callable = method
        self.help_text: str = help_text
        self.power_level: int = power_level
        self.room_id: List[str] = room_id
        self.command_type: str = command_type

    def _is_valid_from_room(self, room_id: str) -> bool:
        """
        Check whether the command is valid for the given room
        :param room_id: room_id to check for
        :return:    True, if the command is allowed on the given room,
                    False, otherwise
        """

        return not self.room_id or room_id in self.room_id


class PluginHook:
    def __init__(
        self,
        event_type: str,
        method: Callable,
        room_id_list: List[str] = [],
        event_ids: List[str] = [],
        hook_type: str = "static",
    ):
        """
        Initialise a PluginHook
        :param event_type: the event_type the hook is being executed for
        :param method: the method that's being called when the hook is called
        :param room_id_list: an optional list of room_ids the hook should be active for
        :param event_ids: optional list of event-ids, the hook is applicable for, currently only useful for "m.reaction"-hooks
        :param hook_type: the optional type of the hook, currently "static" (default) or "dynamic"
        """
        self.event_type: str = event_type
        self.method: Callable = method
        self.room_id_list: List[str] = room_id_list
        self.event_ids: List[str] = event_ids
        self.hook_type: str = hook_type
