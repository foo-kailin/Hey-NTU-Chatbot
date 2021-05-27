import requests
import datetime 
import json
import re 
import random
import math

from telegram.ext import *

#query
import torch

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

#scheduling
from scheduler import book_timeslot, upcoming_events, today_events, search_events, recurring_events

#to-do
import time
import urllib

from dbhelper import DBHelper

db = DBHelper()

TOKEN = '' #bot api
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

#timer
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#create a python file called api_key 
#that contains a dictionary api={"api_key":"your_api_key"}
#import api_key
api_key='' # bot api

def getLastMessage():
    url = "https://api.telegram.org/bot{}/getUpdates".format(api_key)
    response = requests.get(url)
    data=response.json()
    last_msg=data['result'][len(data['result'])-1]['message']['text']        #if error:list index out of range is because getUpdates is empty
    chat_id=data['result'][len(data['result'])-1]['message']['chat']['id']
    update_id=data['result'][len(data['result'])-1]['update_id']
    if len(data['result']) < 100:
        return last_msg,chat_id,update_id
    else:
        print('offseting updates limit...')
        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(api_key,update_id)
        response = requests.get(url)
        data=response.json()
        last_msg=data['result'][len(data['result'])-1]['message']['text']
        chat_id=data['result'][len(data['result'])-1]['message']['chat']['id']
        update_id=data['result'][len(data['result'])-1]['update_id']
        return last_msg,chat_id,update_id

def sendMessage(chat_id,text_message):
    url='https://api.telegram.org/bot'+str(api_key)+'/sendMessage?text='+str(text_message)+'&chat_id='+str(chat_id)
    response = requests.get(url)
    return response

def sendHelpMessage(chat_id,text_message):
    url='https://api.telegram.org/bot'+str(api_key)+'/sendMessage?text='+str(text_message)+'&chat_id='+str(chat_id)+'&parse_mode=Markdown'
    response = requests.get(url)
    return response


#---------------------------------------- greetings -------------------------------------------
def start(chat_id):
    sendMessage(chat_id, 'Hey student! \U0001F981 Nice to meet you, I am your NTU personal assistant bot. I can help you manage schedules, answer your queries, or provide study tools. Go ahead and ask away!\n\nYou can control me using these commands:\n\n/start - to start chatting with the bot\n/help - to view full commands list\n/addevent - to add a new calendar event\n/upcoming - to check your upcoming events\n/map - to view NTU Maps\n/query - to enquire about an academic issue\n/quit - to stop chatting with the bot')

def sendGreetings(chat_id):
    current_time=datetime.datetime.now()
    current_hour=str(current_time)[11:13]
    if int(current_hour) < 4:
        sendMessage(chat_id, 'Good day, how can I help you? \U0001F4AD \n\n/addevent - add a new event\n/upcoming - view your upcoming events\n/map - search for an NTU location\n/query - enquire about academic issue\n/gpa - calculate gpa')
        sendMessage(chat_id, 'It\'s pretty late already, you should rest soon. We can talk again in the morning. :-)')
    elif 4 <= int(current_hour) < 7:
        sendMessage(chat_id, 'Good morning, how can I help you today? \U0001F4AD \n\n/addevent - add a new event\n/upcoming - view your upcoming events\n/map - search for an NTU location\n/query - enquire about academic issue\n/gpa - calculate gpa')
    elif 7 <= int(current_hour) < 12:
        sendMessage(chat_id, 'Good morning, how can I help you today? \U00002600 \n\n/addevent - add a new event\n/upcoming - view your upcoming events\n/map - search for an NTU location\n/query - enquire about academic issue\n/gpa - calculate gpa')
    elif 12 <= int(current_hour) < 18:
        sendMessage(chat_id, 'Good afternoon, how can I help you today? \U000026C5 \n\n/addevent - add a new event\n/upcoming - view your upcoming events\n/map - search for an NTU location\n/query - enquire about academic issue\n/todo - manage to-do list\n/calc - open calculator\n/timer - set a timer\n/gpa - calculate gpa')
    elif 18 <= int(current_hour):
        sendMessage(chat_id, 'Good evening, how can I help you today? \U0001F319 \n\n/addevent - add a new event\n/upcoming - view your upcoming events\n/map - search for an NTU location\n/query - enquire about academic issue\n/gpa - calculate gpa')

def randomGreetings(argument): 
    switcher = { 
        0: "Hey there, what do you want to do today? I'm always here to help :-)", 
        1: "Hi student, how are you feeling today? Hope you are good!", 
        2: "Hello, what do you want to do today? Let me help :-)",
        3: "Hi! Great to see you here. :-)",
        4: "Hello, how are you doing today? :-)",
        5: "Hello, hope you are having a good day. How can I help? :-)",
        6: "Hi there!",
        7: "Hello there!",
        8: "Hey! How are you? :-)",
        9: "Hi there, happy to see you here!",
    } 
    return switcher.get(argument, "Help! There is an error with my greetings.")


