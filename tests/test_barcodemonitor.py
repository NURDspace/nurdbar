from serialEmulator import SerialEmulator
from _basetest import BaseTest
from nurdbar import NurdBar
from twisted.trial import unittest
from nurdbar.barcodemonitor import BarcodeProtocol
from twisted.test import proto_helpers

class TestBarcodeMonitor(unittest.TestCase,BaseTest):

    def setUp(self):
        super(TestBarcodeMonitor,self).setUp()
        self.member=self.bar.addMember(133713371337,'SmokeyD')
        self.item=self.bar.addItem(12312893712938,0.50)
        self.proto = BarcodeProtocol(self.bar)
        self.tr = proto_helpers.StringTransport()
        self.proto.makeConnection(self.tr)

    def test_receiveBarcode(self):
        self.proto.dataReceived('133713371337\r\n')
        self.proto.dataReceived('12312893712938\r\n')
        self.assertEqual(self.member.balance,-0.50)
        self.assertEqual(self.item.stock,-1)

    def tearDown(self):
        super(TestBarcodeMonitor,self).tearDown()
