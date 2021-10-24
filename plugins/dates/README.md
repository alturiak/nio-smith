Plugin: dates
===
Add dates-plugin to store dates and birthdays. Post reminders/birthday wishes at the start of the day and at the 
actual time of the event. All entries and posted reminders are **room-specific**.

Almost any common format (and language) may be used to enter the date:
  - Generic parsing of dates in over 200 language locales plus numerous formats in a language agnostic fashion.
  - Generic parsing of relative dates like: '1 min ago', '2 weeks ago', '3 months, 1 week and 1 day ago', 'in 2 days', 
    'tomorrow'.
  - Generic parsing of dates with time zones abbreviations or UTC offsets like: 'August 14, 2015 EST', 'July 4, 2013 
    PST', '21 July 2013 10:15 pm +0500'.

See [dateparser](https://pypi.org/project/dateparser/) for details.

## Commands

### date
Usage: `date [name or username]`  
Display the details of the next upcoming date or a specific date

### date_add
Usage: `date_add <name or username> <date in most common formats> [description]`  
Add a date or birthday - dates consisting of multiple words must be enclosed in quotes.  

Example: `date_add test tomorrow`  
Add a date called "test" for the next day at the same time of day.

Example: `date_add test2 "in 28 days" "28 days later"`  
Add a date called "test2" 28 days in the future at the same time of day.

Example: `date_add new_year "2022-01-01 00:00" "A new year"`  
Add a date called "new_year" for 01.01.2022 at 00:00.

Example: `date_add start_of_unixtime "01.01.1970 00:00:00" The dawn of time`
Add a date called "start_of_unixtime" for 01.01.1970 at 00:00:00 with the description "The dawn of time"

See [dateparser](https://pypi.org/project/dateparser/) for more information on accepted date formats.

### date_del
Usage: `date_del <name or username>`  
Delete a date or birthday (PL: 50)

### date_list
Usage: `date_list`  
Display a list of all stored dates for the current room

### date_next
Usage: `date_next`  
Display details of the next upcoming date for the current room (doesn't currently display birthdays)

### date_show
Usage: `date_show <name or username>`  
Display details of a specific date

## External Requirements
- [dateparser](https://pypi.org/project/dateparser/) to allow for almost arbitrary input format of dates