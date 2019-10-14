# -*- coding: utf-8 -*-

# Imports and initialization
from chatbot import Chatbot, log
import ascii_jelly
import webstuff

import datetime
import html as HTML
import json
import re
import requests
import time

last_msg = datetime.date(2019, 10, 11)

URL = 'https://github.com/DennisMitchell/jelly/wiki/'
ATOM = re.compile(r'''<tr>\n<td><code>(?:.{1,2}|.&[^;]*;)</code></td>\n<td>(?:(?!</td>).*)</td>\n</tr>''')
QUICK = re.compile(r'''<tr>\n<td><code>(?:.{1,2}|.&[^;]*;)</code></td>\n<td>(?:(?!</td>).*)</td>\n<td>(?:(?!</td>).*)</td>\n</tr>''')
LOOKUP = {}
NAMES = {}
CODE_PAGE = '''¡¢£¤¥¦©¬®µ½¿€ÆÇÐÑ×ØŒÞßæçðıȷñ÷øœþ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~¶°¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ƁƇƊƑƓƘⱮƝƤƬƲȤɓƈɗƒɠɦƙɱɲƥʠɼʂƭʋȥẠḄḌẸḤỊḲḶṂṆỌṚṢṬỤṾẈỴẒȦḂĊḊĖḞĠḢİĿṀṄȮṖṘṠṪẆẊẎŻạḅḍẹḥịḳḷṃṇọṛṣṭụṿẉỵẓȧḃċḋėḟġḣŀṁṅȯṗṙṡṫẇẋẏż«»‘’“”'''
commands = {}
INPUTS = []
ERR_RESPONSE = re.compile('''(?:Real time: \d{1,2}\.\d{3} s ?
User time: \d{1,2}\.\d{3} s ?
Sys\. time: \d{1,2}\.\d{3} s ?
CPU share: \d{2}\.\d{2} % ?
Exit code: )([01])''')
todolist = 'todo.txt'
owners = [274572]

chatbot = Chatbot(last_msg)

n_dict = json.load(open('names.json', encoding='utf-8'))
for key in n_dict:
        value = n_dict[key]
        if type(value) == list:
                for v_key in value:
                        NAMES[v_key] = key
        else:
                NAMES[value] = key

chatbot.login()

def strip_tags(html, to_md=True):
	if to_md: repl = {'code': '`', 'td': '', 'strong': '**', 'sup': '', 'strike': '---', 'b': '**', 'i': '*'}
	else: repl = {'code': '', 'td': '', 'strong': '', 'sup': '', 'strike': '', 'b': '', 'i': ''}
	link = re.compile(r'<a href="([^"]+)"([^>]*)>([^<]+)</a>')

	if link.search(html):
		url, _, disp = link.search(html).groups()
		hurl, hdisp = map(HTML.unescape, [url, disp])
		html = html.replace('<a href="{}"{}>{}</a>'.format(url, _, disp), '[{}]({})'.format(hdisp, hurl))

	for old, new in repl.items():
		html = re.sub(r'</?{}>'.format(old), new, html)

	return HTML.unescape(html)

def initDescriptions(url, page):
        if page in ['Quicks', 'Syntax']: REGEX = QUICK; example = ' Example: '
        else: REGEX = ATOM; example = ' '
        
        f = str(requests.get(url).text).strip()
        start = f.find('<tbody>')
        end = f.rfind('</tbody>')
        table = ''.join(f[start:end].split('</table>'))
        matches = list(map(lambda a: a.split('\n'), REGEX.findall(table)))
        
        for match in matches:
                if len(match) == 5:
                        match = match[0], match[1], match[2] + example + match[3], match[4]
                _, atom, des, _ = map(strip_tags, match)
                LOOKUP[atom] = des
        
for page in ['Atoms', 'Quicks', 'Syntax']:
        initDescriptions(URL + page, page)

def deleted(room, event_data):
        return
        roomid = event_data['room_id']
        roomname = event_data['room_name']
        message = event_data['content']
        user = event_data['user_name']
        regex = r'\[{} - {}\] Got message "{}" from user {}'
        print(regex.format(roomname, roomid, message, user))

