from _basetest import BaseTest
from nurdbar import NurdBar, BarcodeTypes, model
from decimal import Decimal
import logging
log=logging.getLogger(__name__)

class TestBar(BaseTest):

    def setUp(self):
        super(TestBar,self).setUp()
        self.member=self.bar.addMember(133713371337,'SmokeyD')
        self.member2=self.bar.addMember(133713371339,'SmokeyD2')
        self.item=self.bar.addItem(12312893712938,0.50)
        log.debug('Finished setUp')

    def test_barcodeType(self):
        self.assertEqual(self.bar.getBarcodeType(self.item.barcode),BarcodeTypes.ITEMBARCODE)
        self.assertEqual(self.bar.getBarcodeType(self.member.barcode),BarcodeTypes.MEMBERBARCODE)
        self.assertNotEqual(self.bar.getBarcodeType(self.member.barcode),BarcodeTypes.ITEMBARCODE)
        self.assertNotEqual(self.bar.getBarcodeType(self.item.barcode),BarcodeTypes.MEMBERBARCODE)

    def test_filled_tables(self):
        payment_item=self.bar.getItemByBarcode(1010101010)
        self.assertAlmostEqual(payment_item.sell_price,Decimal(0.01))

    def test_item(self):
        item=self.bar.getItemByBarcode(12312893712938)
        self.assertEqual(item.buy_price,0.50)
        self.assertEqual(item.sell_price,0.50)

    def test_member(self):
        member=self.bar.getMemberByNick('SmokeyD')
        self.assertEqual(member.barcode,133713371337)

    def test_duplicateItemBarcode(self):
        item2=self.bar.addItem(12312893712938,0.25)
        item=self.bar.getItemByBarcode(12312893712938)
        self.assertEqual(item.sell_price,0.50)

    def test_differentPrices_smallerPayment(self):
        log.debug('giving item')
        self.bar.giveItem(self.member.barcode,12312893712945,buy_price=0.10,amount=10,sell_price=0.75)
        self.assertEqual(self.member.balance,1.0)
        log.debug('taking item')
        self.bar.takeItem('133713371337',12312893712945,amount=5) #take a 5 beer
        self.assertEqual(self.member.balance,-2.75)

    def test_differentPrices_largerPayment(self):
        log.debug('giving item')
        item2=self.bar.addItem(12312893712945,buy_price=0.10,sell_price=0.75)
        item2.stock=10
        self.bar.payAmount(self.member,10) #pay 10 euro
        self.assertEqual(self.member.balance,10)
        log.debug('taking item')
        self.bar.takeItem('133713371337',12312893712945,amount=5) #take a 5 beer
        self.assertEqual(self.member.balance,6.25) #10-5*0.75=6.25

    def test_transaction(self):
        self.bar.addTransaction(self.item,self.member,self.item.sell_price*10) #add beer
        self.assertEqual(self.bar.getBalance(self.member),5)
        self.bar.addTransaction(self.item,self.member,-1*self.item.sell_price) #take a beer
        self.assertEqual(self.member.balance,4.50)
        self.bar.addTransaction(self.item,self.member,-1*self.item.sell_price) #take a beer
        self.assertEqual(self.member.balance,4)
        self.bar.addTransaction(self.item,self.member,-1*self.item.sell_price) #take a beer
        self.assertEqual(self.member.balance,3.50)
        self.bar.addTransaction(self.item,self.member,-8*self.item.sell_price) #take 8 beer
        self.assertEqual(self.member.balance,-0.50)

    def test_giveItem(self):
        with self.assertRaises(ValueError):
            self.bar.giveItem('133713371338',self.item.barcode,0.10) #give a beer, should fail since member is unkown
        trans=self.bar.giveItem(self.member.barcode,self.item.barcode,0.50,10) #add 10 beer
        trans2=self.bar.giveItem(self.member.barcode,self.item.barcode,0.25,10) #add 10 non-existing beers, which should be added as items
        self.assertEqual(self.bar.session.query(model.Item).filter_by(barcode=self.item.barcode).count(),2)
        self.assertEqual(self.item.stock,10)
        self.assertEqual(trans2.item.stock,10)
        self.assertEqual(self.member.balance,7.50)

    def test_takeItem(self):
        with self.assertRaises(ValueError):
            self.bar.takeItem(self.member.barcode,self.item.barcode) #take a beer, should fail since no stock present
        self.bar.giveItem(self.member.barcode,self.item.barcode,0.50,10) #add 10 beer
        with self.assertRaises(ValueError):
            self.bar.takeItem('133713371338',self.item.barcode) #take a beer, should fail since member is unkown
        self.bar.takeItem(self.member.barcode,self.item.barcode) #take a beer
        self.assertEqual(self.item.stock,9)
        self.assertEqual(self.member.balance,4.50)
        self.bar.takeItem(self.member.barcode,self.item.barcode,3) #take 3 beer
        self.assertEqual(self.item.stock,6)
        self.assertEqual(self.member.balance,3.00)
        trans=self.bar.giveItem(self.member.barcode,self.item.barcode,0.25,10) #add 10 cheaper beer
        self.bar.takeItem(self.member.barcode,self.item.barcode,8) #take 8 beer (6 expenise ones, 2 cheap ones)
        self.assertEqual(self.item.stock,0)
        self.assertEqual(trans.item.stock,8)
        self.assertEqual(self.member.balance,2.00)

    def test_payment(self):
        self.bar.giveItem(self.member2.barcode,self.item.barcode,0.50,20) #give 20 beer
        trans1=self.bar.takeItem(self.member.barcode,self.item.barcode,10) #take 10 beer
        self.assertEqual(self.member.balance,-5)
        trans2=self.bar.payAmount(self.member,6.50) #pay 6.50 euro
        self.assertEqual(self.member.balance,1.5)
        self.assertEqual(trans1.archived,True)
        self.assertEqual(trans2.archived,False)
        self.assertEqual(len(self.bar.getTransactions(self.member)),1)
        print(self.member.allTransactions)
        self.assertEqual(len(self.member.allTransactions),3)#three transactions, since the payment transaction was split in 2 transactions (1 to get to 0 and 1 transaction to get a positive balance of 1.50)
        trans3=self.bar.takeItem(self.member.barcode,self.item.barcode,3) #take 3 beer
        self.assertEqual(self.member.balance,0)
        self.assertEqual(trans2.archived,True)
        self.assertEqual(trans3.archived,True)
        self.assertEqual(len(self.member.transactions),0)#everything should be archived. Balance=0
        self.assertEqual(len(self.member.allTransactions),4)
        trans2=self.bar.giveItem(self.member.barcode,self.item.barcode,0.50,13) #add 13 beer
        self.bar.takeItem(self.member.barcode,self.item.barcode,4)#take 4 beer
        self.assertEqual(self.member.balance,4.50)
        self.assertEqual(len(self.member.transactions),1)#we should still have one transaction left, because of positive balance
        self.assertEqual(len(self.member.allTransactions),7)
        self.item.stock=40
        trans1=self.bar.takeItem(self.member.barcode,self.item.barcode,40) #take 10 beer
        self.assertEqual(self.member.balance,-15.50)
        self.bar.payAmount(self.member,10)
        self.assertEqual(self.member.balance,-5.50)
        self.fail("Line 242 in nurdbar.NurdBar.payAmount (line with if followed by break) not tested!")

