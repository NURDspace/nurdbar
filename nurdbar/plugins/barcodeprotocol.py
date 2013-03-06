from twisted.protocols import basic
from twisted.internet import protocol, reactor, serialport
#from plugins.api import *
from nurdbar.plugins.api import *
import logging
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

@LocalInterfacePlugin
def getLocalInterfacePlugin(bar,reactor):
    log.info('Starting barcode monitor')
    port=bar.config.get('scanner','port')
    log.debug('Using serial port %s'%port)
    baudrate=bar.config.get('scanner','baudrate')
    serialport.SerialPort(BarcodeProtocol(bar),port,reactor, baudrate=baudrate)
