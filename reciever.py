import sys
import socket
from packet import Packet


class Receiver:
    def __init__(self, netHostAddr, netRceiPort, locRceiPort, outputFile):
        self.netHostAddr = netHostAddr
        self.netRceiPort = netRceiPort
        self.locRceiPort = locRceiPort
        self.outputFile = outputFile
        self.expectedSeqNum = 0
        self.lastConfirmed = None
        self.packSize = 1024

        self.sock = self.initSocket()
        self.arrivalLog = self.openFile("arrival.log", "a")
        self.payloadFile = self.openFile(outputFile, "a")

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
        sock.bind(('', self.locRceiPort))
        return sock

    def handlePacket(self, packet):
        # Handle received packets and send appropriate ACKs
        packetType, packetSeqNum, packetLen, packetData = packet

        # Log received packet sequence number
        self.arrivalLog.write(f"{packetSeqNum}\n")

        if packetSeqNum == self.expectedSeqNum:
            if packetType == 2:  # EOT
                print("Received EOT packet")  # Add this line
                self.sendAck(2, packetSeqNum)
                return False  # Terminate the loop in run method
            elif packetType == 1:  # Data
                print("Received file packet")
                self.payloadFile.write(packetData)
                self.sendAck(0, packetSeqNum)
                self.lastConfirmed = packetSeqNum
                self.expectedSeqNum = self.lastConfirmed + 1
        elif self.lastConfirmed:
            self.sendAck(0, self.lastConfirmed)
        return True


    def sendAck(self, packetType, packetSeqNum):
        # Send an ACK packet to the sender
        self.sock.sendto(Packet.encode(Packet(packetType, packetSeqNum, 0, "")), (self.netHostAddr, self.netRceiPort))

    def run(self):
        # Main loop to receive and handle packets
        while True:
            pack, _ = self.sock.recvfrom(self.packSize)
            packet = Packet.decode(Packet(pack))
            if not self.handlePacket(packet):
                break

        # Close the log and payload files
        self.arrivalLog.close()
        self.payloadFile.close()


if __name__ == "__main__":
    netHostAddr, netRceiPort, locRceiPort, outputFile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    receiver = Receiver(netHostAddr, netRceiPort, locRceiPort, outputFile)
    receiver.run()
