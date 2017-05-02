import time
import glob
import mimetypes
import threading
import socket
import os
import sys
import datetime
import hashlib
import json

command_line = False

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
        self.MAX_LENGTH_UDP = 32*1024
        self.DOWNLOAD_TCP = "#!#TCP#!#"
        self.DOWNLOAD_UDP = "#!#UDP#!#"

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
                client_input = self.client_socket.recv(self.MAX_LENGTH)
                if not client_input:
                    self.client_socket.close()
                    continue
                print "got request %s" % client_input
                # process data
                try:
                    self.process(client_input)
                except Exception as e:
                    print str(e)

                # close connection
                self.client_socket.close()
                #print


        except Exception as e:
            print str(e)

        #print
        #print "server closing from", my_host, my_port
        self.server_socket.close()


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


    def process(self, client_input):

        # split into tokens
        tokens = json.loads(client_input)

        if not len(tokens):
            self.client_socket.send("Give command")
        elif tokens[0] == "index":
            self.command_index(tokens)
        elif tokens[0] == "hash":
            self.command_hash(tokens)
        elif tokens[0] == "download":
            self.command_download(tokens)
        else:
            self.client_socket.send("Invalid Input")

    # a function to handle index command
    def command_index(self, tokens):
        ret = []

        # index longlist
        if len(tokens)==1 or tokens[1] == "longlist":
            file_list = os.listdir(".")
            for file in file_list:

                get_file_access(file)

                mtime = os.path.getmtime(file)
                ret.append({
                    "name" : file,
                    "size" : os.path.getsize(file),
                    "timestamp" : datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "realtime" : mtime,
                    "type" : mimetypes.guess_type(file)
                })

                leave_file_access(file)

        # index shortlist
        elif tokens[1] == "shortlist":

            file_list = os.listdir(".")
            if len(tokens) == 2:
                sti = datetime.datetime.now() - datetime.timedelta(days=1)
                eni = datetime.datetime.now()

            elif len(tokens) == 3:
                sti = self.get_dt(tokens[2])
                eni = datetime.datetime.now()

            else:
                sti = self.get_dt(tokens[2])
                eni = self.get_dt(tokens[3])

            for file in file_list:

                get_file_access(file)
                mtime = os.path.getmtime(file)
                dtobj = datetime.datetime.fromtimestamp(mtime)
                if dtobj >= sti and dtobj <= eni:
                    ret.append({
                        "name" : file,
                        "size" : os.path.getsize(file),
                        "timestamp" : dtobj.strftime('%Y-%m-%d %H:%M:%S'),
                        "realtime" : mtime,
                        "type" : mimetypes.guess_type(file)
                    })
                leave_file_access(file)

        # index regex
        elif tokens[1] == "regex":
            if len(tokens) < 3:
                ret.append({
                    "error" : "index regex : regex not given"
                })
            else:
                file_list = glob.glob(tokens[2])
                for file in file_list:
                    get_file_access(file)

                    mtime = os.path.getmtime(file)
                    ret.append({
                        "name" : file,
                        "size" : os.path.getsize(file),
                        "timestamp" : datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "realtime" : mtime,
                        "type" : mimetypes.guess_type(file)
                    })

                    leave_file_access(file)


        # index invalid flag
        else:
            ret.append({
                "error" : "index : invalid flag"
            })

        self.send_string(ret)
        return

    # a function to handle hash command
    def command_hash(self, tokens):
        ret = []

        if len(tokens) < 2:
            ret.append({
                "error" : "hash : argument not given"
            })

        # verify
        elif tokens[1] == "verify":
            if len(tokens) < 3:
                ret.append({
                    "error" : "hash verify : filename not given"
                })
            else:
                file = tokens[2]
                get_file_access(file)
                if not os.path.isfile(file):
                    ret.append({
                        "error" : "hash verify : file doesn't exist"
                    })
                else:
                    mtime = os.path.getmtime(file)
                    ret.append({
                        "name" : file,
                        "hash_md5" : self.md5(file),
                        "timestamp" : datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "realtime" : mtime,
                        "type" : mimetypes.guess_type(file)
                    })
                leave_file_access(file)

        # checkall
        elif tokens[1] == "checkall":
            file_list = os.listdir(".")
            for file in file_list:
                if os.path.isfile(file):
                    get_file_access(file)
                    mtime = os.path.getmtime(file)
                    ret.append({
                        "name" : file,
                        "hash_md5" : self.md5(file),
                        "timestamp" : datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "realtime" : mtime,
                        "type" : mimetypes.guess_type(file)
                    })
                    leave_file_access(file)

        # hash invalid args
        else:
            ret.append({
                "error" : "hash : invalid argument"
            })

        self.send_string(ret)
        return



    # a function to handle download
    def command_download(self, tokens):
        ret = []
        if len(tokens) < 2:
            ret.append({
                "error" : "download : argument not given"
            })

        # send file via TCP
        elif tokens[1] == "TCP":

            if len(tokens) < 3:
                ret.append({
                    "error" : "download TCP : filename not given"
                })
            else:
                file = tokens[2]
                get_file_access(file)
                if not os.path.isfile(file):
                    ret.append({
                        "error" : "download TCP : file doesn't exist"
                    })
                    leave_file_access(file)
                else:
                    f = open(file, 'rb')
                    self.client_socket.send(self.DOWNLOAD_TCP)

                    chunk = f.read(self.MAX_LENGTH)
                    while chunk:
                        self.client_socket.send(chunk)
                        # print "sent :", len(chunk)
                        chunk = f.read(self.MAX_LENGTH)
                    f.close()
                    leave_file_access(file)
                    return

        # send file via UDP
        elif tokens[1] == "UDP":
            if len(tokens) < 4:
                ret.append({
                    "error" : "download UDP : filename not given"
                })
            else:
                file = tokens[2]
                get_file_access(file)
                if not os.path.isfile(file):
                    ret.append({
                        "error" : "download UDP : file doesn't exist"
                    })
                    leave_file_access(file)
                else:
                    self.client_socket.send(self.DOWNLOAD_UDP + self.md5(file))
                    self.client_socket.close()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    f = open(file, 'rb')
                    chunk = f.read(self.MAX_LENGTH_UDP)
                    while chunk:
                        sock.sendto(chunk, (his_host, int(tokens[3])))
                        chunk = f.read(self.MAX_LENGTH_UDP)
                    f.close()
                    sock.close()
                    leave_file_access(file)
                    return

        # download invalid argument
        else:
            ret.append({
                "error" : "download : invalid argument"
            })
        self.send_string(ret)
        return





class ClientThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.PROMPT_HEADER = ">>"
        self.DOWNLOAD_TCP = "#!#TCP#!#"
        self.DOWNLOAD_UDP = "#!#UDP#!#"
        self.MAX_LENGTH_UDP = 32*1024
        self.MAX_LENGTH = 1024

    def run(self):

        print "current directory :", os.getcwd()

        time.sleep(5)

        # terminal loop
        while True:

            """
            # get command
            try:
                command = raw_input(self.PROMPT_HEADER)
            except Exception as e:
                print str(e)
                return
            """


            command = "sync"

            if not command.strip():
                continue

            while True:
                temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                is_off = temp_sock.connect_ex((his_host, his_port))
                temp_sock.close()
                if not is_off:
                    break


            # process command
            if command.strip() == "exit":
                return
            elif command.strip() == "sync":
                self.sync()
            else:
                self.process(command)

            time.sleep(15)


    def process(self, command):

        ans = ""
        tokens = command.split()
        if not len(tokens):
            return

        if tokens[0] == "download":
            if len(tokens) != 1:
                if tokens[1] == "TCP":
                    self.receive_file_tcp(tokens)
                elif tokens[1] == "UDP":
                    count = 1
                    fair = self.receive_file_udp(tokens)
                    while not fair and count < 4:
                        fair = self.receive_file_udp(tokens)
                        count += 1
                    if not fair:
                        print "UDP can't handle this"
                else:
                    print "download : invalid argument"
            else:
                print "download : argument not given"

        else:
            ans = self.receive_string(tokens)
            if command_line:
                print ans
        return ans


    def receive_string(self, tokens):

        # create client socket and connect
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((his_host, his_port))

        # send command to server and get response
        self.client_socket.send(json.dumps(tokens))
        data = ""
        while True:
            chunk = self.client_socket.recv(self.MAX_LENGTH)
            if not chunk:
                break
            data += chunk

        # close socket
        self.client_socket.close()
        return data


    def receive_file_tcp(self, tokens):

        # create client socket and connect
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((his_host, his_port))

        # send command to server and get response
        self.client_socket.send(json.dumps(tokens))
        data = self.client_socket.recv(self.MAX_LENGTH)

        if data.startswith(self.DOWNLOAD_TCP):
            file = tokens[2]
            chunk = data.replace(self.DOWNLOAD_TCP, "")
            get_file_access(file)
            with open(file, 'wb') as f:
                f.write(chunk)
                while True:
                    chunk = self.client_socket.recv(self.MAX_LENGTH)
                    if not chunk:
                        break
                    f.write(chunk)
            f.close()
            leave_file_access(file)
        else:
            print data
        # close socket
        self.client_socket.close()


    def receive_file_udp(self, tokens):

        # create client socket and connect
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((his_host, his_port))

        # create udp socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((my_host, 0))

        if len(tokens) < 4:
            tokens.append(sock.getsockname()[1])
        else:
            tokens[3] = sock.getsockname()[1]

        # send command to server and get response
        self.client_socket.send(json.dumps(tokens))
        data = self.client_socket.recv(self.MAX_LENGTH)
        self.client_socket.close()

        if data.startswith(self.DOWNLOAD_UDP):
            file = tokens[2]
            bla, real_hash_md5 = data.split(self.DOWNLOAD_UDP)

            get_file_access(file)
            with open(file, 'wb') as f:
                try:
                    while True:
                        chunk, bla = sock.recvfrom(self.MAX_LENGTH_UDP)
                        if not chunk:
                            break
                        sock.settimeout(2)
                        f.write(chunk)
                except socket.timeout:
                    pass

            f.close()
            sock.close()
            hash_md5 = self.md5(file)
            leave_file_access(file)
            if hash_md5 != real_hash_md5:
                return False
            else:
                return True

        else:
            sock.close()
            print data
            return True


    def receive_file(self, tokens, data):
        chunk = data.replace(self.DOWNLOAD_TCP, "")
        file = tokens[2]

        with open(file, 'wb') as f:
            f.write(chunk)
            while True:
                chunk = self.client_socket.recv(self.MAX_LENGTH)
                if not chunk:
                    break
                f.write(chunk)
        f.close()
        return ""

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    def sync(self):

        bholo = self.process("hash checkall")
        files_data = json.loads(bholo)

        for file in files_data:
            file_name = file["name"]
            if not os.path.exists(file_name):
                self.process("download TCP %s" % file_name)
            else:
                get_file_access(file_name)
                hash_here = self.md5(file_name)
                realtime_here = os.path.getmtime(file_name)
                leave_file_access(file_name)
                if file["hash_md5"] != hash_here:
                    self.process("download TCP %s" % file_name)
                    if realtime_here < file.realtime:
                        self.process("download TCP %s" % file_name)
                    else:
                        pass
                else:
                    pass


# create server and client
server_thread = ServerThread()
client_thread = ClientThread()

# locks
locks = {}

def get_file_access(file):
    if file in locks:
        lock = locks[file]
    else:
        lock = threading.Lock()
        locks[file] = lock
    lock.acquire()

def leave_file_access(file):
    if file in locks:
        lock = locks[file]
        lock.release()
    else:
        print "Lock problem"
        sys.exit()


# if current thread is at end and server is still running then server will be terminated
# this is to ensure that when client exits or gets some error, then entire proccess (including server thread) should be terminated
server_thread.daemon = True


# start server and client
server_thread.start()
client_thread.start()


# wait for client to exit
client_thread.join()
#server_thread.join()

print "Exiting Here"
