import socket
from threading import Thread
from tkinter import *
from tkinter import ttk
import ntpath 
from ftplib import FTP
import ftplib
from tkinter import filedialog
from pathlib import Path
import os

PORT  = 8080
IP_ADDRESS = '127.0.0.1'
SERVER = None
BUFFER_SIZE = 4096
name = None
listbox = None
textarea = None
labelchat = None
textmsg = None
filepathlabel = None
sendingfile = None
downloadingfile = None
filetodownload = None

def connectToServer():
    global SERVER, name

    name1 = name.get()
    SERVER.send(name1.encode())

def receiveMessage():
    global SERVER, BUFFER_SIZE

    while True:
        chunk = SERVER.recv(BUFFER_SIZE)

        try:
            if 'first' in chunk.decode() and '1.0,' not in chunk.decode():
                l1 = chunk.decode().split(',')
                listbox.insert(l1[0], l1[0] + ':' + l1[1] + ':'+ l1[3] + ' ' + l1[5])
                print(l1[0], l1[0] + ':' + l1[1] + ':'+ l1[3] + ' ' + l1[5])
            elif chunk.decode() == "Access Granted":
                labelchat.configure(text = "")
                textarea.insert(END, chunk.decode('ascii'))
                textarea.see('end')
            elif chunk.decode() == "Access Declined":
                labelchat.configure(text = "")
                textarea.insert(END, chunk.decode('ascii'))
                textarea.see('end')
            elif "download?" in chunk.decode():
                downloadingfile = chunk.decode('ascii').split(' ')[4].strip()
                BUFFER_SIZE = int(chunk.decode('ascii').split(' ')[8])
                textarea.insert(END, chunk.decode("ascii"))
                print(chunk.decode("ascii"))
            elif "Download:" in chunk.decode():
                getfilename = chunk.decode().split(':')
                filetodownload = getfilename[1]
            else:
                textarea.insert(END, '\n' + chunk.decode('ascii'))
                textarea.see('end')
                print(chunk.decode('ascii'))
        except:
            pass

def showClientList():
    global listbox, SERVER

    listbox.delete(0, 'end')
    SERVER.send('showlist'.encode('ascii'))

def connectWithClient():
    global SERVER, listbox

    text = listbox.get(ANCHOR)
    listitem = text.split(':')
    message = 'connect ' + listitem[1]
    print(message)
    SERVER.send(message.encode('ascii'))

def disconnectWithClient():
    global SERVER, listbox

    text = listbox.get(ANCHOR)
    listitem = text.split(':')
    message = 'disconnect ' + listitem[1]
    SERVER.send(message.encode('ascii'))

def getfilesize(filename):
    with open(filename, 'rb') as f:
        chunk = f.read()
        return len(chunk)

def browseFiles():
    global filepathlabel, textarea

    try:
        filename = filedialog.askopenfilename()
        filepathlabel.configure(text = filename)
        hostname = '127.0.0.1'
        username = 'abcd'
        pw = '1234'

        ftpserver = FTP(hostname, username, pw)
        ftpserver.encoding = 'utf-8'
        ftpserver.cwd('shared_files')

        fname = ntpath.basename(filename)

        with open(filename, 'rb') as file:
            ftpserver.storbinary(f'stor {fname}', file)
        
        ftpserver.dir()
        ftpserver.quit()
        msg = "send" + fname

        if msg[:4] == "send":
            print('Please wait.')
            textarea.insert(END, 'Please wait.')
            textarea.see('end')

            sendingfile = msg[5:]
            filesize = getfilesize('shared_files/' + sendingfile)
            finalmsg = msg + ' ' + str(filesize)
            SERVER.send(finalmsg.encode())
            textarea.insert(END, 'in process')

    except FileNotFoundError: 
        print('Cancel button pressed.')

