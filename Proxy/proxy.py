import socket
import threading
from thread import *
import sys
import httplib
import time
import base64
import os
import csv

HOST_NAME = "127.0.0.1"
BIND_PORT = 20100
MAX_REQUEST_LEN = 4096
CONNECTION_TIMEOUT = 5
CACHE = {}
REQUESTS_COUNT = {}
REQUESTS_STIME = {}
REQUESTS_ETIME = {}
USERSFILE = open("users.csv", "r")
USERS = csv.reader(USERSFILE)
CANACCESS = False
AUTHUSERS = []
for row in USERS :
    AUTHUSERS.append(base64.b64encode(row[0]+":"+row[1]))
USERSFILE.close()
BLACKFILE = open('blacklist.txt', 'r')
BLACKLIST = BLACKFILE.readlines()
BLACKFILE.close()
BLACKLIST = [x.strip('\n') for x in BLACKLIST]

class ProxyServer:
    def __init__(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # Create a TCP socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Re-use the socket
        self.serverSocket.bind((HOST_NAME, BIND_PORT)) # bind the socket to a public host, and a port
        self.serverSocket.listen(10)    # become a server socket

    def listenToClient(self):
        while True:
            clientSocketInfo = self.serverSocket.accept()   # Establish the connection
            start_new_thread(self.proxy, clientSocketInfo)

    def proxy(self, conn, clientAddress):
        request = conn.recv(MAX_REQUEST_LEN)        # get the request from browser
        requestLine1 = request.split('\n')[0]                   # parse the first line
        requestType = requestLine1.split(' ')[0]
        url = requestLine1.split(' ')[1]                        # get url
        requestLine3 = request.split('\n')[2]
        authentication = requestLine3.replace("Authorization: Basic","").strip()
        if authentication in AUTHUSERS :
            CANACCESS = True
        url = url.strip()
        http = True
        if "https" in url:
        	http = False

        slashPos = url.find("//")          # find pos of //
        if (slashPos != -1):
            url = url[slashPos+2:]       # get the rest of url

        portPos = url.find(":")           # find the port pos (if any)
        host = url[:portPos]

        portEndPos = url.find("/")
        hostPort = int(url[portPos+1 : portEndPos])
        file = url[portEndPos :]

        if url in REQUESTS_COUNT :
            REQUESTS_COUNT [url] += 1
            REQUESTS_ETIME [url] = time.time()
        else :
            REQUESTS_COUNT [url] = 1
            REQUESTS_STIME [url] = time.time()

        domain = "%s:%s" % (host, hostPort)
        try:
            blocked = False
            if domain in BLACKLIST and not CANACCESS :
                print "Your request %s was blocked" %domain
                blocked = True
            
            if http :
                s = httplib.HTTPConnection(host, hostPort)
            else :
                s = httplib.HTTPSConnection(host, hostPort)
            
            if blocked :
                conn.send("%s has been blacklisted\n" % domain)
                conn.close()
                s.close()
            elif domain in BLACKLIST and CANACCESS:
            	   print "Request to "+domain+" is blacklisted but you are authorized to access it"

            s.putrequest(requestType, file)
            if url in CACHE :
                s.putheader("If-Modified-Since", time.strftime("%a %b %d %H:%M:%S %Z %Y", time.localtime(REQUESTS_ETIME [url])))
            
            s.putheader("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)")
            s.endheaders()

            serverResponse = s.getresponse()
            status = serverResponse.status
            if status == 304 :
                conn.send(CACHE [url])
                s.close()
                conn.close()

            headers = serverResponse.getheaders()
            data = serverResponse.read()          # receive data from web server

            if url in REQUESTS_COUNT and url not in CACHE and len(CACHE) <= 3 :
                if REQUESTS_COUNT [url] >= 2 and (REQUESTS_ETIME [url] - REQUESTS_STIME [url] <= 300) :
            	      REQUESTS_STIME [url] = REQUESTS_ETIME [url]
            	      REQUESTS_ETIME [url] = time.time()
            	      CACHE [url] = data
            elif url in REQUESTS_COUNT and url not in CACHE and len(CACHE) > 3 :
            	   maxTime = 0
            	   for key,value in REQUESTS_ETIME :
            	       if value >= maxTime :
            	           maxURL = key
            	   del CACHE [maxURL]
            	   
            	   if REQUESTS_COUNT [url] >= 2 and (REQUESTS_ETIME [url] - REQUESTS_STIME [url] <= 300) :
            	       REQUESTS_STIME [url] = REQUESTS_ETIME [url]
            	       REQUESTS_ETIME [url] = time.time()
            	       CACHE [url] = data

            if (data) :
                conn.send(data+"\n")                               # send to browser
            else :
                conn.send("No data returned from the server\n")
            s.close()
            conn.close()
        except socket.error as error_msg:
            if s :
                s.close()
            if conn :
                conn.close()

proxyserver = ProxyServer()
proxyserver.listenToClient()