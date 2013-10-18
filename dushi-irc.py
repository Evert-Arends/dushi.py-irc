#!/usr/bin/python
__version__ = "17 okt 2013"
from threading import Thread
from datetime import datetime
import argparse
import socket
import requests
import json
import sys
import random
import time
import re

# Disclaimer: Snelle & Vieze saus

# veranderbaar
ADMIN_PASS = 'CHANGE_ME'
USER = 'trolletje'
IDENT = 'bontkraagIRC'
PORT = 6667
DUSHI_CHANNEL = '#dushi'
DEBUG = True

# optioneel
CMD = '!dushi'
CMD_TRANSLATE = CMD
CMD_SET = '%s+' % CMD
CMD_UNSET = '%s-' % CMD
CMD_GET = '%s?' % CMD

# AFBLIJVEN!!1
API = 'http://dushi.nattewasbeer.nl/aapje'
DIRECT_APIS = []
API_PASS = ''

jwz = '\033[93mjwz\033[92m'
spam = '''\033[92m
 +-----------------------------------------------------------------+
 |          __           __    _         %s         _    %s      |
 | %s ____/ /_  _______/ /_  (_) ____  __  __      (_)_________   |
 |    / __  / / / / ___/ __ \/ / / __ \/ / / /_____/ / ___/ ___/   |
 |   / /_/ / /_/ (__  ) / / / / / /_/ / /_/ /_____/ / /  / /__     |
 |   \__,_/\__,_/____/_/ /_/_(_) .___/\__, /     /_/_/   \___/     |
 |              %s           /_/    /____/                        |
 | %s                                               %s           |
 |                Een aanwist voor \033[93melk\033[92m irc kanaal!                 |
 |                         -}bam G{-                               |
 +-----------------------------------------------------------------+
        | USaGe: ./%s [host] [port] [channel]            |
        +----------------------------------------------------------+
                                                     | \033[93m%s\033[92m |
                                                     +-------------+\033[0m\n'''\
       % (jwz, jwz, jwz, jwz, jwz, jwz, sys.argv[0], __version__)