#------------------------------------------- query --------------------------------------------
def query(chat_id):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    with open('intents.json', 'r') as json_data:
        intents = json.load(json_data)

    FILE = "data.pth"
    data = torch.load(FILE)

    input_size = data["input_size"]
    hidden_size = data["hidden_size"]
    output_size = data["output_size"]
    all_words = data['all_words']
    tags = data['tags']
    model_state = data["model_state"]

    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()

    print("Entered query function. Let's chat!")
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:

            sentence = current_last_msg

            if sentence == "/quit":
                sendMessage(chat_id, 'Closed query function. Use /query if you have any other queries to ask.')
                run()

            sentence = tokenize(sentence)
            X = bag_of_words(sentence, all_words)
            X = X.reshape(1, X.shape[0])
            X = torch.from_numpy(X).to(device)

            output = model(X)
            _, predicted = torch.max(output, dim=1)

            tag = tags[predicted.item()]

            probs = torch.softmax(output, dim=1)
            prob = probs[0][predicted.item()]
            if prob.item() > 0.75:
                for intent in intents['intents']:
                    if tag == intent["tag"]:
                        query_response = random.choice(intent['responses'])
                        print(query_response)
                        sendHelpMessage(chat_id, query_response)
                        query(chat_id)
            else:
                print("I do not understand...")
                sendMessage(chat_id, 'Sorry, I do not understand. :-( Could you rephrase your query? If you wish to exit the query function, use /quit.')
                query(chat_id)


#----------------------------------- scheduling function --------------------------------------
def check_date(date):
    regex = '^202[1-9]-[01][0-9]-[0-3][0-9]$' #'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$' 
    if(re.search(regex,date)):  
        print("Valid Date") 
        return True
    else:  
        print("Invalid Date")
        return False

def check_time(time):
    regex = '^[012][0-9]:[0-5][0-9]$'
    if(re.search(regex,time)):  
        print("Valid Time") 
        return True
    else:  
        print("Invalid Time")
        return False

def sendInlineMessageForEvent(chat_id):
    text_message='What kind of event do you want to schedule?'
    keyboard={'keyboard':[
                        [{'text':'Quiz'},{'text':'Lab'}],
                        [{'text':'Exam'},{'text':'Submission'}],
                        [{'text':'Project'},{'text':'Others'}]
                        ], 'one_time_keyboard': True} #'resize_keyboard': True
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def sendInlineMessageForDescription(chat_id):
    global event_description
    global update_id_for_booking_of_time_slot
    sendMessage(chat_id, 'Please enter the event name:')
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                update_id_for_booking_of_time_slot=''
                event_description=''
                booking_date=''
                booking_start_time=''
                booking_end_time=''
                sendMessage(chat_id,"Event cancelled! See you again soon.")
                run()
            elif current_last_msg != '/quit':
                event_description = current_last_msg
                print(event_description)
                sendInlineMessageForBookingDate(chat_id)

def sendInlineMessageForBookingDate(chat_id):
    global booking_date
    global update_id_for_booking_of_time_slot
    sendMessage(chat_id, 'Please enter the event date in the format YYYY-MM-DD')
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                update_id_for_booking_of_time_slot=''
                event_description=''
                booking_date=''
                booking_start_time=''
                booking_end_time=''
                sendMessage(chat_id,"Event cancelled! See you again soon.")
                run()
            elif check_date(current_last_msg)==True:
                booking_date=current_last_msg
                update_id_for_booking_of_time_slot=current_update_id
                sendInlineMessageForStartTime(chat_id)
            else:
                sendMessage(chat_id,"Invalid date! Try again.")
                sendInlineMessageForBookingDate(chat_id)

def sendInlineMessageForStartTime(chat_id):
    global booking_start_time
    global update_id_for_booking_of_time_slot
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Enter the start time [00:00 - 23:59]:")
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    update_id_for_booking_of_time_slot=''
                    event_description=''
                    booking_date=''
                    booking_start_time=''
                    booking_end_time=''
                    sendMessage(chat_id,"Event cancelled! See you again soon.")
                    run()
                elif check_time(current_last_msg)==True:
                    booking_start_time=current_last_msg
                    update_id_for_booking_of_time_slot=current_update_id
                    sendInlineMessageForEndTime(chat_id)
                    break
                else:
                    sendMessage(chat_id,"Please use the 24hr format!")
                    sendInlineMessageForStartTime(chat_id)

def sendInlineMessageForEndTime(chat_id):
    global booking_end_time
    global update_id_for_booking_of_time_slot
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Enter the end time [00:00 - 23:59]:")
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    update_id_for_booking_of_time_slot=''
                    event_description=''
                    booking_date=''
                    booking_start_time=''
                    booking_end_time=''
                    sendMessage(chat_id,"Event cancelled! See you again soon.")
                    run()
                elif check_time(current_last_msg)==True:
                    booking_end_time=current_last_msg
                    update_id_for_booking_of_time_slot=current_update_id
                    sendBookingSuccess(chat_id)
                    break
                else:
                    sendMessage(chat_id,"Please use the 24hr format!")
                    sendInlineMessageForEndTime(chat_id)

