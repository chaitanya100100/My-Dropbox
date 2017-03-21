import threading
import socket
import os
import sys
import datetime
import hashlib
import json

# get command line args
try:
    my_host = str(sys.argv[1])
    my_port = int(sys.argv[2])

    his_host = str(sys.argv[3])
    his_port = int(sys.argv[4])

    os.chdir(sys.argv[5])

except Exception as e:
    print "Invalid args"
    print "Usage : %s myhost myport hishost hisport myrdir" % sys.argv[0]
    print
    print
    print str(e)
    sys.exit()


class ServerThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.MAX_LENGTH = 1024

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((my_host, my_port))
        self.server_socket.listen(5)

        print "\nserver listening at", my_host, my_port
        print "\ncurrent directory :", os.getcwd()
        print

        try:
            # server loop
            while True:

                # accept connection
                try:
                    self.client_socket, self.client_addr = self.server_socket.accept()
                except Exception as e:
                    print str(e)
                    break
                print "get connection from", self.client_addr

                # get data
                self.client_input = self.client_socket.recv(self.MAX_LENGTH)

                # process data
                try:
                    self.process()
                except Exception as e:
                    print str(e)

                # close connection
                self.client_socket.close()
                print


        except Exception as e:
            print str(e)

        print
        print "server closing from", my_host, my_port
        self.server_socket.close()


    def process(self):
        self.client_socket.send("I got this : %s\n"%self.client_input)

    def send_string(self, ret):
        data = json.dumps(ret)
        total_len = len(data)
        sent_len = 0
        while sent_len < total_len:
            sent = self.client_socket.send(data[sent_len:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            sent_len += sent


    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    # get datetime object from string
    def get_dt(self, time_string):
        l = time_string.split('/')
        if len(l)==0:
            return datetime.datetime.now()

        for i in range(len(l)):
            l[i] = int(l[i])

        if len(l)==1:
            return datetime.datetime(l[0], 1, 1)
        elif len(l)==2:
            return datetime.datetime(l[0], l[1], 1)
        elif len(l)==3:
            return datetime.datetime(l[0], l[1], l[2])
        elif len(l)==4:
            return datetime.datetime(l[0], l[1], l[2], l[3])
        elif len(l)==5:
            return datetime.datetime(l[0], l[1], l[2], l[3], l[4])
        elif len(l)==6:
            return datetime.datetime(l[0], l[1], l[2], l[3], l[4], l[5])



class ClientThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.PROMPT_HEADER = ">>"
        self.DOWNLOAD_INDICATOR = "#!#DownLoadThisFile#!#"
        self.MAX_LENGTH = 1024

    def run(self):

        print "current directory :", os.getcwd()

        # terminal loop
        while True:

            # get command
            try:
                command = raw_input(self.PROMPT_HEADER)
            except Exception as e:
                print str(e)
                return

            if not command.strip():
                continue

            # process command
            self.process(command)


    def process(self, command):

        tokens = command.split()
        if not len(tokens):
            return

        # create client socket and connect
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((his_host, his_port))

        # send command to server and get response
        self.client_socket.send(json.dumps(tokens))
        data = self.client_socket.recv(self.MAX_LENGTH)

        # handle response
        if data.startswith(self.DOWNLOAD_INDICATOR):
            self.handle_download(tokens, data)
        else:
            self.handle_output(data)

        # close socket
        self.client_socket.close()
        return


    def handle_output(self, data):
        while True:
            chunk = self.client_socket.recv(self.MAX_LENGTH)
            if not chunk:
                break
            data += chunk
        print data


    def handle_download(self, tokens, data):
        chunk = data.replace(self.DOWNLOAD_INDICATOR, "")
        file = tokens[2]

        with open(file, 'wb') as f:
            f.write(chunk)
            while True:
                chunk = self.client_socket.recv(self.MAX_LENGTH)
                if not chunk:
                    break
                f.write(chunk)
        f.close()



server_thread = ServerThread()
client_thread = ClientThread()

server_thread.start()
client_thread.start()

server_thread.join()
client_thread.join()

print "Exiting Here"
