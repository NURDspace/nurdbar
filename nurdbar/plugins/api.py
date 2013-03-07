import copy

class PortTakenException(Exception):
    pass

class BasePluginRegistry(object):
    _EMPTY_PLUGIN_CONTAINER=[]
    def __init__(self):
        self.resetPlugins()

    def registerPlugin(self,function):
        raise NotImplementedError('registerPlugin not implemented on %s'%self.__class__.__name__)

    def getPlugins(self):
        raise NotImplementedError('getPlugins not implemented on %s'%self.__class__.__name__)

    def resetPlugins(self):
        self.plugins=copy.deepcopy(self.__class__._EMPTY_PLUGIN_CONTAINER)


class TCPInterfacePluginRegistry(BasePluginRegistry):
    _EMPTY_PLUGIN_CONTAINER={}

    def registerPlugin(self,function,portnum):
        if portnum not in self.plugins.keys():
            self.plugins[portnum]=function
        else:
            raise PortTakenException('Port %s has already been taken by plugin %s'%(portnum,self.plugins[portnum]))

    def getPlugins(self):
        return [(k,v) for k,v in self.plugins.items()]

class TransportInterfacePluginRegistry(BasePluginRegistry):
    _EMPTY_PLUGIN_CONTAINER=[]

    def registerPlugin(self,function):
        self.plugins.append(function)

    def getPlugins(self):
        return self.plugins

pluginregistry={
    'tcpinterfaceplugin':TCPInterfacePluginRegistry(),
    'transportinterfaceplugin':TransportInterfacePluginRegistry()
}

def TCPInterfacePlugin(portnum):
    '''Decorator to register an TCPInterfacePlugin.
    Methods using this plugin need to return a twisted.internet.protocol.Factory instance, which handles a corresponding twisted.internet.protocol.Protocol class.
    The method should accept an argument for a nurdbar.NurdBar instance, providing access to the nurdbar API.
    See http://twistedmatrix.com/documents/12.2.0/core/howto/servers.html#auto6 for more info

    :param portnum: the portnumber to listen on for connections
    :type portnum: int
    '''
    def superwrapped(function):
        pluginregistry['tcpinterfaceplugin'].registerPlugin(function,portnum)
        def wrapped(bar):
            return function(bar)
        return wrapped
    return superwrapped


def TransportInterfacePlugin(function):
    '''Decorator for TransportInterfacePlugin. Transport interfaces get their input through local sockets/files/ports. An example is the twisted.internet.serialport.SerialPort
    transport which monitors a local serial port for information. Methods using this decorator should instantiate their own transport (using the supplied reactor, and don't need to
    return anything. They method should accept an argument for a nurdbar.NurdBar instance, providing access to the nurdbar API, and a reactor argument, needed for the transport.
    '''
    pluginregistry['transportinterfaceplugin'].registerPlugin(function)
    def wrapped(bar,reactor):
        return function(bar,reactor)
    return wrapped
