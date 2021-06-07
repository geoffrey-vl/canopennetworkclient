#!/usr/bin/python

'''
Program reads arguments from standard input or file. It sends commands to 
canopend via socket, line after line. Result is printed to standard output. 
Socket is either unix domain socket (default) or a remote tcp socket (option -t). 
For more information see http://www.can-cia.org/, CiA 309 standard.
'''

__epilog__ = """
Command strings must start with \"[\"<sequence>\"]\" (except if from arguments):
  - SDO upload:   [[<net>] <node>] r[ead]  <index> <subindex> [<datatype>]
  - SDO download: [[<net>] <node>] w[rite] <index> <subindex>  <datatype> <value>
  - Configure SDO time-out: [<net>] set sdo_timeout <value>
  - Enable SDO block transfer: [<net>] set sdo_block <value>
  - Set default node: [<net>] set node <value>

  - Start node:                  [[<net>] <node>] start
  - Stop node:                   [[<net>] <node>] stop
  - Set node to pre-operational: [[<net>] <node>] preop[erational]
  - Reset node:                  [[<net>] <node>] reset node
  - Reset communication:         [[<net>] <node>] reset comm[unication]

Comments started with '#' are ignored. They may be on the beginning of the line
or after the command string. 'sdo_timeout' is in milliseconds, 500 by default.
If <node> is not specified within commands, then value defined by 'set node'
command is used.


Datatypes:
  - b                 - Boolean.
  - u8, u16, u32, u64 - Unsigned integers.
  - i8, i16, i32, i64 - Signed integers.
  - r32, r64          - Real numbers.
  - t, td             - Time of day, time difference.
  - vs                - Visible string (between double quotes).
  - os, us, d         - Octet string, unicode string, domain
                        (mime-base64 (RFC2045) should be used).


Response: \"[\"<sequence>\"]\" \\
    OK | <value> | ERROR: <SDO-abort-code> | ERROR: <internal-error-code>


See also: https://github.com/CANopenNode/CANopenSocket

"""



import sys
import argparse
import textwrap
import socket
import os
import platform  # detect OS
from enum import Enum


__version__ = '1.2.01'


errorLst = {
        100: "Request not supported.",
        101: "Syntax error.",
        102: "Request not processed due to internal state.",
        103: "Time-out (where applicable).",
        104: "No default net set.",
        105: "No default node set.",
        106: "Unsupported net.",
        107: "Unsupported node.",
        200: "Lost guarding message.",
        201: "Lost connection.",
        202: "Heartbeat started.",
        203: "Heartbeat lost.",
        204: "Wrong NMT state.",
        205: "Boot-up.",
        300: "Error passive.",
        301: "Bus off.",
        303: "CAN buffer overflow.",
        304: "CAN init.",
        305: "CAN active (at init or start-up).",
        400: "PDO already used.",
        401: "PDO length exceeded.",
        501: "LSS implementation- / manufacturer-specific error.",
        502: "LSS node-ID not supported.",
        503: "LSS bit-rate not supported.",
        504: "LSS parameter storing failed.",
        505: "LSS command failed because of media error.",
        600: "Running out of memory.",
        0x00000000: "No abort.",
        0x05030000: "Toggle bit not altered.",
        0x05040000: "SDO protocol timed out.",
        0x05040001: "Command specifier not valid or unknown.",
        0x05040002: "Invalid block size in block mode.",
        0x05040003: "Invalid sequence number in block mode.",
        0x05040004: "CRC error (block mode only).",
        0x05040005: "Out of memory.",
        0x06010000: "Unsupported access to an object.",
        0x06010001: "Attempt to read a write only object.",
        0x06010002: "Attempt to write a read only object.",
        0x06020000: "Object does not exist.",
        0x06040041: "Object cannot be mapped to the PDO.",
        0x06040042: "Number and length of object to be mapped exceeds PDO length.",
        0x06040043: "General parameter incompatibility reasons.",
        0x06040047: "General internal incompatibility in device.",
        0x06060000: "Access failed due to hardware error.",
        0x06070010: "Data type does not match, length of service parameter does not match.",
        0x06070012: "Data type does not match, length of service parameter too high.",
        0x06070013: "Data type does not match, length of service parameter too short.",
        0x06090011: "Sub index does not exist.",
        0x06090030: "Invalid value for parameter (download only).",
        0x06090031: "Value range of parameter written too high.",
        0x06090032: "Value range of parameter written too low.",
        0x06090036: "Maximum value is less than minimum value.",
        0x060A0023: "Resource not available: SDO connection.",
        0x08000000: "General error.",
        0x08000020: "Data cannot be transferred or stored to application.",
        0x08000021: "Data cannot be transferred or stored to application because of local control.",
        0x08000022: "Data cannot be transferred or stored to application because of present device state.",
        0x08000023: "Object dictionary not present or dynamic generation fails.",
        0x08000024: "No data available."
}


