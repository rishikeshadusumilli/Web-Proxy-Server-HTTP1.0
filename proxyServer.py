#!/bin/bash/env python3.5

import socket, threading, sys, hashlib, time
dataStorage={}
hrefs=[]

#######################################Pre-Fetch#######################################################################

def pre_fetch(lines, webserver, port, hash_key):
    pre_s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pre_s.connect((webserver, port))
    data1="GET "+lines+" HTTP/1.0"+"\n\n"
    data_pre=data1.encode()
    pre_s.sendall(data_pre)
    
    while 1:
        #print("<------------------------------Entered while loop of pre-fetch-------------------------------->")
        reply_pre=pre_s.recv(102400)
        #print("<------------------------------Received from pre-fetched server------------------------------->")
        if(len(reply_pre)>0):
            time_var=int(time.time())
            dataStorage[hash_key]=[reply_pre, time_var]
        else:
            print("<------------------------------Empty response received for pre-fetching----------------------->")
            break
    
    pre_s.close()

######################################################Link Pre-Fetching################################################

def extractHref(serverData, webserver, port, cconn, request):
    serverData1=serverData.decode()
    for lines in serverData1.splitlines():
        if("a href" in lines):
            abc=lines.split('a href="')[1]
            abcd=abc.split('"')[0]
            abcde=webserver+"/"+abcd
            hrefs.append(abcde)
    
    print("hrefs",hrefs)
    print("webserver:",webserver)
    for lines1 in hrefs:
        if "http://" not in lines1:
            lines="http://"+lines1
        
        #print("lines1:",lines)
        hash_key1=hashlib.sha256(lines.encode())
        hash_key=hash_key1.hexdigest()
        #print("<--------------------------------Prefetched hash", hash_key,"------------------------------------>")
        
        t1=threading.Thread(target=pre_fetch, args=(lines, webserver, port, hash_key))
        #print("<--------------------------------Thread "+t1.getName()+" started--------------------------------->")
        t1.start()
        #print("<--------------------------------Executed after calling thread----------------------------------->")

    print("<---------------------------------Completed for loop of pre-fetching----------------------------------------->")

########################################################Contact Server##################################################

def contactServer(caddr, cconn, pathRequest, webserver, request, port):
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(request)
        while 1:
            print("Web-Server waiting for input...")
            serverData=s.recv(65535)
            if(len(serverData)>0):
                dataStorage[pathRequest]=[serverData, int(time.time())]
                cconn.sendall(serverData)
                extractHref(serverData, webserver, port, cconn, request)
            else:
                print("Empty server data received")
                break

        s.close()
    except socket.error:
        s.close()
        cconn.close()
        quit()

##########################################################Thread Proxy###################################################        

def callThread(caddr, cconn, decodedRequest, request, timeLive):
    try:
        requestCommand=decodedRequest.splitlines()[0].split()[0] 
        if(requestCommand=="GET"):
            reqPath=decodedRequest.splitlines()[0].split()[1]
            #print("reqPath---->",reqPath)
            webserver=reqPath.split("/")[2]
            #print("webserver---->",webserver)
            hashValue=hashlib.sha256(reqPath.encode())
            pathRequest=hashValue.hexdigest()
        else:
            print("Methods other than GET encountered")
            return

        port=80

        if(pathRequest in dataStorage.keys()):
            currentTime=int(time.time())
            userInput=int(timeLive)
            storedTime=dataStorage[pathRequest][1]+userInput
            if(currentTime<storedTime):
                print("************************Data already stored in cache so sending data from proxy server***********************")
                cconn.send(dataStorage[pathRequest][0])
            else:
                print("**********************Cache expired and requesting server for data***********************")
                contactServer(caddr, cconn, pathRequest, webserver, request, port)
        else:
            print("******************************Data not present in cache and requesting server for data*****************************")
            contactServer(caddr, cconn, pathRequest, webserver, request, port)

    except Exception as e:
        print("Error received in parsing loop---->",e)

###################################################Command Arguments#####################################################

def progInputs():
    if(len(sys.argv)!=3):
        print("Enter port information and time for the cache to be active for the proxy server to start!!!")
        quit()
    else:
        return sys.argv[1], sys.argv[2]

########################################################MAIN FUNCTION#####################################################

if __name__ == '__main__':                                                      #Main function
    
    hostInfo=""
    portInfo1, timeLive=progInputs()
    portInfo=int(portInfo1)

    if(portInfo>1024):
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((hostInfo, portInfo))
        s.listen(10)
        try:    
            while 1:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Start of main loop for new accept connections and threads!!!!!!!!!!!!!!!!!!!")
                print("Serving HTTP proxy server on port: "+str(portInfo))
                print("Waiting to accept connection...")
                cconn, caddr=s.accept()
                request=cconn.recv(65535)
                if request:
                    decodedRequest=request.decode()
                    print("Request received from "+str(caddr[1]))
                    thread1=threading.Thread(target=callThread, args=(caddr, cconn, decodedRequest, request, timeLive, ))
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Thread "+thread1.getName()+" started on "+str(caddr[1])+"!!!!!!!!!!!!!!!!!!!")
                    thread1.start()
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Executed after calling thread.start()!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                else:
                    print(request)
                    print("#################Blank request received...#####################")

            print("********************************************Exitted out of main while loop************************************************")
            #s.close()
            #cconn.close()

        except KeyboardInterrupt:
            s.close()
            print("\nProxy server is exitting upon request of administrator, thank you running me !!!")
            quit()

        except Exception as e:
            print("Error received in main loop---->",e)
            s.close()
            quit()
    
    else:
        print("Enter only port numbers greater than 1024")
        quit()

