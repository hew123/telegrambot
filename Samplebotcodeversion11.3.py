# Importing relevant databases to work with our code
from __future__ import print_function                                                           
import httplib2                                                                                 
import os
from pprint import pprint 

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import sys
import time, datetime           
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


# Bot initialisation.
TOKEN = '233924861:AAHUzDmgh_B6gpMwm-MWcht7PfFZCaXg7CI' 
bot = telepot.Bot(TOKEN)
bot_details = bot.getMe()


# This allows us to work with Google Sheets. (Permissions)
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'     # Read/Write Access
CLIENT_SECRET_FILE = 'client_secret.json'                   #Google API Client Authentication
APPLICATION_NAME = 'Google Sheets API Python Quickstart'    


# Function that gets valid user credentials from storage to let you have access to google sheets.
# If nothing stored, or if stored credentials invalid, OAuth2 flow is completed to obtain new credentials.
def get_credentials():
    credential_path = 0
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: 
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
# for us to be able to use Google Sheets, we are required to provide the required credentials


# Function that aids us in reading/writing to Google Sheets.
def GSheet(user_id, query_data, range_name, mode):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1HnYCaSBNhlSML-Tj1d5uiPnsz1d6IgUiCTczxsg7sxY'
    # Our Google Spreadsheet Unique Identifier
    
    values = [ query_data ]
    # telling our program what we want to update
    #print(values)
    body = {
      'values': values
    }

    if str(mode) == 'Read': # Specific only to read values from GSheet
        all_data = []
        result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=range_name).execute()
        values = result.get('values', [])
        if not values: # GSheet is empty.
            print('No data found.')
        else:
            for row in values:
                all_data.append(row)
        counter = len(all_data)
        return counter, all_data
    elif str(mode) == 'Update': # Specific only to update values to GSheet (anywhere)
        result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheetId, range=range_name,
        valueInputOption='RAW', body=body).execute()
    # results = print whatever query_data we have obtained to google docs
    else: # mode = append (Specific only to add values to last row of GSheet)
        result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId, range=range_name,
        valueInputOption='RAW', body=body).execute()
    # results = print whatever query_data we have obtained to google docs
# GSheet()
# first few lines: linking it to our specific Google Spreadsheet
# depending on the function called upon: read/update/append
# read: a list is created, the values in the spreadsheet are obtained and appended into the list
# read: and then printed out depending on the function being used.
# update: a function that involves replacing existing values in the sheets
# append: adding details to the first available line in the sheets


# Function that takes in messages and interpret it for use
def handle(msg):           
    pprint(msg)  # making use of pprint to paraphrase-print out the message for neatness
    content_type, chat_type, user_id = telepot.glance(msg)   # python will find out the important parts of the message using glance
    # Glance through important parts of message, returns the content & chat type, user_id.
    message = msg['text']
    
    if chat_type == "group": # User initiates conversation in a group. 
        main_id = msg['chat']['id'] # ID of group chat
        user_id = msg['from']['id'] # ID of user initiating command
        # Command, /....@(botname), hence removing bot name.
        specialchar_pos = message.find('@') 
        message = message[:specialchar_pos] # Actual message
    else: # user talks to bot in pm
        main_id = user_id
        message = msg['text']
        pass

    print(content_type, chat_type, user_id, "|", message)
    # Display important info for us to see - what kind of message is it? private chat? chat id-who is it from? & message received

    # Initialization of bot, requires user to register with an alias his contacts know him/her by. 
    if message == "/start":
        bot.sendMessage(user_id, "Hello there! What is your alias that your contacts know you by? ")
        bot.sendMessage(user_id, "This will be seen by your contacts when you RSVP.")
        counter, all_users = GSheet(user_id, None, 'ID-Name Matching!A2:B', 'Read')
        if str(user_id) in str(all_users):
            for user in range(len(all_users)):
                if all_users[user][0] == str(user_id):
                    Username = ValidateInput(user_id)
                    query_data = [Username]
                    GSheet(user_id, query_data, 'ID-Name Matching!B%s' % (user + 2), 'Update')
                    bot.sendMessage(user_id, 'Name (%s) updated.' % Username)
                else:
                    pass
        else:
            Username = ValidateInput(user_id)
            query_data = [user_id,Username]
            GSheet(user_id, query_data, 'ID-Name Matching!A2:B', 'Append')
            bot.sendMessage(user_id, 'Name (%s) registered.' % Username)
        on_chat_options(main_id)
    elif message == "/options": # Existing user wants to edit settings. Shows all options
        on_chat_options(main_id)
    elif message == "/create": # User want to create a new event.
        CreateEvent(user_id, main_id)
        # Create new events
    elif message == "/modify": # User want to modify an event
        ModifyEvent(main_id)
    elif message == "/delete": # User wants to delete an event
        DeleteEvent(user_id, main_id)
    elif message == "/track": # User wants to track their events
        TrackEvent(main_id)
    elif message == "/cancel": # Abort operation
        DoNothing(main_id)
    else:
        pass
