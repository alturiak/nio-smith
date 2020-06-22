from typing import List, Callable


class PluginCommand:

    def __init__(self, command: str, method: Callable, help_text: str, room_id: List[str]):
        self.command: str = command
        self.method: Callable = method
        self.help_text: str = help_text
        self.room_id: List[str] = room_id
