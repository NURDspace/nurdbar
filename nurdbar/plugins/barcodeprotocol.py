from twisted.protocols import basic
from twisted.internet import protocol, reactor, serialport
from twisted.internet.task import LoopingCall
from nurdbar.plugins.api import *
from nurdbar.events import BarcodeScannedEvent,OutOfStockEvent,ItemBarcodeScannedEvent,MemberBarcodeScannedEvent,CommandBarcodeScannedEvent
from nurdbar import exceptions
from nurdbar import events
from nurdbar import barcodelookup

from iso3166 import countries

import traceback
import logging
log=logging.getLogger(__name__)


class BarcodeProtocol(basic.LineReceiver):

    def __init__(self,bar,screenObj):
        self.bar=bar
        self.screenObj = screenObj
        self.screenObj.bar = self

        self.maxIdle = 15
        self.idleTime=0
        idle = LoopingCall(self.idleHandler)
        idle.start(1) #seconds

        self.state = 'BUY'
        self.lastLine = ''
        self.resetFlags()
        self.resetVariables()
        self.resetScans()


    def connectionLost(self,reason):
        self.screenObj.addLine('Bar Offline.','top')
        BarcodeScannedEvent.unregister(self.printBarcode)
#        OutOfStockEvent.unregister(self.printOutOfStockEvent)
        ItemBarcodeScannedEvent.unregister(self.scanItem)
        MemberBarcodeScannedEvent.unregister(self.identifyMember)
        CommandBarcodeScannedEvent.unregister(self.modeChange)

    def connectionMade(self):
        self.screenObj.addLine('Bar Online.','top')
        BarcodeScannedEvent.register(self.printBarcode)
#        OutOfStockEvent.register(self.printOutOfStockEvent)
        ItemBarcodeScannedEvent.register(self.scanItem)
        MemberBarcodeScannedEvent.register(self.identifyMember)
        CommandBarcodeScannedEvent.register(self.modeChange)

    def resetFlags(self):
            self.registeringItem=False
            self.registeringUser=False
            self.sellingItem=False
            self.buyingItem=False
            self.depositing=False

    def resetScans(self):
            self.currentMember=None
            self.currentItem=None
            self.currentBarcodeDesc=None

    def resetVariables(self):
            self.lastLine = ''
            self.newUsername=None
            self.newItemNumber=None
            self.oldItemPrice=None
            self.crateMode=None
            self.newItemPrice=None
            self.newItemDesc=None
            self.newItemVolume=None
            self.newItemCountry=None

    def handlerFinish(self):
        try:
            if self.buyingItem: self.buyItemHandler(default=True)
            if self.sellingItem: self.sellItemHandler(default=True)
        except:
            self.screenObj.addLine("Last transaction not completed. Continuing...",'top')
            if self.buyingItem: self.buyItemHandler()
            if self.sellingItem: self.sellItemHandler()
            return False
        return True

    def idleHandler(self):
        self.idleTime = self.idleTime+1
        if self.idleTime>self.maxIdle:
            try:
                if self.buyingItem: self.buyItemHandler(default=True)
                if self.sellingItem: self.sellItemHandler(default=True)
            except:
                self.screenObj.addLine("Last transaction not completed. Cancelled.",'top')
            if self.currentMember is not None:
                self.state = 'BUY'
                self.resetFlags()
                self.resetScans()
                self.screenObj.addLine('Reset.','top')

    def modeChange(self,event):
        command=event.attributes['command']
        if command == 'RESET':
            self.state = 'BUY'
            self.resetFlags()
            self.resetScans()
            self.screenObj.addLine('Transaction cancelled. Resetting to default.','top')
        elif command == 'TOGGLE_IRC':
           if self.currentMember is not None:
               if self.currentMember.irc_report:
                    self.currentMember.irc_report = False
                    self.screenObj.addLine('No longer changing nick.','top')
               else:
                    self.currentMember.irc_report = True
                    self.screenObj.addLine('Automatically changing nick.','top')
           return
        else:
            if not self.handlerFinish(): return
            self.resetFlags()
            self.state = command
            self.screenObj.addLine('Changing to action: '+str(command),'top')
            if self.state == 'DEPOSIT':
                self.depositHandler()


    def scanItem(self,event):
        #Reset state machines if in progress
        if not self.handlerFinish(): return
        self.resetFlags()
        self.resetVariables()
        self.currentItem=event.attributes['item']
        self.currentBarcodeDesc=event.attributes['barcodedesc']
        barcode = self.currentBarcodeDesc.barcode
        name = self.currentBarcodeDesc.description
        self.newBarcode = barcode #Send scanned barcode into selling/buying engines ONLY IF they've finished.
        if self.currentBarcodeDesc is None:
            self.screenObj.addLine("Registering new item...",'top')
            self.registerNewItem()
            return

        if self.currentMember is not None:
            if self.state == 'BUY':
                self.screenObj.addLine("Selling item: "+str(name)+" to "+str(self.currentMember.nick),'top')
                self.buyItemHandler()
                return
            if self.state == 'SELL':
                self.screenObj.addLine("Buying item "+str(name)+" from "+str(self.currentMember.nick),'top')
                self.sellItemHandler()
                return
        #No members logged in - just info.

        try:
            stock = int(self.bar.getItemTotalStock(barcode))
        except:
            stock=0
        self.screenObj.addLine(str(name)+': total stock count: '+str(stock),'top')
        if self.currentItem is not None:
            self.screenObj.addLine("Found item "+str(self.currentItem.item_id),'top')
            price = self.currentItem.sell_price
            self.screenObj.addLine('Current price: EUR '+"{:.2f}".format(price)+' Please scan your ID to buy.','top')
        else:
            self.screenObj.addLine('Current price: Unknown, and has no history.','top')


    def identifyMember(self,event):
        if not self.handlerFinish(): return
        member=event.attributes['member']
        if self.currentMember is not None and self.state == 'NEWUSER':
            self.newBarcode = self.lastBarcode
            self.registerNewUser()
            return
        if member is not None:
            if self.buyingItem: self.buyItemHandler()
            self.currentMember = member
            self.state='BUY'
            self.screenObj.addLine("Hello, "+str(member.nick),'top')
            self.screenObj.addLine("your current Balance: EUR "+"{:.2f}".format(member.balance),'top')
            self.screenObj.addLine("Default action: BUY",'top')
            if member.irc_report:
                self.screenObj.nickChange(str(member.nick))
        else:
            self.screenObj.addLine("Unknown member barcode.",'top')

