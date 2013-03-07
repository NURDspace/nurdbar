Nurdbar
=======

Bar application with barcode scanning functionality to scan.

It aims to provide several frontends to track sales of bar items. It uses Twisted (http://twistedmatrix.com/) to provide the frontends.
Right now it only includes one frontend, which is a serial port Barcode scanner.

PluginSystem
------------

The Nurdbar application uses plugins to register interfaces to the bar. This way, multiple interfaces can be used for the same bar application.
By default a Telnet interface is available, allowing the manipulation of the bar through telnet, and a barcode monitor interface, which monitors
a serial port on the local machine for scanned barcodes.

To register a new plugin, write your code, put it in the plugindir as configured in the config file. To register the plugin, all you need to do
is decorate a method in your code with one of the following decorators from nurdbar.plugins.api:

@TCPInterfacePlugin(portnumber): This decorator registers a plugin which needs to listen on a TCP port. The with the portnumber argument you specify which portnumber
you want the plugin to listen on. Your method, should return an instance of twisted.internet.protocol.Factory.
Your method should accept two arguments: bar and reactor. Bar is an instance of nurdbar.NurdBar() which you can use to access the NurdBar api from your plugin. 
Reactor you probably won't need to use.

@LocalInterfacePlugin: THis decorator can be used to create interfaces not connected to a network, but for instance with a local twisted transport on a serial interface.
You method needs to instantiate the plugin itself, for which it probably uses the reactor argument which your method receives together with a NurdBar instance in the bar argument.


UnitTesting
-----------
From the root dir, run "trial tests" or "nosetests" to run all unittests.

Documentation
-------------
Copy the nurdbar_sample.cfg to your configuration file (nurdbar.cfg for example). Adjust the serial port and db uri configuration parameters. 
Any database which can be used with sqlalchemy can be used, but the database specific python library needs to be installed.

Run "start.py &lt;configfile&gt;" to start the daemon with all interfaceplugins. By default the Telnet interface and Barcode interface are available,
which monitor telnet commands and a serial port for scanned barcodes respectively and act upon them.
See tests/example.py for some example code. To run the example.py as-is, you need socat, which can tie virtual serial ports together, 
so you can write data to one, which is received by another virtual serial port.
