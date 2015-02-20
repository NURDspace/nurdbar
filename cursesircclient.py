#!/usr/bin/env python
import curses
import signal

from twisted.internet import reactor
from twisted.python import log

import cursesclient.cursesirc
import cursesclient.twirc

CHANNEL = '#nurdbottest'
FORGETTIME = 20
SCREENSRATIO=0.333
NICKNAME = 'popcorn'
DEBUGMODE = False
CATCHEXIT = False

def sighandler(signum,frame):
    pass

if CATCHEXIT:
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)
    signal.signal(signal.SIGTSTP, sighandler)

if __name__ == '__main__':
    stdscr = curses.initscr() # initialize curses
    screen = cursesirc.Screen(stdscr,SCREENSRATIO,FORGETTIME)   # create Screen object
    stdscr.refresh()
    ircFactory = twirc.IRCFactory(screen, NICKNAME, CHANNEL, DEBUGMODE)
    reactor.addReader(screen) # add screen object as a reader to the reactor
    reactor.connectTCP("irc.oftc.net",6667,ircFactory) # connect to IRC
    reactor.run() # have fun!
    screen.close()
