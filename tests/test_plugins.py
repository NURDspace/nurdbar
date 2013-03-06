from nurdbar.plugins.api import *
pluginregistry['tcpinterfaceplugin'].plugins={}
pluginregistry['localinterfaceplugin'].plugins=[]
import unittest

@TCPInterfacePlugin(5000)
def testPlugin(bar,reactor):
    pass

@LocalInterfacePlugin
def testPlugin2(bar,reactor):
    pass

class TestPlugins(unittest.TestCase):
    def test_plugins(self):
        self.assertEqual(len(pluginregistry['tcpinterfaceplugin'].getPlugins()),1)
        self.assertEqual(len(pluginregistry['localinterfaceplugin'].getPlugins()),1)
