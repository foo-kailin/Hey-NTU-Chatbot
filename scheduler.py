from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests

# If modified these scopes, delete the file token.pickle. (IMPT)
# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly'] (default)
SCOPES = ['https://www.googleapis.com/auth/calendar']

api_key='1446373870:AAEZTQdFkmUIMa6qNDVo1AngkKZyYcoV4Yw'
chat_id = '241239513'

def sendMessage(chat_id,text_message):
    url='https://api.telegram.org/bot'+str(api_key)+'/sendMessage?text='+str(text_message)+'&chat_id='+str(chat_id)
    response = requests.get(url)
    return response

def book_timeslot(event_description,booking_date,booking_start_time,booking_end_time):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    #--------------------- Manipulating Booking Time ----------------------------
    start_time=booking_date+'T'+booking_start_time+':00+08:00'   #str(datetime.datetime.now())[:10]
    end_time=booking_date+'T'+booking_end_time+':00+08:00'
    #----------------------------------------------------------------------------

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('start time:'+start_time+', end time:'+end_time)
    print('Booking a time slot....')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        event = {
        'summary': str(event_description),
        'location': 'NTU',
        'description': str(event_description),
        'start': {
        'dateTime': start_time,
        'timeZone': 'Asia/Singapore',
        },
        'end': {
        'dateTime': end_time,
        'timeZone': 'Asia/Singapore',
        },
        'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=1'
        ],
        'attendees': [
        {'email': 'fook0008@e.ntu.edu.sg'},
        ],
        'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 10},
        ],
        },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True

    else:
        # --------------------- Check if there are any clash of events --------------------- 
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            print(start, event['summary']) #print upcoming events
            if start <= start_time < end or start < end_time <= end:
                print('Clash of events...')
                return False
            #elif start_time <= end <= end_time:
                #print('Already set...')
                #return False
        # -------------------- Break out of for loop if there are no apppointment that has the same time ----------
        event = {
        'summary': str(event_description),
        'location': 'NTU',
        'description': str(event_description),
        'start': {
        'dateTime': start_time,
        'timeZone': 'Asia/Singapore',
        },
        'end': {
        'dateTime': end_time,
        'timeZone': 'Asia/Singapore',
        },
        'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=1'
        ],
        'attendees': [
        {'email': 'fook0008@e.ntu.edu.sg'},
        ],
        'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 60},
        ],
        },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True
    
def upcoming_events():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time #TRY NOW() > accurate time
    print('Getting the upcoming 10 events...now:'+now)
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        #e_date = start[11:16]
        print(start, event['summary'])
        #sendMessage(chat_id, start[8:10]+'/'+start[5:7]+' '+start[11:16]+'  '+event['summary'])
        if int(start[11:13]) < 12:
            if int(start[11])==0:
                start_e = start[12:16]
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_e+'am    '+event['summary'])
            else:
                start_e = start[11:16]
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_e+'am  '+event['summary'])
        if int(start[11:13]) == 12:
            sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start[11:16]+'pm  '+event['summary'])
        if int(start[11:13]) > 12:
            start_hour = str(int(start[11:13]) - 12)
            if len(start_hour) == 1:
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_hour+start[13:16]+'pm    '+event['summary'])
            else:
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_hour+start[13:16]+'pm  '+event['summary'])
        
