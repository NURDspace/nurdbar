import time, re, traceback
from twisted.internet.protocol import ClientFactory
from twisted.words.protocols.irc import IRCClient

class IRC(IRCClient):

    """ A protocol object for IRC """

    def __init__(self, screenObj, nickname,channel,debugmode=False):
        # screenObj should be 'stdscr' or a curses window/pad object
        self.screenObj = screenObj
        # for testing (hacky way around initial bad design for this example) :)
        self.screenObj.irc = self
        self.debugmode = debugmode
        self.nickname = nickname
        self.originalnick = nickname
        self.realname = ' '
        self.channel = channel
        self.lineRate = 1

    def lineReceived(self, line):
        """ When receiving a line, filter and add it to the output buffer """
        if self.debugmode:
            self.screenObj.addLine(line, 'bottom')
        mmatch = re.search('\A[:]?(.*?) (.*?) :(.+)\Z',line)
        newline = time.strftime('<%H:%M>')
        if mmatch:
            user = mmatch.group(1).split('!',1)
            handle = user[0]
            if len(user)>1: ip = user[1]
            else: ip = ''
            type = mmatch.group(2)
            msg = mmatch.group(3)
        else: 
            handle = ''
            ip = ''
            msg = ''
            type = line
        if 'PING' in type:
            self.sendLine('PONG :'+msg)
        elif 'PRIVMSG' in type:
            if self.channel in type:
                if 'ACTION' in msg:
                    msg = msg[7:-1] #^AACTIONmsg^A
                    newline = newline + handle+''+msg
                else:
                    newline = newline + '<'+handle+'> ' +msg
            else:
                newline = newline + '<'+handle+' PM> ' +msg
        elif 'NICK' in type:
            newline = newline + handle+' is now known as ' +msg
        elif 'TOPIC' in type:
            newline = newline + 'Topic: '+msg
        elif 'PART' in type:
            newline = newline + handle+' leaves the channel.'
        elif 'JOIN' in type:
            newline = newline + handle+' joins the channel.'
        elif msg.strip() is not '':
            newline = newline + handle+': '+msg
        self.screenObj.addLine(newline, 'bottom')

    def connectionMade(self):
        IRCClient.connectionMade(self)
        self.screenObj.addLine("* CONNECTED")
        self.sendLine('JOIN '+self.channel)

    def clientConnectionLost(self, connection, reason):
        self.screenObj.addLine("* DISCONNECTED")
        pass


class IRCFactory(ClientFactory):

    """
    Factory used for creating IRC protocol objects 
    """

    protocol = IRC

    def __init__(self, screenObj,nickname,channel,debug):
        self.irc = self.protocol(screenObj,nickname,channel,debug)

    def buildProtocol(self, addr=None):
        return self.irc

    def clientConnectionLost(self, conn, reason):
        pass
