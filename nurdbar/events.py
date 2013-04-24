class FiredEvent(object):
    def __init__(self,event):
        self.event=event
        self.attributes={}

class _BaseEvent(object):

    def __init__(self):
        self.handlers=[]

    def register(self,func):
        self.handlers.append(func)

    def fire(self,**kwargs):
        event=FiredEvent(self)
        event.attributes.update(kwargs)
        for handler in self.handlers:
            handler(event)
        if len(event.attributes.keys())==1:
            #if there is only one item in the event.attributes dict, return it directly.
            return event.attributes[event.attributes.keys()[0]]
        #return the event.attributes dict
        return event.attributes

    def clearHandlers(self):
        for h in self.handlers:
            self.unregister(h)

    def unregister(self,func):
        self.handlers.remove(func)

class _MemberBarcodeScannedEvent(_BaseEvent):
    def fire(self,member):
        return super(_MemberBarcodeScannedEvent,self).fire(member=member)

class _MemberNotFoundEvent(_BaseEvent):
    def fire(self,barcode):
        return super(_MemberNotFoundEvent,self).fire(barcode=barcode)

class _BarcodeScannedEvent(_BaseEvent):
    def fire(self,barcode):
        return super(_BarcodeScannedEvent,self).fire(barcode=barcode)

class _OutOfStockEvent(_BaseEvent):
    def fire(self,item):
        return super(_OutOfStockEvent,self).fire(item=item)

BarcodeScannedEvent=_BarcodeScannedEvent()
OutOfStockEvent=_OutOfStockEvent()
MemberBarcodeScannedEvent=_MemberBarcodeScannedEvent()
MemberNotFoundEvent=_MemberNotFoundEvent()

__all__=[BarcodeScannedEvent,OutOfStockEvent,MemberBarcodeScannedEvent,MemberNotFoundEvent]
