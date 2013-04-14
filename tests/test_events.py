from nurdbar import events
from _basetest import BaseTest
import unittest
import os

def _scannedBarcode2(barcode):
    print(barcode)

class TestEvents(BaseTest):

    def test_events_register(self):
        events.BarcodeScannedEvent.register(self._scannedBarcode)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),1)
        events.BarcodeScannedEvent.register(_scannedBarcode2)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),2)

    def test_events_unregister(self):
        print(events.BarcodeScannedEvent.handlers)
        events.BarcodeScannedEvent.register(self._scannedBarcode)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),1)
        events.BarcodeScannedEvent.register(_scannedBarcode2)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),2)
        events.BarcodeScannedEvent.unregister(self._scannedBarcode)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),1)
        events.BarcodeScannedEvent.unregister(_scannedBarcode2)
        self.assertEqual(len(events.BarcodeScannedEvent.handlers),0)

    def test_events_fire(self):
        events.BarcodeScannedEvent.register(self._scannedBarcode)
        events.BarcodeScannedEvent.fire('1337133713371337')
        self.assertEqual(self.barcode,'1337133713371337')

    def _scannedBarcode(self,barcode):
        self.assertEqual(barcode,'1337133713371337')
        self.barcode=barcode
        print(barcode)

    def tearDown(self):
        if self._scannedBarcode in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(self._scannedBarcode)
        if _scannedBarcode2 in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(_scannedBarcode2)

