from twisted.protocols import basic
from twisted.internet import protocol, reactor, serialport
from nurdbar.plugins.api import *
from nurdbar.events import BarcodeScannedEvent, OutOfStockEvent, MemberBarcodeScannedEvent, ItemBarcodeScannedEvent
from nurdbar import exceptions
from nurdbar import barcodelookup
import traceback
import logging
log=logging.getLogger(__name__)


class BarcodeProtocol(basic.LineReceiver):

    def __init__(self,bar,screenObj):
        self.bar=bar
        self.screenObj = screenObj
        self.screenObj.bar = self

    def connectionLost(self,reason):
        self.screenObj.addLine('connection Lost','top')
        BarcodeScannedEvent.unregister(self.printBarcode)
#        OutOfStockEvent.unregister(self.printOutOfStockEvent)
#        ItemBarcodeScannedEvent.unregister(self.printItem)
#        MemberBarcodeScannedEvent.unregister(self.printMember)

    def connectionMade(self):
        self.screenObj.addLine('connection Made','top')
        BarcodeScannedEvent.register(self.printBarcode)
#        OutOfStockEvent.register(self.printOutOfStockEvent)
#        ItemBarcodeScannedEvent.register(self.printItem)
#        MemberBarcodeScannedEvent.register(self.printMember)

    def printItem(self,event):
        item=event.attributes['item']
        if item is not None:
            pass
#            print("Found item %s"%item.item_id)
        else:
            self.sendLine('\a')
            print ("Unknown item barcode.")

    def printMember(self,event):
        member=event.attributes['member']
        if member is not None:
            print("Found member %s"%member.member_id)
        else:
            self.sendLine('\a')
            print ("Unknown member barcode.")

    def printOutOfStockEvent(self,event):
        item=event.attributes['item']
        print('Item %s is out of stock'%item.item_id)

    def printBarcode(self,event):
        barcode=event.attributes['barcode']
        self.screenObj.addLine('Scanned the following barcode: %s'%barcode, 'top')
#        x = barcodelookup.BarcodeLookup()
#        try:
#            print (x.lookupBarcode(barcode))
#        except:
#            print ("Error!")

    def lineReceived(self, barcode):
        try:
            self.bar.handleBarcode(barcode)
        except exceptions.ItemOutOfStockError:
            log.warn('Item out of stock')
            self.bar.resetHandleState()
        except exceptions.ItemDoesNotExistError:
            log.warn('Item not registered.')
            self.bar.resetHandleState()
        except Exception:
            self.bar.resetHandleState()
            log.error(traceback.format_exc())


@CursesInterfacePlugin
def getLocalInterfacePlugin(bar,screenObj,reactor):
    log.info('Starting barcode monitor')
    port=bar.config.get('scanner','port')
    log.debug('Using serial port %s'%port)
    baudrate=bar.config.get('scanner','baudrate')
    serialport.SerialPort(BarcodeProtocol(bar,screenObj),port,reactor,baudrate=baudrate)