def handleEvents(room, event):
        if 'user_id' not in event.keys():
                return
        if event['user_id'] == chatbot.bot_chat_id:
                return
        log('> [Room: {}] - Event number: {}'.format(event['room_id'], event['event_type']))
        
        if event['event_type'] == 1:            # new message
                handleMessage(room, event)
        if event['event_type'] == 2:            # message edited
                handleMessage(room, event)
        if event['event_type'] == 3:            # user joins
                log('{} joined the room!'.format(event['user_name']))
        if event['event_type'] == 4:            # user leaves
                log('{} left the room!'.format(event['user_name']))
        if event['event_type'] == 8:            # pinging
                return
        if event['event_type'] == 10:           # message deleted
                deleted(room, event)
        if event['event_type'] == 15:           # kicked / talk in gallery
                pass
        if event['event_type'] == 18:           # replying
                pass
        if event['event_type'] == 20:           # moving messages
                pass
        
def retrieve_description(command):
        command = strip_tags(command)
        try: return '`' + command.replace('`', r'\`') + '`: ' + LOOKUP[command]
        except:
                try: return '`' + command.replace('`', r'\`') + '`: ' + LOOKUP['`'+command+'`']
                except: return 'No such command: `{}`'.format(command)

def addCommand(func, cmd_msg, init='@JHTBot ', sep=' ', restrict=[]):
        # adds commands following the following pattern
        # func(a,b,c) for message '@JHTBot a b c
        if not init in commands:
                commands[init]={}
        commands[init][cmd_msg.lower()]=[func, sep, restrict]

