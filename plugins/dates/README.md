Plugin: dates
===
Add dates-plugin to store dates and birthdays.  
Please keep in mind: all entries and posted reminders are **room-specific**.

The plugin allows storing dates and birthdays, accepting almost any common format (and language) to enter the date.  
See [dateparser](https://pypi.org/project/dateparser/) for details.

## Commands

### date
Usage: `date [name or username]`  
Display the details of the next upcoming date or a specific date

### date_add
Usage: `date_add <name or username> <date in most common formats> [description]`  
Dates consisting of multiple words must be enclosed in quotes.  
Example: `date_add test tomorrow`  
Example: `date_add test "in 28 days" "28 days later"`  
Example: `date_add new_year 2021-01-01 "A new year"`  
Example: `date_add start_of_unixtime "01.01.1970 00:00:00" The dawn of time`  
Add a date or birthday

### date_del
Usage: `date_del <name or username>`  
Delete a date or birthday (PL: 50)

### date_list
Usage: `date_list`  
Display a list of all stored dates

### date_next
Usage: `date_next`  
Display details of the next upcoming date

### date_show
Usage: `date_show <name or username>`  
Display details of a specific date

## External Requirements
- [dateparser](https://pypi.org/project/dateparser/) to allow for almost arbitrary input format of dates