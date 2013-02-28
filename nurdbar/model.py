from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime
from sqlalchemy.types import BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey

Base = declarative_base()

class Member(Base):
    __tablename__ = 'members'
    member_id = Column(Integer, primary_key=True)
    barcode = Column(BigInteger)
    nick = Column(String)

    def __init__(self,barcode,nick):
        self.nick=nick
        self.barcode=barcode

class Item(Base):
    __tablename__ = 'items'
    item_id = Column(Integer, primary_key=True)
    barcode = Column(BigInteger)
    price = Column(Numeric)
    voorraad = Column(Integer)

    def __init__(self,barcode,price):
        self.barcode=barcode
        self.price=price
        self.voorraad=0

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.item_id'))
    member_id = Column(Integer, ForeignKey('members.member_id'))
    _count = Column("count",Integer)
    transactionDate = Column(DateTime)

    item = relationship("Item",backref=backref('transactions'))
    member = relationship("Member",backref=backref('transactions'))

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self,count):
        self.item.voorraad+=count
        self._count=count

    def __init__(self,count,item):
        self.item_id=item.item_id
        self.count=count
