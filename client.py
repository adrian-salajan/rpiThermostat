#from sht1x.Sht1x import Sht1x as SHT1x
import time
import socket
from decimal import Decimal
from mod_python import util
import logging

time.sleep(2)
dataPin = 11
clkPin = 7
#termo = SHT1x(dataPin, clkPin, SHT1x.GPIO_BOARD)

import socket

logging.basicConfig(filename='/var/www/py/client.log',level=logging.DEBUG)


def handleReply(reply):
    parts = reply.split('-');
    d = dict()
    d['temp'] = parts[0]
    d['status'] = parts[1]
    return d


def index(req):
    HOST = 'localhost'    # The remote host
    PORT = 7777               # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    data = s.recv(1024)
    tempString = repr(data).replace('\'', '')
    tempDecimal = Decimal(tempString)
    command = ''
    
    desiredTemp = util.FieldStorage(req, keep_blank_values=1).getfirst("temp")
    
    if (desiredTemp):
        desiredTemp = Decimal(desiredTemp)
        if (tempDecimal < desiredTemp):
            s.sendall("ON")
        elif (tempDecimal > desiredTemp):
            s.sendall("OFF")
    else:
        s.sendall("do nothing")
        
    reply = repr(s.recv(1024)).replace('\'', '')
    replyMap = handleReply(reply)
    s.close()
    return "Temperature is " + replyMap['temp'] + "C. Status is:" + replyMap['status']
    
    
    
