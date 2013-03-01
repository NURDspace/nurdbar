#set the working dir and pyton path to the parent directory, so we can find the config file and nurdbar module.
import sys
import os
parent_path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'..')
sys.path.append(parent_path)
os.chdir(parent_path)

#the actual example
from nurdbar import NurdBar
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
print(item.stock) #+10-1-5=4
print(member.balance) #(10-1-5)*0.50=2.00
bar.payAmount(member,10.50)
print(member.balance) #2.00+10.50=12.50

bar.drop_tables()
