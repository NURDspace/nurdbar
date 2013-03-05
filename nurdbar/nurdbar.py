from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item,Transaction
from decimal import Decimal

class BarcodeTypes(object):
    ITEMBARCODE = 'Item Barcode'
    MEMBERBARCODE = 'Member Barcode'

class NurdBar(object):
    def __init__(self,configfile='nurdbar.cfg'):
        self.config=NurdBar.read_config(configfile)
        self.engine,self.metadata,self.session=NurdBar.setupModel(self.config)
        self.receivedItems=[]
        self.receivedMember=None

    @staticmethod
    def setupModel(config):
        engine=create_engine(config.get('db','uri'))
        Session = sessionmaker(bind=engine)
        metadata=Base.metadata
        metadata.bind=engine
        session = Session()
        return (engine,metadata,session)

    @staticmethod
    def read_config(configfile):
        config=SafeConfigParser()
        config.readfp(open(configfile,'r'))
        return config

    def getBarcodeType(self,barcode):
        if not str(barcode).startswith('1337'):
            return BarcodeTypes.ITEMBARCODE
        if str(barcode).startswith('1337'):
            return BarcodeTypes.MEMBERBARCODE

    def handleBarcode(self,barcode):
        #handle receiving of a barcode. Check the barcode type. Check what was previously received and if that and barcode type make sense, act upon them.
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
        member=self.getMemberByBarcode(member_barcode)
        if member==None:
            raise ValueError('Member with barcode %s is unkown'%(member_barcode,))
        item=self.getItemByBarcodePrice(item_barcode,price)
        if item==None:
            item=self.addItem(item_barcode,price)
        return self.addTransaction(item,member,amount)

    def takeItem(self,member_barcode,item_barcode,amount=1):
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
