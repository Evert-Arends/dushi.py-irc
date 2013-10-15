#!/usr/bin/python
__version__ = "16 okt 2013"
from threading import Thread
from datetime import datetime
import argparse
import socket
import requests
import json
import sys
import random
import time

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
 |    jeweet gew0n tawn2lauwe ircbots voor die \033[93mekte ekte\033[92m chans     |
 |                         -}bam G{-                               |
 +-----------------------------------------------------------------+
        | USaGe: ./%s [host] [port] [channel]            |
        +----------------------------------------------------------+
                                                     | \033[93m%s\033[92m |
                                                     +-------------+\033[0m\n'''\
       % (jwz, jwz, jwz, jwz, jwz, jwz, sys.argv[0], __version__)
for a in ['|', '+', '-']:
    spam = spam.replace(a, '\033[94m%s\033[92m' % a)

# veilig om te veranderen
ADMIN_PASS = 'blabla'
USER = 'trolletje'
IDENT = 'bontkraagIRC'
PORT = 6667
DEBUG = True

CMD = '!dushi'
CMD_TRANSLATE = CMD
CMD_SET = '%s+' % CMD
CMD_UNSET = '%s-' % CMD
CMD_GET = '%s?' % CMD

# dit hieronder niet veranderen
APIS = []
API_PASS = ''

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

        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def log(self, *args, **kwargs):
        color = kwargs['color'] if 'color' in kwargs else colors.OKGREEN
        print "%(color)s%(value)s%(endc)s" % {'color': color, 'value': repr(args), 'endc': colors.ENDC}

    def join(self, room=None):
        room = self.channel if room is None else room

        self.irc.send('JOIN %s\r\n' % room)

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
        user, cmd, arg = self.parse(data)
        if user and cmd and arg:
            user = user[1:] if user.startswith(':') else user

            # if cmd == 'JOIN':
            #     if self.username == user:
            #         self.send('eh')

            elif cmd == 'KICK':
                if self.username == arg[1]:
                    self.kicked(user, data)
            if cmd == 'PRIVMSG' \
                and arg[0] == self.channel \
                and not user == self.username:

                arg[1] = arg[1][1:]
                msg = ' '.join(arg[1:])

                if arg[1] == CMD_TRANSLATE:
                    if len(arg) < 3:
                        self.send('zelluf')
                        return
                    x = self.post('INPUT=%s' % msg[len(CMD_TRANSLATE):]) \
                        if len(msg) >= len(CMD_TRANSLATE) + 3 else False

                    self.send('-!- ' + x['RESULT']) \
                        if x and not 'ERROR' in x and 'RESULT' in x else None

                elif arg[1] == CMD_GET and APIS: # to-do: alphanummeric only
                    msg = msg[len(CMD_GET):]

                    if not msg.startswith(' '):
                        self.send('JAWAT')
                        return

                    k = msg[1:]
                    if len(k) <= 2:
                        self.send('te kort.')
                        return

                    for url in APIS:
                        r = self.post('PASS=%s&GET=%s' % (API_PASS, k), url)
                        if r == 'NONE':
                            self.send('Dushi voor \'%s\' niet gevonden.' % k)
                            return
                        else:
                            keys = '%s:  ' % k
                            for i in range(0, len(r)):
                                keys += '%s. %s ' % (str(i), r[i])

                            self.send(keys)
                            return
                    return

                elif arg[1] == CMD_UNSET and APIS:
                    msg = msg[len(CMD_UNSET):]

                    if not msg.startswith(' ') or len(msg[1:].split(' ', 2)) != 2:
                        self.send('%s <key> <nummer>' % CMD_UNSET)
                        return

                    msg = msg[1:].split(' ', 2)
                    k = msg[0]
                    v = msg[1]

                    try:
                        v = int(v)
                    except:
                        self.send('%s: vrind, hoe is \'%s\' een nummer?' % (user, v))
                        return
                    finally:
                        for url in APIS:
                            r = self.post('PASS=%s&UNSET=%s %s' % (API_PASS, k, v), url)
                            if r == 'NOT FOUND':
                                self.send('Key of nummer niet gevonden.')
                                return
                            else:
                                self.send('Bam.')

                elif arg[1] == CMD_SET and APIS:
                    if len(msg) >= len(CMD_SET) + 3:
                        msg = msg[len(CMD_SET):]

                        if not msg.startswith(' '):
                            self.send('%s, waz met deze' % user)
                            return
                        if not '=' in msg:
                            self.send('Je vergat de \'=\', ei.')
                            return

                        k, v = msg.split('=', 1)

                        if len(k) >= 15 or len(v) >= 15:
                            self.send('doe es kortere defs submitten %s G' % user)

                        for url in APIS:
                            r = self.post('PASS=%s&SET=%s=%s' % (API_PASS, k, v), url)
                            if r == 'DUPLICATE':
                                self.send('Duplicate.')
                            elif r == 'OK':
                                self.send('Toegevoegdt.')
                        return
                    else:
                        self.send('te weinig chars voor key ;@')
                        return

                if arg[1].lower().startswith(self.username):
                    self.send(random.choice(random.choice(RESPONSES_HI)))
                    return
                elif self.username in msg.lower():
                    self.send('zelluf')
                    return

                for i in RESPONSES:
                    if i[0] in msg.lower():
                        self.send(random.choice(i[1]))
                        return
            else:
                if arg[0] == self.username and len(arg) >= 3:
                    arg[1] = arg[1][1:]

                    if arg[1] == ADMIN_PASS:
                        if arg[2] == 'host':
                            self.vhost()
                        if arg[2] == 'nick' and len(arg) == 4:
                            self.nick(arg[3])

    def send(self, message):
        self.irc.send('PRIVMSG %s %s\r\n' % (self.channel, message)) \
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
        self.send(random.choice(KICKS).replace('{USER}', user))

    def post(self, data, uri='http://dushi.nattewasbeer.nl/aapje'):
        try:
            request = requests.request('POST', uri,
                                       timeout=4.000,
                                       headers={
                                           "User-Agent": "dushiBot",
                                           "Content-Type": "application/x-www-form-urlencoded"},
                                       allow_redirects=False,
                                       data=data)
        except requests.exceptions.Timeout:
            return {'RESULT': 'servert plat'}
        except:
            return {'RESULT': 'server unreachable'}
        return json.loads(request.content) if request.status_code == 200 else False

    def parse(self, data):
        if data.startswith(':'):
            try:
                s = data.split('!', 1)
                return s[0],\
                       s[1].split(' ')[1],\
                       [z for z in
                        s[1].replace('\r\n', '').split(' ')[2:] if z]
            except:
                return None, None, None # !!!

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
             ['wat is deze', ['waz met die?', 'zib in je zhina', 'waz met jou']],
             ['skeere tijden', ['w0rd', 'no munnie??', 'ait']],
             ['skeer', ['zelluf skeer G', 'ewa', 'o']],
             ['a zemmel', ['dez ezedjief ek tabra a zemml']],
             ['zemmel', ['o', 'bnice']],
             ['jwz', ['iwz']],
             ['jwt', ['iwz']],
             ['iwz', ['jwt', 'jwz']]]

RESPONSES_HI = ['y0w','j0w','ewa','sup','fakka']

KICKS = ['wholla', 'ewa', 'lief doen {USER}', 'NORMAAL DOEN {USER}', 'ohai', 'waz met deze {USER}', 'waz met die', '...', 'k', 'A {USER} zEmMel']

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