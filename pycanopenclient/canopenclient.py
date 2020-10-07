
import socket
import sys
import os
import platform  # detect OS
from enum import Enum

class SocketType(Enum):
    UNIX = 1
    TCP = 2

class CANopenClient():

    def __init__(self, sock_Type, server_Address, server_Port = 0, show_verbose=False):
        self.sock = None
        self.sock_type = sock_Type
        self.server_address = server_Address
        self.server_port = server_Port
        self.showVerbose = show_verbose


    def __get_constants(self, prefix):
        """Create a dictionary mapping socket module constants to their names."""
        return dict( (getattr(socket, n), n)
                    for n in dir(socket)
                    if n.startswith(prefix)
                    )


    def connect(self):
        if self.sock == None:
            if self.sock_type == SocketType.UNIX:
                return self.connectUnixSocket()
            elif self.sock_type == SocketType.TCP:
                return self.connectTcpSocket()
            else:
                if self.showVerbose:
                    print("ERROR: Socket type not supported")
        else:
            if self.showVerbose:
                print("Socket already opened")
            return True
        return False


    def disconnect(self):
        if self.sock != None:
            if self.showVerbose:
                print("Closing socket")
            self.sock.close()
            self.sock = None
        else:
            if self.showVerbose:
                print("Socket already closed")


    def connectUnixSocket(self):
        if platform.system() == 'Linux':
            # Create a UDS socket
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            # Connect the socket to the unix socket where the server is listening
            if self.showVerbose:
                print("Connecting to: {0}".format(self.server_address))
            try:
                self.sock.connect(self.server_address)
                return True
            except Exception as err:
                if self.showVerbose:
                    print("ERROR: Connecting failed: {0}".format(err))
        else:
            if self.showVerbose:
                print("ERROR: Connecting failed: {0} doesn't support Unix Domain sockets".format(platform.system()))
        return False


    def connectTcpSocket(self):
        if platform.system() == 'Linux' or platform.system() == 'Windows':
            families = self.__get_constants('AF_')
            types = self.__get_constants('SOCK_')
            protocols = self.__get_constants('IPPROTO_')

            # Create & Conenct to a TCP/IP socket
            try:
                if self.showVerbose:
                    print("Connecting to: {0}:{1}".format(self.server_address, self.server_port))
                self.sock = socket.create_connection((self.server_address, self.server_port))
                return True
            except Exception as err:
                if self.showVerbose:
                    print("ERROR: Connecting failed: {0}".format(err))
        else:
            if self.showVerbose:
                print("ERROR: Connecting failed: {0} doesn't support TCP sockets".format(platform.system()))
        return False


    def sendCommand(self, cmd, index=1):
        data=""
        if self.sock == None:
            if self.showVerbose:
                print("TX failed: not connected")
            return data
        try:
            # build message, prepend [x] command index when required
            message= ""
            if cmd[0] == '[':
                message = cmd
            else:
                message = "[{0}] {1}".format(index, cmd)
            if self.showVerbose:
                print("# {0}".format(message))
            txBytes = message.encode('UTF-8', 'strict')

            #send
            self.sock.sendall(txBytes)
            
            # receive
            while True:
                rxBytes = self.sock.recv(1024)
                data += rxBytes.decode('UTF-8', 'strict')
                if "\r\n" in data:
                    break
            data=data.replace("\x00", "").strip()
            print(data)
        except Exception as err:
            if self.showVerbose:
                print("ERROR: TX failed: {0}".format(err))
        return data