#    def printOutOfStockEvent(self,event):
#        item=event.attributes['item']
#        try:
#            name = self.bar.getBarcodeDescByBarcode(item.barcode).description
#        except:
#            name = item.id
#        if self.currentMember and self.state == 'SELL':
#               self.screenObj.addLine('Buying in '+str(name)+'?','top')
#        self.screenObj.addLine('Item '+str(name)+' is out of stock','top')


    def printBarcode(self,event):
#        barcode=event.attributes['barcode']
        self.idleTime=0
        self.lastBarcode=event.attributes['barcode']
#        self.screenObj.addLine('Scanned the following barcode: %s'%barcode, 'top')

    def sendLine(self, line):
        """
        Overriding the default input to run state engine.
        """
        self.idleTime=0
        self.lastLine = line.strip()
        if self.registeringItem:
            self.registerNewItem()
            return
        if self.registeringUser:
            self.registerNewUser()
            return
        if self.sellingItem:
            self.sellItemHandler()
            return
        if self.buyingItem:
            self.buyItemHandler()
            return
        if self.depositing:
            self.depositHandler()
            return
        try:
            self.newItemNumber = int(self.lastLine)
        except:
            pass

    def sellItemHandler(self,default=False):
        '''State machine driving the selling of items to the bar. Gets called multiple times.'''
        if self.sellingItem == False:
            self.resetFlags()
            self.resetVariables()
            self.sellingItem=True
            self.screenObj.addLine('Are you selling an entire crate? (Default: Y)','top')
            return
        try:
            name = self.currentBarcodeDesc.description
        except:
            name = self.newBarcode
        if self.crateMode is None:
            if self.lastLine.strip().lower() in ['','y','yes','true','1']:
                self.crateMode=True
                try:
                    n = self.bar.getItemByBarcode(self.newBarcode).crate_number
                    if n is not None:
                        self.screenObj.addLine('Default for '+name+' is '+str(n)+' per crate/container. Please correct here if this is not so.','top')
                    else: raise ValueError
                except:
                    self.screenObj.addLine('Please enter how many are in each crate/container/etc.','top')
                return
            else:
                self.crateMode=False
                self.screenObj.addLine('How many individual units are you selling? (Default: 1)','top')
                return
        if not self.newItemNumber:
            if self.crateMode:
                try:
                    self.newItemNumber = int(self.lastLine.strip())
                except:
                    if self.crateMode:
                        try:
                            n = self.bar.getItemByBarcode(self.newBarcode).crate_number
                            if n is not None:
                                self.newItemNumber = n
                                self.screenObj.addLine('Defaulting to '+str(self.newItemNumber),'top')
                            else: raise ValueError
                        except:
                            self.screenObj.addLine('Invalid entry. Please try again.','top')
                            return
            else:
                try:
                    self.newItemNumber = int(self.lastLine.strip())
                except:
                    self.screenObj.addLine('Defaulting to 1.','top')
                    self.newItemNumber = 1
            try:
                self.oldItemPrice = self.bar.getItemByBarcode(self.newBarcode).buy_price
            except:
                self.oldItemPrice = None
            if not self.crateMode:
                if self.oldItemPrice:
                    self.screenObj.addLine('Please enter a price per item (including deposits) (in EUR) (Default: '+"{:.2f}".format(self.oldItemPrice)+')','top')
                else:
                    self.screenObj.addLine('Please enter a price per item (including deposits) (in EUR)','top')
            else:
                if self.oldItemPrice:
                    self.oldItemPrice = self.oldItemPrice*self.newItemNumber
                    self.screenObj.addLine('Please enter the price of the entire crate with crate and bottles included. (in EUR) (Default: '+"{:.2f}".format(self.oldItemPrice)+')','top')
                else:
                    self.screenObj.addLine('Please enter the price of the entire crate with bottles and crate (in EUR)','top')
            if default:
                if not self.oldItemPrice: raise exceptions.ItemDoesNotExistError
                self.newItemPrice = self.oldItemPrice
            else:
                return