def sendEventSuccess(chat_id):
    #global event_link
    text_message='Success! Event is set on '+booking_date+'.'
    keyboard={'inline_keyboard':[
                        [{'text':'View Google Calendar', 'url':'https://www.google.com/calendar'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def sendEventFailure(chat_id):
    text_message='Clash! Unable to create new event as there is already an event set at this timing.'
    keyboard={'inline_keyboard':[
                        [{'text':'Check Google Calendar', 'url':'https://www.google.com/calendar'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def sendBookingSuccess(chat_id):
    global update_id_for_booking_of_time_slot
    global event_description, booking_date, booking_start_time, booking_end_time
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Setting event now, please wait...")
        response=book_timeslot(event_description,booking_date,booking_start_time,booking_end_time)
        if response == True:
            sendEventSuccess(chat_id)
            run()
        else:
            update_id_for_booking_of_time_slot=''
            #sendMessage(chat_id,"An error has occurred. Please try again later.")
            sendEventFailure(chat_id)
            run()

def sendGoogleCalendar(chat_id):
    text_message='Check and modify your events via this link.'
    keyboard={'inline_keyboard':[
                        [{'text':'Open Google Calendar', 'url':'https://www.google.com/calendar'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response


#----------------------------------- recurring events -----------------------------------------
def sendRecurringDescription(chat_id):
    global event_description
    global update_id_for_booking_of_time_slot
    sendMessage(chat_id, 'What kind of recurring event do you want to set? Enter name of recurring event:')
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                update_id_for_booking_of_time_slot=''
                event_description=''
                booking_date=''
                booking_start_time=''
                booking_end_time=''
                sendMessage(chat_id,"Event cancelled! See you again soon.")
                run()
            elif current_last_msg != '/quit':
                event_description = current_last_msg
                print(event_description)
                sendRecurringFrequency(chat_id)

def sendRecurringFrequency(chat_id):
    global event_freq, event_count
    global update_id_for_booking_of_time_slot
    sendMessage(chat_id, 'Please enter the event frequency, followed by the event count:\n<daily / weekly / monthly / yearly>, <count>')
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                update_id_for_booking_of_time_slot=''
                event_description=''
                booking_date=''
                booking_start_time=''
                booking_end_time=''
                sendMessage(chat_id,"Event cancelled! See you again soon.")
                run()
            else:
                punc = '''![]{;}'"\ ,<>.?#$%^_~'''  #remove punctuations AND space except / : - & () *
                for ele in current_last_msg:  
                    if ele in punc:  
                        current_last_msg = current_last_msg.replace(ele, "")
                current_last_msg = current_last_msg.lower()   #change to lowercase
                if current_last_msg.startswith('daily'):
                    event_freq = 'DAILY'
                    event_count = current_last_msg[5:]
                    update_id_for_booking_of_time_slot=current_update_id
                    sendRecurringBookingDate(chat_id)
                elif current_last_msg.startswith('weekly'):
                    event_freq = 'WEEKLY'
                    event_count = current_last_msg[6:]
                    update_id_for_booking_of_time_slot=current_update_id
                    sendRecurringBookingDate(chat_id)
                elif current_last_msg.startswith('monthly'):
                    event_freq = 'MONTHLY'
                    event_count = current_last_msg[7:]
                    update_id_for_booking_of_time_slot=current_update_id
                    sendRecurringBookingDate(chat_id)
                elif current_last_msg.startswith('yearly'):
                    event_freq = 'YEARLY'
                    event_count = current_last_msg[6:]
                    update_id_for_booking_of_time_slot=current_update_id
                    sendRecurringBookingDate(chat_id)
                else:
                    sendMessage(chat_id, 'Please use the appropriate format! E.g. Weekly, 13')
                    sendRecurringFrequency(chat_id)

def sendRecurringBookingDate(chat_id):
    global booking_date
    global update_id_for_booking_of_time_slot
    sendMessage(chat_id, 'Enter the first event date in the format YYYY-MM-DD')
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                update_id_for_booking_of_time_slot=''
                event_description=''
                booking_date=''
                booking_start_time=''
                booking_end_time=''
                sendMessage(chat_id,"Event cancelled! See you again soon.")
                run()
            elif check_date(current_last_msg)==True:
                booking_date=current_last_msg
                update_id_for_booking_of_time_slot=current_update_id
                sendRecurringStartTime(chat_id)
            else:
                sendMessage(chat_id,"Invalid date! Try again.")
                sendRecurringBookingDate(chat_id)

def sendRecurringStartTime(chat_id):
    global booking_start_time
    global update_id_for_booking_of_time_slot
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Enter the event start time [00:00 - 23:59]:")
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    update_id_for_booking_of_time_slot=''
                    event_description=''
                    booking_date=''
                    booking_start_time=''
                    booking_end_time=''
                    sendMessage(chat_id,"Event cancelled! See you again soon.")
                    run()
                elif check_time(current_last_msg)==True:
                    booking_start_time=current_last_msg
                    update_id_for_booking_of_time_slot=current_update_id
                    sendRecurringEndTime(chat_id)
                    break
                else:
                    sendMessage(chat_id,"Please use the 24hr format!")
                    sendRecurringStartTime(chat_id)

def sendRecurringEndTime(chat_id):
    global booking_end_time
    global update_id_for_booking_of_time_slot
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Enter the event end time [00:00 - 23:59]:")
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    update_id_for_booking_of_time_slot=''
                    event_description=''
                    booking_date=''
                    booking_start_time=''
                    booking_end_time=''
                    sendMessage(chat_id,"Event cancelled! See you again soon.")
                    run()
                elif check_time(current_last_msg)==True:
                    booking_end_time=current_last_msg
                    update_id_for_booking_of_time_slot=current_update_id
                    setRecurringEvent(chat_id)
                    break
                else:
                    sendMessage(chat_id,"Please use the 24hr format!")
                    sendRecurringEndTime(chat_id)

def recurringEventSuccess(chat_id):
    global event_freq, event_count
    #global event_link
    if event_freq == 'DAILY':
        duration = 'days'
    if event_freq == 'WEEKLY':
        duration = 'weeks'
    if event_freq == 'MONTHLY':
        duration = 'months'
    if event_freq == 'YEARLY':
        duration = 'years'
    text_message='Success! Recurring event is set for '+event_count+' '+duration+'.'
    keyboard={'inline_keyboard':[
                        [{'text':'View Google Calendar', 'url':'https://www.google.com/calendar'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def recurringEventFailure(chat_id):
    text_message='Clash! Unable to create new event as there is already an event set at this timing.'
    keyboard={'inline_keyboard':[
                        [{'text':'Check Google Calendar', 'url':'https://www.google.com/calendar'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def setRecurringEvent(chat_id):
    global update_id_for_booking_of_time_slot
    global event_description, event_freq, event_count, booking_date, booking_start_time, booking_end_time
    if update_id_for_booking_of_time_slot!='':
        sendMessage(chat_id,"Setting event now, please wait...")
        #event_freq = 'DAILY'
        #event_count = '3'
        response=recurring_events(event_description,booking_date,booking_start_time,booking_end_time,event_freq,event_count)
        if response == True:
            recurringEventSuccess(chat_id)
            run()
        else:
            update_id_for_booking_of_time_slot=''
            #sendMessage(chat_id,"An error has occurred. Please try again later.")
            recurringEventFailure(chat_id)
            run()


#------------------------------------------ map -----------------------------------------------
def showMap(chat_id):
    text_message='Click on any of the following buttons to view the NTU interactive map and get real-time directions to your destination. \U0001F9ED \n\n(Remember to enable your location services!)'
    keyboard={'inline_keyboard':[
                        [{'text':'Colleges, Schools, and Institutes', 'url':'https://bit.ly/3c70XTC'}],
                        [{'text':'LTs and Tutorial Rooms', 'url':'https://bit.ly/3f8UVn4'}],
                        [{'text':'Labs, Studios, and Workshops', 'url':'https://bit.ly/3rbkWVk'}],
                        #[{'text':'Offices and Departments', 'url':'https://bit.ly/3tKFeqf'}],
                        [{'text':'Halls and Accommodations', 'url':'https://bit.ly/2Qrn66F'}],
                        [{'text':'Others', 'url':'https://bit.ly/3c6P8gb'}],
            ]}
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response


#------------------------------------------ calc -----------------------------------------------
def calc():
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        try:
            if prev_last_msg==current_last_msg and current_update_id==prev_update_id:
                print('continue')
                continue
            elif current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed calculator. If you want to do calculations together again, send /calc.')
                    run()
                elif current_last_msg in ('/operators','/help'):
                    sendMessage(chat_id, 'List of operators:\n \U00002795        Add\n \U00002796        Subtract\n   *          Multiply\n   /           Divide\n  %          Modulus\n  **          Exponential\n  ( )          Brackets\n sin(x)     Sine function\ncos(x)     Cosine function\n  pi          Pi function')
                    print('operators')
                    calc()
                else:
                    current_last_msg = current_last_msg.replace("sin", "math.sin")
                    current_last_msg = current_last_msg.replace("Sin", "math.sin")
                    current_last_msg = current_last_msg.replace("cos", "math.cos")
                    current_last_msg = current_last_msg.replace("Cos", "math.cos")
                    current_last_msg = current_last_msg.replace("pi", "math.pi")
                    current_last_msg = current_last_msg.replace("Pi", "math.pi")
                    results = eval(str(current_last_msg))
                    print(results)
                    sendMessage(chat_id,'Answer: '+str(results))
                    calc()
        except:
            print('Unable to calculate!')
            sendMessage(chat_id,'Invalid input. Use /operators to view list of available operators or use /quit to exit calculator function.')
            calc()


#------------------------------------------ Timer -----------------------------------------------
def close_timer(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Closed timer function. Use /timer if you want to set a timer.')
    #run() > list index empty cannot run

def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Beep beep! Timer\'s up. \U0000231B')

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def set_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        print(context.args[0])  #show time
        print(context.args[1])  #show seconds, minutes, or hours
        due = int(context.args[0])
        length = str(context.args[1])
        if due < 0:
            update.message.reply_text('Sorry we cannot go back to the past!')
            return
        elif due == 0:
            update.message.reply_text('That is now.')
            return
        else:
            if length in ('seconds','second','secs','sec'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                context.job_queue.run_once(alarm, due, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' second(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length in ('minutes','minute','mins','min'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                minute = due*60
                context.job_queue.run_once(alarm, minute, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' minute(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length in ('hours','hour','hrs','hr'):
                job_removed = remove_job_if_exists(str(chat_id), context)
                hour = due*3600
                context.job_queue.run_once(alarm, hour, context=chat_id, name=str(chat_id))

                text = 'Timer successfully set for '+str(due)+' hour(s)!'
                if job_removed:
                    text += ' Old one was removed.'
                update.message.reply_text(text)
            elif length == '':
                text = 'Please specify time (seconds / minutes / hours).'
                update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Use /set <timing> to set a timer. Remember to specify time (seconds/minutes/hours).')

def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Timer has been cancelled.' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)

def run_timer() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("timer", timer))
    dispatcher.add_handler(CommandHandler("set", set_timer))
    dispatcher.add_handler(CommandHandler("unset", unset))
    dispatcher.add_handler(CommandHandler("quit", close_timer))

    # Start the Bot
    updater.start_polling()

    updater.idle()


#------------------------------------------ To-Do -----------------------------------------------
def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):   #set offset > last message_id
    url = URL + "getUpdates"
    if offset:
        url += "?offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def handle_updates(updates):
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        print('continue')

        done_response = ['Well done!','Keep up the good work!','Great job!','Nice work!','Awesome!','Keep going!','Great work!']

        if text in ("add","Add","do","Do","done","Done","delete","Delete"):
            text = text.lower()
            if text != 'done':
                text = 'to '+text
            send_message("Please specify item "+text+"!", chat)
        elif text.startswith("add "):
                text = "\U000025AB"+text[4:]
                db.add_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text.startswith("Add "):
            text = "\U000025AB"+text[4:]
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text.startswith("do "):
            text = "\U000025AB"+text[3:]
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text.startswith("Do "):
            text = "\U000025AB"+text[3:]
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = "\n".join(items)
            send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text in ("done all","Done all","delete all","Delete all"):
            db.delete_all(chat)
            send_message("All items removed from list!", chat)
        elif text.startswith("done "):
            text = "\U000025AB"+text[5:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                done_response = random.choice(done_response)
                send_message(done_response+" Your to-do list has been updated.", chat)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in to-do list.", chat)
        elif text.startswith("Done "):
            text = "\U000025AB"+text[5:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                done_response = random.choice(done_response)
                send_message(done_response+" Your to-do list has been updated.", chat)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in to-do list.", chat)
        elif text.startswith("delete "):
            text = "\U000025AB"+text[7:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                done_response = random.choice(done_response)
                send_message(done_response+" Your to-do list has been updated.", chat)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in to-do list.", chat)
        elif text.startswith("Delete "):
            text = "\U000025AB"+text[7:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                done_response = random.choice(done_response)
                send_message(done_response+" Your to-do list has been updated.", chat)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in to-do list.", chat)
        elif text.startswith("show"):
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by adding items into your to-do list!", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text.startswith("Show"):
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by adding items into your to-do list!", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text == "/show":
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by adding items into your to-do list!", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
        elif text == "/quit":
            send_message("Closed to-do list. If you wish to add or remove to-do items, send /todo.", chat)
            run()
        else:
            send_message("Here are some terms you can use:\n\nadd... / do... - to add items into the list\ndelete... / done... - to remove items from list\ndelete all / done all - to remove all items\n/show - to view your to-do list\n/quit - to exit to-do function", chat)

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def offset():
    url='https://api.telegram.org/bot'+str(api_key)+'/getUpdates?offset=-1'
    response = requests.get(url)
    return response

def get_todo():
    db.setup()
    offset()
    last_update_id = None 
    while True:
        updates = get_updates(last_update_id)
        print('to-do')
        #print(updates)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)

"""
def to_do():
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        current_last_msg = current_last_msg.lower()   #change to lowercase
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                sendMessage(chat_id, 'Closed To-Do list. If you want to check, add, or remove items from your to-do list again, send /todo.')
                run()
            else:
                get_todo()
                response = get_todo()
                #result = str(get_todo())
                #sendMessage(chat_id, result)
                if response == True:
                    print('done to do')
                    to_do()


            elif current_last_msg.startswith("add "):
                add_todo()
            elif current_last_msg.startswith("done "):
                delete_todo()
            elif current_last_msg.startswith("show"):
                show_todo()
            elif current_last_msg == '/showlist':
                show_todo()
            else:
                sendMessage(chat_id, 'Sorry, I do not understand. Try using words like \"add\", \"done\", or \"show\" to command me. Send /quit to exit this function.')
"""

#---------------------------------------- Gpa calc -----------------------------------------------

def gpa_name(chat_id,i):
    global name1, name2, name3, name4, name5, name6
    sendMessage(chat_id, 'Name of Course '+str(i)+':')
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                i = 1
                run()
            else:
                if i==1:
                    name1 = current_last_msg
                    gpa_grade(chat_id,i)
                if i==2:
                    name2 = current_last_msg
                    gpa_grade(chat_id,i)
                if i==3:
                    name3 = current_last_msg
                    gpa_grade(chat_id,i)
                if i==4:
                    name4 = current_last_msg
                    gpa_grade(chat_id,i)
                if i==5:
                    name5 = current_last_msg
                    gpa_grade(chat_id,i)
                if i==6:
                    name6 = current_last_msg
                    gpa_grade(chat_id,i)


def gpa_grade(chat_id,i):
    global grade1, grade2, grade3, grade4, grade5, grade6
    sendMessage(chat_id, 'Grade:')
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                i = 1
                run()
            else:
                if i==1:
                    grade1 = current_last_msg
                    gpa_au(chat_id,i)
                if i==2:
                    grade2 = current_last_msg
                    gpa_au(chat_id,i)
                if i==3:
                    grade3 = current_last_msg
                    gpa_au(chat_id,i)
                if i==4:
                    grade4 = current_last_msg
                    gpa_au(chat_id,i)
                if i==5:
                    grade5 = current_last_msg
                    gpa_au(chat_id,i)
                if i==6:
                    grade6 = current_last_msg
                    gpa_au(chat_id,i)

def gpa_au(chat_id,i):
    global au1, au2, au3, au4, au5, au6
    sendMessage(chat_id, 'No. of AUs:')
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg != prev_last_msg:
            if current_last_msg == '/quit':
                sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                i = 1
                run()
            else:
                if i==1:
                    au1 = current_last_msg
                    gpa_summary(chat_id,i)
                if i==2:
                    au2 = current_last_msg
                    gpa_summary(chat_id,i)
                if i==3:
                    au3 = current_last_msg
                    gpa_summary(chat_id,i)
                if i==4:
                    au4 = current_last_msg
                    gpa_summary(chat_id,i)
                if i==5:
                    au5 = current_last_msg
                    gpa_summary(chat_id,i)
                if i==6:
                    au6 = current_last_msg
                    gpa_summary(chat_id,i)

def sendInlineMessage(chat_id):
    text_message='Add another module?'
    keyboard={'keyboard':[
                        [{'text':'Yes'},{'text':'No'}]
                        ], 'one_time_keyboard': True} #'resize_keyboard': True
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def sendInlineMessage2(chat_id):
    text_message='Calculate expected GPA again?'
    keyboard={'keyboard':[
                        [{'text':'Yes'},{'text':'No'}]
                        ], 'one_time_keyboard': True} #'resize_keyboard': True
    key=json.JSONEncoder().encode(keyboard)
    url='https://api.telegram.org/bot'+str(api_key)+'/sendmessage?chat_id='+str(chat_id)+'&text='+str(text_message)+'&reply_markup='+key
    response = requests.get(url)
    return response

def gpa_confirm(chat_id,i):
    sendInlineMessage2(chat_id)
    i = 1
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        if current_last_msg == 'Yes':
            gpa_name(chat_id,i)
        if current_last_msg == 'No':
            sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
            run()

def gpa_summary(chat_id,i):
    global name1, name2, grade1, grade2, au1, au2
    if i==1:
        print('Name:'+name1+' Grade:'+grade1+' AU:'+au1)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)
                    
    if i==2:
        print('Name:'+name2+' Grade:'+grade2+' AU:'+au2)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*\n2. Name: *'+name2+'*  Grade: *'+grade2+'*  AUs: *'+au2+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)

    if i==3:
        print('Name:'+name3+' Grade:'+grade3+' AU:'+au3)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*\n2. Name: *'+name2+'*  Grade: *'+grade2+'*  AUs: *'+au2+'*\n3. Name: *'+name3+'*  Grade: *'+grade3+'*  AUs: *'+au3+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)

    if i==4:
        print('Name:'+name4+' Grade:'+grade4+' AU:'+au4)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*\n2. Name: *'+name2+'*  Grade: *'+grade2+'*  AUs: *'+au2+'*\n3. Name: *'+name3+'*  Grade: *'+grade3+'*  AUs: *'+au3+'*\n4. Name: *'+name4+'*  Grade: *'+grade4+'*  AUs: *'+au4+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)

    if i==5:
        print('Name:'+name5+' Grade:'+grade5+' AU:'+au5)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*\n2. Name: *'+name2+'*  Grade: *'+grade2+'*  AUs: *'+au2+'*\n3. Name: *'+name3+'*  Grade: *'+grade3+'*  AUs: *'+au3+'*\n4. Name: *'+name4+'*  Grade: *'+grade4+'*  AUs: *'+au4+'*\n5. Name: *'+name5+'*  Grade: *'+grade5+'*  AUs: *'+au5+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)

    if i==6:
        print('Name:'+name6+' Grade:'+grade6+' AU:'+au6)
        sendHelpMessage(chat_id, '1. Name: *'+name1+'*  Grade: *'+grade1+'*  AUs: *'+au1+'*\n2. Name: *'+name2+'*  Grade: *'+grade2+'*  AUs: *'+au2+'*\n3. Name: *'+name3+'*  Grade: *'+grade3+'*  AUs: *'+au3+'*\n4. Name: *'+name4+'*  Grade: *'+grade4+'*  AUs: *'+au4+'*\n5. Name: *'+name5+'*  Grade: *'+grade5+'*  AUs: *'+au5+'*\n6. Name: *'+name6+'*  Grade: *'+grade6+'*  AUs: *'+au6+'*')
        #sendMessage(chat_id, 'Add another module?')
        sendInlineMessage(chat_id)
        prev_last_msg,chat_id,prev_update_id=getLastMessage()
        while True:
            current_last_msg,chat_id,current_update_id=getLastMessage()
            if current_last_msg != prev_last_msg:
                if current_last_msg == '/quit':
                    sendMessage(chat_id, 'Closed GPA calculator. Send /gpa if you wish to calculate your expected gpa.')
                    i = 1
                    run()
                else:
                    if current_last_msg=='Yes':
                        i+=1
                        gpa_name(chat_id,i)
                    if current_last_msg=='No':
                        sendMessage(chat_id, 'Calculating semester gpa now...')
                        gpa_calculate(chat_id,i)

def grading(grade):
    if grade == 'A+':
        return 5
    elif grade == 'A':
        return 5
    elif grade == 'A-':
        return 4.5
    elif grade == 'B+':
        return 4
    elif grade == 'B':
        return 3.5
    elif grade == 'B-':
        return 3
    elif grade == 'C+':
        return 2.5
    elif grade == 'C':
        return 2
    elif grade == 'D+':
        return 1.5
    elif grade == 'D':
        return 1
    elif grade == 'F':
        return 0

def gpa_calculate(chat_id,i):
    global au1, grade1, au2, grade2, au3, grade3, au4, grade4, au5, grade5, au6, grade6
    if i==1:
        total = int(au1)
        grade1 = grading(grade1)
        gpa = (grade1*int(au1))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)

    if i==2:
        total = int(au1)+int(au2)
        grade1 = grading(grade1)
        grade2 = grading(grade2)
        gpa = (grade1*int(au1)+grade2*int(au2))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)

    if i==3:
        total = int(au1)+int(au2)+int(au3)
        grade1 = grading(grade1)
        grade2 = grading(grade2)
        grade3 = grading(grade3)
        gpa = (grade1*int(au1)+grade2*int(au2)+grade3*int(au3))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)

    if i==4:
        total = int(au1)+int(au2)+int(au3)+int(au4)
        grade1 = grading(grade1)
        grade2 = grading(grade2)
        grade3 = grading(grade3)
        grade4 = grading(grade4)
        gpa = (grade1*int(au1)+grade2*int(au2)+grade3*int(au3)+grade4*int(au4))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)

    if i==5:
        total = int(au1)+int(au2)+int(au3)+int(au4)+int(au5)
        grade1 = grading(grade1)
        grade2 = grading(grade2)
        grade3 = grading(grade3)
        grade4 = grading(grade4)
        grade5 = grading(grade5)
        gpa = (grade1*int(au1)+grade2*int(au2)+grade3*int(au3)+grade4*int(au4)+grade5*int(au5))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)

    if i==6:
        total = int(au1)+int(au2)+int(au3)+int(au4)+int(au5)+int(au6)
        grade1 = grading(grade1)
        grade2 = grading(grade2)
        grade3 = grading(grade3)
        grade4 = grading(grade4)
        grade5 = grading(grade5)
        grade6 = grading(grade6)
        gpa = (grade1*int(au1)+grade2*int(au2)+grade3*int(au3)+grade4*int(au4)+grade5*int(au5)+grade6*int(au6))/total
        print('sem gpa: '+str(gpa))
        sendHelpMessage(chat_id, 'GPA: *'+str(round(gpa, 2))+'*')
        gpa_confirm(chat_id,i)


#--------------------------------------- Main Event ----------------------------------------------
def run():

    global update_id_for_booking_of_time_slot
    global event_description, booking_date, booking_start_time, booking_end_time
    update_id_for_booking_of_time_slot=''
    prev_last_msg,chat_id,prev_update_id=getLastMessage()
    while True:
        current_last_msg,chat_id,current_update_id=getLastMessage()
        punc = '''![]{;}'"\ ,<>.?#$%^_~'''  #remove punctuations AND space except / : - & () *
        for ele in current_last_msg:  
            if ele in punc:  
                current_last_msg = current_last_msg.replace(ele, "")
        current_last_msg = current_last_msg.lower()   #change to lowercase
        if prev_last_msg==current_last_msg and current_update_id==prev_update_id:
            print('continue')
            continue
        #--------- available actions -----------
        elif current_last_msg=='/start':
            start(chat_id)
        elif current_last_msg=='heyntu':
            start(chat_id)
        elif current_last_msg in ('hey','heythere','goodmorning','goodafternoon','goodevening','morning','afternoon','evening'):
            sendGreetings(chat_id)
        elif current_last_msg in ('hello','hi','whatsup','hihi'):
            #sendMessage(chat_id, "Hey there, what do you want to do today? I'm always here to help :-)")
            argument=random.randint(0,9)
            sendMessage(chat_id, str(randomGreetings(argument)))
        elif current_last_msg in ('goodnight','night','okgoodnight','okaygoodnight'):
            goodnight_response = ['Goodnight. :-)','Goodnight! Sleep tight. :-)','Goodnight! Don\'t let the bed bugs bite. :-)','Sweet dreams!']
            goodnight_response = random.choice(goodnight_response)
            sendMessage(chat_id, goodnight_response)
        elif current_last_msg=='/help': #help list
            sendHelpMessage(chat_id, 'Hey! I am your personal assistant bot in NTU. You can manage your school schedule, view the campus map, access study tools, or enquire about any academic issue. I am always happy to help!\n\nYou can control me by sending these commands:\n\n/start - start chatting\n/quit - exit function\n\n*Planner*  \U0001F4D5 \n/addevent - create a new event\n/recurring - create recurring event\n/upcoming - view your upcoming events\n/today - view events for today\n/search - search for specific events\n/calendar - access Google Calendar\n\n*Study Tools*  \U0000270F \n/todo - create a to-do list\n/calc - use the calculator\n/timer - set a timer\n/gpa - calculate gpa\n\n*Campus Map*   \U0001F5FA \n/map - link to interactive NTU map\n\n*Enquiries* \U00002753 \n/query - ask an academic-related question')
        elif current_last_msg=='/commands': #command list
            sendHelpMessage(chat_id, 'Hey! I am your personal assistant bot in NTU. You can manage your school schedule, view the campus map, access study tools, or enquire about any academic issue. I am always happy to help!\n\nYou can control me by sending these commands:\n\n/start - start chatting\n/quit - exit function\n\n*Planner*  \U0001F4D5 \n/addevent - create a new event\n/recurring - create recurring event\n/upcoming - view your upcoming events\n/today - view events for today\n/search - search for specific events\n/calendar - access Google Calendar\n\n*Study Tools*  \U0000270F \n/todo - create a to-do list\n/calc - use the calculator\n/timer - set a timer\n/gpa - calculate gpa\n\n*Campus Map*   \U0001F5FA \n/map - link to interactive NTU map\n\n*Enquiries* \U00002753 \n/query - ask an academic-related question')
        elif current_last_msg=='/map':
            showMap(chat_id)
        elif current_last_msg=='/query':
            sendMessage(chat_id, 'Have an academic query? Ask away!')
            query(chat_id)
        elif current_last_msg=='/addevent':
            sendInlineMessageForEvent(chat_id)
        elif current_last_msg in ['quiz','lab','exam','submission','project']: #current_last_msg != prev_last_msg and current_last_msg != '/start':
            current_last_msg = current_last_msg.capitalize() #capitalize input string
            event_description=current_last_msg
            sendInlineMessageForBookingDate(chat_id)
        elif current_last_msg=='others':
            sendInlineMessageForDescription(chat_id)
        elif current_last_msg=='/calendar':
            sendGoogleCalendar(chat_id)
        elif current_last_msg=='/upcoming':
            sendMessage(chat_id, 'Here are your upcoming events:') #next 10
            upcoming_events()
        elif current_last_msg=='/today':
            sendMessage(chat_id, 'Here are your events for today:')
            today_events()
        elif current_last_msg=='/search':
            sendMessage(chat_id, 'Please specify the event you are searching for. Use /search followed by the keyword!')
        elif current_last_msg.startswith('/search'):
            sendMessage(chat_id, 'Relevant upcoming events:')
            event_desc = current_last_msg[8:]
            search_events(event_desc)
        elif current_last_msg=='/recurring':    #input your timetable schedule or annual events
            sendRecurringDescription(chat_id)
        elif current_last_msg in ('okay','ok','okie','k','kk'):
            sendMessage(chat_id,'That\'s good!')
        elif current_last_msg.startswith('thank'): #current_last_msg in ('thanku', 'thanks', 'thankyou', 'thanksalot'):
            welcome_response = ['You\'re welcome. :-)', 'No worries!', 'No problem. :-)', 'Glad to help. :-)', 'My pleasure!','No issue, I\'m happy to help! :-)']
            welcome_response = random.choice(welcome_response)
            sendMessage(chat_id, welcome_response)
        elif current_last_msg=='/quit':
            update_id_for_booking_of_time_slot=''
            event_description=''
            booking_date=''
            booking_start_time=''
            booking_end_time=''
            sendMessage(chat_id,"Have a nice day, see you again soon!")
            run()
            # return
            # continue
        elif current_last_msg=='/todo':
            sendMessage(chat_id, 'Welcome to your personal to-do list. \U0001F4CB You can add items, remove items, or view your to-do list. Try it now!') #\n\nTo begin, use terms like: \"add math assignment\", \"done math assignment\", \"show my list\", etc.')
            get_todo()
        elif current_last_msg=='/calc':
            sendMessage(chat_id, 'Have some calculations to do? Type them in below and let me help! \U0001F981')
            calc()
        elif current_last_msg=='/timer':
            sendMessage(chat_id, 'To use the timer function, send /set <timing> to set a timer.')
            run_timer()
        elif current_last_msg=='/gpa':
            i=1
            gpa_name(chat_id,i)
        else:
            sendMessage(chat_id,"Sorry, I do not understand. :-( Here's a list of commands to use if you need help!\n\n/start - start chatting with me\n/help - view full list of commands\n/addevent - add a new calendar event\n/map - view the NTU interactive map\n/query - enquire about an academic issue\n/quit - exit function")
            #query(chat_id)
  
        prev_last_msg=current_last_msg
        prev_update_id=current_update_id
        
            
if __name__ == "__main__":
    run()

    """
    bold - *text*
    italics - _text_
    underline - __text__
    link - [inline URL](http://www.example.com/)
    """
