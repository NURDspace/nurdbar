"""
This file contains the main API to manipulate the bar and database. All plugins should use the instance methods of the NurdBar object.
"""
from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item,Transaction,BarcodeDesc
import events
import exceptions
from decimal import Decimal
import logging
import logging.config
import traceback
from iso3166 import countries

class BarcodeTypes(object):
    ITEMBARCODE = 'Item Barcode'
    COMMANDBARCODE = 'Command Barcode'
    MEMBERBARCODE = 'Member Barcode'

class NurdBar(object):
    """
    The main NurdBar API. Use this API to interact with the bar. Plugins receive an instance of this class, so they can interact with the bar.
    """
    def __init__(self,configfile='nurdbar.cfg'):
        """
        Instantiate the NurdBar

        :param configfile: The filename of the configuration file to read.
        :type configfile: str
        """
        logging.config.fileConfig(configfile)
        self.log=logging.getLogger(__name__)
        self.config=NurdBar.read_config(configfile)
        self.log.debug('Read config')
        print('setup nurdbar')
        self.engine,self.metadata,self.session=self.setupModel()
        self.commandPrefix='CMD'
        self.memberPrefix='USR'
        self.receivedItems=[]
        self.receivedMember=None

    def setupModel(self):
        #setup the model
        engine=create_engine(self.config.get('db','uri'))
        Session = sessionmaker(bind=engine)
        metadata=Base.metadata
        metadata.bind=engine
        session = Session()
        self.log.debug('Session setup')
        return (engine,metadata,session)

    @staticmethod
    def read_config(configfile):
        #read the config
        config=SafeConfigParser()
        config.readfp(open(configfile,'r'))
        return config

    def getBarcodeType(self,barcode):
        """
        Return the type of barcode.

        :param barcode: The barcode to check
        :type barcode: str
        :return: BarcodeTypes -- Constant for the type of barcode.

        """
        if str(barcode).startswith(self.memberPrefix):
            return BarcodeTypes.MEMBERBARCODE
        elif str(barcode).startswith(self.commandPrefix):
            return BarcodeTypes.COMMANDBARCODE
        else:
            return BarcodeTypes.ITEMBARCODE

    def resetHandleState(self):
        """
        Reset the state of handling barcodes. It resets self.receivedMember and self.receivedItems
        """
        self.receivedMember=None
        self.recevedItems=[]

    def handleBarcode(self,barcode):
        """
        Handle the reception of a barcode. The barcode type is checked, and the state of previously received barcodes is checked. If a sane combination of barcodes is
        received, act upon them.

        :param barcode: the received barcode.
        :type barcode: str
        """
        barcode=events.BarcodeScannedEvent.fire(barcode)
        if self.getBarcodeType(barcode) == BarcodeTypes.MEMBERBARCODE:
            self.receivedMember=self.getMemberByBarcode(barcode)
            self.receivedMember=events.MemberBarcodeScannedEvent.fire(self.receivedMember)
        elif self.getBarcodeType(barcode) == BarcodeTypes.COMMANDBARCODE:
            events.CommandBarcodeScannedEvent.fire(self.commandChange(barcode))
        elif self.getBarcodeType(barcode) == BarcodeTypes.ITEMBARCODE:
            item=self.getAvailableItemByBarcode(barcode)
            bdesc=self.getBarcodeDescByBarcode(barcode)
            if not bdesc and not item:
                raise exceptions.ItemDoesNotExistError('Item %s does not exist'%barcode)
#                    events.ItemBarcodeScannedEvent.fire(item)
#                    events.OutOfStockEvent.fire(item)
#                    raise exceptions.ItemOutOfStockError('Item %s (%s) is out of stock'%(item.item_id,item.barcode))
            events.ItemBarcodeScannedEvent.fire(item,bdesc)