# handle()
# the telepot.glance function paraphrase-prints a variety of information about
# the messages that is sent to the bot, which includes eg the details of the person sending the
# message, the length of the message, etc.
# after, the content of the message is determined by the bot using if, elif, else and the == operator
# depending on the message, the respective functions are called up.
 

# On user's chat message to view available options, shows all commands available
def on_chat_options(main_id):
    keyboard_options = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Create Event', callback_data='Create Event')],\
               [InlineKeyboardButton(text='Modify Event', callback_data='Modify Event')],\
               [InlineKeyboardButton(text='Track Event', callback_data='Track Event')],\
               [InlineKeyboardButton(text='Delete Event', callback_data='Delete Event')],\
               [InlineKeyboardButton(text='Cancel Operation', callback_data='Skip')]
           ])
    bot.sendMessage(main_id, 'What would you like to do? ', reply_markup=keyboard_options)
# main command to bring up all the available features of our bot


# User's choice upon selecting the options, function that captures and redirects them to the correct page
def on_callback_query(msg):
    query_id, user_id, query_data = telepot.glance(msg, flavor='callback_query')
    main_id = msg['message']['chat']['id'] # ID of group chat.
    print('Callback Query:', query_id, user_id, query_data
          )
    bot.answerCallbackQuery(query_id, text='Option %s captured.' % (query_data))
    # black box that replies you according to what you entered
    if query_data == "Create Event": # (Options) Case 1: User want to create event
        CreateEvent(user_id, main_id)
    elif query_data == "Modify Event": # (Options) Case 2: User want to modify event
        ModifyEvent(main_id)
    elif query_data == "Track Event": # (Options) Case 3: User want to track event
        TrackEvent(main_id)
    elif query_data == "Delete Event": # (Options) Case 4: Delete an event
        DeleteEvent(user_id, main_id)
    elif query_data == "Modify Event Name": # (Modify) Case 1: User wants to modify event name
        ModifyEventName(user_id, main_id)
    elif query_data == "Modify Event Date": # (Modify) Case 2: User want to modify event date
        ModifyEventDate(user_id, main_id)
    elif query_data == "Modify Event Location": # (Modify) Case 3: User want to modify event location
        ModifyEventLocation(user_id, main_id)
    elif query_data == "Modify Event AOR": # (Modify) Case 4: User want to modify event AOR
        ModifyEventAOR(user_id, main_id)
    elif query_data[:9] == "Attending": # (Attendance) Case 1: Attending
        eventid = str(int(query_data[10:]) + 1) # Slicing to get EventID user is registering for.
        UpdateAttendance(user_id, eventid, 'Attending')
    elif query_data[:13] == "Not attending": # (Attendance) Case 2: Not attending
        eventid = str(int(query_data[14:]) + 1)
        UpdateAttendance(user_id, eventid, 'Not attending')
    else: # User doesn't want to do anything
        DoNothing(user_id)