gDefaultPort = 6000


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

            # Create & Connect to a TCP/IP socket
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




class AppArgs():
    def __init__(self):
        self.inputFile=None
        self.socketPath='/tmp/CO_command_socket'
        self.tcpSocket=None
        self.tcpPort=gDefaultPort
        self.printErrors=False
        self.command=None
        self.showVerbose=False

    def printErrorCodes(self):
        print("Internal error codes:")
        isInternalErr = True
        for key, val in errorLst.items():
            if key == 0:
                isInternalErr = False
                print("SDO abort codes:")
            if isInternalErr:
                print("  - {0} - {1}".format(key, val))
            else:
                print("  - 0x{0:08x} - {1}".format(key, val))
        exit(1)


    def showVersion(self):
        print("APP VERSION v%s" % (__version__))
        exit(1)

    def parse(self, argv):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(__doc__),
            epilog=__epilog__
        )

        parser.add_argument('command', type=str, nargs='?',  help='command to send to the canopen network')
        parser.add_argument("-f", type=str, help="Path to the input file")
        parser.add_argument("-s", type=str, help="Path to the socket (default '/tmp/CO_command_socket')")
        parser.add_argument("-t", type=str, help="Connect via tcp to remote <host>")
        parser.add_argument("-p", type=int, help="Tcp port to connect to when using -t. Defaults to "+str(gDefaultPort))
        parser.add_argument("-d", help=" Display description of error codes in case of error.\n(Default, if command is passed by program arguments.)", action="store_true")
        parser.add_argument("--version", help="Show version", action="store_true")
        parser.add_argument("--verbose", help="Show verbose info", action="store_true")
        parser.add_argument("--listErrors", help="Display internal and SDO error codes.", action="store_true")
        args = parser.parse_args()

        if args.command:
            self.command=""
            for cmd in args.command:
                self.command=self.command+cmd + " "
            self.command= self.command.strip()
        if args.f:
            self.inputFile=args.f
        if args.s:
            self.socketPath=args.s
        if args.t:
            self.tcpSocket=args.t
        if args.p:
            self.tcpPort=args.p
        if args.d:
            self.printErrors=args.d
        if args.verbose:
            self.showVerbose = True
        if args.version:
            self.showVersion()
        if args.listErrors:
            self.printErrorCodes()


def main(argv):
    args = AppArgs()
    args.parse(argv)

    client = None
    if args.tcpSocket != None and args.tcpPort > 0 and args.tcpPort < 65535:
        client = CANopenClient(SocketType.TCP, args.tcpSocket, args.tcpPort, args.showVerbose)
    else:
        client = CANopenClient(SocketType.UNIX, args.socketPath, 0, args.showVerbose)

    isOk = client.connect()
    if isOk == False:
        return

    # get command from input file
    if args.inputFile != None:
        file=None
        try:
            file = open(args.inputFile, "r")
            for line in file:
                client.sendCommand(line)
        except:
            print("ERROR: input file not found")
            pass
        finally:
            if file != None:
                file.close()
    #get command from arguments
    elif args.command != None:
        client.sendCommand(args.command)
    #get command from stdin
    else:
        while True:
            cmd=input()
            if "exit" in cmd:
                break
            client.sendCommand(cmd)
        
    client.disconnect()

if __name__ == '__main__':
    main(sys.argv)