for a in ['|', '+', '-']:
    spam = spam.replace(a, '\033[94m%s\033[92m' % a)

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class Boat():
    def __init__(self, client, host, channel, port, debug=True):
        self.username, self.ident = random.choice(NICKS), USER
        self.host, self.channel, self.port = host, channel, port

        self.debug = debug
        self.hostmask = True

        self.connected = False
        self.client = client

        self.nickthread = Thread(target=self.nickthread).start()

        self.only_dushi_channel = False

        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def log(self, *args, **kwargs):
        color = kwargs['color'] if 'color' in kwargs else colors.OKGREEN
        print "%(color)s%(value)s%(endc)s" % {'color': color, 'value': repr(args), 'endc': colors.ENDC}

    def join(self, room=None):
        room = self.channel if room is None else room

        self.irc.send('JOIN %s\r\n' % room)
        self.irc.send('JOIN %s\r\n' % DUSHI_CHANNEL) if DUSHI_CHANNEL else None

    def doe_ding(self):
        if self.debug:
            self.log("BEzug: ", self.host, self.channel, self.port, color=colors.WARNING)
        try:
            self.irc.connect((self.host, self.port))
        except Exception as e:
            self.log("Ewa: ", str(e), color=colors.FAIL)
            sys.exit()

        self.log(self.irc.recv(4096), color=colors.OKBLUE)

        self.nick(self.username)
        self.irc.send('USER %s foo bar :%s\r\n' % (self.ident, self.client))

        while True:
            self.process()

    def process(self, size=4096):
        data = self.irc.recv(size)

        if not self.connected:
            self.log(data, color=colors.OKBLUE)
        elif self.debug:
            if not data:
                self.log("Server dood. Wholla!", color=colors.FAIL)
                sys.exit()
            self.log(data)

        if '001 %s' % self.username in data and not self.connected:
            self.connected = True
            self.log('Bam.', color=colors.WARNING)

            self.join()

        if 'PING' in data:
            self.ping(data)
        else:
            self.jwz(data)

        if data.startswith(':') and self.username in data and ':Nickname is already in use.' in data:
            if not 'PRIVMSG %s' % self.channel in data:
                self.nick(random.choice(NICKS))
                return

    def ping(self, data):
        if self.debug:
            self.log("Pong of ", data)

        try:
            self.irc.send('PONG %s\r\n' % self.host)
        except IndexError:
            self.irc.send('EWA PONG!')

    def jwz(self, data):
        parsed = self.parse(data)
        if not parsed:
            return

        user, cmd, arg = self.parse(data)

        if user and cmd and arg:
            user = user[1:] if user.startswith(':') else user

            if cmd == 'KICK':
                if self.username == arg[1]:
                    self.kicked(user, arg[0])

            elif cmd == 'PRIVMSG' and not user == self.username:
                if arg[0] == self.username and len(arg) >= 3:
                    arg[1] = arg[1][1:]

                    if arg[1] == ADMIN_PASS:
                        if arg[2] == 'host':
                            self.vhost()
                        if arg[2] == 'nick' and len(arg) == 4:
                            self.nick(arg[3])
                        if arg[2] == 'priv':
                            self.only_dushi_channel = False if self.only_dushi_channel else True
                        if arg[2] == 'msg' and len(arg) >= 4:
                            self.send(' '.join(arg[3:]), self.channel)
                    return

                if not arg[0] == self.channel and not arg[0] == DUSHI_CHANNEL:
                    return

                arg[1] = arg[1][1:]
                msg = ' '.join(arg[1:])

                if arg[1] == CMD_TRANSLATE:
                    if len(arg) < 3:
                        self.send('Zelluf.', arg[0])
                        return

                    x = self.post('INPUT=%s' % msg[len(CMD_TRANSLATE):].strip()) \
                        if len(msg) >= len(CMD_TRANSLATE) + 3 else False

                    self.send('-!- ' + x['RESULT'], arg[0]) \
                        if x and not 'ERROR' in x and 'RESULT' in x else None
                    return

                elif arg[1] == CMD_GET and DIRECT_APIS:
                    if arg[0] == self.channel and self.only_dushi_channel:
                        return

                    msg = msg[len(CMD_GET):]

                    if not msg.startswith(' '):
                        self.send('JaWat', arg[0])
                        return

                    k = msg[1:]
                    k = re.sub(r'[^a-z0-9.\'-]', '', k, flags=re.IGNORECASE)

                    if len(k) <= 2:
                        self.send('Te kort.', arg[0])
                        return

                    for url in DIRECT_APIS:
                        r = self.post('PASS=%s&GET=%s' % (API_PASS, k), url)

                        if not r:
                            return
                        elif r == 'NONE':
                            self.send('Dushi voor \'%s\' niet gevonden.' % k, arg[0])
                            return
                        elif 'RESULT' in r:
                            self.send(r['RESULT'], arg[0])
                            return
                        else:
                            keys = '%s:  ' % k
                            for i in range(0, len(r)):
                                keys += '%s. %s ' % (str(i + 1), r[i])

                            self.send(keys, arg[0])
                        return

                elif arg[1] == CMD_UNSET and DIRECT_APIS:
                    if arg[0] == self.channel and self.only_dushi_channel:
                        return

                    msg = msg[len(CMD_UNSET):]

                    if not msg.startswith(' ') or len(msg[1:].split(' ', 2)) != 2:
                        self.send('%s <key> <nummer>' % CMD_UNSET, arg[0])
                        return

                    msg = msg[1:].split(' ', 2)
                    k = msg[0]
                    v = msg[1]

                    try:
                        v = int(v)
                    except:
                        self.send('vrind, hoe is \'%s\' een nummer?' % (v), arg[0])
                        return

                    skip = False
                    for url in DIRECT_APIS:
                        r = self.post('PASS=%s&UNSET=%s %s' % (API_PASS, k, v), url)
                        if not r:
                            return
                        elif r == 'NOT FOUND':
                            self.send('Key of nummer niet gevonden.', arg[0])
                            return
                        elif r == 'OK':
                            self.send('Verwijderd.', arg[0]) if not skip else None
                            skip = True
                        elif r == 'ERROR':
                            self.send('normaal doen %s ;@' % user, arg[0]) if not skip else None
                            skip = True
                    return

                elif arg[1] == CMD_SET and DIRECT_APIS:
                    if arg[0] == self.channel and self.only_dushi_channel:
                        return

                    msg = msg[len(CMD_SET):]

                    if not msg.startswith(' '):
                        self.send('Gebruik: %s <key>=<value>' % CMD_SET, arg[0])
                        return
                    if not '=' in msg:
                        self.send('Je vergat de \'=\', ei.', arg[0])
                        return

                    k, v = msg.split('=', 1)
                    v = re.sub(r'[^a-z0-9.-]', '', v)

                    if len(k) >= 15 or len(v) >= 15:
                        self.send('Doe es kortere defs submitten.', arg[0])
                        return
                    if len(k) <= 2:
                        self.send('Te weinig chars voor key ;@', arg[0])
                        return
                    elif len(v) <= 1:
                        self.send('Te weinig chars voor val ;@', arg[0])
                        return

                    skip = False
                    for url in DIRECT_APIS:
                        r = self.post('PASS=%s&SET=%s=%s' % (API_PASS, k, v), url)

                        if r == 'DUPLICATE':
                            self.send('Duplicate.', arg[0])
                            return
                        elif r == 'OK':
                            self.send('Dushi toegevoegd.', arg[0]) if not skip else None
                            skip = True
                    return

                if arg[1].lower().startswith(self.username):
                    self.send(random.choice(RESPONSES_HI), arg[0])
                    return
                elif self.username in msg:
                    self.send('zelluf', arg[0])
                    return

                for i in RESPONSES:
                    if i[0] in msg.lower():
                        self.send(random.choice(i[1]), arg[0])
                        return


    def send(self, message, target):
        self.irc.send('PRIVMSG %s %s\r\n' % (target, message)) \
            if self.connected else None

    def nick(self, username):
        self.username = username
        self.irc.send('NICK %s\r\n' % username)

    def vhost(self):
        self.hostmask = True if not self.hostmask else False
        self.irc.send('MODE %s +x\r\n' % self.username) \
            if self.hostmask else self.irc.send('MODE %s -x\r\n' % self.username)

    def kicked(self, user, channel):
        self.join(channel)
        self.send(random.choice(KICKS).replace('{USER}', user), channel)

    def post(self, data, uri=API):
        try:
            request = requests.request('POST', uri,
                                       timeout=3.000,
                                       headers={
                                           "User-Agent": "dushiBot",
                                           "Content-Type": "application/x-www-form-urlencoded"},
                                       allow_redirects=False,
                                       data=data)
            return json.loads(request.content) if request.status_code == 200 else False
        except requests.exceptions.Timeout:
            return {'RESULT': 'servert beetje brak'}
        except:
            return {'RESULT': 'servert dood'}

    def parse(self, data):
        if data.startswith(':'):
            try:
                s = data.split('!', 1)
                return s[0],\
                       s[1].split(' ')[1],\
                       [z for z in
                        s[1].replace('\r\n', '').split(' ')[2:] if z]
            except:
                return None  # NEIN NEIN NEIN !!!

    def nickthread(self):
        while True:
            timeout = 60
            found = False
            if datetime.now().strftime("%H:%M") == '04:20' or found:
                self.nick(random.choice(NICKS))
                if not found:
                    timeout = 86400
                    found = True
            time.sleep(timeout)

