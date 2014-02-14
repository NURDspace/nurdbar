#!/usr/bin/env python
#!/usr/bin/env python
from twisted.internet import reactor
from nurdbar import NurdBar

import sys, os
import logging
import pkgutil

from nurdbar.plugins.api import *

import curses
import signal

from cursesclient import cursesirc
from cursesclient import twirc

logging.basicConfig(level=logging.DEBUG)

log=logging.getLogger(__name__)
#fh = logging.FileHandler('logging.log')
#fh.setLevel(logging.DEBUG)

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

def importPlugins(plugindir):
    log.debug('importing plugins from %s'%plugindir)
    print('contents of plugindir: %s'%os.listdir(plugindir))
    for i in pkgutil.iter_modules([plugindir]):
        log.debug('importing %s'%i[1])
        if i[1]!='api':
                i[0].find_module(i[1]).load_module('%s.%s'%(plugindir,i[1]))

def main(configfile):
    log.debug('Starting interfaces')
    stdscr = curses.initscr() # initialize curses
    screen = cursesirc.Screen(stdscr,SCREENSRATIO)   # create Screen object
    stdscr.refresh()

    bar=NurdBar(configfile)
    importPlugins('nurdbar/plugins')
    if bar.config.has_option('plugins','plugindir'):
        plugindir=bar.config.get('plugins','plugindir')
        importPlugins(plugindir)

    for portnum,factory in pluginregistry['tcpinterfaceplugin'].getPlugins():
        reactor.listenTCP(portnum, factory(bar))

    for factory in pluginregistry['transportinterfaceplugin'].getPlugins():
        factory(bar,reactor)

    for factory in pluginregistry['cursesinterfaceplugin'].getPlugins():
        factory(bar,screen,reactor)

    ircFactory = twirc.IRCFactory(screen, NICKNAME, CHANNEL, FORGETTIME, DEBUGMODE)
    reactor.addReader(screen) # add screen object as a reader to the reactor
    reactor.connectTCP("irc.oftc.net",6667,ircFactory) # connect to IRC
    reactor.run() # have fun!
    screen.close()

if __name__=='__main__':
    try:
        configfile=sys.argv[1]
    except:
        configfile = 'config.cfg'
        if not os.path.isfile(configfile):
            logging.warn('No config.cfg file exists, creating a blank one.')
            with open (configfile,'a'):
                os.utime(configfile,None)
    main(configfile)

