#!/usr/bin/python


import sys
from appargs import AppArgs
from pycanopenclient.canopenclient import CANopenClient, SocketType




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