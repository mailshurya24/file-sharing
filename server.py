import socket
from  threading import Thread
import time
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

IP_ADDRESS = '127.0.0.1'
PORT = 8080
SERVER = None
BUFFER_SIZE = 4096
clients = {}

def handleShowList(client):
    global clients

    counter = 0

    for c in clients:
        counter += 1
        clientaddr = clients[c]['addr'][0]
        connectedwith = clients[c]['connectedwith']
        msg = ''

        if connectedwith:
            msg = f'{counter},{c},{clientaddr}, connected with {connectedwith}, first, \n'
        else:
            msg = f'{counter},{c},{clientaddr}, Available, first, \n'
        client.send(msg.encode())
        time.sleep(1)

def connectClient(msg, client, clientname):
    global clients

    enteredClientName = msg[8:].strip()

    if enteredClientName in clients:
        if not clients[clientname]['connectedwith']:
            clients[enteredClientName]['connectedwith'] = clientname
            clients[clientname]['connectedwith'] = enteredClientName
            clientsocket = clients[enteredClientName]['client']
            m1 = f'Hello, {enteredClientName}, {clientname} connected with you'
            clientsocket.send(m1.encode())
            message = f'You are successfully connected with {enteredClientName}'
            client.send(message.encode())
        else:
            otherClient = clients[clientname]['connectedwith']
            msg = f'You are already connected with {otherClient}'
            client.send(msg.encode())

def disconnectClient(msg, client, clientname):
    global clients

    enteredClientName = msg[11:].strip()

    if enteredClientName in clients:
        clients[enteredClientName]['connectedwith'] = ''
        clients[clientname]['connectedwith'] = ''
        clientsocket = clients[enteredClientName]['client']
        m1 = f'Hello, {enteredClientName}, you are succesfully disconnected with {clientname}'
        clientsocket.send(m1.encode())
        message = f'You are successfully disconnected with {enteredClientName}'
        client.send(message.encode())

def sendTextMessage(clientname, msg):
    global clients

    otherClient = clients[clientname]['connectedwith']
    clientSocket = clients[otherClient]['client']
    message = clientname + ": " + msg
    clientSocket.send(message.encode())

def handleErrorMessage(client):
    global clients

    msg = '''
    You need to connect with one of the clients first before sending any message.
    Click on Refresh to see all available users.
'''
    client.send(msg.encode())

def handleSendFile(clientname, filename, filesize):
    global clients

    clients[clientname]['filename'] = filename
    clients[clientname]['filesize'] = filesize

    otherclient = clients[clientname]['connectedwith']
    clientSocket = clients[otherclient]['client']

    msg = f'\n{clientname} wants to send {filename} file with size {filesize} bytes, do you want to download? y/n'
    clientSocket.send(msg.encode())
    msgdown = f'Download: {filename}'
    clientSocket.send(msgdown.encode())

def grantAccess(clientname):
    global clients

    otherclient = clients[clientname]['connectedwith']
    clientSocket = clients[otherclient]['client']
    msg = "Access Granted"
    clientSocket.send(msg.encode())

def declineAccess(clientname):
    global clients

    otherclient = clients[clientname]['connectedwith']
    clientSocket = clients[otherclient]['client']
    msg = "Access Declined"
    clientSocket.send(msg.encode())


def handleMessage(client, msg, clientname):
    if msg == 'showlist':
        handleShowList(client)
    elif msg[:7] == 'connect':
        connectClient(msg, client, clientname)
    elif msg[:10] == 'disconnect':
        disconnectClient(msg, client, clientname)
    elif msg[:4] == "send":
        filename = msg.split(' ')[1]
        filesize = int(msg.split(' ')[2])
        handleSendFile(clientname, filename, filesize)
        print(clientname + " " + filename + " " + filesize)
    elif msg == "y" or msg == 'Y':
        grantAccess(clientname)
    elif msg == "n" or msg == "N":
        declineAccess(clientname)
    else:
        connected = clients[clientname]['connectedwith']
        if connected:
            sendTextMessage(clientname, msg)
        else:
            handleErrorMessage(client)

def removeClient(clientname):
    try: 
        if clientname in clients:
            del clients[clientname]
    except KeyError: pass

def handleClient(client, clientname):
    global clients, SERVER, BUFFER_SIZE

    banner1 = 'Welcome! You are now connected to the server\nClick on Refresh to see all available users\nSelect the user and click on Connect to start chatting'
    
    client.send(banner1.encode())

    while True:
        try:
            BUFFER_SIZE = clients[clientname]['filesize']
            chunk = client.recv(BUFFER_SIZE)
            msg = chunk.decode().strip().lower()

            if msg:
                handleMessage(client, msg, clientname)
            else:
                removeClient(clientname)
        except: 
            pass

def acceptConnections():
    global SERVER
    global clients

    while True:
        client, addr = SERVER.accept()
        clientname = client.recv(4096).decode().lower()
        clients[clientname] = {
            'client': client,
            'addr': addr,
            'connectedwith': '',
            'filename': '',
            'filesize': 4096
        }
        print(f'Connection established with {clientname}:{addr}')

        thread1 = Thread(target = handleClient, args = (client, clientname))
        thread1.start()

def setup():
    print("\n\t\t\t\t\t\tIP MESSENGER\n")

    global PORT
    global IP_ADDRESS
    global SERVER

    SERVER  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((IP_ADDRESS, PORT))
    SERVER.listen(100)

    print("\t\t\t\tSERVER IS WAITING FOR INCOMING CONNECTIONS...")
    print("\n")

    acceptConnections()

def ftp():
    global IP_ADDRESS

    authorizer = DummyAuthorizer()
    authorizer.add_user('abcd', '1234', '.', perm = 'elradfmw')
    
    handler = FTPHandler
    handler.authorizer = authorizer

    ftpserver = FTPServer((IP_ADDRESS, 21), handler)
    ftpserver.serve_forever()

setup_thread = Thread(target = setup)           
setup_thread.start()

ftpthread = Thread(target = ftp)
ftpthread.start()