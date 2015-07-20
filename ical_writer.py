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
from calendar_utils import copy_current_to_archive, cancel_calendar, cancel_event, person_calendar



logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)





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
        dirpath = r'Documents/Programming/general'
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
        if col not in emails:
            logger.info('skipping {0}'.format(col))
            continue 
        # get new calendar 
        shifts = df[col].tolist()
        schedule = [(date, shift) for date,shift in zip(dates, shifts)]
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



    



