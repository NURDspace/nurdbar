.. NurdBar documentation master file, created by
   sphinx-quickstart on Thu Mar  7 19:22:09 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NurdBar's documentation!
===================================

Getting started
---------------
Copy the nurdbar_sample.cfg to your configuration file (nurdbar.cfg for example). Adjust the serial port and db uri configuration parameters.
Any database which can be used with sqlalchemy can be used, but the database specific python library needs to be installed.

Run "start.py <configfile>" to start the daemon with all interfaceplugins. By default the Telnet interface and Barcode interface are available,
which monitor telnet commands and a serial port for scanned barcodes respectively and act upon them.
See tests/example.py for some example code. To run the example.py as-is, you need socat, which can tie virtual serial ports together,
so you can write data to one, which is received by another virtual serial port.

NurdBar
-------
.. automodule:: nurdbar
    :members:

.. autoclass:: NurdBar
    :members:

nurdbar.plugins.api
-------------------
.. automodule:: nurdbar.plugins.api
    :members:

nurdbar.model
-------------------
.. automodule:: nurdbar.model

.. autoclass:: Member
    :members:

.. autoclass:: Item
    :members:

.. autoclass:: Transaction
    :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

