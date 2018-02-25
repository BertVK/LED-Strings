from neopixel import *
import random
import time
import RPi.GPIO as GPIO
import os.path
import sys

STATE          = 0
MAXSTATE       = 2

 # LED strip configuration:
LED_COUNT      = 300     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 127     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
BLINGDELAY     = 10      # Set number of cycles before a white "bling" LED is shown
CYCLECOUNTER   = 0
COOLING        = 30
SPARKING       = 75
FLAMELENGTH    = 150
BRIGHTNESS     = 0

class FirePixel:
    
    def __init__(self, colorPart=0, intensityPart=255):
        self.color = colorPart
        self.intensity = intensityPart
        
    def getColor(self):
        return self.color
    
    def setColor(self, colorPart, intensityPart=255):
        self.color = colorPart
        self.intensity = intensityPart
        
    def coolDown(self, cooling, num_leds):
        maxCooling = ((cooling * 10) / num_leds) + 2
        self.color = self.color - random.randint(0, maxCooling)
        if self.color < 0:
            self.color = 0
        
    def average(self, pixel1, pixel2):
        self.color = (pixel1.color + pixel2.color + pixel2.color) / 3
        
    def getHeatColor(self):
        if self.color == 0:
            return Color(0,0,0)
        t192 = (self.color * 192) / 255
        heatramp = t192 & 0x3F
        heatramp = heatramp * 4
        if t192 > 127:
            return Color(255, 255, heatramp)
        elif t192 > 63:
            return Color(heatramp, 255, 0)
        else:
            return Color(0, heatramp, 0)
    
    
def attrs (** kwds):
    ''' taken from PEP 318 '''
    def decorate (f):
        for k in kwds:
            setattr (f, k, kwds [k])
        return f
    return decorate

def buttonStateUp (pin):
    global STATE
    STATE += 1
    if STATE > MAXSTATE:
        STATE = 0
    print "STATE = " + str(STATE)
    
def buttonStateDown (pin):
    global STATE
    STATE -= 1
    if STATE < 0:
        STATE = MAXSTATE
    print "STATE = " + str(STATE)

def buttonBrightnessUp (pin):
    global LED_BRIGHTNESS
    if LED_BRIGHTNESS < 10:
        LED_BRIGHTNESS += 1
    else:
        LED_BRIGHTNESS += int(LED_BRIGHTNESS / 10)
    if LED_BRIGHTNESS > 255:
        LED_BRIGHTNESS = 255
    print "LED_BRIGHTNESS = " + str(LED_BRIGHTNESS)
    
def buttonBrightnessDown (pin):
    global LED_BRIGHTNESS
    LED_BRIGHTNESS -= int(LED_BRIGHTNESS / 10)
    if LED_BRIGHTNESS < 10:
        LED_BRIGHTNESS -= 1
    if LED_BRIGHTNESS < 0:
        LED_BRIGHTNESS = 0
    print "LED_BRIGHTNESS = " + str(LED_BRIGHTNESS)
    
def buttonSave(pin):
    try: 
        file = open("config.txt","w")
        file.write("state=" + str(STATE) + "\n")
        file.write("brightness=" + str(LED_BRIGHTNESS) + "\n")
        file.close()
        print "data saved to disk"
    except:
        e = sys.exc_info()[0]
        print "failed to save data to disk"
        print "Error: " + str(e)

def loadConfig():
    global STATE
    global LED_BRIGHTNESS
    tmpState = 0
    tmpBrightness = 0
    try:
        if os.path.isfile("config.txt"):
            file = open("config.txt","r")
            for line in file:
                parts = line.split("=",2)
                if parts[0] == "state":
                    tmpState = int(parts[1])
                    print "state loaded : " + str(tmpState)
                if parts[0] == "brightness":
                    tmpBrightness = int(parts[1])
                    print "brightness loaded : " + str(tmpBrightness)
            file.close()
    except:
        e = sys.exc_info()[0]
        print "failed to load data from disk"
        print "Error: " + str(e)
    if tmpBrightness != 0:
        STATE = tmpState
        LED_BRIGHTNESS = tmpBrightness

def clearStrip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
        
def setBrightness(strip):
    strip.setBrightness(LED_BRIGHTNESS)
    
def off(strip):
    clearStrip(strip)
    strip.show()
    time.sleep(0.2)        

