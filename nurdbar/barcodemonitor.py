#!/usr/bin/env python
from twisted.internet import protocol, reactor, serialport
from twisted.protocols import basic
from nurdbar import NurdBar
from telnetprotocol import TelnetFactory
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

log=logging.getLogger(__name__)

class BarcodeProtocol(basic.LineReceiver):

    def __init__(self,bar):
        self.bar=bar

    def lineReceived(self, barcode):
        log.debug('received barcode %s'%barcode)
        self.bar.handleBarcode(barcode)


class BarcodeProtocolFactory(protocol.Factory):

    def __init__(self,bar):
        self.bar = bar

    def buildProtocol(self,addr):
        return BarcodeProtocol(self.bar)

def main(configfile):
    log.debug('Starting barcode monitor')
    bar=NurdBar(configfile)
    port=bar.config.get('scanner','port')
    baudrate=bar.config.get('scanner','baudrate')
    log.debug('Using serial port %s'%port)

    factory=BarcodeProtocolFactory(bar)

    serialport.SerialPort(BarcodeProtocol(bar),port,reactor, baudrate=baudrate)
    reactor.listenTCP(1079, TelnetFactory(bar))
    reactor.run()

if __name__=='__main__':
    configfile=sys.argv[1]
    main(configfile)
