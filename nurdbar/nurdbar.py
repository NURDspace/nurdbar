"""
This file contains the main API to manipulate the bar and database. All plugins should use the instance methods of the NurdBar object.
"""
from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item,Transaction
import events
import exceptions
from decimal import Decimal
import logging
import logging.config
import traceback


class BarcodeTypes(object):
    ITEMBARCODE = 'Item Barcode'
    MEMBERBARCODE = 'Member Barcode'

class NurdBar(object):
    """
    The main NurdBar API. Use this API to interact with the bar. Plugins receive an instance of this class, so they can interact with the bar.
    """
    def __init__(self,configfile='nurdbar.cfg'):
        """
        INstantiate the NurdBar

        :param configfile: The filename of the configuration file to read.
        :type configfile: str
        """
        logging.config.fileConfig(configfile)
        self.log=logging.getLogger(__name__)
        self.config=NurdBar.read_config(configfile)
        self.log.debug('Read config')
        print('setup nurdbar')
        self.engine,self.metadata,self.session=self.setupModel()
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
        if not str(barcode).startswith('1337'):
            return BarcodeTypes.ITEMBARCODE
        if str(barcode).startswith('1337'):
            return BarcodeTypes.MEMBERBARCODE

    def resetHandleState(self):
        """
        Reset the state of handling barcodes. It reseults self.receivedMember and self.receivedItems
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
        if self.getBarcodeType(barcode) == BarcodeTypes.MEMBERBARCODE:
            self.receivedMember=self.getMemberByBarcode(barcode)
        elif self.getBarcodeType(barcode) == BarcodeTypes.ITEMBARCODE:
            item=self.getAvailableItemByBarcode(barcode)
            if not item:
                item=self.getItemByBarcode(barcode)
                if item:
                    events.OutOfStockEvent.fire(item)
                    raise exceptions.ItemOutOfStockError('Item %s (%s) is out of stock'%(item.item_id,item.barcode))
                raise exceptions.ItemDoesNotExistError('Item %s does not exist'%barcode)
            self.receivedItems.append(item)
        if self.receivedMember is not None and len(self.receivedItems)>0:
            for item in self.receivedItems:
                self.takeItem(self.receivedMember.barcode,item.barcode)
            self.receivedItems = []
            self.receivedMember = None

    def giveItem(self,member_barcode,item_barcode,buy_price=None,amount=1,sell_price=None):
        """
        Give an item, or on other words, sell something to the bar/add stock. This both changes the stock of the item being given, and changes the balance for the Member giving the item.
        If the Item already exists (with the same buy_price), this item is used. If the Item is new, a new Item is stored in the database.
        If the Member is unkown, ValueError is raised.

        :param member_barcode: The barcode of the Member giving the Item.
        :type member_barcode: str
        :param item_barcode: The barcode fo the Item being given.
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
            raise ValueError('Member with barcode %s is unkown'%(member_barcode,))
        if sell_price==None:
            sell_price=buy_price
        item=self.getItemByBarcodePrice(item_barcode,buy_price)
        if item==None:
            item=self.addItem(item_barcode,buy_price,sell_price)
        self.log.info('Changing stock of item %s from %s to %s'%(item.item_id,item.stock,item.stock+amount))
        item.stock+=amount
        return self.addTransaction(item,member,transaction_price=buy_price*amount)

    def takeItem(self,member_barcode,item_barcode,amount=1):
        """
        Take an Item from the bar. In other words: buy something. This both changes the stock of the Item, and the balance of the Member taking the Item.
        If multiple Items with the same barcode but different buy_price exist, the oldest Item is sold first untill it stock runs out, then the next-oldest Item will be sold, etc.
        If no stock is present, or the Member is unkown, a ValueError will be raised.

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
            raise ValueError('Member with barcode %s is unkown'%member_barcode)
        rest_amount=0
        item=self.getAvailableItemByBarcode(item_barcode)
        payment_item=self.getItemByBarcode(1010101010)
        if not item:
            raise ValueError('Item is not available (no stock present)')
        self.log.info('Member %s has taken %s item(s) %s with barcode %s and sell_price %s'%(member.member_id,amount,item.item_id,item.barcode,item.sell_price))
        if amount>item.stock:
            #check if more items are taken then we have in stock. Only add transaction up to amount stock
            rest_amount=amount-item.stock
            amount=item.stock
        self.log.info('Changing stock of item %s from %s to %s'%(item.item_id,item.stock,item.stock-amount))
        item.stock-=amount
        taken_price=amount*item.sell_price
        self.log.debug('total taken_price: %s'%taken_price)
        if len(member.positiveTransactions)>0:
            #check if there are still postive transactions, if so, substract the current taken items from them
            processed_payment_price=0
            for t in member.positiveTransactions:
                payment_price=t.transaction_price
                self.log.debug('Found positive transaction: %s with payment_price: %s'%(t,payment_price))
                if payment_price>taken_price-processed_payment_price:
                    #we found a payment, worth more that what we are taking. Split it in 2 and mark one as archived
                    paid_price=taken_price-processed_payment_price
                    self.log.debug('Changing transaction %s transaction_price to %s'%(t,t.transaction_price-paid_price))
                    t.transaction_price=t.transaction_price-paid_price
                    trans=self.addTransaction(payment_item,member,paid_price)
                    trans.archived=True
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
                raise
            taken_price=taken_price-processed_payment_price #only process the remaining price
        if taken_price>0:
            trans=self.addTransaction(item,member,-taken_price)
        if rest_amount>0:
            return self.takeItem(member_barcode,item_barcode,rest_amount)
        else:
            return trans

    def fill_tables(self):
        payment_item=self.addItem(1010101010,0.01)

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
        return self.session.query(Member).filter_by(barcode=barcode).first()

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
        Get an Item by it's barcode. Whether or not it is in stock, is not taken into account. The oldest item is returned.

        :param barcode: The barcode of the Item to get.
        :type barcode: str
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter_by(barcode=barcode).order_by(Item.creationDateTime).first()

    def getItemByBarcodePrice(self,barcode,buy_price):
        """
        Get an Item by it's barcode and buy_price. Whether or not it is in stock, is not taken into account.

        :param barcode: The barcode of the Item to get.
        :type barcode: str
        :param buy_price: The buy_price of the Item to get.
        :type buy_price: float
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter_by(barcode=barcode,buy_price=buy_price).order_by(Item.creationDateTime).first()

    def getAvailableItemByBarcode(self,barcode):
        """
        Get the first available (stock>0) Item by barcode. If several items with the same barcode are available, the oldest available Item is returned.

        :param barcode: The barcode for which to get the Item.
        :type barcode: str
        :returns: nurdbar.model.Item
        """
        return self.session.query(Item).filter(Item.barcode==barcode,Item.stock>0).order_by(Item.creationDateTime).first()

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
        payment_item=self.getItemByBarcode(1010101010)
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
        Add an Item to the bar.

        :param barcode: The barcode of the new Item
        :type barcode: str
        :param buy_price: The price for which the Item is bought by the bar
        :type buy_price: float
        :param sell_price: The price by which the Item is sold by the bar (defaults to buy_price)
        :type sell_price: float
        :returns: model.Member
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
            raise
        return item
