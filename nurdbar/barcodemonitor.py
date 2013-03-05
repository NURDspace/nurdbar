#!/usr/bin/env python
from twisted.internet import protocol, reactor, serialport
from twisted.protocols import basic
from nurdbar import NurdBar
import sys

class BarcodeProtocol(basic.LineReceiver):

    def __init__(self,bar):
        self.bar=bar

    def lineReceived(self, barcode):
        self.bar.handleBarcode(barcode)

class BarcodeProtocolFactory(protocol.Factory):

    def __init__(self,bar):
        self.bar = bar

    def buildProtocol(self,addr):
        return BarcodeProtocol(self.bar)

def main(configfile):
    bar=NurdBar(configfile)
    port=bar.config.get('scanner','port')
    baudrate=bar.config.get('scanner','baudrate')

    factory=BarcodeProtocolFactory(bar)

    serialport.SerialPort(BarcodeProtocol(bar),port,reactor, baudrate=baudrate)
    #reactor.listenTCP(1079, factory)
    reactor.run()

if __name__=='__main__':
    configfile=sys.argv[1]
    main(configfile)