# on_callback_query()
# this function links the InlineKeyboard buttons to the various functions that we have defined
# with this function, for example if someone enters the "Create Event" button
# CreateEvent() will be called up
        
        
# Function to allow a user to create a new event
def CreateEvent(user_id, main_id):
    event_details = [] 
    counter, all_data = GSheet(None, None, 'Events Info!A2:K', 'Read') # read all events
    counter += 1 # increment by 1 to get current event number
    event_id = str(main_id) + "_" + str(format(counter, '03')) # unique event ID, userid_counter
    event_details.append(event_id) 
    currentdate = str(now.year) + '-' + str(format(now.month, '02')) + '-' + str(format(now.day, '02'))
    event_details.append(currentdate)
    bot.sendMessage(user_id, 'Let us collect some details regarding your event...')
    bot.sendMessage(user_id, 'What is the name of your event?')
    event_name = ValidateInput(user_id)
    event_details.append(event_name) 
    bot.sendMessage(user_id, 'When is your event? \n(follow the format "yyyy-mm-dd hh:mm")')
    event_date = VerifyDateTime(user_id)
    event_details.append(event_date) 
    bot.sendMessage(user_id, 'What is the location?')
    event_location = ValidateInput(user_id)
    event_details.append(event_location)
    bot.sendMessage(user_id, 'Are there any other remarks that you would like to add?')
    event_AOR = ValidateInput(user_id)
    event_details.append(event_AOR) 
    for i in range(4): # new event, no attendees.
        event_details.append('- ') 
    GSheet(user_id, event_details, 'Events Info!A2:K', 'Append')
    bot.sendMessage(main_id, '[%s]\n\nEvent Name: %s\nEvent Date/Time: %s\nEvent Location: %s\nAdditional Info: %s' % ((event_details[0].split("_"))[1], event_details[2], event_details[3], event_details[4], event_details[5]))
    keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Attending', callback_data='Attending,'+str((event_details[0].split("_"))[1]))],\
               [InlineKeyboardButton(text='Not Attending', callback_data='Not attending,'+str((event_details[0].split("_"))[1]))]
           ])
    bot.sendMessage(main_id, 'Please indicate your attendance for event [%s].' % ((event_details[0].split("_"))[1]), reply_markup = keyboard_attendance)
# CreateEvent()   
# this function initializes an empty list to store all the current event details that are found on Google Sheets.
# counter +1 to the int of all the events to get a current event number
# a unique event id will be created in the form of (userid)_(currenteventno).
# bot asks user for their input on the time/date, location etc of the event
# Upon calling the ValidateInput function, python jumps to the code at 'def ValidateInput' and loops until it becomes true and exits the loop
# THEN it will continue from the next line eg (when is your event) and repeat the process until ValidateInput is no longer called upon
# these details are then send to Google Sheets via GSheet()
# bot asks user whether they are attending or not (InlineKeyboard)
# depending on the user's input, their id is added to the GSheet column, and +1 to the number of attending or not attending respectively


# brings up four InlineKeyboard buttons for the user to choose
# comments at the bottom after ModifyEventAOR()      
def ModifyEvent(user_id):
        keyboard_modify = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Modify Event Name', callback_data='Modify Event Name')],\
               [InlineKeyboardButton(text='Modify Event Date', callback_data='Modify Event Date')],\
               [InlineKeyboardButton(text='Modify Event Location', callback_data='Modify Event Location')],\
               [InlineKeyboardButton(text='Modify Event AOR', callback_data='Modify Event AOR')]
           ])
        bot.sendMessage(user_id, 'What would you like to modify? ', reply_markup=keyboard_modify)
        
# function to change the name of an event
def ModifyEventName(user_id, main_id):
    user_events = event_tracing(main_id)
    print('123', user_events)
    all_event_list = []
    for each_event in user_events:
        all_event_list.append(each_event[2])
    bot.sendMessage(user_id, all_event_list)
    bot.sendMessage(user_id, 'Which event would you like to modify the name of?')
    Eventname = ValidateInput(user_id)
    for each_event in user_events:
        c=each_event[0].split("_")
        for j in each_event:
            if j==Eventname:
                    bot.sendMessage(user_id, 'What is the updated name of your event?')
                    UpdatedName = ValidateInput(user_id)
                    query_data = [None, None, UpdatedName, None, None, None]
                    data_pos = str(int(c[1]) + 1)
                    GSheet(user_id, query_data, 'Events Info!A%s:K' % data_pos, 'Update')
                    bot.sendMessage(user_id, 'Event name successfully changed.')
                    break

