from nurdbar.plugins.api import *
@TCPInterfacePlugin(5000)
def testPlugin(bar):
    pass

@TransportInterfacePlugin
def testPlugin2(bar,reactor):
    pass

