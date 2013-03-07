from nurdbar.plugins.api import *
@TCPInterfacePlugin(5000)
def testPlugin(bar,reactor):
    pass

@LocalInterfacePlugin
def testPlugin2(bar,reactor):
    pass

