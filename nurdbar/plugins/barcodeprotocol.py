from twisted.protocols import basic
from twisted.internet import protocol, reactor, serialport
from nurdbar.plugins.api import *
from nurdbar.events import BarcodeScannedEvent,OutOfStockEvent,ItemBarcodeScannedEvent,MemberBarcodeScannedEvent,CommandBarcodeScannedEvent
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

        self.state = 'BUY'
        self.currentMember = None
        self.currentItem = None
        self.lastLine = ''

        self.registeringItem=False
        self.sellingItem=False
        self.buyingItem=False

        self.newItemBarcode=None
        self.newItemPrice=None
        self.newItemNumber=0
        self.newItemDesc=None
        self.newItemVolume=None
        self.newItemCountry=None

    def connectionLost(self,reason):
        self.screenObj.addLine('connection Lost','top')
        BarcodeScannedEvent.unregister(self.printBarcode)
#        OutOfStockEvent.unregister(self.printOutOfStockEvent)
        ItemBarcodeScannedEvent.unregister(self.scanItem)
        MemberBarcodeScannedEvent.unregister(self.identifyMember)
        CommandBarcodeScannedEvent.unregister(self.modeChange)

    def connectionMade(self):
        self.screenObj.addLine('connection Made','top')
        BarcodeScannedEvent.register(self.printBarcode)
#        OutOfStockEvent.register(self.printOutOfStockEvent)
        ItemBarcodeScannedEvent.register(self.scanItem)
        MemberBarcodeScannedEvent.register(self.identifyMember)
        CommandBarcodeScannedEvent.register(self.modeChange)

    def scanItem(self,event):
        item=event.attributes['item']
        barcodedesc=event.attributes['barcodedesc']
        if item is None:
            self.screenObj.addLine('This item has no entry in the database.','top')
#            self.newItemBarcode = barcode
#            self.registerNewItem()
#            return
            id = ''
            barcode = barcodedesc.barcode
        else:
            id = item.item_id
            barcode = item.barcode
            self.currentItem = item
            self.screenObj.addLine("Found item "+str(item.item_id),'top')
#            self.sendLine('\a')
        if self.currentMember is not None:
            if self.state == 'BUY' and item is not None:
                self.screenObj.addLine("Selling item "+str(id)+" to "+str(self.currentMember.nick),'top')
                self.newItemBarcode = barcode
                self.buyItemHandler()
            if self.state == 'SELL':
                self.screenObj.addLine("Buying item "+str(id)+" from "+str(self.currentMember.nick),'top')
                self.newItemBarcode = barcode
                self.sellItemHandler()
        try:
            name = barcodedesc.description
        except:
            name = item.id
