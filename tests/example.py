from nurdbar import NurdBar
bar=NurdBar()
bar.metadata.create_all()
bar.addItem(12312893712938,0.50)
bar.addMember('SmokeyD',133713371337)
item=bar.getItemByBarcode(12312893712938)
member=bar.getMemberByNick('SmokeyD')
bar.addTransaction(item,member,10)
