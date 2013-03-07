from twisted.internet import protocol
from twisted.protocols import basic
import logging
import traceback
from nurdbar.plugins.api import *

log=logging.getLogger(__name__)

class TelnetProtocol(basic.LineReceiver):
    def __init__(self,bar):
        self.commands={
            'help':(self.help,'help [<command>]:    get help on NurdBar. The optional <command> arguments will give you the help on a specific command.')
        }
        self.bar=bar

    def help(self,command=None):
        helpmessage="""
NurdBar telnet interface.

This interface allows the manipulation of Nurdbar through telnet.
Enter commands, if applicable followed by a space separated list of arguments. Valid commands are:

%s
"""
        allCommandHelp="\r\n".join([c[1] for c in self.commands.values()])
        if command and command in self.commands.keys():
            helpmessage="%s\r\n"%self.commands[command][1]
        elif command and command not in self.commands.keys():
            helpmessage="Unkown command %s.\r\n\r\n%s"%(command,helpmessage%allCommandHelp)
        else:
            helpmessage=helpmessage%allCommandHelp
        self.transport.write(helpmessage)

    def lineReceived(self,command):
        command=command.strip()
        log.debug('received %s'%command)
        if command=='':
            self.transport.write('Please enter a valid command. Type help to get the help screen.\r\n')
            return
        args=command.split(' ')
        command=args.pop(0)
        func=self.commands.get(command)
        if func==None:
            errormsg='Unkown command %s.'%command
            log.error(errormsg)
            self.transport.write('%s\n%s'%(errormsg,'\nType help to get the help screen.\r\n'))
            return
        func=func[0]
        try:
            if args:
                func(*args)
            else:
                func()
        except Exception:
            errormsg='An error occured when executing command %s with arguments %s.'%(command,args)
            log.error("%s\n%s"%(errormsg,traceback.format_exc()))
            self.transport.write("%s\n%s"%(errormsg,'Type help for more info. See log for details on the error.\r\n'))

class TelnetFactory(protocol.Factory):

    def __init__(self,bar):
        self.bar = bar

    def buildProtocol(self,addr):
        return TelnetProtocol(self.bar)

@TCPInterfacePlugin(1079)
def getFactory(bar):
    log.info('Starting telnet protocol')
    return TelnetFactory(bar)
