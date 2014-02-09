from nurdbar import events
from _basetest import BaseTest
import unittest
import os

def _scannedBarcode2(event):
    barcode=event.attributes['barcode']
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

    def test_events_fire_modified(self):
        events.BarcodeScannedEvent.register(self._scannedBarcode3)
        events.BarcodeScannedEvent.register(self._scannedBarcode4)
        barcode=events.BarcodeScannedEvent.fire('1337133713371337')
        self.assertEqual(barcode,'1337133713371338')

    def _scannedBarcode(self,event):
        barcode=event.attributes['barcode']
        self.assertEqual(barcode,'1337133713371337')
        self.barcode=barcode
        print(barcode)

    def _scannedBarcode3(self,event):
        barcode=event.attributes['barcode']
        self.barcode=barcode
        event.attributes['barcode']='1337133713371338'

    def _scannedBarcode4(self,event):
        barcode=event.attributes['barcode']
        self.assertEqual(barcode,'1337133713371338')
        self.barcode=barcode

    def tearDown(self):
        if self._scannedBarcode in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(self._scannedBarcode)
        if _scannedBarcode2 in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(_scannedBarcode2)
        if self._scannedBarcode3 in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(self._scannedBarcode3)
        if self._scannedBarcode4 in events.BarcodeScannedEvent.handlers:
            events.BarcodeScannedEvent.unregister(self._scannedBarcode4)