#        self.screenObj.addLine('DEBUG: ItemNumber: '+str(self.newItemNumber),'top')
        if not self.newItemPrice:
            try:
                self.newItemPrice = float(self.lastLine.strip())
            except:
                if self.oldItemPrice:
                    self.newItemPrice = self.oldItemPrice
                    self.screenObj.addLine('Defaulting to '+"{:.2f}".format(self.oldItemPrice),'top')
                else:
                    self.newItemPrice = None
                    self.screenObj.addLine('Invalid value. Please try again.','top')
                    return
#        self.screenObj.addLine('DEBUG: Price: '+str(self.newItemPrice),'top')
        try:
            name = self.currentBarcodeDesc.description
        except:
            name = self.newBarcode
        if self.crateMode:
            self.newItemPrice = self.newItemPrice/self.newItemNumber
        self.screenObj.addLine('Buying from '+str(self.currentMember.nick)+' Item: '+str(name),'top')
        self.screenObj.addLine('Number: '+str(self.newItemNumber)+' Buying at EUR '+"{:.2f}".format(self.newItemPrice),'top')
        self.bar.sellItem(self.currentMember.barcode, self.newBarcode, self.newItemPrice, amount=self.newItemNumber)
        if self.crateMode:
            self.bar.getItemByBarcode(self.newBarcode).crate_number = self.newItemNumber
            self.screenObj.sendIrcLine('Sell '+str(self.newItemNumber)+'x crate of '+str(name)+': EUR '+"{:.2f}".format(self.newItemPrice)+' each.')
        else:
            self.screenObj.sendIrcLine('Sell: '+str(self.newItemNumber)+'x '+str(name)+' at EUR '+"{:.2f}".format(self.newItemPrice))


        self.resetFlags()
        self.resetVariables()
        return

    def buyItemHandler(self,default=False):
        '''State machine driving the buying of items from the bar. Gets called multiple times.'''
        if self.buyingItem == False:
            self.resetFlags()
            self.resetVariables()
            self.buyingItem=True
            price = self.currentItem.sell_price
            currentstock = self.bar.getItemTotalStock(self.newBarcode)
            self.screenObj.addLine("Price: EUR "+"{:.2f}".format(price)+" How many individual units are you buying? (Default: 1, Max: "+str(currentstock)+")","top")
            return
        if not self.newItemNumber:
            if self.lastLine.strip() == '':
                self.newItemNumber = 1
            else:
                try:
                    self.newItemNumber = int(self.lastLine.strip())
                except:
                    self.newItemNumber = 1
                    self.screenObj.addLine('Invalid entry. Defaulting to 1...','top')
            currentstock = self.bar.getItemTotalStock(self.newBarcode)
            if self.newItemNumber>currentstock:
                self.newItemNumber = None
                self.screenObj.addLine("You can't buy that many! We only have "+str(currentstock),"top")
                return
            try:
                name = self.currentBarcodeDesc.description
            except:
                name = self.newBarcode
            price = self.currentItem.sell_price
            self.screenObj.addLine('Selling '+str(self.newItemNumber)+'x '+str(name)+' to '+str(self.currentMember.nick)+' at EUR '+"{:.2f}".format(price),'top')
            self.screenObj.sendIrcLine('Buy: '+str(self.newItemNumber)+'x '+str(name)+' at EUR '+"{:.2f}".format(price))
            self.bar.buyItem(self.currentMember.barcode, self.newBarcode, amount=self.newItemNumber)
            self.resetFlags()
            self.resetVariables()
            return

    def depositHandler(self,default=False):
        if self.currentMember is None:
            self.screenObj.addLine("Please log in first.","top")
            return            
        if self.depositing == False:
            self.resetFlags()
            self.resetVariables()
            self.depositing=True
            self.screenObj.addLine("How much are you depositing? (in EUR)","top")
            return
        if not self.newItemPrice:
            try:
                self.newItemPrice = float(self.lastLine.strip())
            except:
                self.newItemPrice = 0
                self.screenObj.addLine('Invalid entry.','top')
                return
            self.screenObj.addLine('Depositing EUR '+"{:.2f}".format(self.newItemPrice)+' to '+str(self.currentMember.nick),'top')