# function to change the name of an event 
def ModifyEventDate(user_id, main_id):
    user_events = event_tracing(main_id)
    all_event_list = []
    for each_event in user_events:
        all_event_list.append(each_event[2])
    bot.sendMessage(user_id, all_event_list)
    bot.sendMessage(user_id, 'Which event would you like to modify the date of?')
    Eventname = ValidateInput(user_id)
    for each_event in user_events:
        c=each_event[0].split("_")
        for j in each_event:
            if j==Eventname:
                bot.sendMessage(user_id, 'When do you want to change your event to?\n(yyyy-mm-dd hh:mm)')
                UpdatedDate = VerifyDateTime(user_id)
                query_data = [None, None, None, UpdatedDate, None, None]
                data_pos = str(int(c[1]) + 1)
                GSheet(user_id, query_data, 'Events Info!A%s:K' % data_pos, 'Update')
                bot.sendMessage(user_id, 'Event date successfully changed.')
                break

# function to change the name of an event
def ModifyEventLocation(user_id, main_id):
    user_events = event_tracing(main_id)
    all_event_list = []
    for each_event in user_events:
        all_event_list.append(each_event[2])
    bot.sendMessage(user_id, all_event_list)
    bot.sendMessage(user_id, 'Which event would you like to modify the location of?')
    Eventname = ValidateInput(user_id)
    for each_event in user_events:
        c=each_event[0].split("_")
        for j in each_event:
            if j==Eventname:
                bot.sendMessage(user_id, 'What is the new location of the event?')
                UpdatedLocation = ValidateInput(user_id)
                print(UpdatedLocation)
                query_data = [None, None, None, None, UpdatedLocation, None]
                data_pos = str(int(c[1]) + 1)
                GSheet(user_id, query_data, 'Events Info!A%s:K' % data_pos, 'Update')
                bot.sendMessage(user_id, 'Event location successfully changed.')
                break

# function to change the name of an event            
def ModifyEventAOR(user_id, main_id):
    user_events = event_tracing(main_id)
    all_event_list = []
    for each_event in user_events:
        all_event_list.append(each_event[2])
    bot.sendMessage(user_id, all_event_list)
    bot.sendMessage(user_id, 'For which event, do you want to modify the remarks of ')
    Eventname = ValidateInput(user_id)
    for each_event in user_events:
        c=each_event[0].split("_")
        for j in each_event:
            if j==Eventname:
                bot.sendMessage(user_id, 'What are your updated remarks!!')
                UpdatedAOR = ValidateInput(user_id)
                query_data = [None, None, None, None, None,  UpdatedAOR]
                data_pos = str(int(c[1]) + 1)
                GSheet(user_id, query_data, 'Events Info!A%s:K' % data_pos, 'Update')
                break
# ModifyEvent() and related functions
# event_tracing locates all the events that start with the user's telegram id (ie, all the events that have been created by the user only)
# appends these events into a list
# depending on which InlineKeyboard button the user enters, user is prompted to enter what they want to modify
# no matter what is selected, bot will ask for your current event name that you want to change
# from the list, it will find the details of the event that is being modified
# and then the bot will ask the user for the new details
# GSheet() will append the new details into the Events Info sheet
            

# function to allow a user to track an event
def TrackEvent(user_id):
    user_events = event_tracing(user_id)
    print("Track Event")
    count = 0
    while True: 
        if len(user_events) == 0:
            bot.sendMessage(user_id, 'You currently have no events.')
            break
        elif count == len(user_events):
            break
        else:
            event_id = (user_events[count][0].split('_'))[1]
            attending_list = ID_Name_Matching(str(user_events[count][7][2:]))
            print(attending_list)
            not_attending_list =  ID_Name_Matching(str(user_events[count][9][2:]))
            print(not_attending_list)
            bot.sendMessage(user_id, 'Event Name: %s [%s]\nEvent Date/Time: %s\nEvent Location: %s\nEvent AOR: %s \
                            \nAttending:\n%s\n\nNot Attending:\n%s' % (str(user_events[count][2]), str(event_id), str(user_events[count][3]),\
                            str(user_events[count][4]), str(user_events[count][5]), attending_list, not_attending_list))
            keyboard_attendance = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='Attending', callback_data='Attending,'+str(event_id))],\
                       [InlineKeyboardButton(text='Not Attending', callback_data='Not attending,'+str(event_id))]
                   ])
            bot.sendMessage(user_id, 'Please indicate your attendance for event [%s].' % (event_id), reply_markup = keyboard_attendance)
            count += 1
