"""
Written by Kelly Galway 



A program to convert a csv-based schedule into a .ics file suitable for importing 
into a Google Calendar 

Contains functionality to track changes from a previous schedule and have any updates 
be reflected in the new schedule. 

App-specic imports include a "shifts" module containing a dictionary of name:(startime, duration)
key:value pairs describing how the shift from the CSV should be reflected in the calendar 

The people module exports a dictionary of initials to person names and a dictionary of 
initials to email addresses for future development of an auto-mailer when the new shift 
schedule comes out. 



"""

import logging
import sys
import os
import shutil
from datetime import timedelta, time, datetime  

# third-party imports 
import ics
import pandas as pd 
import pytz 

# app-specific modules 
from people import people, emails
from shifts import shift_durations, shift_map




logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def copy_current_to_archive():
    """ copy all 'current' files to 'archive' folder. Used to prep for a new schedule coming in """ 
    archive = os.path.join('.', 'archive')
    current = os.path.join('.','current')
    if os.listdir(current):
    # if there is actualy anything in the current folder 
        for fil in os.listdir(current):
            if not fil.endswith('.ics'):
                # only want .ics type files
                continue
            archive_path = os.path.join(archive, fil)
            current_path = os.path.join(current,fil)
            shutil.copyfile(current_path, archive_path)
            logger.info('copied {0} to {1}'.format(current_path, archive_path))

def cancel_event(event):
    """ Cancel an Event instance previously-good event. 
    return the modified instance 
    """ 
    event.status = 'CANCELLED'
    event.method = 'CANCEL'
    event.sequence = 2
    return event 

def cancel_calendar(calendar):
    """ Given a Calendar instance, go through and cancel all 'live' events and write these 
    cancelled events to a new Calendar instance. These cancelled events are appended to a new Calendar 
    to make sure that only the latest shift schedule is reflected in the Calendar, but also deleting 
    all the old events
    """ 
    new_cal = ics.Calendar()
    for event in calendar.events:
        if event.status == 'CANCELLED' or event.begin < datetime.today().replace(tzinfo = pacific):
            # don't consider events in the past or events that were already cancelled 
            logger.debug('Ignoring event {0}'.format(str(event)))
            continue
        event = cancel_event(event)
        new_cal.events.append(event)
    return new_cal         

def person_calendar(schedule):
    """ create a ics.Calendar instance for a person based on a tuple of (date, shift) tuples """
    cal = ics.Calendar() 
      
    for date, shift in schedule:
        if date < today or shift == 'ignore':
            continue
        event = ics.Event()
        event.name = shift 
        if shift in shift_map:
            shift_startTime, shift_length = shift_map[shift]
        else:
            shift_startTime, shift_length  = shift_map['other']
        
        start_time = date + timedelta(hours = shift_startTime.hour, minutes = shift_startTime.minute)
        event.begin = start_time 
        if shift_length is not None:
            event.duration = shift_length
        else:
            event.make_all_day()

        cal.events.append(event)
    return cal

def write_ical(person, calendar):
    """ Wrapper around some boilerplate to actually write the calendar """ 
    dirpath = 'current'
    filename = person + '.ics'
    filepath = os.path.join(dirpath,filename)
    with open(filepath,'w') as f:
        f.writelines(calendar)
    f.close()



if __name__ == '__main__':
    
    
    # optionally set initials as cmd line args for specific calendars to run. Default is to run all by 
    # not inputting any cmd line args 
    if len(sys.argv) > 1:
        to_parse = sys.argv[1:]
    else:
        to_parse = None

    pacific = pytz.timezone('America/Vancouver')
    today = datetime.today().replace(tzinfo = pacific)
    
 
    
    if to_parse is not None:
        # over-write global emails if argv are given
        emails = {key:val for key,val in emails.items() if key in to_parse}
    
    if sys.platform == 'darwin':
        os.chdir(os.environ['HOME'])
        dirpath = r'anaconda/repos/powerex_schedule'
    else:
        dirpath = r'C:\temp'

    schedule_csv_filename = 'schedule.csv'


    logger.info('on system {0}'.format(sys.platform))
    logger.info('searching in directory {0}'.format(dirpath))
    
    os.chdir(dirpath)

    # copy .ics files in ./current to ./archive so that we can use the ./archive 
    # files as a reference for cancelling any stale events 
    copy_current_to_archive()

    df = pd.read_csv(schedule_csv_filename, parse_dates = [0], index_col = [0])
    df.fillna('ignore',inplace=True)
    df.index = df.index.tz_localize(pacific)
    dates = df.index.tolist()

    for col in df:
        # looping through people as cols in the dataframe and getting their shift schedule 
        if col not in emails:
            logger.info('skipping {0}'.format(col))
            continue 
        # get new calendar 
        shifts = df[col].tolist()
        schedule = [(date, shift) for date,shift in zip(dates, shifts)]

        # create a new Calendar instance from the list of (date, shift) values 
        calendar = person_calendar(schedule)
        logger.info('parsed calendar for {0}'.format(col))
        
        # read and cancel all events in the previous version of the calendar located in the ./archive 
        # folder, if it exists 
        archive = 'archive'
        fil = col + '.ics'
        archive_path = os.path.join(archive,fil)
        logger.debug('looking for filename {0}'.format(archive_path))
        if os.path.isfile(archive_path):
            logger.info('found old calendar for {0}; adding deleted events to new calendar'.format(col))
            with open(archive_path,'r') as f:
                lines = f.read()
            f.close()
            old_cal = ics.Calendar(lines)
            # now go and modify the event stream
            old_cal = cancel_calendar(old_cal)
            for event in old_cal.events:
                calendar.events.append(event)
                
      
        write_ical(col, calendar)
        logger.info('wrote calendar for {0}'.format(col))
    handler.close()
    sys.exit()



    