def drawFractionalBar(strip, pos16, width, red, green, blue):
    i = pos16 / 16 #get pixel position
    frac = pos16 & 0x0F;
    firstpixelbrightness = 255 -(frac * 16)
    lastpixelbrightness = 255 - firstpixelbrightness
    brightness = 0
    for n in range(width):
        if n == 0:
            brightness = firstpixelbrightness
        elif n == (width - 1):
            brightness = lastpixelbrightness
        else:
            brightness = 255
        if i < LED_COUNT:
            strip.setPixelColorRGB(i, int((red * brightness) / 255), int((green * brightness) / 255), int((blue * brightness) / 255))
        i += 1
        if i == LED_COUNT:
            i = 0

'''
def heatColor(color):
    if color == 0:
        return Color(0,0,0)
    t192 = (color * 192) / 255
    heatramp = t192 & 0x3F
    heatramp = heatramp * 4
    #print heatramp
    if t192 > 127:
        return Color(255, 255, heatramp)
    elif t192 > 63:
        return Color(heatramp, 255, 0)
    else:
        return Color(0, heatramp, 0)
'''
            
@attrs (heat=[FirePixel(0) for i in range(FLAMELENGTH)])
def fire(strip, state):
    for i in range(len(fire.heat)):
        fire.heat[i].coolDown(COOLING, len(fire.heat))
        if (STATE != state):
            break
    for i in range(len(fire.heat) - 1, 2, -1):
        fire.heat[i].average(fire.heat[i - 1], fire.heat[i - 2])
        if (STATE != state):
            break
    #step 3 - ramdomly ignite new sparks near the bottom
    if random.randint(0, 256) < SPARKING:
        y = random.randint(0, 7)
        fire.heat[y].setColor(random.randint(100,255))
    for j in range(len(fire.heat)):
        pixelColor = fire.heat[j].getHeatColor()
        strip.setPixelColor(j, pixelColor)
        strip.setPixelColor(strip.numPixels() - j, pixelColor)
        if LED_COUNT > 300:
            strip.setPixelColor(j + 300, pixelColor)
            strip.setPixelColor(j + 600, pixelColor)
            strip.setPixelColor(strip.numPixels() - 300 - j, pixelColor)
            strip.setPixelColor(strip.numPixels() - 600 - j, pixelColor)
        if (STATE != state):
            off(strip)
            break
    setBrightness(strip)
    strip.show()
    time.sleep(0.01)

def frietjes(strip, state):
    #print "frietjes started"
    minWidth = 5
    maxWidth = 30
    minSpeed = 5
    maxSpeed = 20
    start = [random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16]
    width = [random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth)]
    speed = [random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed)]
    pos = [start[0], start[1], start[2], start[3]]
    colorR = [255, 200, 255, 128]
    colorG = [255, 255, 200, 128]
    colorB = [ 10,  10,  10,  10]
    strip.setBrightness(255)
    virtLED_COUNT = LED_COUNT * 16
    while True:
        clearStrip(strip)
        for i in range(4):
            pos[i] += speed[i]
            if pos[i] + (width[i] * 16) > virtLED_COUNT:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            if pos[i] < 0:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            drawFractionalBar(strip, pos[i], width[i], colorR[i], colorG[i], colorB[i])
            if (STATE != state):
                break
        if (STATE != state):
            off(strip)
            break
        strip.show()
        time.sleep(0.05)
        
# Main program logic follows:
if __name__ == '__main__':
    
    #Start neopixel setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    #brightness up - orange
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #brightness down - blue
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #state up - 
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #state down
    GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #save
    GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #App running indication
    GPIO.setup(4, GPIO.OUT)
    
    #hook up events
    GPIO.add_event_detect(17, GPIO.FALLING, callback=buttonStateUp, bouncetime=300)
    GPIO.add_event_detect(27, GPIO.FALLING, callback=buttonStateDown, bouncetime=300)
    GPIO.add_event_detect(22, GPIO.FALLING, callback=buttonBrightnessUp, bouncetime=300)
    GPIO.add_event_detect(25, GPIO.FALLING, callback=buttonBrightnessDown, bouncetime=300)
    GPIO.add_event_detect(24, GPIO.FALLING, callback=buttonSave, bouncetime=1000)
    
    #light green LED to show the app has started
    GPIO.output(4,True)
    
    
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    loadConfig()
    
    #fillStateList()

    print ('Press Ctrl-C to quit.')
    while True:
        while STATE == 0:
            off(strip)
        # Color wipe animations.
        while STATE == 1:
            fire(strip, STATE)
            setBrightness(strip)
        while STATE == 2:
            frietjes(strip, STATE)

    print "cleaning up GPIO prior to exit"
    GPIO.cleanup()