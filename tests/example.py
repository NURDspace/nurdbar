#set the working dir and pyton path to the parent directory, so we can find the config file and nurdbar module.
import sys
import os
import subprocess
import time
parent_path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'..')
sys.path.append(parent_path)
os.chdir(parent_path)

#the actual example
configfile = 'config.cfg'
from nurdbar import NurdBar
#from serialEmulator import SerialEmulator
bar=NurdBar(configfile)
bar.drop_tables()
bar.create_tables()
bar.fill_tables()

bar.addMember('USR2232','SmokeyD')
print (bar.getMemberByBarcode('USR2232').balance)
bar.sellItem('USR2232','12310038',10,amount=2)
bar.addBarcodeDesc('12310038','A test sandwich','1x','germany')
bar.sellItem('USR2232','12310038',12,amount=3)
bar.sellItem('USR2232','23111038',20,amount=5)
assert bar.getMemberByBarcode('USR2232').balance == 156
bar.buyItem('USR2232','12310038')
print (bar.getMemberByBarcode('USR2232').balance)
bar.buyItem('USR2232','12310038')
print (bar.getMemberByBarcode('USR2232').balance)
bar.buyItem('USR2232','12310038')
#bar.buyItem('USR2232','12310038',5)
item=bar.getAvailableItemByBarcode('12310038')
print (bar.getMemberByBarcode('USR2232').balance)
member=bar.getMemberByBarcode('USR2232')
bar.payAmount(member,40.00)
member=bar.getMemberByBarcode('USR2232')
print("item.stock=%s. Correct? %s"%(item.stock,item.stock==1)) #+3-1=1
print("item.totalstock=%s. Correct? %s"%(bar.getItemTotalStock(item),bar.getItemTotalStock(item)==2)) #+5-3=2
print("member.balance=%s Correct? %s"%(member.balance,member.balance==164.00)) #2*10+3*12+5*20+40-10-10-12=64.00
print (member.allTransactions)
#print("member,balance=%s Correct? %s"%(member.balance,member.balance==93.00))

#start nurdbar/barcodemonitor.py <configfile>, normally done in the shell.
#monitor_proc=subprocess.Popen('python nurdbar/barcodemonitor.py %s'%configfile,shell=True)

#start a fake serial device and write some barcodes to the barcode monitor.
#em=SerialEmulator(configfile)
#em.writeLine('USR2232\r\n')
#em.writeLine('12312893712938\r\n')

#time.sleep(1) #give the serial monitor to commit stuff to the db

#re-fetch the item and member from the database
#bar.session.commit()
#bar.session.flush()
#member=bar.getMemberByBarcode('USR2232')
#item=bar.getItemByBarcode('12310038')

#check new stock and balance
#print("item.stock=%s Correct? %s"%(item.stock,item.stock==3)) #4-1=3
#print("member.balance=%s Correct? %s"%(member.balance,member.balance==12.00)) #12.50-0.50=12.00

#stop the barcode monitor and drop the tables
#monitor_proc.kill()
