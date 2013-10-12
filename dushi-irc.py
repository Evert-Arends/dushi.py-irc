#!/usr/bin/python
# D&R (Death and Repudiation) License
# ===================================
#
# This software may not be used directly by any living being.  ANY use of this
# software (even perfectly legitimate and non-commercial uses) until after death
# is explicitly restricted.  Any living being using (or attempting to use) this software
# will be punished to the fullest extent of the law.
#
# For your protection, corpses will not be punished.  We respectfully request
# that you submit your uses (revisions, uses, distributions, uses, etc.) to
# your children, who may vicariously perform these uses on your behalf.  If
# you use this software and you are found to be not dead, you will be punished
# to the fullest extent of the law.
#
# If you are found to be a ghost or angel, you will be punished to the fullest
# extent of the law.
#
# After your following the terms of this license, the author has vowed to repudiate
# your claim, meaning that the validity of this contract will no longer be recognized.
# This license will be unexpectedly revoked (at a time which is designated to be
# most inconvenient) and involved heirs will be punished to the fullest extent
# of the law.
#
# Furthermore, if any parties (related or non-related) escape the punishments
# outlined herein, they will be severely punished to the fullest extent of a new
# revised law that (1) expands the statement "fullest extent of the law" to encompass
# an infinite duration of infinite punishments and (2) exacts said punishments
# upon all parties (related or non-related).
__version__ = "13 okt 2013"
from threading import Thread
from datetime import datetime
import argparse
import socket
import requests
import json
import sys
import random
import time

IDENT = 'bontkraagIRC'
HOST = 'irc.test.nl'
PORT = 6667
CHANNEL = '#test'
VERBOSE = True
CMD = '!dushi'

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class Boat():
    def __init__(self, client, host, channel, port, debug=True):
        self.username, self.ident = random.choice(NICKS), 'dushi'
        self.host, self.channel, self.port = host, channel, port

        self.debug = debug

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

        if data.startswith('PING'):
            self.ping(data)
        else:
            self.jwz(data)

    def ping(self, data):
        if self.debug:
            self.log("Pong of ", data)

        try:
            self.irc.send('PONG %s\r\n' % data.split()[1])
        except IndexError:
            self.irc.send('EWA PONG!')

    def jwz(self, data):
        cmd = self.parse(data)
        if cmd:
            c = cmd['cmd']
            arg = cmd['args']

            if c == 'PING':
                self.ping(data)

            elif c == 'KICK' and cmd['args'][1] == self.username:  # :((
                self.join()
                self.send(random.choice(KICKS))

            elif c == 'PRIVMSG' and not cmd['user'] == self.username:
                if arg[0] == self.channel:
                    arg[1] = arg[1][1:]
                    msg = ' '.join(arg[1:])

                    if arg[1] == CMD:
                        if len(arg) >= 3:
                            x = self.dushi(msg[len(CMD):]) \
                                if len(msg) >= len(CMD) + 3 else False

                            self.send('-!- ' + x['RESULT']) \
                                if x and not 'ERROR' in x and 'RESULT' in x else None
                        else:
                            self.send('zelluf')

                    for k, v in RESPONSES.iteritems():
                        if k in msg:
                            self.send(v)
                            break

    def send(self, message):
        self.irc.send('PRIVMSG %s %s\r\n' % (self.channel, message)) if self.connected else None

    def nick(self, nickname):
        self.irc.send('NICK %s\r\n' % nickname)

    def dushi(self, message):
        try:
            request = requests.request('POST', 'http://dushi.nattewasbeer.nl/aapje',
                                       timeout=4.000,
                                       headers={
                                           "User-Agent": "dushiBot",
                                           "Content-Type": "application/x-www-form-urlencoded"},
                                       allow_redirects=False,
                                       data='INPUT=%s' % message)
        except requests.exceptions.Timeout:
            return {'RESULT': 'servert plat'}
        return json.loads(request.content) if request.status_code == 200 else False

    def parse(self, data):
        if data.startswith(':'):
            try:
                s = data.split('!', 1)
                return {'user': s[0],
                        'cmd': s[1].split(' ')[1],
                        'args': [z for z in s[1].replace('\r\n', '').split(' ')[2:] if z]
                }
            except:
                pass

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

NICKS = ['zemmel', 'sahbi', 'wasbeer', 'dushi', 'lobbi',
         'rickeyG', 'ronnieP', 'cyberzemmel', 'chickie', 'skotoe',
         'shoppa', 'monie_G', 'OG', 'fa2', 'bezem', 'fatima']


RESPONSES = {'waz met jou': 'waz met deze',
             'waz met deze': 'waz met jou',
             'skeere tijden': 'w0rd',
             'skeer': 'j4 G',
             'ewa': 'faffie',
             'a zemmel': ':@',
             'zemmel': 'o',
             'jwz': 'iwz',
             'jwt': 'iwz',
             }


KICKS = ['wholla', 'ewa', 'lief doen', 'NORMAAL DOEN', 'ohai', 'waz met deze', 'waz met die', '...', 'k', ':((((']

if __name__ == '__main__':
    dushi = Boat(client=IDENT,
                 host=HOST,
                 channel=CHANNEL,
                 port=PORT,
                 debug=VERBOSE)

    dushi.doe_ding()