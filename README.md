# CANopen network client in Python

This application acts as a CANopen network client.
It connects to a CANopen gateway either through a Unix domain or TCP socket.

![Topology](doc/topology.png)

The application is meant to be a pure Python based drop-in replacement for *canopencomm*, 
the latter being part of the [CANopenSocket](https://github.com/CANopenNode/CANopenSocket) repository.

## Using this application

Mostly you can follow the [README](https://github.com/CANopenNode/CANopenSocket/blob/master/README.md) of the CANopenSocket repository 
to setup a working CANopen gateway and network client. Use this application as replacement for *canopencomm*.

This application takes input and sends it over to the CANopen gateway who will translate the message into the CANopen
network. The input commands can either be passed into the application as command line arguments, as a file, or read from stdin.
The network connection can be either a UNIX domain socket (Linux only) or TCP socket (Windows and Linux).

### Through the command line

```
$ python cli.py 4 start
```

### From a file

First create a file containing your commands. For example, `mycommands.txt`:

```
4 start
3 start
```

The commands will be executed line by line:

```
$ python cli.py -f mycommands.txt
```

### From stdin

```
$ python cli.py
4 start
```

Press `enter` after each command to send. The reply should appear swiftly. 
Enter `exit` to exit the application.

### Unix domain socket

The appliction uses will by default use a Unix domain socket at `/tmp/CO_command_socket` to connect to the gateway.
You can override that socket file:

```
$ python cli.py -s /tmp/mysocket
```

### TCP socket

For remote execution or for Windows machines this option comes in handy.
By default port 60000 is used but both hostname/ip and port can be used defined:

```
$ python cli.py -t 192.168.0.10 -p 5000
```