def sendMessage():
    global SERVER, textarea, textmsg

    msg = textmsg.get()
    SERVER.send(msg.encode('ascii'))

    textarea.insert(END, '\n' + 'You: ' + msg)
    textarea.see('end')
    textmsg.delete(0, 'end')

    if msg == 'y' or msg == "Y":
        print('Please wait, file is downloading')
        textarea.insert(END, 'Please wait, file is downloading')
        hostname = '127.0.0.1'
        username = 'abcd'
        pw = '1234'
        home = str(Path.home())
        downloadpath = home + '/Downloads'
        ftpserver = ftplib.FTP(hostname, username, pw)
        ftpserver.encoding = 'utf-8'
        ftpserver.cwd('shared_files')
        fname = filetodownload
        localfilename = os.path.join(downloadpath, fname)
        file = open(localfilename, 'wb')
        ftpserver.retrbinary('retr' + fname, file.write)
        ftpserver.dir()
        file.close()
        ftpserver.quit()
        print('File successfully downloaded to path' + downloadpath)
        textarea.insert(END, 'File successfully downloaded to path' + downloadpath)
        textarea.see('end')


def openChatWindow():
    global name, listbox, textarea, labelchat, textmsg, filepathlabel

    window = Tk()
    window.title('Messenger')
    window.geometry('500x350')

    namelabel = Label(window, text = 'Enter Your Name', font = ('Calibri', 10))
    namelabel.place(x = 10, y = 8)

    name = Entry(window, width = 30, font = ('Calibri', 10))
    name.place(x = 120, y = 8)
    name.focus()

    connectserver = Button(window, text = 'Connect to Chat Server', font = ('Calibri', 10), command = connectToServer)
    connectserver.place(x = 350, y = 6)

    separator = ttk.Separator(window, orient = 'horizontal')
    separator.place(x = 0, y = 35, relwidth = 1, height = 0.1)

    userlabel = Label(window, text = 'Active Users', font = ('Calibri', 10))
    userlabel.place(x = 10, y = 50)

    listbox = Listbox(window, height = 5, width = 67, font = ('Calibri', 10))
    listbox.place(x = 10, y = 70)

    scroll1 = Scrollbar(listbox)
    scroll1.place(relheight = 1, relx = 1)
    scroll1.config(command = listbox.yview)

    connectbutton = Button(window, text = 'Connect', font = ('Calibri', 10), command = connectWithClient)
    connectbutton.place(x = 282, y = 160)

    disconnectbutton = Button(window, text = 'Disconnect', font = ('Calibri', 10), command = disconnectWithClient)
    disconnectbutton.place(x = 350, y = 160)

    refreshbutton = Button(window, text = 'Refresh', font = ('Calibri', 10), command = showClientList)
    refreshbutton.place(x = 435, y = 160)

    chatlabel = Label(window, text = "Chat Window", font = ('Calibri', 10))
    chatlabel.place(x = 10, y = 180)

    textarea = Text(window, width = 67, height = 6, font = ('Calibri', 10))
    textarea.place(x = 10, y = 200)

    scroll2 = Scrollbar(textarea)
    scroll2.place(relheight = 1, relx = 1)
    scroll2.config(command = textarea.yview)

    attach = Button(window, text = "Attach & Send", font = ("Calibri", 10), command = browseFiles)
    attach.place(x = 10, y = 305)

    textmsg = Entry(window, width = 43, font = ('Calibri', 12))
    textmsg.place(x = 98, y = 306)

    sendbutton = Button(window, text = 'Send', font = ('Calibri', 10), command = sendMessage)
    sendbutton.place(x = 450, y = 305)

    filepathlabel = Label(window, text = "", fg = 'blue', font = ("Calibri", 8))
    filepathlabel.place(x = 10, y = 330)

    window.resizable(False, False)
    window.mainloop()

def setup():
    global SERVER
    global PORT
    global IP_ADDRESS

    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.connect((IP_ADDRESS, PORT))

    thread1 = Thread(target = receiveMessage)
    thread1.start()

    openChatWindow()

setup()