#!/usr/bin/env python
import sys
from xmlrpclib import ServerProxy, Error
from BeautifulSoup import BeautifulSoup
import urllib2
from string import digits
import logging
logging.getLogger(__name__)

GS_CC = {'622': 'EGY','621': 'SYR','627': 'KWT','626': 'IRN','625': 'JOR','624': 'LBY','955': 'MYS','629': 'ARE','628': 'SAU','880': 'KOR','64': 'FIN','69': 'CHN','600': 'ZAF','977': 'ISSN','790': 'BRA','885': 'THA','745': 'PAN','779': 'ARG','858': 'SVK','859': 'CZE','979': 'ISBN','978': 'ISBN','0': 'USA','890': 'IND','569': 'ISL','750': 'MEX','755': 'CAN','754': 'CAN','560': 'PRT','759': 'VEN','99': 'Voucher','91': 'AUT','90': 'AUT','93': 'AUS','94': 'NZL','84': 'ESP','777': 'BOL','868': 'TUR','54': 'BEL','57': 'DNK','865': 'MNG','50': 'GBR','867': 'PRK','535': 'MLT','531': 'MKD','860': 'SRB','539': 'IRL','729': 'ISR','740': 'GTM','590': 'POL','742': 'HND','743': 'NIC','601': 'ZAF','594': 'ROU','746': 'DOM','599': 'HUN','980': 'Currency Coupon','888': 'SGP','609': 'MUS','608': 'BHR','789': 'BRA','893': 'VNM','82': 'ITA','83': 'ITA','80': 'ITA','81': 'ITA','87': 'NLD','70': 'NOR','958': 'MAC','49': 'JPN','46': 'RUS','44': 'DEU','45': 'JPN','42': 'DEU','43': 'DEU','40': 'DEU','41': 'DEU','1': 'USA','520': 'GRC','521': 'GRC','899': 'IDN','528': 'LBN','529': 'CYP','744': 'CRI','775': 'PER','618': 'CIV','619': 'TUN','771': 'COL','770': 'COL','773': 'URY','850': 'CUB','613': 'DZA','611': 'MAR','616': 'KEN','380': 'BGR','76': 'CHE','383': 'SVN','73': 'SWE','385': 'HRV','489': 'HKG','387': 'BIH','487': 'KAZ','486': 'GEO','485': 'ARM','484': 'MDA','482': 'UKR','481': 'BLR','480': 'PHL','784': 'PRY','869': 'TUR','786': 'ECU','780': 'CHL','33': 'FRA','32': 'FRA','31': 'FRA','30': 'FRA','37': 'FRA','36': 'FRA','35': 'FRA','34': 'FRA','470': 'KGZ','471': 'TWN','476': 'AZE','477': 'LTU','474': 'EST','475': 'LVA','478': 'UZB','479': 'LKA','741': 'SLV'}

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
        if len(barcode) in [8,13] and all(x in digits for x in barcode):#We have an EAN-8 or EAN-13
            for p in self.providers:
                if p.lookupBarcode(barcode) not in ('',None):
                    results.append(p.lookupBarcode(barcode))
            if len(results)>0:
                return results[0]
            else:
                for code in GS_CC:
                    if barcode.startswith(code):
                        return (None,None,GS_CC[code])
        return (None,None,None)


if __name__=='__main__':
    print(BarcodeLookup([UPCDatabaseProvider(),StreepjescodescannerProvider()]).lookupBarcode(sys.argv[1]))
    #print(BarcodeLookup([StreepjescodescannerProvider(),UPCDatabaseProvider()]).lookupBarcode(sys.argv[1]))
