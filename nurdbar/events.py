
class _BaseEvent(object):

    def __init__(self):
        self.handlers=[]

    def register(self,func):
        self.handlers.append(func)

    def fire(self,**kwargs):
        for handler in self.handlers:
            handler(**kwargs)

    def unregister(self,func):
        self.handlers.remove(func)

class _BarcodeScannedEvent(_BaseEvent):
    def fire(self,barcode):
        super(_BarcodeScannedEvent,self).fire(barcode=barcode)

BarcodeScannedEvent=_BarcodeScannedEvent()

__all__=[BarcodeScannedEvent]