def initCommands():
        def describe(room, reply, user, event, char):
                des = retrieve_description(char)
                room.sendMessage(':' + str(reply) + ' ' + des)

        def find(room, reply, user, event, *args):
                args = ' '.join(args).capitalize()
                try: msg = 'Found `{}` for description: {}'.format(NAMES[args], args)
                except: msg = 'Unknown description: {}'.format(args)
                room.sendMessage(':' + str(reply) + ' ' + msg)

        def unknown(room, reply, user, event, message):
                room.sendMessage(":{} Unknown command: `{}`. Send `@JHTBot help` for a list of commands".format(reply, message))

        def code_page(room, reply, user, event, *_):
                room.sendMessage('''    @{}
    {}'''.format(user, CODE_PAGE))

        def from_ascii(room, reply, user, event, *args):
                for chars in args:
                        chars = strip_tags(chars)
                        try: room.sendMessage(':{} Converted `{}` to `{}`'.format(reply, chars, ascii_jelly.replacements[chars]))
                        except KeyError:
                                if len(chars) == 1: room.sendMessage(':{} Converted `{}` to `{}`'.format(reply, chars, chars))
                                else: room.sendMessage(':{} Unable to convert `{}`'.format(reply, chars))

        def join_ascii(room, reply, user, event, *args):
                find = ':{} Constructed the code: {}{}{}'
                repl = ''
                for chars in args:
                        chars = strip_tags(chars)
                        if len(chars) == 1 and ord(chars) in list(range(32, 128)):
                                repl += chars
                        else:
                                try: repl += ascii_jelly.replacements[chars]
                                except KeyError:
                                        return room.sendMessage(':{} Unable to convert `{}`'.format(reply, chars))
                if repl[-1] == '`':
                        repl[-1] = r'\`'
                forms = [reply, '`'+'`'*('`' in repl), repl, '`'+'`'*('`' in repl)]
                room.sendMessage(find.format(*forms))

        def run_tio(room, reply, user, event, *args):
                if len(args) > 1: code, *args = args
                else: code = args[0]; args = '[]'
                if INPUTS: local_ins = '\n'.join(INPUTS.copy())
                else: local_ins = ''
                print(code, args, local_ins)
                args = ' '.join(args)
                code = strip_tags(code)
                if args and args[0] != '[' and args[-1] != ']':
                        args = '[' + args + ']'
                try: args = eval(args)
                except: pass
                
                try:
                        out, err = webstuff.sendtioreq(code, args, local_ins)
                except:
                        return room.sendMessage(':{} No output produced, check TIO'.format(reply))
                exit_code = int(ERR_RESPONSE.findall(err.strip())[0])
                if out:
                        room.sendMessage('    @{}\n    {}'.format(user, out))
                else:
                        if err:
                                err = err.split('\n\n')[0]
                                room.sendMessage('    @{}\n    Error:\n    {}'.format(user, '\n    '.join(err.split('\n'))))
                        else: room.sendMessage(':{} No output produced, check TIO'.format(reply))

        def add_input(room, reply, user, event, *args):
                INPUTS.append(' '.join(args))
                room.sendMessage(":{} Added '{}' as an input".format(reply, INPUTS[-1]))

        def clear_input(room, reply, user, event, *args):
                INPUTS.clear()
                room.sendMessage(':{} Cleared input'.format(reply))

        def read_input(room, reply, user, event, *args):
                room.sendMessage(':{} {}'.format(reply, '\n'.join(INPUTS or ['No input saved'])))

        def resources(room, reply, user, event, *args):
                room.sendMessage(':{} [Resources](https://golfingsuccess.github.io/jelly-hypertraining/)'.format(reply))

        def addtodo(room, reply, user, event, *args):
                with open(todolist, 'a') as file:
                        file.write(' '.join(args) + '\n')
                msg = ':{} Added to the todo list'.format(reply)
                room.sendMessage(msg)

        def removetodo(room, reply, user, event, *args):
                if not args:
                        return
                msg = ':{} Removed the '.format(reply)
                length = len(args)
                with open(todolist) as file:
                        contents = file.readlines()
                sieve = [1] * len(contents)
                
                while args:
                        index = int(args.pop(0)) - 1
                        sieve[index] = 0  
                        msg += '{}{}, '.format(index + 1, ['st', 'nd', 'rd', 'th'][index if index < 3 else 3])

                contents = [line for i, line in enumerate(contents) if sieve[i]]
                with open(todolist, 'w') as file:
                        file.write(''.join(contents))
                msg = msg.strip(', ') + ' item{}'.format('s' * (length > 1))
                room.sendMessage(msg)

        def readtodo(room, reply, user, event, *args):
                with open(todolist) as file:
                        contents = file.read()
                msg = ':{} Todo list\n{}'.format(reply, contents)
                room.sendMessage(msg)

        def respond(room, reply, user, event, *args):
                if not args:
                        args = ['Hello!']
                room.sendMessage(':{} {}'.format(reply, ' '.join(args)))

        def quit_(room, reply, user, event, *_):
                room.sendMessage('Goodbye!')
                quit()
                
        addCommand(describe, 'describe')
        addCommand(find, 'find')
        addCommand(code_page, 'codepage')
        addCommand(code_page, 'code page', sep='//')
        addCommand(code_page, 'code_page')
        addCommand(from_ascii, 'replace')
        addCommand(join_ascii, 'construct')
        addCommand(run_tio, 'run')
        addCommand(add_input, 'addinput')
        addCommand(clear_input, 'clearinput')
        addCommand(read_input, 'readinput')
        addCommand(resources, 'resources')
        addCommand(addtodo, 'addtodo', restrict=owners)
        addCommand(removetodo, 'removetodo', restrict=owners)
        addCommand(readtodo, 'readtodo', restrict=owners)
        addCommand(respond, 'reply')
        addCommand(respond, 'echo')
        addCommand(quit_, 'quit', restrict=owners)

        return unknown
        
initCommands()

