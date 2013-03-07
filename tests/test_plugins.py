from nurdbar.plugins.api import *
pluginregistry['tcpinterfaceplugin'].resetPlugins()
pluginregistry['localinterfaceplugin'].resetPlugins()
from start import importPlugins
import unittest
import os

class TestPlugins(unittest.TestCase):
    def test_plugins(self):
        importPlugins(os.path.join(os.path.abspath(os.path.dirname(__file__)),'plugins'))
        print(pluginregistry['tcpinterfaceplugin'].getPlugins())
        print(pluginregistry['localinterfaceplugin'].getPlugins())
        self.assertEqual(len(pluginregistry['tcpinterfaceplugin'].getPlugins()),1)
        self.assertEqual(len(pluginregistry['localinterfaceplugin'].getPlugins()),1)
        with self.assertRaises(PortTakenException):
            @TCPInterfacePlugin(5000)
            def test(bar,reactor):
                pass
        self.fail("Check how transports are started from the reactor for the LocalInterfacePlugin and do something with the return value")
