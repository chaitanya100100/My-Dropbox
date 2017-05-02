# My Dropbox
A client-server pipeline implemented with python socket programming to serve basic file sharing functionality with automatic syncing.

## Description
- There are three parts of the project
	- ![1_before_thread](/1_before_thread) , in which one box can run server and other client. Client can ask for any service via command line interface and it is served by the server on the other side.
	- ![2_with_thread](/2_with_thread) , in which each box can run server and client simulteneously via threads. So both the boxes can ask services to one another via command line.
	- ![3_with_sync](/3_with_sync) , in which both the boxes run the code in background and sync the directory to each other after some specific time interval.

## Features
- There are several command line commands implemented. See ![here](/problem_statement.pdf) for full description of commands.
	- `index longlist` : to list files residing on the other side, along with their details
	- `index shortlist` : to list files residing on the other side, between two specific timestamps
	- `index regex` : to list files residing on the other side, matching some patterns in their names
	- `hash verify` : get the hash of specific file residing on the other side
	- `hash checkall` : get the hash of all files residing on the other side
	- `download UDP` : UDP download of specific file until full file is downloaded without error
	- `download TCP` : TCP download of specific file

- See ![here](/problem_statement.pdf) for full description of commands.
- Mutex locks on each file separately to ensure integrity of the file transfer
- Automatic syncing

## How to run
- Needed python libraries :
	- time
	- glob
	- mimetypes
	- threading
	- socket
	- os
	- sys
	- datetime
	- hashlib
	- json
- First part i.e. 1_before_thread, can run a client in one directory and a server in other directory. Initiating bash scripts for server and client are there.
- Second and third part have both the sides technically similar so the same code should reside on both the sides. `main.py` has that code. `update.sh` is to copy the main code to both the boxes. Each box has Initiating bash scripts.
- First and second part will show the server and client output on the prompt whereas third will run on the background.
