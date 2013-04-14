
class _BaseEvent(object):

    def __init__(self):
        self.handlers=[]

    def register(self,func):
        self.handlers.append(func)

    def fire(self,**kwargs):
        for handler in self.handlers:
            handler(**kwargs)

    def clearHandlers(self):
        for h in self.handlers:
            self.unregister(h)

    def unregister(self,func):
        self.handlers.remove(func)

class _BarcodeScannedEvent(_BaseEvent):
    def fire(self,barcode):
        super(_BarcodeScannedEvent,self).fire(barcode=barcode)

class _OutOfStockEvent(_BaseEvent):
    def fire(self,item):
        super(_OutOfStockEvent,self).fire(item=item)

BarcodeScannedEvent=_BarcodeScannedEvent()
OutOfStockEvent=_OutOfStockEvent()

__all__=[BarcodeScannedEvent,OutOfStockEvent]
