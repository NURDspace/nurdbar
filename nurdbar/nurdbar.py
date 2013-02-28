from ConfigParser import SafeConfigParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base,Member,Item



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

    def getNewOrExistingMember(self,barcode=False,nick=False):
        member=(barcode and self.getMemberByBarcode(barcode)) or (nick and self.getMemberByNick(nick)) or None
        if not member:
            member=Member(barcode,nick)
            self.session.add(member)
        else:
            if nick:
                member.nick=nick
            if barcode:
                member.barcode=barcode
        self.session.commit()
        self.session.flush()
        return member

    def getItemByBarcode(self,barcode):
        self.session.query(Item).filter_by(barcode=barcode)

    def getNewOrExistingItem(self,barcode=None):
        item=(barcode and self.getItemByBarcode(barcode)) or None
        if not item:
            item=Item(barcode,0)
            self.session.add(item)
        self.session.commit()
        self.session.flush()
        return item
