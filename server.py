import socket
import os
import sys
import datetime
import hashlib

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
def command_index(tokens):
    file_list = os.listdir(".")
    ret = "\n"
    if not len(file_list):
        return ret
    ret = "name\tsize\ttimestamp\n"

    # index longlist
    if len(tokens)==1 or tokens[1] == "longlist":
        for file in file_list:
            ret += "%s\t%s\t%s\n" % (
                    file,
                    str(os.path.getsize(file)),
                    datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
                )
        return ret

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
                ret += "%s %s %s\n" % (
                        file,
                        str(os.path.getsize(file)),
                        mtime.strftime('%Y-%m-%d %H:%M:%S')
                    )
        return ret

    # index invalid flag
    else:
        return "\nInvalid args in index\n"


# a function to handle hash command
def command_hash(tokens):
    ret = "\n"
    if len(tokens) < 2:
        return "\nProvide args\n"

    # verify
    elif tokens[1] == "verify":
        if len(tokens) < 3:
            return "\nGive filename\n"
        file = tokens[2]
        if not os.path.isfile(file):
            return "\nFile doesn't exist : %s\n" % file
        ret += "%s\n%s\n%s\n" % (
                file,
                md5(file),
                datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
            )
        return ret

    # checkall
    elif tokens[1] == "checkall":
        file_list = os.listdir(".")
        for file in file_list:
            if os.path.isfile(file):
                ret += "%s\n%s\n%s\n\n" % (
                        file,
                        md5(file),
                        datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
                    )
        return ret

    # hash invalid args
    else:
        return "\nInvalid args in hash\n"

# a function to handle download
def command_download(tokens, client_socket):
    ret = "\n"
    if len(tokens) < 2:
        return "\nProvide args\n"
    elif tokens[1] == "TCP":
        if len(tokens) < 3:
            return "\nGive filename\n"
        file = tokens[2]
        if not os.path.isfile(file):
            return "\nFile doesn't exist : %s\n" % file

        f = open(file, 'rb')
        client_socket.send(DOWNLOAD_INDICATOR)

        chunk = f.read(MAX_LENGTH)
        while chunk:
            client_socket.send(chunk)
            # print "sent :", len(chunk)
            chunk = f.read(MAX_LENGTH)
        f.close()
        return ""
    else:
        return "\nInvalid args in download\n"


def process(client_socket, command):

    # split into tokens
    tokens = command.split()
    ret = "\n"
    print tokens

    if not len(tokens):
        return ret
    elif tokens[0] == "index":
        return command_index(tokens)
    elif tokens[0] == "hash":
        return command_hash(tokens)
    elif tokens[0] == "download":
        return command_download(tokens, client_socket)
    else:
        return "Invalid command\n"


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
            client_output = process(client_socket, client_input)
        except Exception as e:
            print str(e)
            client_output = "Error occurred\n"

        # send data
        client_socket.send(client_output)

        # close connection
        client_socket.close()
        print


except Exception as e:
    print str(e)

print
print "server closing from", my_host, my_port
server_socket.close()
