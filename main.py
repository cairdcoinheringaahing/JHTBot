# -*- coding: utf-8 -*-

# Imports and initialization
from chatbot import Chatbot, log
import ascii_jelly
import tio

import json
import re
import requests
import time

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

def HTMLtoMD(string, no_conv=False):
        string = from_md(string)
        replace = {'strong': '**', 'code': '`', 'td': '', 'i':'*', 'b':'**'}
        if no_conv: replace = {'strong': '', 'code': '', 'td': '', 'i':'', 'b':''}
        chresc = {'lt':'<', 'gt':'>', 'amp':'&', 'quot': '"'}
        for html in replace:
                string = re.sub(r'</?{}>'.format(html), replace[html], string)
        for charesc in chresc:
                string = string.replace('&'+charesc+';', chresc[charesc])
        return re.sub("<a href='([^']+)'>((?!</td>).*)</a>", r'[\2](\1)', string)

def removeHTML(string, mode):
        if mode == 1:
                start = 10; end = -12
        if mode == 2:
                start = 4; end = -5
        return HTMLtoMD(string[start:end])

def from_md(string, p=False):
        string = re.sub(r'</?code>', '', string)
        tokens = r'([^&]*)(&#[1234567890abcdef]+;)([^&]*)'
        try: matches = list(re.match(tokens, string).groups())
        except: return string
        for i, elem in enumerate(matches):
                if re.search('^&#[1234567890abcdef]+;$', elem):
                        matches[i] = chr(int(elem[2:-1]))
        return ''.join(matches)

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
        command = HTMLtoMD(command, True)
        try: return '`' + command + '`: ' + LOOKUP[command]
        except: return 'No such command: {}'.format(command)

def addCommand(func, cmd_msg, init='@JHTBot ', sep=' '):
        # adds commands following the following pattern
        # func(a,b,c) for message '@JHTBot a b c
        if not init in commands:
                commands[init]={}
        commands[init][cmd_msg.lower()]=[func, sep]

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
                        chars = HTMLtoMD(chars, True)
                        try: room.sendMessage(':{} Converted `{}` to `{}`'.format(reply, chars, ascii_jelly.replacements[chars]))
                        except KeyError:
                                if len(chars) == 1: room.sendMessage(':{} Converted `{}` to `{}`'.format(reply, chars, chars))
                                else: room.sendMessage(':{} Unable to convert `{}`'.format(reply, chars))

        def join_ascii(room, reply, user, event, *args):
                find = ':{} Constructed the code: {}{}{}'
                repl = ''
                for chars in args:
                        chars = HTMLtoMD(chars, True)
                        if len(chars) == 1 and ord(chars) in list(range(32, 128)):
                                repl += chars
                        else:
                                try: repl += ascii_jelly.replacements[chars]
                                except KeyError:
                                        return room.sendMessage(':{} Unable to convert `{}`'.format(reply, chars))
                repl += ' ' * (repl[-1] == '`')
                forms = [reply, '`'+'`'*('`' in repl), repl, '`'+'`'*('`' in repl)]
                room.sendMessage(find.format(*forms))

        def help_msg(room, reply, user, event, *args):
                if len(args) == 1:
                        about = args[0].lower()
                else:
                        about = 'all'
                cmds = list(sorted(commands['@JHTBot '].keys()))
                cmds.remove('codepage')
                cmds.remove('code page')
                cmds.append('replace codes')
                if about == 'all':
                        msg = '''Hello! I am JHTBot, a chatbot used as a learning resource in [Jelly Hypertraining](https://chat.stackexchange.com/rooms/57815/jelly-hypertraining)\nTo find information about each command, send `@JHTBot help:<command>`\nThe current available commands are:\n{}'''.format(', '.join(cmds))
                if about == 'addinput':
                        msg = '''Usage: `@JHTBot addinput <string>`\nAdds `<string>` to the current list of inputs'''
                if about == 'clearinput':
                        msg = '''Usage: `@JHTBot clearinput`\nClears the list of inputs'''
                if about.replace('_', '').replace(' ', '') == 'codepage':
                        msg = '''Usage: `@JHTBot Code page`\nReturns the complete Jelly code page in lexographical order'''
                if about == 'construct':
                        msg = '''Usage: `@JHTBot Replace <code> <code> (...) <code>`\nGenerates a single string sent as a single message constructed from the codes given'''
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
                        msg == '''Usage: `@JHTBot Run <code> [<arg1>, ... <argn>]`\nRuns the given code, and repliues with the correct output'''

                room.sendMessage(((':{} '.format(reply))*(about != 'all')) + msg.split('\n')[0])
                for message in msg.split('\n')[1:]:
                        room.sendMessage(message)

        def run_tio(room, reply, user, event, *args):
                if len(args) > 1: code, *args = args
                else: code = args[0]; args = '[]'
                if INPUTS: local_ins = '\n'.join(INPUTS.copy())
                else: local_ins = '' 
                args = ' '.join(args)
                code = from_md(code)
                if args[0] != '[' and args[-1] != ']':
                        args = '[' + args + ']'
                try: args = eval(args)
                except: pass
                #try:
                out, err = tio.sendreq(code, args, local_ins)
                #except: return room.sendMessage(':{} No output produced, check TIO'.format(reply))
                exit_code = int(ERR_RESPONSE.findall(err.strip())[0])
                room.sendMessage('    @{}\n    {}'.format(user, out))

        def add_input(room, reply, user, event, *args):
                if not args: return
                INPUTS.append(' '.join(args))
                room.sendMessage(":{} Added '{}' as an input".format(reply, INPUTS[-1]))

        def clear_input(room, reply, user, event, *args):
                INPUTS.clear()
                room.sendMessage(':{} Cleared input'.format(reply))
                
        addCommand(describe, 'describe')
        addCommand(find, 'find')
        addCommand(code_page, 'codepage')
        addCommand(code_page, 'code page', sep='//')
        addCommand(code_page, 'code_page')
        addCommand(from_ascii, 'replace')
        addCommand(join_ascii, 'construct')
        addCommand(help_msg, 'help', sep=':')
        addCommand(run_tio, 'run')
        addCommand(add_input, 'addinput')
        addCommand(clear_input, 'clearinput')

        return unknown
        
unknown = initCommands()
        
def handleMessage(room, event):
        content = event['content']
        user_name = event['user_name']
        user_id = event['user_id']
        chat_room_name = event['room_name']
        chat_room_id = event['room_id']
        msg_id = event['message_id']
        log('[{} - {}] Got message "{}" from user {}'.format(chat_room_name, chat_room_id, content, user_name, user_id))
        username = user_name.replace(' ', '')
        found = True
        
        for init in commands:
                if content.find(init) == 0:
                        found = False
                        content_ = content[len(init):]
                        for cmd_msg in commands[init]:
                                if content_.lower().find(cmd_msg) == 0:
                                        found = True
                                        func, sep = commands[init][cmd_msg.lower()]
                                        content_ = content_[len(cmd_msg)+len(sep):]
                                        args = content_.split(sep)
                                        if args == ['']: args=[]
                                        if args == ['codes'] and cmd_msg == 'replace': return
                                        try:
                                                func(room, msg_id, username, event, *args)
                                        except Exception as e:
                                                log("An error occured while launcing function '{}' with args {} : {}".format(cmd_msg, args, repr(e)))
                                                #room.sendMessage('@cairdcoinheringaahing Uncaught error: {}'.format(repr(e)))
        if not found:
                unknown(room, msg_id, username, event, content)
                                                                
chatbot.joinRoom(57815, handleEvents) # JHT
chatbot.joinRoom(1, handleEvents) # Sandbox
