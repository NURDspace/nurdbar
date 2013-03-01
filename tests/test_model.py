from _basetest import BaseTest
from nurdbar import NurdBar

class TestModel(BaseTest):

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
        self.bar.addTransaction(item,member,10)
        self.assertEqual(member.balance,5)
        self.assertEqual(item.stock,10)
