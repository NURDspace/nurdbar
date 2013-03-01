from _basetest import BaseTest
from nurdbar import NurdBar
from decimal import Decimal

class TestModel(BaseTest):

    def test_filled_tables(self):
        payment_item=self.bar.getItemByBarcode(1010101010)
        self.assertAlmostEqual(payment_item.price,Decimal(0.01))

    def test_item(self):
        self.bar.addItem(12312893712938,0.50)
        item=self.bar.getItemByBarcode(12312893712938)
        self.assertEqual(item.price,0.50)

    def test_member(self):
        self.bar.addMember(133713371337,'SmokeyD')
        member=self.bar.getMemberByNick('SmokeyD')
        self.assertEqual(member.barcode,133713371337)

    def test_transaction(self):
        member=self.bar.addMember(133713371337,'SmokeyD')
        item=self.bar.addItem(12312893712938,0.50)
        self.bar.addTransaction(item,member,10) #add beer
        self.assertEqual(member.balance,5)
        self.assertEqual(item.stock,10)
        self.bar.addTransaction(item,member,-1) #take a beer
        self.assertEqual(item.stock,9)
        self.assertEqual(member.balance,4.50)
        self.bar.addTransaction(item,member,-1) #take a beer
        self.assertEqual(item.stock,8)
        self.assertEqual(member.balance,4)
        self.bar.addTransaction(item,member,-1) #take a beer
        self.assertEqual(item.stock,7)
        self.assertEqual(member.balance,3.50)
        self.bar.addTransaction(item,member,-8) #take 7 beer
        self.assertEqual(item.stock,-1)
        self.assertEqual(member.balance,-0.50)
        payment_item=self.bar.getItemByBarcode(1010101010)
        self.bar.addTransaction(payment_item,member,150) #pay 1.50 euro
        self.assertEqual(member.balance,1)
