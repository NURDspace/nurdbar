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
    __tablename__ = 'members'
    member_id = Column(Integer, primary_key=True)
    creationDateTime = Column(DateTime,default=datetime.datetime.now)
    lastModifiedDateTime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    barcode = Column(BigInteger,unique=True)
    nick = Column(String)

    @property
    def balance(self):
        return sum([t.count*t.item.price for t in self.transactions])

    @property
    def transactions(self):
        return self._transactions.filter(Transaction.archived==False).order_by(Transaction.transactionDateTime).all()

    @property
    def negativeTransactions(self):
        return self._transactions.filter(Transaction.archived==False,Transaction._count<0).order_by(Transaction.transactionDateTime).all()

    @property
    def positiveTransactions(self):
        return self._transactions.filter(Transaction.archived==False,Transaction._count>0).order_by(Transaction.transactionDateTime).all()

    @property
    def allTransactions(self):
        return self._transactions.order_by(Transaction.transactionDateTime).all()

    def __init__(self,barcode,nick):
        self.nick=nick
        self.barcode=barcode

class Item(Base):
    __tablename__ = 'items'
    __table_args__ = (UniqueConstraint('price','barcode'),)
    item_id = Column(Integer, primary_key=True)
    barcode = Column(BigInteger,nullable=False)
    creationDateTime = Column(DateTime,default=datetime.datetime.now)
    lastModifiedDateTime = Column(DateTime,onupdate=datetime.datetime.now,default=datetime.datetime.now)
    price = Column(Numeric)
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