# function tied to TrackEvent(), that allows event creators to see the names of who is going for their event
# but only if the attendees has /start and input their own names
# so that their unique telegram id is tied to a name, in our ID Matching Sheet
def ID_Name_Matching(attendance):
    counter, all_user = GSheet(None, None, 'ID-Name Matching!A2:B', 'Read')
    attendance_list = attendance.split(', ')
    name_list = []
    for individual in attendance_list:
        for i in range(len(all_user)):
            if str(all_user[i][0]) == str(individual):
                name_list.append(all_user[i][1])
                break
            else:
                continue
    return name_list
# TrackEvent()
# event_tracing locates all the events that start with the user's telegram id (ie, all the events that have been created by the user only)
# bot counts the number of events that particular user has created (length function)
# if == 0, break
# else, GSheet() reads data from the Google Sheets
# prints out the list of people going for the very first event down the list that the user created
# +1 and loops until no more events matches the userid


# function to allow a user to delete an event
def DeleteEvent(user_id, main_id):
    user_events = event_tracing(main_id)
    all_event_list = []
    for each_event in user_events:
        all_event_list.append(each_event[2])
    bot.sendMessage(user_id, all_event_list)
    bot.sendMessage(user_id, 'Which event do you want to delete?')
    Eventname = ValidateInput(user_id)
    bot.sendMessage(user_id, 'This process is not reversible. Proceed? (Y/N)')
    valid_input = False
    while valid_input == False:
        confirmation_response = ValidateInput(user_id)
        if confirmation_response.upper() == 'Y': # Y confirmation is not case sensitive.
            print("Delete Event")
            for each_event in user_events:
                user_id = each_event[0].split("_")
                for j in each_event:
                    if j==Eventname:
                        query_data = ["X", None, None, None, None, None]
                        data_pos = str(int(user_id[1][1:]) + 1)
                        GSheet(user_id, query_data, 'Events Info!A%s:K' % data_pos, 'Update')
            valid_input = True
            bot.sendMessage(user_id, '%s has been successfully deleted.' % Eventname)
        elif confirmation_response.upper() == 'N':
            bot.sendMessage(user_id, 'Action cancelled.')
            valid_input = True
            bot.sendMessage(user_id, 'Action cancelled.')
        else:
            bot.sendMessage(user_id, 'Unrecognised input. Please try again.')
# DeleteEvent()
# event_tracing locates all the events that start with the user's telegram id (ie, all the events that have been created by the user only)
# bot asks for the name of the user event that is to be deleted
# if name matches the ones in the list, user is prompted to enter either y/n
# if y, GSheet() locates the particular event and replaces the unique id with a X
# thereby rendering the event details unable to be read as the id wont match
# effectively deleting it
# if n, action cancelled
# if something other than y/n, loops until y/n in input or operation is cancelled.


def ValidateInput(user_id):
    valid_input=False           
    while valid_input == False: 
        updates=bot.getUpdates()
        pprint(updates)
        if len(updates) == 0:
            pass
        else:
            if str(updates[0]['message']['chat']['id']) == str(user_id): 
                event_info = updates[0]['message']['text']                
                bot.sendMessage(user_id, "You have entered '%s'" % (event_info))
                valid_input=True 
                return event_info
            else:                
                pass
# ValidateInput()
# used in many other functions, this function treats whatever the user inputs as a false statement initially
# so, when it is identified as false, this function will carry on running and the message the user sends will be stores in a list
# for each element in the list, if the length of the message is not 0 aka the message contains SOMETHING, pprint it
# next, this function verifies whether the message is from the same user or not
# the event info is read and then, the message inside the list is popped to save space
# now, the bot prints the user's message for confirmation and hence, now, the input is true and the while loop isn't satisfied
# hence exiting the while loop and ending this process


