#!/usr/bin/env python

import time
import serial

ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

#ser.open()
#ser.isOpen()
ser.write('s=0\n')
time.sleep(1)
ser.write('s=1\n')
time.sleep(1)
ser.write('s=2\n')
time.sleep(1)
ser.write('s=3\n')
time.sleep(1)
ser.write('s=4\n')
time.sleep(1)
ser.write('s=5\n')
time.sleep(1)
ser.write('s=6\n')
time.sleep(1)
ser.write('s=7\n')
time.sleep(1)
ser.write('s=8\n')
time.sleep(1)
ser.write('s=9\n')
time.sleep(1)
ser.write('s=10\n')
time.sleep(1)
ser.write('s=0\n')
time.sleep(5)
ser.write('b=0\n')
time.sleep(1)
ser.write('b=5\n')
time.sleep(1)
ser.write('b=10\n')
time.sleep(1)
ser.write('b=20\n')
time.sleep(1)
ser.write('b=50\n')
time.sleep(1)
ser.write('b=128\n')
time.sleep(1)
ser.write('b=200\n')
time.sleep(1)
ser.write('b=255\n')
time.sleep(1)
ser.write('t=21.5\n')
time.sleep(1)
ser.write('t=22.0\n')
time.sleep(1)
ser.write('t=22.5\n')
time.sleep(1)
ser.write('t=23.5\n')
time.sleep(1)
