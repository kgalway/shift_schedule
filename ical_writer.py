import logging
import sys
import os
import shutil


import ics
import pandas as pd 
from datetime import timedelta, time, datetime  
import pytz 


from people import people, emails
from shifts import shift_durations, shift_map




logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def copy_current_to_archive():
    archive = os.path.join('.', 'archive')
    current = os.path.join('.','current')
    if os.listdir(current):
    # if there is actualy anything in the current folder 
        for fil in os.listdir(current):
            archive_path = os.path.join(archive, fil)
            current_path = os.path.join(current,fil)
            shutil.copyfile(current_path, archive_path)
            logger.info('copied {0} to {1}'.format(current_path, archive_path))

def cancel_event(event):
    event.status = 'CANCELLED'
    event.method = 'CANCEL'
    event.sequence = 2
    return event 

def cancel_calendar(calendar):
    new_cal = ics.Calendar()
    for event in calendar.events:
        if event.status == 'CANCELLED' or event.begin < datetime.today().replace(tzinfo = pacific):
            # found an already-cancelled event. Skip it 
            logger.debug('Ignoring event {0}'.format(str(event)))
            continue
        event = cancel_event(event)
        new_cal.events.append(event)
    return new_cal         

def person_calendar(schedule):
    """ create a list of events for a person based on a tuple of (date, shift) tuples """
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
    dirpath = 'current'
    filename = person + '.ics'
    filepath = os.path.join(dirpath,filename)
    with open(filepath,'w') as f:
        f.writelines(calendar)
    f.close()



if __name__ == '__main__':
    
    

    if len(sys.argv) > 1:
        to_parse = sys.argv[1:]
    else:
        to_parse = None

    pacific = pytz.timezone('America/Vancouver')
    today = datetime.today().replace(tzinfo = pacific)
    
 
    
    if to_parse is not None:
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
    # copy old files over 
    copy_current_to_archive()

    df = pd.read_csv(schedule_csv_filename, parse_dates = [0], index_col = [0])
    df.fillna('ignore',inplace=True)
    df.index = df.index.tz_localize(pacific)
    dates = df.index.tolist()

    for col in df:
        # looping through people
        if col not in emails:
            logger.info('skipping {0}'.format(col))
            continue 
        # get new calendar 
        shifts = df[col].tolist()
        schedule = [(date, shift) for date,shift in zip(dates, shifts)]

        # get a new Calendar instance from the list of (date, shift) values 
        calendar = person_calendar(schedule)
        logger.info('parsed calendar for {0}'.format(col))
        
        # read and delete old calendar, if it exists
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
    raw_input('Press Any Key to Exit')

handler.close()

    