#            self.screenObj.sendIrcLine('Deposit: EUR '+"{:.2f}".format(self.newItemPrice))
            self.bar.payAmount(self.currentMember,self.newItemPrice)
            self.resetFlags()
            self.resetVariables()
            return

    def askNextNewItemQuestion(self):
        if not self.newItemDesc:
            self.screenObj.addLine('Please enter a description or name.','top')
            return
        if not self.newItemVolume:
            self.screenObj.addLine('Please enter a size or volume (e.g. 500ml).','top')
            return
        if not self.newItemCountry:
            self.screenObj.addLine('Please enter a country of origin (e.g. Germany).','top')
            return
        if self.newItemPrice is None:
            self.screenObj.addLine("Please enter a price (in EUR). If you don't know one, leave blank.",'top')
            return

    def registerNewItem(self):
        if self.registeringItem == False:
            self.resetFlags()
            self.resetVariables()
            self.registeringItem=True

            self.screenObj.addLine('Looking online for what this is...','top')
            response = barcodelookup.BarcodeLookup().lookupBarcode(self.newBarcode)
            if response:
                self.newItemDesc,self.newItemVolume,self.newItemCountry = response
                try:
                    name = countries.get(self.newItemCountry).name
                except:
                    name = self.newItemCountry
                self.screenObj.addLine('I think this is '+str(self.newItemDesc)+' '+str(self.newItemVolume)+' from '+name+'.','top')
                self.askNextNewItemQuestion()
                return
            else:
                self.screenObj.addLine('Not found. Now asking you for a description, then a size, a country of origin and a price.','top')
                self.askNextNewItemQuestion()
                return
        if not self.newItemDesc:
            self.newItemDesc = str(self.lastLine.strip())
            self.askNextNewItemQuestion()
            return
        if not self.newItemVolume:
            self.newItemVolume = str(self.lastLine.strip())
            self.askNextNewItemQuestion()
            return
        if self.newItemCountry is None:
            if self.lastLine.strip() is not '':
                try:
                    countries.get(str(self.lastLine.strip()))
                except:
                    self.screenObj.addLine("Unrecognised country. Please try again (or leave blank) (HINT: ccTLD's work best).",'top')
                    return
            self.newItemCountry = str(self.lastLine.strip())
            self.askNextNewItemQuestion()
            return
        if self.newItemPrice is None:
            if self.lastLine.strip() == '':
                self.newItemPrice = 0
            try:
                self.newItemPrice = float(self.lastLine.strip())
            except:
                self.newItemPrice = 0
                self.screenObj.addLine('Invalid value. Skipping...','top')
        self.screenObj.addLine('Entering data now.','top')
        if self.newItemPrice is not 0:
            self.bar.addItem(self.newBarcode,self.newItemPrice)
        if self.newItemDesc and self.newItemVolume and self.newItemCountry:        
            self.bar.addBarcodeDesc(self.newBarcode,self.newItemDesc,self.newItemVolume,self.newItemCountry)
            self.resetFlags()
            self.resetVariables()
            return

    def registerNewUser(self):
        if self.registeringUser == False:
            self.resetFlags()
            self.resetVariables()
            self.registeringUser=True

            self.screenObj.addLine('New user. Please enter a username.','top')
            return
        if not self.newUsername:
            self.newUsername = str(self.lastLine.strip())
            self.screenObj.addLine('Adding new user '+str(self.newUsername)+'...','top')
            self.bar.addMember(self.newBarcode,self.newUsername)
            self.resetFlags()
            self.resetVariables()
            self.state = 'BUY'
            return

    def lineReceived(self, barcode):
        try:
            self.bar.handleBarcode(barcode)
        except exceptions.ItemOutOfStockError:
            pass
        except exceptions.ItemDoesNotExistError:
            pass
            self.screenObj.addLine("Unknown item barcode. Registering...",'top')
            self.newBarcode = barcode
            self.registerNewItem()
#            self.bar.resetHandleState()
        except Exception:
#            self.bar.resetHandleState()
            log.error(traceback.format_exc())


@CursesInterfacePlugin
def getLocalInterfacePlugin(bar,screenObj,reactor):
    log.info('Starting barcode monitor')
    port=bar.config.get('scanner','port')
    log.debug('Using serial port %s'%port)
    baudrate=bar.config.get('scanner','baudrate')
    serialport.SerialPort(BarcodeProtocol(bar,screenObj),port,reactor,baudrate=baudrate)
