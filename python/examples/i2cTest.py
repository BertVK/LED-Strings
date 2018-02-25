import smbus
import time
# for RPI version 1, use "bus = smbus.SMBus(0)"
bus = smbus.SMBus(1)

# This is the address we setup in the Arduino Program
address = 0x04

def StringToBytes(val):
    retVal = []
    for c in val:
        retVal.append(int(ord(c)))
    return retVal

def sendMessage(message):
    valMessage = StringToBytes(message)
    print "valMessage = " + str(valMessage)
    print "address = " + str(address)
    bus.write_i2c_block_data(address, int(ord("W")), valMessage)
    
'''
def writeNumber(value):
    bus.write_byte(address, value)
    # bus.write_byte_data(address, 0, value)
    return -1

def readNumber():
    message = bus.read_byte(address)
    # number = bus.read_byte_data(address, 1)
    return message
'''

while True:
    message = raw_input("Enter message: ")
    if not message:
        continue

    sendMessage(message)
    print "RPI: Hi Arduino, I sent you : ", message
    #clear message
    message = ""
    # sleep one second
    time.sleep(1)

    '''
    message = readNumber()
    print "Arduino: Hey RPI, I received a message : ", message
    print
    '''