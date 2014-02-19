#!/usr/bin/env python
import sys
from xmlrpclib import ServerProxy, Error
from BeautifulSoup import BeautifulSoup
import urllib2
import logging
logging.getLogger(__name__)

class BarcodeLookupProvider(object):
    def lookupBarcode(self,barcode):
        raise NotImplementedError("This method needs to be implemented, but is not.")

class StreepjescodescannerProvider(BarcodeLookupProvider):
    def lookupBarcode(self,barcode):
        soup=BeautifulSoup(urllib2.urlopen('http://www.streepjescodescanner.nl/?search=%s'%barcode).read())
#        logging.warn(soup.table)
        products=soup.table.findAll('td')[2].a.contents[0]
        return products

class UPCDatabaseProvider(BarcodeLookupProvider):

    def __init__(self):
        self.server = ServerProxy('http://www.upcdatabase.com/xmlrpc')
        self.rpc_key = 'c4a7f4f0bd0a0f2ea4df549d4f8bcbd3e0229b08'

    def lookupBarcode(self,barcode):
        if len(barcode)<13:
            barcode = '0'*(13-len(barcode)) + barcode
        params = { 'rpc_key': self.rpc_key, 'ean': barcode }
        logging.warn(params)
        results = self.server.lookup(params)
        logging.warn(results)
        try:
            if results['found']:
                return (results['description'],results['size'],results['issuerCountry'])
            return None
        except:
            logging.warn('Scan resulted in error.')
            return None

class BarcodeLookup(object):

    def __init__(self,providers=[]):
        providers.append(UPCDatabaseProvider())
#        providers.append(StreepjescodescannerProvider())
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
