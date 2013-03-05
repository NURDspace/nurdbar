nurdbar
=======

Bar application with barcode scanning functionality to scan.

It aims to provide several frontends to track sales of bar items. It uses Twisted (http://twistedmatrix.com/) to provide the frontends.
Right now it only includes one frontend, which is a serial port Barcode scanner.

UnitTesting
-----------
From the root dir, run "trial tests" or "nosetests" to run all unittests.

Documentation
-------------
Copy the nurdbar_sample.cfg to your configuration file (nurdbar.cfg for example). Adjust the serial port and db uri configuration parameters. 
Any database which can be used with sqlalchemy can be used, but the database specific python library needs to be installed.

Run "nurdbar/barcodemonitor.py <configfile>" to start the BarcodeMonitor, which monitors a serial port for scanned barcodes and acts upon them.
See tests/example.py for some example code. To run the example.py as-is, you need socat, which can tie virtual serial ports together, so you can write data to one, which is received by another virtual serial port.
