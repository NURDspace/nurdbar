from nurdbar.plugins.api import *
pluginregistry['tcpinterfaceplugin'].resetPlugins()
pluginregistry['transportinterfaceplugin'].resetPlugins()
from start import importPlugins
import unittest
import os

class TestPlugins(unittest.TestCase):
    def test_plugins(self):
        importPlugins(os.path.join(os.path.abspath(os.path.dirname(__file__)),'plugins'))
        print(pluginregistry['tcpinterfaceplugin'].getPlugins())
        print(pluginregistry['transportinterfaceplugin'].getPlugins())
        self.assertEqual(len(pluginregistry['tcpinterfaceplugin'].getPlugins()),1)
        self.assertEqual(len(pluginregistry['transportinterfaceplugin'].getPlugins()),1)
        with self.assertRaises(PortTakenException):
            @TCPInterfacePlugin(5000)
            def test(bar,reactor):
                pass
