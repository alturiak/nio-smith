# importing nio-stuff
from types import AsyncGeneratorType
from core.plugin import Plugin
import logging

# importing cash up stuff
# functools for reduce()
import functools

# importing regular expressions for parsing numbers
import re


logger = logging.getLogger(__name__)
plugin = Plugin("cash-up", "General", "A very simple cash-up plugin to share expenses in a group")


def setup():
    # first command will be called when plugin name is called
    plugin.add_command("cash-up-help", help, "cash up help info text")
    plugin.add_command("cash-up-register", register, "Resets existing room DB and initializes all group members for sharing expenses.")
    plugin.add_command("cash-up-add-expense", add_expense_for_user, "Adds a new expense for the given user-name.")
    plugin.add_command("cash-up-print", read, "debug print function")
    plugin.add_command("cash-up", cash_up, "Settle all registered expenses among the previously registered group.") 
    plugin.add_command("cash-up-r", register, "Short form for `chash-up-register`")
    plugin.add_command("cash-up-ae", add_expense_for_user, "Short form for `chash-up-add-expense`")
    plugin.add_command("cash-up-p", read, "Short form for `cash-up-print`")


class Group_payments:
    def __init__(self, splits_evenly: bool):
        self.payments = []
        self.splits_evenly = splits_evenly
    
    def append_new_member(self, new_uid:str, new_percentage: float = None):
        new_member = {}
        if self.splits_evenly == False:
            if new_percentage is not None:
                new_member = {"uid": new_uid, "percentage": new_percentage, "expenses": 0}  
            else:
                logger.error("cash-up Group_payments append_new_member failed: members percentage is not defined for a group that does not split evenly")
                # TODO throw error!
        else:
            new_member = {"uid": new_uid, "expenses": 0}
        self.payments.append(new_member)


    def reset_all_expenses(self):
        # für alle payments
        for payment in self.payments:
            payment["expenses"] = 0

    def increase_expense(self, search_uid, new_expense: float):
        # TODO implement error handling when uid not found!
        # find all payments where uid matches
        payment_to_increase = list(filter(lambda payment: payment['uid'] == search_uid, self.payments))
        # update first and hopefully only match
        payment_to_increase[0]["expenses"] += new_expense

    def print(self):
        print("group:")
        print("payments:",self.payments)
    
    def to_str(self):
        return f"Group: splits_evenly: {self.splits_evenly}, member list: {self.payments}"


class Persistent_groups:
    def __init__(self, store):
        self.store = store

    async def delete_group(self, search_room_id: str):
        # delete group if exists
        return await self.store.clear_data(search_room_id)

    async def load_group(self, search_room_id: str):
        return await self.store.read_data(search_room_id)
    
    async def save_group(self, room_id: str, group_to_save: Group_payments):
        return await self.store.store_data(room_id, group_to_save)


pg = Persistent_groups(plugin)

class Cash_up(object):
    def __init__(self, group_payments):
        """Setup Cash_up algorithm
        For a set of people who owe each other some money or none
        this algorithm can settle expense among this group.

        Optionally it can be specified how much percentage of
        the over all expenses should be paid by each person.
        If not specified the expenses are distributed equally.
        Args:
            group_payments (array): Dict per person
                {"uid": some **unique** id/name [str],
                "expenses": sum of this persons expenses [int/float],
                "percentage": [optional] percentage (0 to 1) to pay for the group [float]}
                * uid must be unique in this group
                * array length must be > 1
                * percentage must be defined for all or no one
        """
        nr_percentage_defined = 0
        for payment in group_payments:
            if "percentage" in payment:
                    nr_percentage_defined += 1
        # check for correct split percentage in total, if defined
        if nr_percentage_defined == len(group_payments):
            self._split_uneven = True
        else:
            self._split_uneven = False
        self._payments = group_payments


    def distribute_expenses(self):
        """distribute the given expenses within the group
        and return who owes who texts
        
        returns: (array of str)
            Text elements per payment to
            settle expense among the group."""
        self._calculate_sum_and_mean_group_expenses()
        self._calculate_parts_to_pay()
        return self._who_owes_who()

    def _calculate_sum_and_mean_group_expenses(self):
        """calculate the sum & mean of all expenses in the group"""
        self._sum_group_expenses = functools.reduce(lambda acc, curr: acc+ int(curr['expenses']), self._payments, 0)
        self._mean_group_expenses = self._sum_group_expenses / len(self._payments)
        # print("sum of expenses",self._sum_group_expenses)
        
    def _calculate_parts_to_pay(self):
        """calculate the parts each person has to pay
        depending on _split_uneven or not"""
        if self._split_uneven:
            self._parts_to_pay = [{"uid": payment["uid"], "has_to_pay": (payment['expenses'] - (self._sum_group_expenses * payment['percentage']))} for payment in self._payments]
        else:
            self._parts_to_pay = [{"uid": payment["uid"], "has_to_pay": (payment['expenses'] - (self._mean_group_expenses))} for payment in self._payments]
        # print("parts to pay:",self._parts_to_pay)

    def _who_owes_who(self):
        """Build strings of who owes who how much.
        Source is the JavaScript version found at:
        https://stackoverflow.com/questions/974922/algorithm-to-share-settle-expenses-among-a-group
        
        returns:
            output_texts: (array of str)
                Text elements per payment to
                settle expense among the group."""
        # some function
        ordered_parts_to_pay = sorted(self._parts_to_pay, key=lambda d: d["has_to_pay"])
        sortedPeople = [part["uid"] for part in ordered_parts_to_pay]
        sortedValuesPaid = [part["has_to_pay"] for part in ordered_parts_to_pay]
        i = 0
        j = len(sortedPeople)-1
        debt = 0
        output_texts=[]
        while i < j:
            debt = min(-(sortedValuesPaid[i]), sortedValuesPaid[j])
            sortedValuesPaid[i] += debt
            sortedValuesPaid[j] -= debt
            # generate output string
            new_text=str(sortedPeople[i])+" owes "+str(sortedPeople[j])+" "+str(debt)+" €"
            output_texts.append(new_text)
            if sortedValuesPaid[i] == 0:
                i+=1
            if sortedValuesPaid[j] ==0:
                j-=1
        return output_texts

