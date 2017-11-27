# -*- coding: utf-8 -*-

# Imports and initialization
from chatbot import Chatbot, log

import re
import requests
import time
import json

URL = 'https://github.com/DennisMitchell/jelly/wiki/'
ATOM = re.compile(r'''<tr>\n<td><code>(?:.{1,2}|.&[^;]*;)</code></td>\n<td>(?:(?!</td>).*)</td>\n</tr>''')
QUICK = re.compile(r'''<tr>\n<td><code>(?:.{1,2}|.&[^;]*;)</code></td>\n<td>(?:(?!</td>).*)</td>\n<td>(?:(?!</td>).*)</td>\n</tr>''')
LOOKUP = {}
NAMES = {}
chatbot = Chatbot()

n_dict = json.load(open('names.json', encoding='utf-8'))
for key in n_dict:
    value = n_dict[key]
    if type(value) == list:
        for v_key in value:
            NAMES[v_key] = key
    else:
        NAMES[value] = key

chatbot.login()

def HTMLtoMD(string):
	replace = {'strong': '**', 'code': '`', 'td': ''}
	chresc = {'lt':'<', 'gt':'>', 'amp':'&'}
	for html in replace:
		string = re.sub(r'</?{}>'.format(html), replace[html], string)
	for charesc in chresc:
		string = string.replace('&'+charesc+';', chresc[charesc])
	return re.sub('<a href="([^"]+)">((?!</td>).*)</a>', r'[\2](\1)', string)

def removeHTML(string, mode):
	if mode == 1:
		start = 10; end = -12
	if mode == 2:
		start = 4; end = -5
	return HTMLtoMD(string[start:end])

def initDescriptions(url, page):
	if page in ['Quicks', 'Syntax']: REGEX = QUICK
	else: REGEX = ATOM
	
	f = str(requests.get(url).text).strip()
	start = f.find('<tbody>')
	end = f.rfind('</tbody>')
	table = ''.join(f[start:end].split('</table>'))
	matches = list(map(lambda a: a.split('\n'), REGEX.findall(table)))
	
	for match in matches:
		if len(match) == 5:
			match = match[0], match[1], match[2]+' '+match[3], match[4]
		_, atom, des, _ = match
		LOOKUP[removeHTML(atom, 1)] = removeHTML(des, 2)
	
for page in ['Atoms', 'Quicks', 'Syntax']:
	initDescriptions(URL + page, page)

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
	try: return command + ': ' + LOOKUP[command]
	except: return 'No such command: {}'.format(command)

commands={} #format :: {init : {cmd_msg : [func, sep]}, ...}
def addCommand(func, cmd_msg, init='@JHTBot ', sep=' '):
	# adds commands following the following pattern
	# func(a,b,c) for message "@JHTBot a b c
	if not init in commands:
		commands[init]={}
	commands[init][cmd_msg]=[func, sep]

def initCommands():
	def describe(room, user, event, char):
		des = retrieve_description(char)
		log('@' + user + ' ' + des)
		room.sendMessage('@' + user + ' ' + des)

	def find(room, user, event, *args):
		args = ' '.join(args).capitalize()
		try: msg = ' Found `{}` for description: {}'.format(NAMES[args], args)
		except: msg = ' Unknown description: {}'.format(args)
		log('@' + user + msg)
		room.sendMessage('@' + user + msg)
	
	addCommand(describe, 'Describe')
	addCommand(describe, 'describe')
	addCommand(find, 'Find')
	addCommand(find, 'find')
	
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
					# This try has been commented so that the full err message can be seen
					#try:
					sent = func(room, user_name.replace(' ',''), event, *args)
					#except Exception as e:
						#log("An error occured while launcing function {} with args {} : {}".format(cmd_msg, args, e))
				
chatbot.join_room(57815, handleEvents) # JHT
chatbot.join_room(1, handleEvents) # Sandbox
