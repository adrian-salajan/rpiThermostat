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
logging.basicConfig(filename='/home/pi/thermostat/server.log',level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)    

from sht1x.Sht1x import Sht1x as SHT1x
termo = SHT1x(dataPin, clkPin, SHT1x.GPIO_BOARD)




#temperature = sht1x.read_temperature_C()
#humidity = sht1x.read_humidity()
#dewPoint = sht1x.calculate_dew_point(temperature, humidity)

#bind the socket to a public host,
# and a well-known port
status = ''
statusEvent = threading.Event()

SAFETY_OFF_TIME = 60 * 32 #32minutes

def scheduleSafetyOff():
    statusEvent.set()
    safetyTimerOff = Timer(SAFETY_OFF_TIME, safetyTimer)
    safetyTimerOff.start()

def heaterOn():
    GPIO.setup(heaterPin, GPIO.OUT)
    GPIO.output(heaterPin, True)
    logger.info("set heater: ON")
    scheduleSafetyOff()
    

def safetyTimer():
    if (statusEvent.isSet()):
        heaterOff()

def heaterOff():
    GPIO.setup(heaterPin, GPIO.OUT)
    GPIO.output(heaterPin, False)
    logger.info("set heater: OFF")
    statusEvent.clear()
    
def controlTemp(stopEvent, desiredTemp=16):
    DELAY = 60
    heaterStatus = None
    temp = Decimal(desiredTemp)
    while (stopEvent.isSet() == False):
        currentTemp =  Decimal(termo.read_temperature_C())
        if (currentTemp < temp and heaterStatus != True):
            heaterOn()
            heaterStatus = True
        if (currentTemp > temp and heaterStatus != False):
            heaterOff()
            heaterStatus = False
        time.sleep(DELAY)
                

def startServer():
    #GPIO.setmode(GPIO.BOARD)
    try:
        GPIO.setup(heaterPin, GPIO.OUT)
        GPIO.output(heaterPin, False)
        logger.info("set heater default: OFF")
        status = 'OFF'
        server.bind(('localhost', 7777))
        server.listen(1);
    except Exception as e:
        logger.error("Exception on server init  " + str(e))
    
    while (True):
        try:
            (client, addr) = server.accept()
            temperature = str(termo.read_temperature_C())
            
            client.sendall(temperature)
            
            command = repr(client.recv(1024)).replace('\'', '')
            
            logger.info("got command: " + command) 
    
            if (str(command) == 'ON'):
                heaterOn()
                status = 'ON'
            elif (str(command) == 'OFF'):
                heaterOff()
                status = 'OFF'
                
            reply(client, temperature, status)
    
            client.close()
        except Exception as e:
            logger.error("Exception on client communication " + str(e))
            
def reply(client, temp, status):
    client.sendall(temp + '-' + status)
    

def main():
    s = threading.Timer(1, startServer)
    s.start()
    logger.info("SERVER START")
    return


if __name__ == "__main__":
    main()
    
    
    
    
