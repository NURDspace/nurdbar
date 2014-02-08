#!/usr/bin/env python
from twisted.internet import reactor
from nurdbar import NurdBar
import sys, os
import logging
import pkgutil
from nurdbar.plugins.api import *
logging.basicConfig(level=logging.DEBUG)


log=logging.getLogger(__name__)

def importPlugins(plugindir):
    log.debug('importing plugins from %s'%plugindir)
    print('contents of plugindir: %s'%os.listdir(plugindir))
    for i in pkgutil.iter_modules([plugindir]):
        log.debug('importing %s'%i[1])
        if i[1]!='api':
                i[0].find_module(i[1]).load_module('%s.%s'%(plugindir,i[1]))

def main(configfile):
    log.debug('Starting interfaces')
    bar=NurdBar(configfile)
    importPlugins('nurdbar/plugins')
    if bar.config.has_option('plugins','plugindir'):
        plugindir=bar.config.get('plugins','plugindir')
        importPlugins(plugindir)

    for portnum,factory in pluginregistry['tcpinterfaceplugin'].getPlugins():
        reactor.listenTCP(portnum, factory(bar))

    for factory in pluginregistry['transportinterfaceplugin'].getPlugins():
        factory(bar,reactor)
    reactor.run()

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