#            self.receivedItems.append(item)
#        if self.receivedMember is not None and len(self.receivedItems)>0:
#            if self.commandState == 'SELL':
#                buyprice = None #Need to add user input for this one.
#                for item in self.receivedItems:
#                    self.sellItem(self.receivedMember.barcode,item.barcode,buyprice)
#            else:
#                for item in self.receivedItems:
#                    self.buyItem(self.receivedMember.barcode,item.barcode)
#            self.receivedItems = []
#            self.receivedMember = None #Timeout needed for this.

    def sellItem(self,member_barcode,item_barcode,buy_price=None,amount=1,sell_price=None):
        """
        Sell something to the bar/add stock. This both changes the stock of the item being given, and changes the balance for the Member giving the item.
        If the Item already exists (with the same buy_price), this item is used. If the Item is new, a new Item is stored in the database.
        If the Member is unkown, ValueError is raised.

        :param member_barcode: The barcode of the Member giving the Item.
        :type member_barcode: str
        :param item_barcode: The barcode of the Item being given.
        :type item_barcode: str
        :param buy_price: The buy price (for which the bar buys it) of the item being given
        :type buy_price: float
        :param amount: The amount of Items being given
        :type amount: int
        :param sell_price: The sell price (for which the bar buys it) of the item being given. It defaults to the buy_price
        :type sell_price: float
        :returns: nurdbar.model.Transaction
        :raises: ValueError
        """
        member=self.getMemberByBarcode(member_barcode)
        if member==None:
            raise ValueError('Member with barcode %s is unknown'%(member_barcode,))
        if sell_price==None:
            sell_price=buy_price
        item=self.getItemByBarcodePrice(item_barcode,buy_price)
        if item==None:
            item=self.addItem(item_barcode,buy_price,sell_price)
        self.log.info('Changing stock of item %s from %s to %s'%(item.item_id,item.stock,item.stock+amount))
        item.stock+=amount
        return self.addTransaction(item,member,transaction_price=buy_price*amount)

    def buyItem(self,member_barcode,item_barcode,amount=1):
        """
        Buy an Item from the bar. This both changes the stock of the Item, and the balance of the Member taking the Item.
        If multiple Items with the same barcode but different buy_price exist, the oldest Item is sold first untill it stock runs out, then the next-oldest Item will be sold, etc.
        If no stock is present, or the Member is unknown, a ValueError will be raised.

        :param member_barcode: The barcode of the Member giving the Item.
        :type member_barcode: str
        :param item_barcode: The barcode fo the Item being given.
        :type item_barcode: str
        :param amount: The amount of Items being given
        :type amount: int
        :return: nurdbar.model.Transaction
        :raises: ValueError
        """
        member=self.getMemberByBarcode(member_barcode)
        if not member:
            raise ValueError('Member with barcode %s is unknown'%member_barcode)
#        item=self.getAvailableItemByBarcode(item_barcode)
#        payment_item=self.getItemByBarcode('CASH')
        itemlist=self.getAvailableItemsByBarcode(item_barcode)
        taken_price=0#amount*item.sell_price
        if not itemlist: #None:
            raise ValueError('Item is not available (no stock present)')
        self.log.info('Member %s has taken %s item(s) %s with barcode %s'%(member.member_id,amount,itemlist[0].item_id,itemlist[0].barcode))
        for item in itemlist:
            if amount>item.stock:
                #check if more items are taken then we have in stock. Only add transaction up to amount stock
                taken_price=taken_price+item.stock * item.sell_price
                amount=amount-item.stock
                self.log.info('Changing stock of item %s from %s to %s'%(item.item_id,item.stock,0))
                item.stock = 0
            else:
                taken_price=taken_price+amount * item.sell_price
                self.log.info('Partially changing stock of item %s from %s to %s'%(item.item_id,item.stock,item.stock-amount))
                item.stock=item.stock-amount
                amount=0
                break
        if amount>0:
            raise ValueError('Trying to buy more Items than the bar has.')
        self.log.debug('total taken_price: %s'%taken_price)
        if len(member.positiveTransactions)>0:
            #check if there are still positive transactions, if so, substract the current taken items from them
            processed_payment_price=0
            for t in member.positiveTransactions:
                payment_price=t.transaction_price
                self.log.debug('Found positive transaction: %s with payment_price: %s'%(t,payment_price))
                if payment_price>taken_price-processed_payment_price:
                    #we found a payment, worth more that what we are taking. Split it in 2 and mark one as archived
                    paid_price=taken_price-processed_payment_price
                    self.log.debug('Changing transaction %s transaction_price to %s'%(t,t.transaction_price-paid_price))
                    t.transaction_price=t.transaction_price-paid_price
