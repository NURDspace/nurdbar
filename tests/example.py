#set the working dir and pyton path to the parent directory, so we can find the config file and nurdbar module.
import sys
import os
import subprocess
import time
parent_path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'..')
sys.path.append(parent_path)
os.chdir(parent_path)

#the actual example
from nurdbar import NurdBar
from serialEmulator import SerialEmulator
bar=NurdBar('test.cfg')
bar.create_tables()
bar.fill_tables()
bar.addItem(12312893712938,0.50)
bar.addMember(133713371337,'SmokeyD')
bar.giveItem(133713371337,12312893712938,10)
bar.takeItem(133713371337,12312893712938)
bar.takeItem(133713371337,12312893712938,5)
item=bar.getItemByBarcode(12312893712938)
member=bar.getMemberByBarcode(133713371337)
print("item.stock=%s. Correct? %s"%(item.stock,item.stock==4)) #+10-1-5=4
print("member.balance=%s Correct? %s"%(member.balance,member.balance==2.00)) #(10-1-5)*0.50=2.00
bar.payAmount(member,10.50)
print("member,balance=%s Correct? %s"%(member.balance,member.balance==12.50))

configfile = 'test.cfg'
#start nurdbar/barcodemonitor.py <configfile>, normally done in the shell.
monitor_proc=subprocess.Popen('python nurdbar/barcodemonitor.py %s'%configfile,shell=True)

#start a fake serial device and write some barcodes to the barcode monitor.
em=SerialEmulator(configfile)
em.writeLine('133713371337\r\n')
em.writeLine('12312893712938\r\n')

time.sleep(1) #give the serial monitor to commit stuff to the db

#re-fetch the item and member from the database
bar.session.commit()
bar.session.flush()
member=bar.getMemberByBarcode(133713371337)
item=bar.getItemByBarcode(12312893712938)

#check new stock and balance
print("item.stock=%s Correct? %s"%(item.stock,item.stock==3)) #4-1=3
print("member.balance=%s Correct? %s"%(member.balance,member.balance==12.00)) #12.50-0.50=12.00

#stop the barcode monitor and drop the tables
monitor_proc.kill()
bar.drop_tables()