def event_tracing(user_id):
    counter, all_data = GSheet(user_id, None, 'Events Info!A2:K', 'Read')
    event_fromuser = []
    for i in all_data:
        userid = i[0][:-4] #Take away the _event#
        if userid == str(user_id): #Find all the event by a specific user and append to a list
            event_fromuser.append(i)
        else:
            pass
    print(len(event_fromuser))
    print(event_fromuser)
    return event_fromuser
# event_tracing()
# the GSheet function is called upon to read the Events Info sheet
# a list is created, and for every element in the first column of this sheet (i[0]), the userid of the user is compared the id of the event
# [:-4] is slicing, with the -, aka reverse, from the back, the last four digits are singled out ( event id = (user_id)_xxx )
# if the resulting number matches the user_id, append the event to the list
# print length of the list (aka number of events), print event details


def DoNothing(user_id):
    bot.sendMessage(user_id, 'Operation cancelled.')
#meh.


def VerifyDateTime(user_id):
    valid_input=False            
    while valid_input == False: 
        updates=bot.getUpdates()
        #message_store.append(a)         
        if len(updates) == 0: 
            pass
        else:
            if str(updates[0]['message']['chat']['id']) == str(user_id):
                event_info = updates[0]['message']['text']
                from datetime import datetime
                now = datetime.now()
                one_year_later = now.replace(year=now.year+1)
                try:
                    input_datetime = datetime.strptime(event_info,'%Y-%m-%d %H:%M')
                    if(input_datetime < now):
                        bot.sendMessage(user_id,'Date cannot be before current date! Please key in again (yyyy-mm-dd hh:mm)')
                        valid_input=False
                    elif(input_datetime > one_year_later):
                        bot.sendMessage(user_id,'Date cannot be more than one year later than current date! Please key in again (yyyy-mm-dd hh:mm)')
                        valid_input=False  
                    else:
                        bot.sendMessage(user_id, "You have entered '" + event_info + "'")
                        valid_input=True
                        return event_info
                except ValueError:
                    bot.sendMessage(user_id,'Incorrect format of date and time. \nPlease key in again (yyyy-mm-dd hh:mm)')
                    valid_input=False
            else:
                pass
# VerifyDateTime()
# this function treats whatever the user inputs as a false statement initially
# so, when it is identified as false, this function will carry on running and the message the user sends will be stores in a list
# for each element in the list, if the length of the message is not 0 aka the message contains SOMETHING, pprint it
# from a = bot.getUpdates(), if the userid in a matches the id of the user, the event details will be extracted from getUpdates
# the datetime funciton will be put to use
# if the date/time entered by the user has passed, they would be denied
# else, their date/time entry will be successful
# if the enter it in the wrong format, they will be looped until the enter it in the right format/cancel operation
                    

# Functions to update the attendance of users
def UpdateAttendance(user_id, eventid, attendance):
    range_name = 'H'+eventid # Attending list.
    counter, attending_list = GSheet(user_id, None, range_name, 'Read')
    range_name = 'J'+eventid # Not attending list
    counter, not_attending_list = GSheet(user_id, None, range_name, 'Read')
    attending_list = (attending_list[0]) 
    not_attending_list = (not_attending_list[0])
    if str(attendance) == 'Attending': # User is attending
        if str(user_id) in str(attending_list): # UserID already registered.
            bot.sendMessage(user_id, 'You have already registered.')
        elif str(user_id) in str(not_attending_list): # User previously registered BUT different attendance
            RemoveAttendance(not_attending_list, user_id, eventid, 'NA') # NA = Attending
            AddAttendance(attending_list, user_id, eventid, 'A')
            bot.sendMessage(user_id, 'Attendance successfully updated (Not Attending -> Attending)')
        else:
            AddAttendance(attending_list, user_id, eventid, 'A') # First time
    else: # User not attending
        if str(user_id) in str(not_attending_list): # UserID already registered.
            bot.sendMessage(user_id, 'You have already registered.')
        elif str(user_id) in str(attending_list):
            RemoveAttendance(attending_list, user_id, eventid, 'A') # NA = Not Attending
            AddAttendance(not_attending_list, user_id, eventid, 'NA')
            bot.sendMessage(user_id, 'Attendance successfully updated (Attending -> Not Attending)')
        else: 
            AddAttendance(not_attending_list, user_id, eventid, 'NA') # First time
