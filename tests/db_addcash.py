#set the working dir and pyton path to the parent directory, so we can find the config file and nurdbar module.
import sys
import os
import subprocess
import time
parent_path=os.path.join(os.path.abspath(os.path.dirname(__file__)),'..')
sys.path.append(parent_path)
os.chdir(parent_path)

configfile = 'config.cfg'
from nurdbar import NurdBar

bar=NurdBar(configfile)
bar.addBarcodeDesc('CASH','Cash')
