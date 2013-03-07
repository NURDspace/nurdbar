from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item,Transaction
from decimal import Decimal

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
        self.config=NurdBar.read_config(configfile)
        self.engine,self.metadata,self.session=NurdBar.setupModel(self.config)
        self.receivedItems=[]
        self.receivedMember=None

    @staticmethod
    def setupModel(config):
        #setup the model
        engine=create_engine(config.get('db','uri'))
        Session = sessionmaker(bind=engine)
        metadata=Base.metadata
        metadata.bind=engine
        session = Session()
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
                raise ValueError('Item is not available (no stock present)')
            self.receivedItems.append(item)
        if self.receivedMember is not None and len(self.receivedItems)>0:
            for item in self.receivedItems:
                self.takeItem(self.receivedMember.barcode,item.barcode)
            self.receivedItems = []
            self.receivedMember = None

    def giveItem(self,member_barcode,item_barcode,price,amount=1):
        """
        Give an item, or on other words, sell something to the bar/add stock. This both changes the stock of the item being given, and changes the balance for the Member giving the item.
        If the Item already exists (with the same price), this item is used. If the Item is new, a new Item is stored in the database.
        If the Member is unkown, ValueError is raised.

        :param member_barcode: The barcode of the Member giving the Item.
        :type member_barcode: str
        :param item_barcode: The barcode fo the Item being given.
        :type item_barcode: str
        :param price: The price of the item being given
        :type price: float
        :param amount: The amount of Items being given
        :type amount: int
        :returns: nurdbar.model.Transaction
        :raises: ValueError
        """
        member=self.getMemberByBarcode(member_barcode)
        if member==None:
            raise ValueError('Member with barcode %s is unkown'%(member_barcode,))
        item=self.getItemByBarcodePrice(item_barcode,price)
        if item==None:
            item=self.addItem(item_barcode,price)
        return self.addTransaction(item,member,amount)

    def takeItem(self,member_barcode,item_barcode,amount=1):
        """
        Take an Item from the bar. In other words: buy something. This both changes the stock of the Item, and the balance of the Member taking the Item.
        If multiple Items with the same barcode but different price exist, the oldest Item is sold first untill it stock runs out, then the next-oldest Item will be sold, etc.
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

        rest_amount=0
        item=self.getAvailableItemByBarcode(item_barcode)
        if not item:
            raise ValueError('Item is not available (no stock present)')
        if amount>item.stock:
            #check if more items are taken then we have in stock. Only add transaction up to amount stock
            rest_amount=amount-item.stock
            amount=item.stock
        member=self.getMemberByBarcode(member_barcode)
        if not member:
            raise ValueError('Member with barcode %s is unkown'%member_barcode)
        trans=self.addTransaction(item,member,-amount)
        if rest_amount>0:
            return self.takeItem(member_barcode,item_barcode,rest_amount)
        else:
            return trans

    def fill_tables(self):
        payment_item=self.addItem(1010101010,0.01)

    def create_tables(self):
        self.metadata.create_all()

    def drop_tables(self):
        self.metadata.drop_all()

    def getMemberByBarcode(self,barcode):
        return self.session.query(Member).filter_by(barcode=barcode).first()

    def getMemberByNick(self,nick):
        return self.session.query(Member).filter_by(nick=nick).first()

    def addMember(self,barcode,nick):
        member=Member(barcode,nick)
        self.session.add(member)
        self.session.commit()
        self.session.flush()
        return member

    def getItemByBarcode(self,barcode):
        return self.session.query(Item).filter_by(barcode=barcode).first()

    def getItemByBarcodePrice(self,barcode,price):
        return self.session.query(Item).filter_by(barcode=barcode,price=price).order_by(Item.creationDateTime).first()

    def getAvailableItemByBarcode(self,barcode):
        return self.session.query(Item).filter(Item.barcode==barcode,Item.stock>0).order_by(Item.creationDateTime).first()

    def getBalance(self,member):
        return member.balance

    def getTransactions(self,member):
        return member.transactions

    def payAmount(self,member,amount):
        payment_item=self.getItemByBarcode(1010101010)
        self.addTransaction(payment_item,member,int(amount*100))

    def addTransaction(self,item,member,count):
        trans=Transaction()
        self.session.add(trans)
        trans.item=item
        trans.member=member
        self.session.commit()
        self.session.flush()
        trans.count=count
        self.session.commit()
        self.session.flush()
        return trans

    def addItem(self,barcode,price):
        item=Item(barcode,price)
        self.session.add(item)
        self.session.commit()
        self.session.flush()
        return item
