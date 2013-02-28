from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item,Transaction

class Bill(object):
    def __init__(self,member,transactions):
        self.member=member
        self.transactions=transactions
        self.total=member.balance


class NurdBar(object):
    def __init__(self,configfile='nurdbar.cfg'):
        self.config=self.read_config(configfile)
        self.engine=create_engine(self.config.get('db','uri'))
        Session = sessionmaker(bind=self.engine)
        self.metadata=Base.metadata
        self.metadata.bind=self.engine
        self.session = Session()

    def create_tables(self):
        self.metadata.create_all()

    def read_config(self,configfile):
        config=SafeConfigParser()
        config.readfp(open('nurdbar.cfg','rw'))
        return config

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

    def getBill(self,member):
        transactions=self.session.query(Transaction).filter_by(member_id=member.member_id).all()
        return Bill(transactions=transactions,member=member)

    def addTransaction(self,item,member,count):
        trans=Transaction()
        trans.item=item
        trans.member=member
        self.session.add(trans)
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
