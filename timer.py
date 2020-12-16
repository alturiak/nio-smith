import datetime
from typing import List, Callable


class Timer:

    """
    A class for storing timers that call a specific method in a specified interval

    Attributes:
        name (str): the name of a timer, usually derived from the plugin that added it and the name of the method that is being called
        method (Callable): the method called when the timer is triggered
        last_execution (datetime.datetime): timestamp of the timer's last execution
        valid_frequencies (List[str]): List of valid hardcoded frequencies needed for special cases
        frequency (str or datetime.timedelta or None): the frequency in which the timer is allowed to trigger, None will allow the timer to trigger every
            time it is being called
    """

    def __init__(self, name: str, method: Callable, frequency: str or datetime.timedelta or None = None, last_execution: datetime.datetime or None = None):

        """
        Initialisation of a timer
        """
        self.name: str = name
        self.method: Callable = method
        self.last_execution: datetime.datetime or None = last_execution
        self.valid_frequencies: List[str] = ["weekly", "daily", "hourly"]

        if frequency is None or isinstance(frequency, datetime.timedelta) or (isinstance(frequency, str) and frequency in self.valid_frequencies):
            self.frequency: str or datetime.timedelta or None = frequency
        else:
            raise Exception

    async def should_trigger(self) -> bool:
        """
        Check if the timer should trigger, e.g. because the last_execution is further in the past than the defined frequency

        :return (bool): True if the conditions for triggering the timer are met. A timer that has never been triggered will always return True.
                        False if the conditions are not met.
        """

        # no frequency, always trigger
        if self.frequency is None:
            return True

        else:
            # timer has never been executed, always trigger
            if self.last_execution is None:
                return True

            else:
                # check hardcoded intervals
                if isinstance(self.frequency, str):
                    last_execution_date: datetime.date = self.last_execution.date()
                    last_execution_week: int = last_execution_date.isocalendar()[1]
                    last_execution_hour: int = self.last_execution.time().hour
                    current_week: int = datetime.datetime.today().isocalendar()[1]
                    current_hour: int = datetime.datetime.now().hour

                    if self.frequency == "weekly":
                        # triggers if week_numbers differ
                        if last_execution_week != current_week:
                            return True

                    elif self.frequency == "daily":
                        # triggers if day of month differs
                        if last_execution_date.day != datetime.datetime.today().day:
                            return True

                    elif self.frequency == "hourly":
                        # triggers if hour or day differ
                        if last_execution_hour != current_hour or last_execution_date.day != datetime.datetime.today().day:
                            return True

                # check timedelta intervals
                elif isinstance(self.frequency, datetime.timedelta):
                    if datetime.datetime.now() - self.last_execution > self.frequency:
                        return True

    async def trigger(self, client) -> bool:
        """
        Actually run the timer's stored method after checking if the timer should trigger
        :param client: (nio.AsyncClient) the bot's matrix client
        :return (bool): True if the conditions have been met and the timer has been triggered
                        False otherwise
        """

        if await self.should_trigger():
            await self.method(client)
            self.last_execution = datetime.datetime.now()
            return True

        else:
            return False
