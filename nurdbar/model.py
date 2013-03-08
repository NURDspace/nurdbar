"""
The datamodel for the NurdBar. The datamodel is created using SQLAlchemy. Instances of each datamodel object represent a row.
Manipulation of the database can be done by instantiating and manipulating these objects.
For a first intro on SQLAlchemy see http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html#querying
"""
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Boolean
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
    creationDateTime = Column(DateTime,default=datetime.datetime.now)
    #: DateTime on which the Member was last modified
    lastModifiedDateTime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    #: Barcode of the Member.
    barcode = Column(BigInteger,unique=True)
    #: Nick of the Member
    nick = Column(String)

    @property
    def balance(self):
        """
        The (financial) balance for the Member. It is dynamically calculated from the member's (non-archived) transactions.
        """
        return sum([t.count*t.item.price for t in self.transactions])

    @property
    def transactions(self):
        """
        The members (non-archived) transactions.
        """
        return self._transactions.filter(Transaction.archived==False).order_by(Transaction.transactionDateTime).all()

    @property
    def negativeTransactions(self):
        """
        The members (non-archived) negative transactions (items bought).
        """
        return self._transactions.filter(Transaction.archived==False,Transaction._count<0).order_by(Transaction.transactionDateTime).all()

    @property
    def positiveTransactions(self):
        """
        The members (non-archived) positive transactions (items sold and payments).
        """
        return self._transactions.filter(Transaction.archived==False,Transaction._count>0).order_by(Transaction.transactionDateTime).all()

    @property
    def allTransactions(self):
        """
        All transactions of the member.
        """
        return self._transactions.order_by(Transaction.transactionDateTime).all()

    def __init__(self,barcode,nick):
        self.nick=nick
        self.barcode=barcode

class Item(Base):
    """
    All items that can be sold. When the NurdBar is initialized with fill_tables(), also an Item is instantiated for payments.
    """
    __tablename__ = 'items'
    __table_args__ = (UniqueConstraint('price','barcode'),)
    #: Id of the item (primary key)
    item_id = Column(Integer, primary_key=True)
    #: Barcode of the item. The combination of barcode and price should be unique (but the barcode itself does not have to be).
    barcode = Column(BigInteger,nullable=False)
    #: Creation DateTime of the Item.
    creationDateTime = Column(DateTime,default=datetime.datetime.now)
    #: Last modification DateTime of the Item.
    lastModifiedDateTime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    #: Price of the Item
    price = Column(Numeric)
    #: The amount of the Item in stock (modified by creating transactions).
    stock = Column(Integer)

    def __init__(self,barcode,price):
        self.barcode=barcode
        self.price=price
        self.stock=0

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.item_id'))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    _count = Column("count",Integer)
    transactionDateTime = Column(DateTime)
    archived = Column(Boolean,default=False)

    item = relationship("Item",backref=backref('_transactions',lazy='dynamic'))
    member = relationship("Member",backref=backref('_transactions',lazy='dynamic'))

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self,count):
        log.debug('changing item %s stock from %s to %s'%(self.item.item_id,self.item.stock,self.item.stock+count))
        self.item.stock+=count
        self._count=count

    def __init__(self):
        log.debug('Starting new transaction')
        pass

    def __repr__(self):
        return "<Transaction count:%s price:%s item:%s member:%s archived:%s>"%(self._count,self.item.price,self.item.item_id,self.member.member_id,self.archived)