# UpdateAttendance()
# at column H, list of people attending, column J, list of people not attending.
# using the GSheet function, the information that comes is already in a list.
# an attending_list and not_attending_list is created. column H for attending_list, and column J for not_attending_list
# effectively, this means that attending_list contains the list of all the users whom are going for all the respective events
# and that the not_attending_list contains the list of all the users whom have indicated that they are not going for their respective events
# so, if a user indicates that he is going for any event, but he has already done so (ie clicked indicated), he will be informed that he has already registered.
# if the user indicated that he is attending but click the not attending button, he will be informed that his attendance has been updated from going to not going.
# lastly, if he indicates that he is going but his name is in neither of these two lists, it means that it is his first time registering
# his name will be naturally added to the 'attending' list.
# for the 'not attending' button, this process works similarly.

# Reflect user's attendance into the spreadsheet.
def AddAttendance(attending_list, user_id, eventid, old_attendance):
    attending_list.append(str(user_id)+', ') # Adding to the list first.
    attendees = ''.join(attending_list) # Concatenating the list of all attendees together.
    num_attending = len(attendees.split(', ')) - 1 # Split by ', ', then counting number of attendees.
    print(attendees.split(', '), '123')
    print(num_attending, 'numattend')
    if old_attendance == 'A': # Previously registered attending, so remove from attending
        query_data = [None, None, None, None, None, None, num_attending, attendees, None, None]
    else: # Previously registered NOT attending, so remove from NOT attending
        query_data = [None, None, None, None, None, None, None, None, num_attending, attendees]
    range_name = 'Events Info!A%s:K' % (eventid)
    GSheet(user_id, query_data, range_name, 'Update')
# AddAttendance()
# a string of all the users attending the event is added to a list
# the list of all the attendees are concatenated together
# this list is then split by commas, and the length is obtained to get the number of attendees.
# if the function calls for the user details to be added to the attending column, columns G and H will be updated to reflect his attendance.
# else, if the function calls for the user details to be added to the not attending column, columns I and J will be updated to reflect his attendance.

# Remove pre-existing attendance from the spreadsheet.
def RemoveAttendance(attending_list, user_id, eventid, old_attendance):
    try: 
        attending_list.remove(str(user_id)+', ')
    except ValueError: # Item is first in list and contains "- " before user_id.
        attending_list = attending_list[0].split(', ')
        attending_list.pop(0) # Removing the user_id
        attending_list.insert(0, '- ') # Adding back - for neatness and clarity. (Also, GSheet can't have blanks)
    print(attending_list)
    attendees = ''.join(attending_list) # Concatenating the list of all attendees together.
    print(attendees)
    num_attending = len(attending_list) - 2 # Split by ', ', then counting number of attendees.
    if old_attendance == 'A':
        query_data = [None, None, None, None, None, None, num_attending, attendees, None, None]
    else:
        query_data = [None, None, None, None, None, None, None, None, num_attending, attendees]
    range_name = 'Events Info!A%s:K' % (eventid)
    GSheet(user_id, query_data, range_name, 'Update')
# RemoveAttendance()
# the user's id is simply removed from the list of all attendees.
# if it results in an error, the list of attendees is split using commas, the user id is removed and then a '-' is added back in for clarity
# if the function calls for the user details to be removed from the attending column (eg he doesnt want to go for the event), it is removed
# else, his id will be in the not attending column, so the details from there will be removed instead.
                    
response = bot.getUpdates()     
pprint(response)
# get updates from the server
bot.getUpdates(offset=100000001)
# using offset essentially acknowledges to the server that you have received all update_ids lower than offset.

# a list to store current messages
#message_store = []              # a list that we created
now = datetime.datetime.now()   # getting current date, specific to the library datetime


#loop such that whenever the bot receive a message, process it depending on what type of message it is
#bot.message_loop(handle)
bot.message_loop({'chat': handle,
                  'callback_query': on_callback_query})
print('Listening ...')