def help_msg(room, reply, user, event, *args):
        if len(args) == 1:
                about = args[0].lower()
        else:
                about = 'all'
        cmds = list(sorted(commands['@JHTBot '].keys()))
        rem = ['codepage', 'code page']
        for r in rem:
                cmds.remove(r)
        cmds.append('replace codes')
        msg = 'Unknown help request: {}'.format(about)
        if about == 'all':
                msg = '''Hello! I am JHTBot, a chatbot used as a learning resource in [Jelly Hypertraining](https://chat.stackexchange.com/rooms/57815/jelly-hypertraining)\nTo find information about each command, send `@JHTBot help:<command>`\nThe current available commands are:\n{}'''.format(', '.join(cmds))
        if about == 'addinput':
                msg = '''Usage: `@JHTBot addinput <string>`\nAdds `<string>` to the current list of inputs'''
        if about == 'clearinput':
                msg = '''Usage: `@JHTBot clearinput`\nClears the list of inputs'''
        if about.replace('_', '').replace(' ', '') == 'codepage':
                msg = '''Usage: `@JHTBot Code page`\nReturns the complete Jelly code page in lexographical order'''
        if about == 'construct':
                msg = '''Usage: `@JHTBot Construct <code> <code> (...) <code>`\nGenerates a single string sent as a single message constructed from the codes given'''
        if about == 'describe':
                msg = '''Usage: `@JHTBot Describe <atom/quick/syntax>`\nUsed to describe the given command. Returns the official description from the wiki page'''
        if about == 'find':
                msg = '''Usage: `@JHTBot Find <name>`\nLooks for an atom, quick or syntax with the official name given.'''
        if about == 'help':
                msg = '''Hello! I am JHTBot, a chatbot used as a learning resource in [Jelly Hypertraining](https://chat.stackexchange.com/rooms/57815/jelly-hypertraining)\nTo find information about each command, send `@JHTBot help:<command>`\nThe current available commands are:\n{}'''.format(', '.join(cmds))
        if about == 'replace':
                msg = '''Usage: `@JHTBot Replace <code>`\nUsed to generate a specific symbol, dependant on the code given.'''
        if about == 'replace codes':
                msg = '''Replacement codes for the `Replace` command\nCheck [this gist](https://gist.github.com/cairdcoinheringaahing/b24ab7802c5979ab9ce398fedb811795) for a complete table'''
        if about == 'run':
                msg = '''Usage: `@JHTBot Run <code> [<arg1>, ... <argn>]`\nRuns the given code, and replies with the correct output'''
        if about == 'addtodo':
                msg = '''Usage: `@JHTBot addtodo <thing to do>`\nOnly avilable to approved users'''
        if about == 'readtodo':
                msg = '''Usage: `@JHTBot readtodo <thing to do>`\nOnly avilable to approved users'''
        if about == 'removetodo':
                msg = '''Usage: `@JHTBot removetodo <thing to do>`\nOnly avilable to approved users'''
        
        room.sendMessage(((':{} '.format(reply))*(about != 'all')) + msg.split('\n')[0])
        for message in msg.split('\n')[1:]:
                room.sendMessage(message)
                time.sleep(1)
        
def handleMessage(room, event):
        content = strip_tags(event['content'])
        user_name = event['user_name']
        user_id = event['user_id']
        chat_room_name = event['room_name']
        chat_room_id = event['room_id']
        msg_id = event['message_id']
        log('[{} - {}] Got message "{}" from user {}'.format(chat_room_name, chat_room_id, content, user_name, user_id))
        username = user_name.replace(' ', '')
        found = True

        if content.startswith('@JHTBot help:'):
                content = content[13:]
                help_msg(room, msg_id, username, event, content)
                return False

        if content.startswith('@JHTBot help'):
                content = 'all'
                help_msg(room, msg_id, username, event, content)
                return False
        
        for init in commands:
                if content.find(init) == 0:
                        content_ = content[len(init):]
                        for cmd_msg in commands[init]:
                                if content_.lower().find(cmd_msg) == 0:
                                        func, sep, allowed = commands[init][cmd_msg.lower()]
                                        if allowed:
                                                if user_id not in allowed:
                                                       room.sendMessage(':{} Who are you? Ping caird coinheringaahing if you want to do that'.format(msg_id))
                                                       return
                                                
                                        if cmd_msg[:4] == 'read':
                                                func(room, msg_id, username, event, None)
                                        content_ = content_[len(cmd_msg)+len(sep):]
                                        args = content_.split(sep)
                                        if args == ['']: args=[]
                                        if args == ['codes'] and cmd_msg == 'replace': return
                                        try:
                                                func(room, msg_id, username, event, *args)
                                                found = True
                                        except Exception as e:
                                                log("An error occured while launching function '{}' with args {} : {}".format(cmd_msg, args, repr(e)))
                                                found = False
                                                #room.sendMessage('@cairdcoinheringaahing Uncaught error: {}'.format(repr(e)))
                                                                
# chatbot.joinRoom(57815, handleEvents) # JHT
# chatbot.joinRoom(1, handleEvents)     # Sandbox
chatbot.joinRoom(71687, handleEvents) # Testing room
