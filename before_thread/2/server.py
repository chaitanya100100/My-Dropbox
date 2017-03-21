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


# initialize data
MAX_LENGTH = 1024
DOWNLOAD_INDICATOR = "DownLoadThisFile"



# Functions
# -----------------------------------------------

def send_string(client_socket, ret):
    data = json.dumps(ret)
    total_len = len(data)
    sent_len = 0
    while sent_len < total_len:
        sent = client_socket.send(data[sent_len:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        sent_len += sent


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# get datetime object from string
def get_dt(time_string):
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



# a function to handle index command
def command_index(client_socket, tokens):
    file_list = os.listdir(".")
    ret = []

    # index longlist
    if len(tokens)==1 or tokens[1] == "longlist":
        for file in file_list:
            ret.append({
                "name" : file,
                "size" : os.path.getsize(file),
                "timestamp" : datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
            })

    # index shortlist
    elif tokens[1] == "shortlist":

        if len(tokens) == 2:
            sti = datetime.datetime.now() - datetime.timedelta(days=1)
            eni = datetime.datetime.now()

        elif len(tokens) == 3:
            sti = get_dt(tokens[2])
            eni = datetime.datetime.now()

        else:
            sti = get_dt(tokens[2])
            eni = get_dt(tokens[3])

        for file in file_list:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            if mtime >= sti and mtime <= eni:
                ret.append({
                    "name" : file,
                    "size" : os.path.getsize(file),
                    "timestamp" : mtime.strftime('%Y-%m-%d %H:%M:%S')
                })

    # index invalid flag
    else:
        ret.append({
            "error" : "index : invalid flag"
        })

    send_string(client_socket, ret)
    return


# a function to handle hash command
def command_hash(client_socket, tokens):
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
            if not os.path.isfile(file):
                ret.append({
                    "error" : "hash verify : file doesn't exist"
                })
            else:
                ret.append({
                    "name" : file,
                    "md5" : md5(file),
                    "timestamp" : datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
                })


    # checkall
    elif tokens[1] == "checkall":
        file_list = os.listdir(".")
        for file in file_list:
            if os.path.isfile(file):
                ret.append({
                    "name" : file,
                    "md5" : md5(file),
                    "timestamp" : datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
                })

    # hash invalid args
    else:
        ret.append({
            "error" : "hash : invalid argument"
        })

    send_string(client_socket, ret)
    return



# a function to handle download
def command_download(client_socket, tokens):
    ret = []
    if len(tokens) < 2:
        ret.append({
            "error" : "download : argument not given"
        })

    # send file via TCP
    elif tokens[1] == "TCP":

        if len(tokens) < 3:
            ret.append({
                "error" : "download : filename not given"
            })
        else:
            file = tokens[2]
            if not os.path.isfile(file):
                ret.append({
                    "error" : "download : file doesn't exist"
                })
            else:
                f = open(file, 'rb')
                client_socket.send(DOWNLOAD_INDICATOR)

                chunk = f.read(MAX_LENGTH)
                while chunk:
                    client_socket.send(chunk)
                    # print "sent :", len(chunk)
                    chunk = f.read(MAX_LENGTH)
                f.close()
                return

    # download invalid argument
    else:
        ret.append({
            "error" : "download : invalid argument"
        })
    send_string(client_socket, ret)
    return


def process(client_socket, client_input):

    # split into tokens
    tokens = json.loads(client_input)

    if not len(tokens):
        client_socket.send("Give command")
    elif tokens[0] == "index":
        command_index(client_socket, tokens)
    elif tokens[0] == "hash":
        command_hash(client_socket, tokens)
    elif tokens[0] == "download":
        command_download(client_socket, tokens)
    else:
        client_socket.send("Invalid Input")


# create server socket and bind
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((my_host, my_port))
server_socket.listen(5)

print "\nserver listening at", my_host, my_port
print "\ncurrent directory :", os.getcwd()
print

try:
    # server loop
    while True:

        # accept connection
        try:
            client_socket, client_addr = server_socket.accept()
        except KeyboardInterrupt:
            break
        print "get connection from", client_addr

        # get data
        client_input = client_socket.recv(MAX_LENGTH)

        # process data
        try:
            process(client_socket, client_input)
        except Exception as e:
            print str(e)

        # close connection
        client_socket.close()
        print


except Exception as e:
    print str(e)

print
print "server closing from", my_host, my_port
server_socket.close()
