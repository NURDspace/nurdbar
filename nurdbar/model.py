"""
The datamodel for the NurdBar. The datamodel is created using SQLAlchemy. Instances of each datamodel object represent a row.
Manipulation of the database can be done by instantiating and manipulating these objects.
For a first intro on SQLAlchemy see http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html#querying
"""
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Boolean, func
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.types import BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
import logging
import datetime
log=logging.getLogger(__name__)

Base = declarative_base()

class Member(Base):
    """
    Members represent the "customers" of the bar.
    """
    __tablename__ = 'members'
    #: Id of the member
    member_id = Column(Integer, primary_key=True)
    #: Date the Member was created
    creationdatetime = Column(DateTime,default=datetime.datetime.now)
    #: DateTime on which the Member was last modified
    lastmodifieddatetime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    #: Barcode of the Member.
    barcode = Column(String,unique=True)
    #: Nick of the Member
    nick = Column(String)

    @property
    def balance(self):
        """
        The (financial) balance for the Member. It is dynamically calculated from the member's (non-archived) transactions.
        """
        return sum([t.transaction_price for t in self.transactions])

    @property
    def transactions(self):
        """
        The members (non-archived) transactions.
        """
        return self._transactions.filter(Transaction.archived==False).order_by(Transaction.transactiondatetime).all()

    @property
    def negativeTransactions(self):
        """
        The members (non-archived) negative transactions (items bought).
        """
        return self._transactions.filter(Transaction.archived==False,Transaction.transaction_price<0).order_by(Transaction.transactiondatetime).all()

    @property
    def positiveTransactions(self):
        """
        The members (non-archived) positive transactions (items sold and payments).
        """
        return self._transactions.filter(Transaction.archived==False,Transaction.transaction_price>0).order_by(Transaction.transactiondatetime).all()

    @property
    def allTransactions(self):
        """
        All transactions of the member.
        """
        return self._transactions.order_by(Transaction.transactiondatetime).all()

    def __init__(self,barcode,nick):
        self.nick=nick
        self.barcode=barcode

class Item(Base):
    """
    All items that can be sold. When the NurdBar is initialized with fill_tables(), also an Item is instantiated for payments.
    """
    __tablename__ = 'items'
    __table_args__ = (UniqueConstraint('buy_price','barcode'),)
    #: Id of the item (primary key)
    item_id = Column(Integer, primary_key=True)
    #: Barcode of the item. The combination of barcode and buy_price should be unique (but the barcode itself does not have to be).
    barcode = Column(String,nullable=False)
    #: Creation DateTime of the Item.
    creationdatetime = Column(DateTime,default=datetime.datetime.now)
    #: Last modification DateTime of the Item.
    lastmodifieddatetime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    #: Buy price of the Item (for which the Item was bought)
    buy_price = Column(Numeric)
    #: Sell price of the Item (for which the Item will be sold). Defaults to buy_price
    sell_price = Column(Numeric)
    #: The amount of the Item in stock (modified by creating transactions).
    stock = Column(Integer)

    def __init__(self,barcode,buy_price,sell_price=None,stock=0):
        log.debug('Adding Item with barcode %s, buy_price %s, sell_price %s'%(barcode,buy_price,sell_price))
        if sell_price == None:
            sell_price = buy_price
            log.debug('Setting sell price to %s'%sell_price)
        self.barcode=barcode
        self.buy_price=buy_price
        self.sell_price=sell_price
        self.stock=stock

class BarcodeDesc(Base):
    """
    All descriptions for barcodes. May or may not be automatically generated.
    """
    __tablename__ = 'barcodedesc'
    #: id of the desc (primary key)
    desc_id = Column(Integer, primary_key=True)
    #: Barcode of the item. This must be present. MAY clash in the future with RCN-8s - Functionality to fix then.
    barcode = Column(String,nullable=False)
    #: Creation DateTime of the name.
    creationdatetime = Column(DateTime,default=datetime.datetime.now)
    #: text description of this barcode.
    description = Column(String)
    #: size/weight of this barcode item.
    volume = Column(String)
    #: issuing country of this barcode.
    issuing_country = Column(String)

    def __init__(self,barcode,description,volume='',issuing_country=''):
        log.debug('Adding barcode description with barcode %s, description %s, volume %s, issuing country %s'%(barcode,description,volume,issuing_country))
        self.barcode=barcode
        self.description=description
        self.volume=volume
        self.issuing_country=issuing_country

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.item_id'))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    transactiondatetime = Column(DateTime,default=datetime.datetime.now)
    archived = Column(Boolean,default=False)
    transaction_price = Column(Numeric)

    _item = relationship("Item",backref=backref('_transactions',lazy='dynamic'))
    member = relationship("Member",backref=backref('_transactions',lazy='dynamic'))

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self,item):
        if self.transaction_price==None:
            self.transaction_price=item.sell_price
        self._item=item

    def __init__(self):
        log.debug('Starting new transaction')
        pass

    def __repr__(self):
        return "<Transaction transaction_price:%s item:%s member:%s archived:%s>"%(self.transaction_price,self.item.item_id,self.member.member_id,self.archived)
