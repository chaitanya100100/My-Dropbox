import socket
import os
import sys
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
PROMPT_HEADER = ">>"
DOWNLOAD_INDICATOR = "DownLoadThisFile"


# functions

def handle_download(client_socket, tokens, chunk):
    chunk = chunk.replace(DOWNLOAD_INDICATOR, "")
    file = tokens[2]

    with open(file, 'wb') as f:
        f.write(chunk)
        while True:
            chunk = client_socket.recv(MAX_LENGTH)
            if not chunk:
                break
            f.write(chunk)
    f.close()


def handle_output(client_socket, data):
    while True:
        chunk = client_socket.recv(MAX_LENGTH)
        if not chunk:
            break
        data += chunk
    print data



def process(command):

    tokens = command.split()
    if not len(tokens):
        return

    # create client socket and connect
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((his_host, his_port))

    # send command to server and get response
    client_socket.send(json.dumps(tokens))
    data = client_socket.recv(MAX_LENGTH)

    # handle response
    if data.startswith(DOWNLOAD_INDICATOR):
        handle_download(client_socket, tokens, data)
    else:
        handle_output(client_socket, data)

    # close socket
    client_socket.close()
    return


print "current directory :", os.getcwd()

# terminal loop
while True:

    # get command
    try:
        command = raw_input(PROMPT_HEADER)
    except KeyboardInterrupt:
        print
        sys.exit()

    if not command.strip():
        continue

    # process command
    process(command)
