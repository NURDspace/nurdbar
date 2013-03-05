import os, subprocess, serial, time
from ConfigParser import SafeConfigParser


class SerialEmulator(object):
    def __init__(self,configfile):
        config=SafeConfigParser()
        config.readfp(open(configfile,'r'))
        self.inport=os.path.expanduser(config.get('virtualSerialPorts','inport'))
        self.outport=os.path.expanduser(config.get('virtualSerialPorts','outport'))
        cmd=['/usr/bin/socat','-d','-d','PTY,link=%s,raw,echo=1'%self.inport,'PTY,link=%s,raw,echo=1'%self.outport]
        self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        time.sleep(3)
        self.serial=serial.Serial(self.inport)
        self.err=''
        self.out=''
    def writeLine(self,line):
        line=line.strip('\r\n')
        self.serial.write('%s\r\n'%line)
    def __del__(self):
        self.stop()
    def stop(self):
        self.proc.kill()
        self.out,self.err=self.proc.communicate()
