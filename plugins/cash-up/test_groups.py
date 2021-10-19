#from core.plugin import Plugin

class Group:
    def __init__(self, room_id: str, payments):
        self.room_id = room_id
        self.payments = payments

    def reset_all_expenses(self):
        # für alle payments
        for payment in self.payments:
            payment["expenses"] = 0

    def increase_expense(self, search_uid, new_expense):
        # find all payments where uid matches
        payment_to_increase = list(filter(lambda payment: payment['uid'] == search_uid, self.payments))
        # update first and hopefully only match
        payment_to_increase[0]["expenses"] += new_expense

    def print(self):
        print("group:")
        print("room id:",self.room_id)
        print("payments:",self.payments)

example_payments = [
    {"uid": "A", "percentage": 0.25, "expenses": 75},
    {"uid": "B", "percentage": 0.5, "expenses": 60},
    {"uid": "C", "percentage": 0.25, "expenses": 15}
]
group = Group("example_id", example_payments)
group.increase_expense("A",25)
group.print()
group.reset_all_expenses()
group.print()

class Persistent_groups:
    def __init__(self):
        self.groups = []
    
    def append_new_group(self, new_group: Group):
        # delete group for room if it already exists
        self.delete_group(new_group.room_id)
        # append new group
        self.groups.append(new_group)

    def find_group(self, search_room_id):
        # find all groups where room_id matches
        groups_found = list(filter(lambda group: group.room_id == search_room_id, self.groups))
        # should never contain more than one group per room_id
        return groups_found[0]

    def delete_group(self, search_room_id):
        # delete group if exists
        for index, group in enumerate(self.groups):
            if group.room_id == search_room_id:
                del self.groups[index]
                break

    def load(self):
        print("implement load from db file")
    
    def save(self):
        print("implement save to file")

    def print(self):
        print("persistent_groups:",self.groups)


example_payments2 = [
    {"uid": "A", "expenses": 75},
    {"uid": "B", "expenses": 60},
    {"uid": "C", "expenses": 15}
]

pg = Persistent_groups()
pg.append_new_group(group)
pg.print()
pg.append_new_group(group)
pg.print()
group2 = Group("222", example_payments2)
pg.append_new_group(group2)
pg.print()
group2_found1 = pg.find_group("222")
group2_found1.print()
group2_found1.increase_expense("A",2050)

group1_found1 = pg.find_group("example_id")
group1_found1.increase_expense("B",999999999999)

group2_found2 = pg.find_group("222")
group2_found2.print()

group1_found2 = pg.find_group("example_id")
group1_found2.print()