NICKS = ['zemmel', 'sahbi', 'wasbeer', 'dushi', 'lobbi', 'brennoW',
         'rickeyG', 'ronnieP', 'cyberzemmel', 'chickie', 'fiveO',
         'shoppa', 'monie_G', 'OG', 'fa2', 'bezem', 'skeer']

RESPONSES = [['waz met jou', ['waz met deze', 'waz met die']],
             ['waz met deze', ['waz met jou', 'waz met die']],
             ['waz met die', ['waz met deze', 'waz met jou']],
             ['waz met haar', ['waz met die sma', 'weenie']],
             ['waz met hem', ['waz met die zemmel', 'weenie']],
             ['watz met', ['watz met deze', 'watz met die', 'watz met jou']],
             ['wat is deze', ['waz met die?', 'zib in je zhina', 'waz met jou']],
             ['skeere tijden', ['w0rd', 'no munnie??', 'ait']],
             ['skeer', ['zelluf skeer G', 'ewa', 'o']],
             ['a zemmel', ['dez ezedjief ek tabra a zemml']],
             ['zemmel', ['bezems', 'zemmeltjes', 'wholla?']],
             ['jwz', ['iwz']],
             ['jwt', ['iwz']],
             ['iwz', ['jwt', 'jwz']]]

RESPONSES_HI = ['y0w','j0w','ewa','sup','fakka']

KICKS = ['wholla', 'normaal doen', 'lief doen {USER}', 'sup {USER}', 'ohai', 'waz met deze {USER}', 'waz met die {USER}', 'wasbeer {USER}', 'k', 'A {USER} zEmMel']

if __name__ == '__main__':
    print spam

    p = argparse.ArgumentParser()
    p.add_argument('host', type=str, help='host')
    p.add_argument('port', type=int, help='port')
    p.add_argument('channel', type=str, help='channel')
    args = p.parse_args()

    dushi = Boat(client=IDENT,
                 host=args.host,
                 channel=args.channel,
                 port=args.port,
                 debug=DEBUG)

    dushi.doe_ding()