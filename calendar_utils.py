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