async def help(command):
    """Echo back the command's arguments"""
    response = "this is some basic help text for the cash-up plugin"
    await plugin.reply(command, response)

async def register(command):
    """Register a set of people as a new group to share expenses"""
    response_input_error = "You need to register at least two users: `chash-up-register <user-name1> [<user1-percentage>]; <user-name2> [<user2-percentage>]; ...` [optional]"
    # TODO error response new text line with example:  `chash-up-register A 0.2; B 0.8;` A pays 20%, B pays 80% or `chash-up-register A; B;` to split expenses evenly
    # TODO run cash-up ald data if available before deleting it!
    if command.args:
        logger.debug(f"cash-up-register called with {command.args}")
        # cash-up-register called with ['Marius', '0,7;', 'Andrea', '0.3;']
        # cash-up-register called with ['Marius;', 'Andrea;']
        # generate lists of names and optional percentages
        new_names = []
        new_percentages = []
        for arg in command.args:
            print("arg:",arg)
            # remove all ; from arg element;
            arg = arg.replace(';', '')
            # find any numbers in string (eg: 12; 12,1; 12.1)
            match_arg_nr = re.search('\d*[.,]?\d+',arg)
            # returns a match object
            if match_arg_nr:
                # TODO fail if len > 1?
                # number (as string) found
                # replace "," of german numbers by a "." decimal point
                # convert the number to a real float number
                arg_float = float(match_arg_nr.group().replace(',', '.'))
                if len(new_percentages) == (len(new_names)-1):
                    new_percentages.append(arg_float)
                else:
                    await plugin.reply_notice(command, response_input_error)
                    return
            else:
                new_names.append(arg)        
        if (len(new_names) == len(new_percentages) and len(new_names) > 1):
            # every name got a percentage value
            new_group_not_even = Group_payments(splits_evenly=False)
            for idx, name in enumerate(new_names):
                # create a new group member with split percentage
                new_group_not_even.append_new_member(name, new_percentages[idx])
            # persist new group for current room id
            await pg.save_group(command.room.room_id, new_group_not_even)
        elif (len(new_percentages) == 0 and len(new_names) > 1):
            # no name got a percentage value
            new_group_even = Group_payments(splits_evenly=True)
            for name in new_names:
                # create a new group member without split percentage (split expenses equally)
                new_group_even.append_new_member(name)
            # persist new group for current room id
            await pg.save_group(command.room.room_id, new_group_even)
        else:
            # sth went terribly wrong
            await plugin.reply_notice(command, response_input_error)
            return
    else:
        # no command args defined
        await plugin.reply_notice(command, response_input_error)
        return
    response_success = "Successfully registered new group!"
    await plugin.reply(command, response_success)

async def read(command):
    """Read the database for the group registered for the current room [debugging helper function]"""
    loaded_group: Group_payments = await pg.load_group(command.room.room_id)
    response = "No group registered for this room!"
    if loaded_group is not None:
        response = loaded_group.to_str()
    await plugin.reply(command, response)

async def add_expense_for_user(command):
    """Adds a new expense for the given username"""
    response_input_error = "You need to provide a previously registered user-name and expense value: `chash-up-add-expense <user-name> <expense-value>[€/$] [optional]`"
    # TODO run cash-up of old data if available before deleting it!
    if len(command.args) != 2:
        # command should only contain <user-name> and <expense-value>
        await plugin.reply_notice(command, response_input_error)
        return
    else:
        # first command arg is <user-name>
        user_name = command.args[0]
        # second command arg is <expense-value>
        # clean up expense-value from additional currency signs etc
        # find any number in string (eg: 12; 12,1; 12.1)
        match_expense_nr = re.search('\d*[.,]?\d+',command.args[1])
        if match_expense_nr:
            # extract match, then replace "," of german numbers by a "." decimal point
            expense_float = float(match_expense_nr.group().replace(',', '.'))
            # TODO try catch?! room_id not defined OR user_name not defined!
            try:
                # Persistent_groups.load_group throws AttributeError when group not found
                loaded_group: Group_payments = await pg.load_group(command.room.room_id)
                # Group.increase_expense throws IndexError when user_name not found
                loaded_group.increase_expense(user_name, expense_float)
            except (AttributeError, IndexError) as e:
                await plugin.reply(command, response_input_error)
                return
            await pg.save_group(command.room.room_id, loaded_group)
            # TODO make currency sign configureable
            await plugin.reply(command, f"Successfully added {expense_float}€ expense for {user_name}!")
        else:
            await plugin.reply(command, response_input_error)

async def cash_up(command):
    """Settle all registered expenses among the previously registered group."""
    try:
        loaded_group: Group_payments = await pg.load_group(command.room.room_id)
    except AttributeError:
        response_error = "No cash-up possible because there was no group registered for this room."
        await plugin.reply(command, response_error)
    cash_up = Cash_up(loaded_group.payments)
    message: str = ""
    who_owes_who_texts = cash_up.distribute_expenses()
    message += f"**Result of group cash-up**:  \n"
    for line in who_owes_who_texts:
        message += f"{line}  \n"
    await plugin.reply(command, message)
    loaded_group.reset_all_expenses()
    await pg.save_group(command.room.room_id,loaded_group)


    

setup()
