#!/usr/bin/env python
import sys
from xmlrpclib import ServerProxy, Error
from BeautifulSoup import BeautifulSoup
import urllib2

class BarcodeLookupProvider(object):
    def lookupBarcode(self,barcode):
        raise NotImplementedError("This method needs to be implemented, but is not.")

class StreepjescodescannerProvider(BarcodeLookupProvider):
    def lookupBarcode(self,barcode):
        soup=BeautifulSoup(urllib2.urlopen('http://www.streepjescodescanner.nl/?search=%s'%barcode).read())
        products=soup.table.findAll('td')[2].a.contents[0]
        return products

class UPCDatabaseProvider(BarcodeLookupProvider):

    def __init__(self):
        self.server = ServerProxy('http://www.upcdatabase.com/xmlrpc')
        self.rpc_key = 'c4a7f4f0bd0a0f2ea4df549d4f8bcbd3e0229b08'

    def lookupBarcode(self,barcode):
        params = { 'rpc_key': self.rpc_key, 'ean': barcode }
        results = self.server.lookup(params)
        if results['found']:
            return results['description']
        return None

class BarcodeLookup(object):

    def __init__(self,providers):
        for p in providers:
            if not isinstance(p,BarcodeLookupProvider):
                raise ValueError('%s is doest not inherit from BarcodeLookupProvider. Please supply a list of BarcodeLookupProviders as providers argument to BarcodeLookup'%p)
        self.providers=providers

    def lookupBarcode(self,barcode):
        results=[]
        for p in self.providers:
            if p.lookupBarcode(barcode) not in ('',None):
                results.append(p.lookupBarcode(barcode))
        if len(results)>0:
            return results[0]
        else:
            return ''


if __name__=='__main__':
    print(BarcodeLookup([UPCDatabaseProvider(),StreepjescodescannerProvider()]).lookupBarcode(sys.argv[1]))
    #print(BarcodeLookup([StreepjescodescannerProvider(),UPCDatabaseProvider()]).lookupBarcode(sys.argv[1]))
