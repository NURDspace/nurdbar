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

class LocalInterfacePluginRegistry(BasePluginRegistry):
    _EMPTY_PLUGIN_CONTAINER=[]

    def registerPlugin(self,function):
        self.plugins.append(function)

    def getPlugins(self):
        return self.plugins

pluginregistry={
    'tcpinterfaceplugin':TCPInterfacePluginRegistry(),
    'localinterfaceplugin':LocalInterfacePluginRegistry()
}

def TCPInterfacePlugin(portnum):
    '''Decorator to register an TCPInterfacePlugin.
    @param portnum the portnumber to listen on for connections
    '''
    def superwrapped(function):
        pluginregistry['tcpinterfaceplugin'].registerPlugin(function,portnum)
        def wrapped(bar,reactor):
            return function(bar,reactor)
        return wrapped
    return superwrapped


def LocalInterfacePlugin(function):
    '''Decorator for LocalInterfacePlugin. They don't listen for internet connections but get their data on the local machine,
    like a serialPort or other places
    '''
    pluginregistry['localinterfaceplugin'].registerPlugin(function)
    def wrapped(bar,reactor):
        return function(bar,reactor)
    return wrapped
