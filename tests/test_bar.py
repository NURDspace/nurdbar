from _basetest import BaseTest
from nurdbar import NurdBar
from decimal import Decimal

class TestModel(BaseTest):

    def setUp(self):
        super(TestModel,self).setUp()
        self.member=self.bar.addMember(133713371337,'SmokeyD')
        self.item=self.bar.addItem(12312893712938,0.50)

    def test_filled_tables(self):
        payment_item=self.bar.getItemByBarcode(1010101010)
        self.assertAlmostEqual(payment_item.price,Decimal(0.01))

    def test_item(self):
        item=self.bar.getItemByBarcode(12312893712938)
        self.assertEqual(item.price,0.50)

    def test_member(self):
        member=self.bar.getMemberByNick('SmokeyD')
        self.assertEqual(member.barcode,133713371337)

    def test_transaction(self):
        self.bar.addTransaction(self.item,self.member,10) #add beer
        self.assertEqual(self.member.balance,5)
        self.assertEqual(self.item.stock,10)
        self.bar.addTransaction(self.item,self.member,-1) #take a beer
        self.assertEqual(self.item.stock,9)
        self.assertEqual(self.member.balance,4.50)
        self.bar.addTransaction(self.item,self.member,-1) #take a beer
        self.assertEqual(self.item.stock,8)
        self.assertEqual(self.member.balance,4)
        self.bar.addTransaction(self.item,self.member,-1) #take a beer
        self.assertEqual(self.item.stock,7)
        self.assertEqual(self.member.balance,3.50)
        self.bar.addTransaction(self.item,self.member,-8) #take 7 beer
        self.assertEqual(self.item.stock,-1)
        self.assertEqual(self.member.balance,-0.50)

    def test_giveItem(self):
        self.bar.giveItem(self.member.barcode,self.item.barcode,10) #add 10 beer
        self.assertEqual(self.item.stock,10)
        self.assertEqual(self.member.balance,5.00)

    def test_takeItem(self):
        self.bar.giveItem(self.member.barcode,self.item.barcode,10) #add 10 beer
        self.bar.takeItem(self.member.barcode,self.item.barcode) #take a beer
        self.assertEqual(self.item.stock,9)
        self.assertEqual(self.member.balance,4.50)
        self.bar.takeItem(self.member.barcode,self.item.barcode,3) #take a beer
        self.assertEqual(self.item.stock,6)
        self.assertEqual(self.member.balance,3.00)

    def test_payment(self):
        self.bar.addTransaction(self.item,self.member,-10) #take 10 beer
        self.assertEqual(self.member.balance,-5)
        self.bar.payAmount(self.member,6.50) #pay 6.50 euro
        self.assertEqual(self.member.balance,1.5)
