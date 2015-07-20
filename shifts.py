from datetime import time, timedelta	

shift_durations = {'afternoon':timedelta(hours = 8.5), 'day':timedelta(hours = 9.5), 'night':timedelta(hours = 6.5), 'other':timedelta(hours = 9)}
    
shift_map = ({'A3':(time(15,15), shift_durations['afternoon']), 'D3':(time(6,15),shift_durations['day']), 'N3':(time(23,55),shift_durations['night']),
               'D1':(time(5,15), shift_durations['day']), 'A1':(time(14,15),shift_durations['afternoon']), 'N1':(time(23,15),shift_durations['night']),
               'D2':(time(6,0),shift_durations['day']), 'A2':(time(15,0),shift_durations['afternoon']), 'N2':(time(23,55),shift_durations['night']),
               'other':(time(7,0),shift_durations['other'])})   
