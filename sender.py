import sys
import os
import socket
import threading
from packet import Packet


class Sender:
    def __init__(self, netHostAddr, netRcvPort, localRcvPort, timeoutIntv, payload):
        self.netHostAddr = netHostAddr
        self.netRcvPort = netRcvPort
        self.localRcvPort = localRcvPort
        self.timeoutIntv = timeoutIntv
        self.payload = payload
        self.packSize = 1024
        self.seqCntr = 0
        self.charLimit = 500
        self.packets = []
        self.totalPackets = 0
        self.winSize = 1
        self.onConfirm = 0
        self.onCall = False
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.sock = self.initSocket()
        self.segLog = self.openFile("segnum.log", "a")
        self.ackLog = self.openFile("ack.log", "a")
        self.packetTimers = {}
        self.lastAcked = -1

    @staticmethod
    def openFile(filePath, mode):
        # Open a file safely with error handling
        try:
            file = open(filePath, mode)
        except IOError:
            sys.stderr.write(f"Error: Failed to open {filePath}.")
            sys.exit(1)
        return file

    def initSocket(self):
        # Initialize and bind a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.localRcvPort))
        return sock

    def loadPayloadData(self):
        with open(self.payload, 'r') as payloadFile:
            # Create packets from data and add to list
            packetData = payloadFile.read(self.charLimit)
            while packetData:
                self.packets.append(Packet(1, self.totalPackets, len(packetData), packetData))
                packetData = payloadFile.read(self.charLimit)
                self.totalPackets += 1

    def forward(self):
        print("In forward method")
        while True:
            # Receive Packet and parse data
            newPacket = Packet.decode(Packet(self.sock.recvfrom(self.packSize)[0]))
            packetType, packetSeqNum, packetLen, packetData = newPacket

            with self.lock:
                if packetType == 1:  # data
                    sys.stderr.write("error Data Type.")
                    sys.exit(1)
                elif packetType == 2:  # EOT (End of Transmission)
                    self.ackLog.write(str(packetSeqNum) + "\n")
                    return
                else:
                    self.ackLog.write(str(packetSeqNum) + "\n")
                    if packetSeqNum >= self.onConfirm:
                        self.onConfirm = packetSeqNum + 1
                        self.onCall = True
                        self.cv.notify_all()

    def sendPackets(self):
        print("In sendPackets method")
        # Main loop for sending packets until all are confirmed
        while self.onConfirm < self.totalPackets:
            with self.lock:
                # Send packets within the current window
                while self.seqCntr < self.onConfirm + self.winSize and self.seqCntr < self.totalPackets:
                    packet = self.packets[self.seqCntr]
                    if not self.sock:
                        break
                    self.sock.sendto(Packet.encode(packet), (self.netHostAddr, self.netRcvPort))
                    self.segLog.write(str(self.seqCntr) + "\n")
                    self.seqCntr += 1
                    # Start a timer for the packet
                    timer = threading.Timer(self.timeoutIntv, self.sendPacket, args=[packet])
                    timer.start()
                    self.packetTimers[packet.seqnum] = timer
                eotPacket = Packet(2, self.seqCntr, 0, "")
                if not self.sock:
                    break
                self.sock.sendto(Packet.encode(eotPacket), (self.netHostAddr, self.netRcvPort))
                eotTimer = threading.Timer(self.timeoutIntv, self.sendEOT, args=[eotPacket])
                eotTimer.start()
                self.packetTimers[eotPacket.seqnum] = eotTimer
                # Wait for a notification from the receiver
                self.cv.wait()

                # Cancel timers for all packets that were acknowledged
                for seqnum in range(self.onConfirm, self.seqCntr):
                    timer = self.packetTimers.get(seqnum)
                    if timer is not None:
                        timer.cancel()
                        del self.packetTimers[seqnum]

        self.sock.close()

        # Close log files for segment numbers and acknowledgements
        self.segLog.close()
        self.ackLog.close()

    def sendPacket(self, packet):

        with self.lock:
            # Resend the packet if it hasn't been acknowledged
            if packet.seqnum >= self.onConfirm and self.sock:
                try:
                    print("Resending")
                    self.sock.sendto(Packet.encode(packet), (self.netHostAddr, self.netRcvPort))
                    self.segLog.write(str(packet.seqnum) + "\n")
                    # Restart the timer for the packet
                    timer = threading.Timer(self.timeoutIntv, self.sendPacket, args=[packet])
                    timer.start()
                    self.packetTimers[packet.seqnum] = timer
                except OSError as e:
                    print("Sender out.")

    def sendEOT(self, packet):

        with self.lock:
            # Resend the EOT packet if it hasn't been acknowledged
            if packet.seqnum >= self.onConfirm and self.sock:
                try:
                    print('sending EOT')
                    self.sock.sendto(Packet.encode(packet), (self.netHostAddr, self.netRcvPort))
                    self.segLog.write(str(packet.seqnum) + "\n")
                    # Restart the timer for the EOT packet
                    timer = threading.Timer(self.timeoutIntv, self.sendEOT, args=[packet])
                    timer.start()
                    self.packetTimers[packet.seqnum] = timer
                except OSError as e:
                    print("Sender out.")

    def run(self):
        self.loadPayloadData()
        recvThread = threading.Thread(target=self.forward)
        recvThread.daemon = True
        recvThread.start()
        self.sendPackets()

        # Send EOT (End of Transmission) packet and close the receiver thread
        # self.sock.sendto(Packet.encode(Packet(2, self.seqCntr, 0, "")), (self.netHostAddr, self.netRcvPort))
        # print('sending EOT')
        recvThread.join()
        # self.sock.close()

        # # Close log files for segment numbers and acknowledgements
        # self.segLog.close()
        # self.ackLog.close()


def main():
    netHostAddr, netRcvPort, localRcvPort, timeoutIntv, payload = sys.argv[1:6]
    netRcvPort, localRcvPort, timeoutIntv = map(int, (netRcvPort, localRcvPort, timeoutIntv))

    sender = Sender(netHostAddr, netRcvPort, localRcvPort, timeoutIntv, payload)
    sender.run()


if __name__ == "__main__":
    main()