#         if self.currentMember and self.state == 'SELL':
#                   self.screenObj.addLine('Buying in '+str(name)+'?','top')
        try:        
            stock = self.bar.getItemTotalStock(item.barcode)
            self.screenObj.addLine(str(name)+': total stock count: '+str(stock),'top')
        except:
            pass

    def identifyMember(self,event):
        member=event.attributes['member']
        if member is not None:
            self.currentMember = member
            self.screenObj.addLine("Hello, "+str(member.nick),'top')
        else:
            self.sendLine('\a')
            self.screenObj.addLine("Unknown member barcode.",'top')

    def printOutOfStockEvent(self,event):
        item=event.attributes['item']
        try:
            name = self.bar.getBarcodeDescByBarcode(item.barcode).description
        except:
            name = item.id
        if self.currentMember and self.state == 'SELL':
               self.screenObj.addLine('Buying in '+str(name)+'?','top')
        self.screenObj.addLine('Item '+str(name)+' is out of stock','top')

    def modeChange(self,event):
        command=event.attributes['command']
        if command == 'RESET':
            self.state = 'BUY'
            self.currentMember = None
            self.currentItem = None
            self.registeringItem=False
            self.sellingItem=False
            self.buyingItem=False
            self.screenObj.addLine('Resetting.','top')
        else:
            self.state = command
            self.screenObj.addLine('Changing to mode: '+str(command),'top')


    def printBarcode(self,event):
        barcode=event.attributes['barcode']
        self.screenObj.addLine('Scanned the following barcode: %s'%barcode, 'top')

    def sendLine(self, line):
        """
        Overriding the default input to run state engine.
        """
        self.lastLine = line
        if self.registeringItem: self.registerNewItem()
        if self.sellingItem: self.sellItemHandler()
        if self.buyingItem: self.buyItemHandler()

    def sellItemHandler(self):
        if self.sellingItem == False:
            self.sellingItem=True
            self.newItemNumber=0
            self.newItemPrice=None
            self.screenObj.addLine('How many are you selling? (default: 1)','top')
            return
        if not self.newItemNumber:
            if self.lastLine.strip() == '':
                self.newItemNumber = 1
            else:
                try:
                    self.newItemNumber = int(self.lastLine)
                except:
                    self.newItemNumber = 1
                    self.screenObj.addLine('Invalid entry. Defaulting to 1...','top')
            self.screenObj.addLine('Please enter a price (in EUR).','top')
            return
        if not self.newItemPrice:
            try:
                self.newItemPrice = float(self.lastLine)
            except:
                self.newItemPrice = None
                self.screenObj.addLine('Invalid value. Please try again.','top')
                return
            self.screenObj.addLine('Buying from'+str(self.currentMember.barcode),'top')
            self.screenObj.addLine('Item: '+str(self.newItemBarcode),'top')
            self.screenObj.addLine('Number: '+str(self.newItemNumber),'top')
            self.screenObj.addLine('Buying at EUR '+str(self.newItemPrice),'top')
            self.bar.sellItem(self.currentMember.barcode, self.newItemBarcode, self.newItemPrice, amount=self.newItemNumber)
            self.sellingItem=False
            self.newItemNumber=0
            self.newItemPrice=None

    def buyItemHandler(self):
        if self.buyingItem == False:
            self.buyingItem=True
            self.newItemNumber=0
            self.screenObj.addLine('How many are you buying? (default: 1)','top')
            return
        if not self.newItemNumber:
            if self.lastLine.strip() == '':
                self.newItemNumber = 1
            else:
                try:
                    self.newItemNumber = int(self.lastLine)
                except:
                    self.screenObj.addLine('Invalid entry. Defaulting to 1...','top')
            currentstock = self.bar.getItemTotalStock(self.newItemBarcode)
            if self.newItemNumber>currentstock:
                self.newItemNumber = None
                self.screenObj.addLine("You can't buy that many! We only have "+str(currentstock),'top')
                return
            self.screenObj.addLine('Selling '+str(self.newItemBarcode),'top')
            self.bar.buyItem(self.currentMember.barcode, self.newItemBarcode, amount=self.newItemNumber)
            self.buyingItem=False
            self.newItemNumber=0

    def registerNewItem(self):
        if self.registeringItem == False:
            self.registeringItem=True
            self.newItemPrice=None
            self.newItemDesc=None
            self.newItemVolume=None
            self.newItemCountry=None
            self.lastLine = ''
            self.screenObj.addLine("Please enter a price (in EUR). If you don't know one, leave blank.",'top')
            return
        if self.newItemPrice is None:
            if self.lastLine.strip() == '':
                self.newItemPrice = 0
            try:
                self.newItemPrice = float(self.lastLine)
            except:
                self.newItemPrice = 0
                self.screenObj.addLine('Invalid value. Skipping...','top')
            self.screenObj.addLine('Please enter a description or name.','top')
            return
        if not self.newItemDesc:
            self.newItemDesc = str(self.lastLine)
            self.screenObj.addLine('Please enter a size or volume (e.g. 500ml).','top')
            return
        if not self.newItemVolume:
            self.newItemVolume = str(self.lastLine)
            self.screenObj.addLine('Please enter a country of origin (e.g. Germany).','top')
            return
        if not self.newItemCountry:
            self.newItemCountry = str(self.lastLine)
            self.screenObj.addLine('Entering data now.','top')
            if self.newItemPrice is not 0:
                self.bar.addItem(self.newItemBarcode,self.newItemPrice)
            self.bar.addBarcodeDesc(self.newItemBarcode,self.newItemDesc,self.newItemVolume,self.newItemCountry)
            self.registeringItem=False
            self.newItemBarcode=None
            self.newItemPrice=None
            self.newItemDesc=None
            self.newItemVolume=None
            self.newItemCountry=None
            return

    def lineReceived(self, barcode):
        try:
            self.bar.handleBarcode(barcode)
        except exceptions.ItemOutOfStockError:
            log.warn('Item out of stock')
            self.bar.resetHandleState()
        except exceptions.ItemDoesNotExistError:
            self.screenObj.addLine("Unknown item barcode. Registering...",'top')
            self.newItemBarcode = barcode
            self.registerNewItem()
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