#                    trans=self.addTransaction(payment_item,member,paid_price)
#                    trans.archived=True
                    processed_payment_price=taken_price
                elif payment_price<=taken_price-processed_payment_price:
                    self.log.debug('Setting transaction %s to archived=True'%t)
                    processed_payment_price+=payment_price
                    t.archived=True
                if processed_payment_price==taken_price:
                    break
            trans=self.addTransaction(item,member,-processed_payment_price) #add an archived transaction for all the taken items that were compensated with pre-existing payments
            trans.archived=True
            try:
                self.session.commit()
                self.session.flush()
            except Exception:
                self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
                self.session.rollback()
                raise exceptions.SessionCommitError
            taken_price=taken_price-processed_payment_price #only process the remaining price
        if taken_price>0:
            trans=self.addTransaction(item,member,-taken_price)
#        if rest_amount>0:
#            return self.buyItem(member_barcode,item_barcode,rest_amount)
        else:
            return trans

    def fill_tables(self):
        payment_item=self.addItem('CASH',0.01)
        pass

    def create_tables(self):
        self.metadata.create_all()
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise

    def drop_tables(self):
        self.metadata.drop_all()
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise

    def getMemberByBarcode(self,barcode):
        member=self.session.query(Member).filter_by(barcode=barcode).first()
        if member is None:
            events.MemberNotFoundEvent.fire(barcode=barcode)
        return member

    def getMemberByNick(self,nick):
        return self.session.query(Member).filter_by(nick=nick).first()

    def addMember(self,barcode,nick):
        """
        Add a member to the bar.

        :param barcode: The barcode of the new member
        :type barcode: str
        :param nick: The Nick of the member
        :type nick: str
        :returns: model.Member
        """
        member=Member(barcode,nick)
        self.session.add(member)
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise
        return member

    def getItemByBarcode(self,barcode):
        """
        Get an Item by it's barcode. Whether or not it is in stock, is not taken into account. The newest item is returned.

        :param barcode: The barcode of the Item to get.
        :type barcode: str
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter_by(barcode=barcode).order_by(Item.creationdatetime.desc()).first()

    def getItemByBarcodePrice(self,barcode,buy_price):
        """
        Get an Item by it's barcode and buy_price. Whether or not it is in stock, is not taken into account.

        :param barcode: The barcode of the Item to get.
        :type barcode: str
        :param buy_price: The buy_price of the Item to get.
        :type buy_price: float
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter_by(barcode=barcode,buy_price=buy_price).order_by(Item.creationdatetime).first()

    def getAvailableItemsByBarcode(self,barcode):
        """
        Get all available (stock>0) Item by barcode..

        :param barcode: The barcode for which to get the Items.
        :type barcode: str
        :returns: list of nurdbar.model.Item
        """
        return self.session.query(Item).filter(Item.barcode==barcode,Item.stock>0).order_by(Item.creationdatetime).all()

    def getAvailableItemByBarcode(self,barcode):
        """
        Get the first available (stock>0) Item by barcode. If several items with the same barcode are available, the oldest available Item is returned.

        :param barcode: The barcode for which to get the Item.
        :type barcode: str
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter(Item.barcode==barcode,Item.stock>0).order_by(Item.creationdatetime).first()

    def getItemTotalStock(self,barcode):
        """
        Get the total stock count of this item.

        :param barcode: The barcode to look for total stock count.
        :type barcode: str
        :returns: int
        """
        return self.session.query(func.sum(Item.stock)).filter(Item.barcode==barcode).first()[0]

    def getBalance(self,member):
        """
        Get the balance for the member

        :param member: The member for which to get the balance
        :type member: nurdbar.model.Member
        :returns: float
        """
        return member.balance

    def getTransactions(self,member):
        """
        Get all transactions for Member

        :param member: The model.Member object for which to get the transactions
        :type member: nurdbar.model.Member
        :returns: [nurdbar.model.Member]
        """
        return member.transactions

    def payAmount(self,member,amount):
        """
        Pay an amount to the bar.

        :param member: The member for which a payment is being done
        :type member: model.Member
        :param amount: The amount being paid
        :type amount: float
        """
        trans=None
        amount=Decimal(amount)
        processed_price=0
        for t in member.negativeTransactions:
            if processed_price-t.transaction_price<=amount:
                t.archived=True
                processed_price-=t.transaction_price
            if processed_price>=amount:
                self.log.debug('processed everything')
                break
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise
        payment_item=self.getItemByBarcode('CASH')
        if processed_price>0:
            trans=self.addTransaction(payment_item,member,processed_price)
            trans.archived=True
            try:
                self.session.commit()
                self.session.flush()
            except Exception:
                self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
                self.session.rollback()
                raise
        if amount-processed_price>0:
            trans=self.addTransaction(payment_item,member,amount-processed_price)
        return trans

    def addTransaction(self,item,member,transaction_price):
        self.log.debug('Adding transaction with item %s, transaction_price %s for member %s'%(item.item_id,transaction_price,member.member_id))
        trans=Transaction()
        self.session.add(trans)
        trans.item=item
        trans.member=member
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise
        trans.transaction_price=transaction_price
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise
        return trans

    def addItem(self,barcode,buy_price,sell_price=None):
        """
        Add a new Item entry to the bar.

        :param barcode: The barcode of the new Item
        :type barcode: str
        :param buy_price: The price for which the Item is bought by the bar
        :type buy_price: float
        :param sell_price: The price by which the Item is sold by the bar (defaults to buy_price)
        :type sell_price: float
        :returns: model.Item
        """
        if sell_price==None:
            sell_price=buy_price
        item=Item(barcode,buy_price,sell_price)
        self.session.add(item)
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise exceptions.SessionCommitError
        return item

    def addBarcodeDesc(self,barcode,description,volume='',issuing_country=''):
        """
        Add a new barcode description entry to the bar.

        :param barcode: The barcode of the new Item
        :type barcode: str
        :param description: The description of the barcode item
        :type description: str
        :param volume: The weight or size of the item in question.
        :type volume: str
        :param issuing_country: The issuing country.
        :type issuing_country: str
        :returns: model.BarcodeDesc
        """
        try:
            if issuing_country is not '':
                issuing_country = countries.get(issuing_country.lower()).alpha3.lower()
                self.log.debug("Identified country as %s"%issuing_country)
        except:
            raise ValueError("Unidentified country of origin")
        barcodedesc=BarcodeDesc(barcode,description,volume,issuing_country)
        self.session.add(barcodedesc)
        try:
            self.session.commit()
            self.session.flush()
        except Exception:
            self.log.error("Exception occured during commit:\n%s"%traceback.format_exc())
            self.session.rollback()
            raise exceptions.SessionCommitError
        return barcodedesc

    def getBarcodeDescByBarcode(self,barcode):
        """
        Get a Barcode Descriptor by it's barcode.

        :param barcode: The barcode of the description to get.
        :type barcode: str
        :returns: nurdbar.model.BarcodeDesc
        """
        return self.session.query(BarcodeDesc).filter_by(barcode=barcode).first() #In case of an RCN-8 clash, this will need modification.

    def commandChange(self,barcode):
        """
        Change the command mode of the engine by barcode lookup. Essentially a tiny hardlocked DB.
        :param barcode: The barcode of the command.
        :type barcode: str
        :returns: str containing mode selection.
        """
        if barcode == self.commandPrefix+'001':
            self.receivedItems = []
            self.receivedMember = None
            return 'RESET'
        elif barcode == self.commandPrefix+'002':
            return 'NEWUSER'
        elif barcode == self.commandPrefix+'010':
            return 'SELL'
        elif barcode == self.commandPrefix+'011':
            return 'BUY'
        elif barcode == self.commandPrefix+'012':
            return 'DEPOSIT'
        elif barcode == self.commandPrefix+'013':
            return 'TOGGLE_IRC'
