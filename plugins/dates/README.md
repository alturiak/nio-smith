Plugin: dates
===
Add dates-plugin to store dates and birthdays. All entries and posted reminders are room-specific.

The plugin allows storing dates and birthdays, accepting almost any common format (and language) to enter the date.  
See [dateparser](https://pypi.org/project/dateparser/) for details.  
This adds dateparser to the requirements.

## Commands
### date_add
Usage: `date_add <name or username> <date in most common formats> [description]`  
Dates consisting of multiple words must be enclosed in quotes.  
Example: `date_add test tomorrow`  
Example: `date_add test "in 28 days" "28 days later"`  
Example: `date_add new_year 2021-01-01 "A new year"`  
Example: `date_add start_of_unixtime "01.01.1970 00:00:00" The dawn of time`  


### date_del
Usage: `date_del <name or username>`

### date_show
Usage: `date_show <name or username>`
