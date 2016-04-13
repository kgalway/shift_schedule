An ics writer for a CSV-based shift schedule containing person names in the header row and dates in the first column. 

ical_writer.py is the main progrma and relies in imports from (private) modules called emails.py and shifts.py. 

emails.py contains a dictionary of person:email key:value pairs that is used to test for membership in the group prior to parsing a calendar 

shifts.py contains a dictionary of shift:(start_time, duration) key:value pairs to map shift names provided in the CSV shift schedule to the appropriate start time and duration of the shift. 


