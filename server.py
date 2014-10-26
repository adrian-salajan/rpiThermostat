import time
import socket
import threading
import RPi.GPIO as GPIO 
import logging
from threading import Timer
from decimal import Decimal

time.sleep(2)
dataPin = 11
clkPin = 7
heaterPin = 13

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

logging.basicConfig(format='%(lineno)d %(asctime)s %(message)s', filename='/home/pi/thermostat/server.log',level=logging.DEBUG)
logger = logging.getLogger('thermoLog')
  

from Sensor import Sensor
termo = Sensor(dataPin, clkPin, Sensor.GPIO_BOARD)




#temperature = sht1x.read_temperature_C()
#humidity = sht1x.read_humidity()
#dewPoint = sht1x.calculate_dew_point(temperature, humidity)

#bind the socket to a public host,
# and a well-known port


#def scheduleSafetyOff():
#    HEATER.set()
#    safetyTimerOff = Timer(SAFETY_OFF_TIME, safetyTimer)
#    safetyTimerOff.start()
    
#def safetyTimer():
#    if (HEATER.isSet()):
#        heaterOff()

desiredTempGlobal = Decimal(0)

MIN_TEMPERATURE = Decimal(14)
MAX_TEMPERATURE = Decimal(22)
THRESHOLD = Decimal(0.2)

HEATER = threading.Event()

def heaterOn():
    GPIO.setup(heaterPin, GPIO.OUT)
    GPIO.output(heaterPin, True)
    logger.info("set heater: ON")
    HEATER.set()
    

def heaterOff():
    GPIO.setup(heaterPin, GPIO.OUT)
    GPIO.output(heaterPin, False)
    logger.info("set heater: OFF")
    HEATER.clear()
    
    
def controlTempThread(stopEvent, desiredTemp=16):
    DELAY = 30
    global desiredTempGlobal
    desiredTempGlobal = Decimal(desiredTemp)
    try:
        logger.info("new heatControlThread created..")
        while (stopEvent.isSet() == False):
            currentTemp =  Decimal(getTemp())
            logger.info("current temp is " +  str(currentTemp) + ", desired temp is " +  str(desiredTempGlobal))
            if (currentTemp < (desiredTempGlobal - THRESHOLD) and not HEATER.isSet()):
                heaterOn()
            if (currentTemp > (desiredTempGlobal + THRESHOLD) and HEATER.isSet()):
                heaterOff()
            time.sleep(DELAY)
    except Exception as e:
        logger.error("Exception in heatControlThread:  " + str(e))
                

def parseClientCommand(command):
    params = command.split('-')
    if (len(params) == 2):
        return ClientCommand(params[0], safeTemperature(params[1]))
    if (len(params) == 1):
        return ClientCommand(params[0], 16)


def safeTemperature(tempString):
    t = Decimal(tempString)
    if (t < MIN_TEMPERATURE):
        return MIN_TEMPERATURE
    if (MAX_TEMPERATURE < t):
        return MAX_TEMPERATURE
    return t
    

class ClientCommand:
    def __init__(self, command, temp):
        self.command = command
        self.temp = temp
        
    def __repr__(self):
        return "[" + str(self.command) + " " + str(self.temp) + "]"


def stopPreviousThread(heatControlThread, stopEvent, clientCommand):
    if (heatControlThread != None):
        logger.info("stopping old HeatControl")
        stopEvent.set()
        heatControlThread.join(60)
        if (heatControlThread.isAlive()):
            logger.info("could not stop in time HeatControl")



def startControlThread(clientCommand, stopEvent):
    stopEvent.clear()
    heatControlThread = threading.Thread(None, controlTempThread, "heatControlThread", (stopEvent, clientCommand.temp))
    heatControlThread.start()
    return heatControlThread

def startServer():
    #GPIO.setmode(GPIO.BOARD)
    try:
        GPIO.setup(heaterPin, GPIO.OUT)
        GPIO.output(heaterPin, False)
        logger.info("set heater default: OFF")
        server.bind(('localhost', 7777))
        server.listen(1);
    except Exception as e:
        logger.error("Exception on server init  " + str(e))
    
    heatControlThread = None
    stopEvent = threading.Event()
    
    while (True):
        try:
            heatControlThread = handleClientCommand(heatControlThread, stopEvent)
        except Exception as e:
            logger.error("Exception on client communication " + str(e))
            
def handleClientCommand(heatControlThread, stopEvent):
    (client, addr) = server.accept(
                                   )
    clientCommand = parseClientCommand(repr(client.recv(1024)).replace('\'', ''))
    
    if (clientCommand.command == "newHeatControl"):
        logger.info("got command newHeatControl")
        stopPreviousThread(heatControlThread, stopEvent, clientCommand)
        heatControlThread = startControlThread(clientCommand, stopEvent)
        
    if (clientCommand.command == "stop"):
        logger.info("got command stop")
        stopPreviousThread(heatControlThread, stopEvent, clientCommand)
        heatControlThread = None
        global desiredTempGlobal
        desiredTempGlobal = Decimal(0)
        heaterOff()
        
    if (clientCommand.command == "queryTemp"):
        logger.info("got command queryTemp")
        
    time.sleep(1)
    sendResponseToClient(client)
    
    return heatControlThread
            
def sendResponseToClient(client):
    temperature = str(getTemp())
    reply(client, temperature)
    client.close()         
          
          
def getTemp():
    return round(termo.read_temperature_C(), 1) #rounds to one decimal place 19.75 -> 19.8
  
def reply(client, temp):
    logger.info("reply to client")
    client.sendall(temp + '-' + str(desiredTempGlobal) + "-"  + getHeaterStatus())
    
def getHeaterStatus():
    if (HEATER.isSet()):
        return "ON"
    return "OFF"

def main():
    s = threading.Timer(1, startServer)
    s.start()
    logger.info("SERVER START")
    return


if __name__ == "__main__":
    main()
    
    
    
    

