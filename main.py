# -*- coding: utf-8 -*-
## V 3.0
"""
ChangeLog
- V3.0 -
Rewrote main.py to work with the new chatbot.py
Cleaned the code



"""
## Description
"""
A chatbot used for JHT
"""

# Imports and initialization
from chatbot import Chatbot, log # chatbot.py, the chatbot framework
import random # chose a random element from a table
import shutil # file manipulation (creating images from bytes)
from PIL import Image # check if images are valid / images format conversion
from imgurpython import ImgurClient # upload images to imgur
import time # sleeping

client_id = 'fb1b922cb86bb0f'  # Imgur module setup
client_secret = 'cffaf5da440289a8923f9be60c22b26e25675d3d'
clientImg = ImgurClient(client_id, client_secret)

## Initialization
# Create chatbot
chatbot=Chatbot()
# Login to SE
chatbot.login()

def handleEvents(room, event):
	if event['user_id']==chatbot.bot_chat_id: return # don't consider events from the bot*
	if event['event_type']==1: # event: new message
		handleMessage(room, event)
	if event['event_type']==3: # event: user entered the room
		pass
	if event['event_type']==6: # event: change in the stars on a message
		pass
	if event['event_type']==10: # event: message deleted
		pass
	
def retrieve_description(command):
	pass

commands={} #format :: {init : {cmd_msg : [func, sep]}, ...}
def addCommand(func, cmd_msg, init='@JHTBot ', sep=' '):
	# adds commands following the following pattern
	# func(a,b,c) for message "!!cmd_msg/a/b/c"
	if not init in commands:
		commands[init]={}
	commands[init][cmd_msg]=[func, sep]

def initCommands():
	def decribe(room, event, char):
		des = retrieve_description(char)
		room.sendMessage(des)
	
	addCommand(describe, 'Describe')
	
initCommands()
	
def handleMessage(room, event):
	content = event["content"]
	user_name = event['user_name']
	user_id = event['user_id']
	chat_room_name = event['room_name']
	chat_room_id = event['room_id']
	log('[{} - {}] Got message "{}" from user {}, id={}'.format(chat_room_name, chat_room_id, content, user_name, user_id))
	
	for init in commands:
		if content.find(init)==0: # find if the init is registered
			content_=content[len(init):]
			for cmd_msg in commands[init]:
				if content_.find(cmd_msg)==0: # find if the command is registered
					func, sep=commands[init][cmd_msg]
					content_=content_[len(cmd_msg)+len(sep):]
					args=content_.split(sep)
					if args==['']: args=[]
					try:
						func(room, event, *args)
					except Exception as e:
						log("An error occured while launcing function {} with args {} : {}".format(cmd_msg, args, e))
				
			

chatbot.join_room(57815, handleEvents) # JHT
chatbot.join_room(1, handleEvents) # Sandbox












































