#!/usr/bin/python
# -*- coding: UTF-8 –*- 
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license
import socket
import select
import time
import sys
import bcprotocol

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.0001
forward_to = ('batmud.bat.org', 23)

class RemoteParser:
    def parse(self, data):
        return data

class LocalParser (RemoteParser):
    def __init__(self, options):
        self.bc_parser = bcprotocol.Parser(options)

    def parse(self, data):
        return self.bc_parser.parse(data) 

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False

class TheServer:
    input_list = []
    channel = {}
    parser = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                try:
                    self.data = self.s.recv(buffer_size)
                    if len(self.data) == 0 or self.data ==  -1:
                        self.on_close()
                        break
                    else:
                        self.on_recv()
                except socket.error, ex:
                    self.on_drop()

                
                
    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print clientaddr, "has connected"
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock

            self.parser[clientsock] = RemoteParser()
            self.parser[forward] = LocalParser(options)

            # Enable batclient private protocol
            forward.send("\033bc 1\n")
        else:
            print "Can't establish connection with remote server.",
            print "Closing connection with client side", clientaddr
            clientsock.close()

    def on_close(self):
        print self.s.getpeername(), "has disconnected"
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        self.on_drop()

    def on_drop(self):
        out = self.channel[self.s]
        self.input_list.remove(self.s)
        self.input_list.remove(out)
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        new_data = self.parser[self.s].parse(data)
        self.channel[self.s].sendall(new_data)


if __name__ == '__main__':
    ################
    # User options #
    ################
    port = 9999
    codes = ["50", "52", "53", "54", "60", "61", "62", "63", "64", "70"]
    enable_color = True
    enable_combat_plugin = True

    try:
        options = bcprotocol.Options(codes, enable_color, enable_combat_plugin)
        server = TheServer('', port)
        print "Bat proxy is running at {}:{}".format("localhost", port)
        server.main_loop()
    except KeyboardInterrupt:
        print "Ctrl C - Stopping server"

sys.exit(1)
