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
bar.addItem(12312893712938,0.50)
bar.addMember(133713371337,'SmokeyD')
item=bar.getItemByBarcode(12312893712938)
member=bar.getMemberByNick('SmokeyD')
bar.addTransaction(item,member,10)

bar.drop_tables()