def today_events():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    # Call the Calendar API
    now = datetime.datetime.now().isoformat() + 'Z' # 'Z' indicates UTC time
    #not working, has it got to do with timezones? utcnow()
    now_year = now[0:4]
    now_month = now[5:7]
    now_day = now[8:10]
    if int(now_day)==1:
        yester_day = 31
        curr_month = int(now_month)-1
    else:
        yester_day = int(now_day)-1
        curr_month = int(now_month)
    print('year='+now_year+' month='+now_month+' day='+now_day)
    today_start = datetime.datetime(int(now_year), curr_month, yester_day, 16, 00, 00, 0).isoformat() + 'Z' #to counter +08:00 timezone
    today_end = datetime.datetime(int(now_year), int(now_month), int(now_day), 15, 59, 59, 0).isoformat() + 'Z'
    print (today_start+' to '+today_end)
    print('Getting the events for today...now:'+now)
    events_result = service.events().list(calendarId='primary', timeMin=today_start+'', timeMax=today_end,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No events for today.')
        sendMessage(chat_id, 'No events for today. Enjoy your day!')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        #e_date = start[11:16]
        print(start, event['summary'])
        #sendMessage(chat_id, start[8:10]+'/'+start[5:7]+' '+start[11:16]+'-'+end[11:16]+'  '+event['summary'])
        if int(start[11:13]) == 12:
            end_hour = str(int(end[11:13]) - 12)
            sendMessage(chat_id, start[11:16]+' - '+end_hour+end[13:16]+'pm  '+event['summary'])
        elif int(start[11:13]) > 12:
            start_hour = str(int(start[11:13]) - 12)
            end_hour = str(int(end[11:13]) - 12)
            sendMessage(chat_id, start_hour+start[13:16]+' - '+end_hour+end[13:16]+'pm  '+event['summary'])
        elif int(end[11:13]) == 12:
            sendMessage(chat_id, start[11:16]+'am - '+end[11:16]+'pm  '+event['summary'])
        elif int(end[11:13]) > 12:
            end_hour = str(int(end[11:13]) - 12)
            sendMessage(chat_id, start[11:16]+'am - '+end_hour+end[13:16]+'pm  '+event['summary'])
        else:
            start_e = start[11:16]
            end_e = end[11:16]
            if int(start[11])==0:
                start_e = start[12:16]
            if int(end[11])==0:
                end_e = end[12:16]
            sendMessage(chat_id, start_e+' - '+end_e+'am  '+event['summary'])

def search_events(event_desc):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time #TRY NOW() > accurate time
    print('Searching for events...now:'+now)
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=20, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    #event_desc = 'Project'
    count = 0
    if not events:
        count = 1
        print('No upcoming events found.')
        sendMessage(chat_id, '- no upcoming events -')
    for event in events:
        if event_desc in event['summary']:
            count += 1
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            print(start, event['summary'])
            if int(start[11:13]) == 12:
                end_hour = str(int(end[11:13]) - 12)
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start[11:16]+' - '+end_hour+end[13:16]+'pm  '+event['summary'])
            elif int(start[11:13]) > 12:
                start_hour = str(int(start[11:13]) - 12)
                end_hour = str(int(end[11:13]) - 12)
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_hour+start[13:16]+' - '+end_hour+end[13:16]+'pm  '+event['summary'])
            elif int(end[11:13]) == 12:
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start[11:16]+'am - '+end[11:16]+'pm  '+event['summary'])
            elif int(end[11:13]) > 12:
                end_hour = str(int(end[11:13]) - 12)
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start[11:16]+'am - '+end_hour+end[13:16]+'pm  '+event['summary'])
            else:
                start_e = start[11:16]
                end_e = end[11:16]
                if int(start[11])==0:
                    start_e = start[12:16]
                if int(end[11])==0:
                    end_e = end[12:16]
                sendMessage(chat_id, start[8:10]+'/'+start[5:7]+'  '+start_e+' - '+end_e+'am  '+event['summary'])
    if count == 0:
        print('none')
        sendMessage(chat_id, '- no relevant events found -')

def recurring_events(event_description,booking_date,booking_start_time,booking_end_time,event_freq,event_count):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    #--------------------- Manipulating Booking Time ----------------------------
    start_time=booking_date+'T'+booking_start_time+':00+08:00'   #str(datetime.datetime.now())[:10]
    end_time=booking_date+'T'+booking_end_time+':00+08:00'
    #----------------------------------------------------------------------------

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('start time:'+start_time+', end time:'+end_time)
    print('Booking a time slot....')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        event = {
        'summary': str(event_description),
        'location': 'NTU',
        'description': str(event_description),
        'start': {
        'dateTime': start_time,
        'timeZone': 'Asia/Singapore',
        },
        'end': {
        'dateTime': end_time,
        'timeZone': 'Asia/Singapore',
        },
        'recurrence': [
        'RRULE:FREQ='+str(event_freq)+';COUNT='+str(event_count)  #FREQ=DAILY;COUNT=1
        ],
        'attendees': [
        {'email': 'fook0008@e.ntu.edu.sg'},
        ],
        'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 10},
        ],
        },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True

    else:
        # --------------------- Check if there are any clash of events --------------------- 
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            print(start, event['summary']) #print upcoming events
            if start <= start_time < end or start < end_time <= end:
                print('Clash of events...')
                return False
            #elif start_time <= end <= end_time:
                #print('Already set...')
                #return False
        # -------------------- Break out of for loop if there are no apppointment that has the same time ----------
        event = {
        'summary': str(event_description),
        'location': 'NTU',
        'description': str(event_description),
        'start': {
        'dateTime': start_time,
        'timeZone': 'Asia/Singapore',
        },
        'end': {
        'dateTime': end_time,
        'timeZone': 'Asia/Singapore',
        },
        'recurrence': [
        'RRULE:FREQ='+str(event_freq)+';COUNT='+str(event_count)
        ],
        'attendees': [
        {'email': 'fook0008@e.ntu.edu.sg'},
        ],
        'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 60},
        ],
        },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        print ('Event created: %s' % (event.get('htmlLink')))
        return True

if __name__ == '__main__': 
    event_description = 'recurring test'
    booking_date = '2021-04-11'
    booking_start_time = '12:00'
    booking_end_time = '14:00'
    event_freq = 'MONTHLY'
    event_count = '3'
    recurring_events(event_description,booking_date,booking_start_time,booking_end_time,event_freq,event_count)
    """
    event_description='Test scheduler.py'   #test if calendar function is working properly
    #input_email='fookailin910@gmail.com'
    booking_date=str(datetime.datetime.now())[:10]

    current_time=datetime.datetime.now()
    current_hour=str(current_time)[11:13]
    booking_start_time=str(int(current_hour))+':00'

    later_hour = int(current_hour) + 2
    booking_end_time=str(later_hour)+':00'

    result=book_timeslot(event_description,booking_date,booking_start_time,booking_end_time)
    """