import curses, time, traceback, sys, re
import curses.wrapper

from twisted.python import log

class CursesStdIO:
    """fake fd to be registered as a reader with the twisted reactor.
       Curses classes needing input should extend this"""
    def fileno(self):
        """ We want to select on FD 0 """
        return 0
    def doRead(self):
        """called when input is ready"""
    def logPrefix(self): return 'CursesClient'

class Screen(CursesStdIO):
    def __init__(self, stdscr,screensratio):
        self.timer = 0
        self.statusText = "NO NAME SELECTED: /nick <name>"
        self.ircText = ''
        self.barText = ''
        self.prevText = ['']
        self.prevCount = 0
        self.stdscr = stdscr

        # set screen attributes
        self.stdscr.nodelay(1) # this is used to make input calls non-blocking
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.curs_set(2)     # no annoying cursor

        self.rows, self.cols = self.stdscr.getmaxyx()
        self.toprows = int(self.rows*screensratio)
        self.toplines = []
        self.bottomrows = self.rows - self.toprows
        self.bottomlines = []
        self.cursorpos = 'bottom'
        curses.start_color()

        # create color pair's 1 and 2
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        self.paintStatus(self.statusText)

    def connectionLost(self, reason):
        self.close()

    def addLine(self, text, window='bottom'):
        """ add a line to the internal list of lines"""
        if window == 'bottom':
            self.bottomlines.append(text)
        elif window == 'top':
            self.toplines.append(text)
        self.redisplayLines()

    def redisplayLines(self):
        """ method for redisplaying lines 
            based on internal list of lines """

        self.stdscr.clear()
        self.paintStatus(self.statusText)
        i = 0
        index = len(self.toplines) - 1
        while i < (self.toprows) and index >= 0:
            self.stdscr.addstr(self.rows-self.bottomrows-1-i, 0, self.toplines[index][:self.cols-1], 
                               curses.color_pair(3))
            i = i + 1
            index = index - 1
        i = 0
        index = len(self.bottomlines) - 1
        while i < (self.bottomrows - 3) and index >= 0:
            self.stdscr.addstr(self.rows-2-i, 0, self.bottomlines[index][:self.cols-1], 
                               curses.color_pair(2))
            i = i + 1
            index = index - 1
        self.stdscr.move(self.rows-1, len(self.ircText))
        self.stdscr.refresh()

    def paintStatus(self, text):
 #       text = text + '' + str(self.stdscr.getyx())
        if len(text) > self.cols: text = text[:self.cols]
        self.stdscr.addstr(self.toprows+1,0,text + ' ' * (self.cols-len(text)), 
                           curses.color_pair(1))
        # move cursor to input line

    def doRead(self):
        """ Input is ready! """
        curses.noecho()
        if self.cursorpos == 'bottom': text = self.ircText
        elif self.cursorpos == 'top': text = self.barText
        self.timer = self.timer + 1
        c = self.stdscr.getch() # read a character

        if c == curses.KEY_BACKSPACE:
            text = text[:-1]

        if c == curses.KEY_DOWN:
            if self.prevCount < len(self.prevText)-1:
                text = self.prevText[self.prevCount]
                self.prevCount = self.prevCount+1
                self.redisplayLines()

        if c == curses.KEY_UP:
            if self.prevCount > 0:
                text = self.prevText[self.prevCount]
                self.prevCount = self.prevCount-1
                self.redisplayLines()

        if c == ord('\t'): #TAB
#            self.addLine('You pressed Tab!','top')
            if self.cursorpos == 'bottom':
                text = self.barText
                self.cursorpos = 'top'
            elif self.cursorpos == 'top':
                text = self.ircText
                self.cursorpos = 'bottom'
            self.redisplayLines()

        elif c == curses.KEY_ENTER or c == 10:
            if self.cursorpos == 'bottom':
                idchange = re.match ('/nick (\w+)',text)
                if idchange:
                    handle = idchange.group(1)
                    self.statusText = 'IDENTIFIED AS '+handle+'. CHANGE NAMES WITH /nick <name>'
                    self.irc.nickname = self.irc.originalnick+'-'+handle
                    self.irc.sendLine('NICK '+self.irc.nickname)
                    self.redisplayLines()
                elif self.irc.nickname != self.irc.originalnick:
                    newline = time.strftime('<%H:%M>')
                    self.addLine(newline+'<'+self.irc.nickname+'> '+text, 'bottom')
                    cmd = 'PRIVMSG '+self.irc.channel+' :'+text
                    try:
                        self.irc.sendLine(cmd)
                        self.prevText.append(self.ircText)
                        if len(self.prevText)>20: pop(self.prevText)
                        self.prevCount = 0
                    except:
                        self.addLine('irc is not connected.','bottom')
            elif self.cursorpos == 'top':
                self.addLine(text, 'top')
                try:
                    self.bar.sendLine(text)
                except:
                    self.addLine('bar is not connected.','top')
                #try sending it to the bar engine
            text = ''

        else:
            self.handleTimeout = 0
            if len(text) == self.cols-2: return
            try:
                    text = text + chr(c)
            except:
                pass #You've sent a special char.

        if self.cursorpos == 'bottom':
            self.ircText = text
        if self.cursorpos == 'top':
            self.barText = text

        self.stdscr.addstr(self.rows-1, 0, 
                           self.ircText + (' ' * (
                           self.cols-len(self.ircText)-2)),
                               curses.color_pair(2))
        self.stdscr.addstr(self.toprows, 0, 
                           self.barText + (' ' * (
                           self.cols-len(self.barText)-2)),
                               curses.color_pair(3))
        self.cursorMove()
        self.stdscr.refresh()


    def cursorMove(self):
        if self.cursorpos == 'bottom':
            self.stdscr.move(self.rows-1, len(self.ircText))
        if self.cursorpos == 'top':
            self.stdscr.move(self.toprows, len(self.barText))

    def Ping(self):
        self.irc.sendLine('PING space.nurdspace.nl')

    def checkForgetHandle(self):
        self.handleTimeout = self.handleTimeout + 1
        if self.handleTimeout > self.forgettime:
            self.statusText = "NO NAME SELECTED: /nick <name>"
            self.irc.nickname = self.irc.originalnick
            self.irc.sendLine('NICK '+self.irc.nickname)
            self.redisplayLines()

    def close(self):
        """ clean up """

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
