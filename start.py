#!/usr/bin/env python
from twisted.internet import reactor
from nurdbar import NurdBar
import sys
import logging
import pkgutil
from nurdbar.plugins.api import *
logging.basicConfig(level=logging.DEBUG)


log=logging.getLogger(__name__)

def importPlugins(plugindir):
    log.debug('importing plugins from %s'%plugindir)
    for i in pkgutil.iter_modules([plugindir]):
        log.debug('importing %s'%i[1])
        if i[1]!='api':
                i[0].find_module(i[1]).load_module('%s.%s'%(plugindir,i[1]))

def main(configfile):
    log.debug('Starting interfaces')
    bar=NurdBar(configfile)
    importPlugins('nurdbar/plugins')
    plugindir=bar.config.get('plugins','plugindir',None)
    if plugindir:
        importPlugins(plugindir)

    for portnum,factory in pluginregistry['tcpinterfaceplugin'].getPlugins():
        reactor.listenTCP(portnum, factory(bar,reactor))

    for factory in pluginregistry['localinterfaceplugin'].getPlugins():
        factory(bar,reactor)
    reactor.run()

if __name__=='__main__':
    configfile=sys.argv[1]
    main(configfile)
