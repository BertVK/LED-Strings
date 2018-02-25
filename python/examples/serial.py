import serial

ser = serial.Serial(
    port='/dev/ttyUSB1',
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBIT_ONE,
    bytesize=serial.SEVENBITS
)

ser.open()
ser.isOpen()