
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


import argparse
import textwrap
import pycanopenclient.version
import pycanopenclient.errors

class AppArgs():
    def __init__(self):
        self.inputFile=None
        self.socketPath='/tmp/CO_command_socket'
        self.tcpSocket=None
        self.tcpPort=60000
        self.printErrors=False
        self.command=None
        self.showVerbose=False

    def printErrorCodes(self):
        print("Internal error codes:")
        isInternalErr = True
        for key, val in pycanopenclient.errors.errorLst.items():
            if key == 0:
                isInternalErr = False
                print("SDO abort codes:")
            if isInternalErr:
                print("  - {0} - {1}".format(key, val))
            else:
                print("  - 0x{0:08x} - {1}".format(key, val))
        exit(1)


    def showVersion(self):
        print("APP VERSION v%s" % (pycanopenclient.version.__version__))
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
        parser.add_argument("-p", type=int, help="Tcp port to connect to when using -t. Defaults to 60000")
        #parser.add_argument("-d", type=bool, help=" Display description of error codes in case of error.\n(Default, if command is passed by program arguments.)")
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