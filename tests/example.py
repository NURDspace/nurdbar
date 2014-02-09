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
#bar.addItem('12310038',0.50)
bar.addMember('USER4432','SmokeyD')
bar.sellItem('USER4432','12310038',10)
bar.sellItem('USER4432','12310038',15)
bar.sellItem('USER4432','12310038',20)
bar.sellItem('USER4432','12310038',25)
bar.sellItem('USER4432','12310038',25)
bar.buyItem('USER4432','12310038')
#bar.buyItem('USER4432','12310038',5)
item=bar.getItemByBarcode('12310038')
member=bar.getMemberByBarcode('USER4432')
print("item.stock=%s. Correct? %s"%(item.stock,item.stock==3)) #+10-1-5=4
print("member.balance=%s Correct? %s"%(member.balance,member.balance==85.00)) #(10-1-5)*0.50=2.00
bar.payAmount(member,8.00)
print("member,balance=%s Correct? %s"%(member.balance,member.balance==93.00))

#start nurdbar/barcodemonitor.py <configfile>, normally done in the shell.
#monitor_proc=subprocess.Popen('python nurdbar/barcodemonitor.py %s'%configfile,shell=True)

#start a fake serial device and write some barcodes to the barcode monitor.
#em=SerialEmulator(configfile)
#em.writeLine('USER4432\r\n')
#em.writeLine('12312893712938\r\n')

#time.sleep(1) #give the serial monitor to commit stuff to the db

#re-fetch the item and member from the database
bar.session.commit()
bar.session.flush()
member=bar.getMemberByBarcode('USER4432')
item=bar.getItemByBarcode('12312893712938')

#check new stock and balance
print("item.stock=%s Correct? %s"%(item.stock,item.stock==3)) #4-1=3
print("member.balance=%s Correct? %s"%(member.balance,member.balance==12.00)) #12.50-0.50=12.00

#stop the barcode monitor and drop the tables
#monitor_proc.kill()
