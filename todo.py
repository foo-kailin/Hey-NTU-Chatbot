import json
import requests
import time
import urllib
import re

from dbhelper import DBHelper
#from main import run

db = DBHelper()

TOKEN = '1446373870:AAEZTQdFkmUIMa6qNDVo1AngkKZyYcoV4Yw'
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):   #set offset = -1 or offset = last_update_id + 1
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
        #send_message("Welcome to your personal To-Do list. You can add items, remove items, or use /showlist to view your To-Do list.\n\nTo begin, use terms like: \"add math assignment\", \"done math assignment\", \"show my to-do\", etc. Try it now!", chat) 

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
                #return True
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
            #return True
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
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in To-Do list.", chat)
                #return True
        elif text.startswith("Done "):
            text = "\U000025AB"+text[5:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in To-Do list.", chat)
                #return True
        elif text.startswith("delete "):
            text = "\U000025AB"+text[7:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in To-Do list.", chat)
                #return True
        elif text.startswith("Delete "):
            text = "\U000025AB"+text[7:]
            if text in items:
                db.delete_item(text, chat)
                items = db.get_items(chat)
                message = "\n".join(items)
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
            else:
                message = 'Item not found in To-Do list.'
                send_message("Item not found in To-Do list.", chat)
                #return True
        elif text.startswith("show"):
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by saying \"add...\" to add items into your list.", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
        elif text.startswith("Show"):
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by saying \"add...\" to add items into your list.", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
        elif text == "/show":
            items = db.get_items(chat)
            message = "\n".join(items)
            if message == '':
                send_message("Your to-do list is empty. Start by saying \"add...\" to add items into your list.", chat)
            else:
                send_message("To-Do List \U0001F4CB:\n\n"+message, chat)
                #return True
        elif text == "/quit":
            #message = 'Closed To-Do list. If you want to add or remove items from your to-do, send /todo.'
            send_message("Closed to-do list. If you want to add or remove to-do items, send /todo.", chat)
            #run()
        else:
            send_message("Sorry, invalid input. You can use terms like:\n\nadd... / do... - to add items into the list\ndelete... / done... - to remove items from list\n/show - to view your to-do list\n/quit - to exit to-do function", chat)

"""
def add_todo():
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        print('continue')
        text = text[4:]
        db.add_item(text, chat)
        items = db.get_items(chat)
        todo_message = "\n".join(items)
        send_message("To-Do List:\n\n"+todo_message, chat)


def delete_todo():
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        print('continue')
        text = text[5:]
        if text in items:
            db.delete_item(text, chat)
            items = db.get_items(chat)
            todo_message = "\n".join(items)
            send_message("To-Do List:\n\n"+todo_message, chat)
        else:
            send_message("Item not found in To-Do list.", chat)


def show_todo():
    for update in updates["result"]:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        items = db.get_items(chat)
        print('continue')
        items = db.get_items(chat)
        todo_message = "\n".join(items)
        send_message("To-Do List:\n\n"+todo_message, chat)
"""

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def get_todo():
    db.setup()
    last_update_id = None 
    while True:
        updates = get_updates(last_update_id)
        print('continue')
        #print(updates)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    get_todo()