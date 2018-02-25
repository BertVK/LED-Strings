from flask import Flask, jsonify, render_template, request
from flask_bootstrap import Bootstrap
import threading
from neopixel import *
from gpiozero import CPUTemperature
import random
import time
import RPi.GPIO as GPIO
import os.path
import sys

# LED strip configuration:
LED_COUNT      = 900     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
BLINGDELAY     = 10      # Set number of cycles before a white "bling" LED is shown
CYCLECOUNTER   = 0
COOLING        = 30
SPARKING       = 75
FLAMELENGTH    = 150
STATE          = 4
MAXSTATE       = 18
STATELIST      = ['' for i in range(MAXSTATE + 1)]
BRIGHTNESS     = 0
TEMP           = -20.0
RANDOMON       = False
randomTimer    = 60

# 0.0.0.0 is listining on all ports
hostIP = "0.0.0.0"
hostPort = 80
app = Flask(__name__)
Bootstrap(app)
app.debug = False
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

states = []
states.append('Off')
states.append('Green Wipe')
states.append('Red wipe')
states.append('Blue wipe')
states.append('Yellow wipe')
states.append('Breathing Green')
states.append('Breathing Red')
states.append('Breathing Blue')
states.append('Breathing Yellow')
states.append('Green Theater Chase')
states.append('Red Theater Chase')
states.append('Blue Theater Chase')
states.append('Yellow Theater Chase')
states.append('Breathing Rainbow')
states.append('Cycle Ranbow')
states.append('Rainbow Theater Chase')
states.append('Fire')
states.append('Frietjes')
states.append('Kerst')

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

def StringToBytes(val):
    retVal = []
    for c in val:
        retVal.append(int(ord(c)))
    return retVal

def buttonStateUp (pin):
    global STATE
    STATE += 1
    if STATE > MAXSTATE:
        STATE = 0
    message = 's=%d\n'%(STATE)
    print message
    
def buttonStateDown (pin):
    global STATE
    STATE -= 1
    if STATE < 0:
        STATE = MAXSTATE
    message = 's=%d\n'%(STATE)
    print message

def buttonBrightnessUp (pin):
    global LED_BRIGHTNESS
    if LED_BRIGHTNESS < 10:
        LED_BRIGHTNESS += 1
    else:
        LED_BRIGHTNESS += int(LED_BRIGHTNESS / 10)
    if LED_BRIGHTNESS > 255:
        LED_BRIGHTNESS = 255
    message = 'b=%d\n'%(LED_BRIGHTNESS)
    print message
    
def buttonBrightnessDown (pin):
    global LED_BRIGHTNESS
    LED_BRIGHTNESS -= int(LED_BRIGHTNESS / 10)
    if LED_BRIGHTNESS < 10:
        LED_BRIGHTNESS -= 1
    if LED_BRIGHTNESS < 0:
        LED_BRIGHTNESS = 0
    message = 'b=%d\n'%(LED_BRIGHTNESS)
    print message
    
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

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, state, maxBrightness, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels() / 2):
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.setPixelColor(i, color)
        strip.setPixelColor(strip.numPixels() - i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
        if (STATE != state):
            break
    for i in range(strip.numPixels() / 2):
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.setPixelColor(strip.numPixels() - i, Color(0, 0, 0))
        strip.show()
        time.sleep(wait_ms / 1000.0)
        if (STATE != state):
            off(strip)
            break

def theaterChase(strip, color, state, maxBrightness, wait_ms=50):
    """Movie theater light style chaser animation."""
    for q in range(3):
        for i in range(0, strip.numPixels() / 2, 3):
            strip.setPixelColor(i + q, color)
            strip.setPixelColor(strip.numPixels() - (i + q), color)
            if (STATE != state):
                break
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.show()
        time.sleep(wait_ms / 1000.0)
        for i in range(0, strip.numPixels() / 2, 3):
            strip.setPixelColor(i + q, 0)
            strip.setPixelColor(strip.numPixels() - (i + q), 0)
            if (STATE != state):
                break
        if (STATE != state):
            off(strip)
            break

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbowCycle(strip, state, maxBrightness, wait_ms=20, bling=True):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for i in range(255):
        for j in range(strip.numPixels()):
            color = ((j * 255) / 300) + i
            while color > 255:
                color -= 255
            strip.setPixelColor(j, wheel(color))
            if (STATE != state):
                break
        if bling:
            global CYCLECOUNTER
            CYCLECOUNTER = CYCLECOUNTER + 1
            if CYCLECOUNTER > BLINGDELAY:
                CYCLECOUNTER = 1
            if CYCLECOUNTER == BLINGDELAY:
                strip.setPixelColor(random.randint(0, strip.numPixels()), Color(255, 255, 255))
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.show()
        if (STATE != state):
            off(strip)
            break
        time.sleep(wait_ms / 1000.0)

def theaterChaseRainbow(strip, state, maxBrightness, wait_ms=50, bling=True):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
                if (STATE != state):
                    break
            if (STATE != state):
                break
            if bling:
                global CYCLECOUNTER
                CYCLECOUNTER = CYCLECOUNTER + 1
                if CYCLECOUNTER > BLINGDELAY:
                    CYCLECOUNTER = 1
                if CYCLECOUNTER == BLINGDELAY:
                    strip.setPixelColor(random.randint(0, strip.numPixels()), Color(255, 255, 255))
            brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
            strip.setBrightness(brightness)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)
        if (STATE != state):
            off(strip)
            break
def breathingColor(strip, color, state, maxBrightness, wait_ms=25):
    global BRIGHTNESS
    direction = 1
    step = 1
    minBreath = 8
    maxBreath = 128
    
    if BRIGHTNESS < minBreath:
        BRIGHTNESS = minBreath
    for j in range(256):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, color)
            if (STATE != state):
                break
        BRIGHTNESS = BRIGHTNESS + (direction * step)
        if BRIGHTNESS >= maxBreath or BRIGHTNESS < minBreath:
            direction = direction * -1
        #adjust brightness to maxBrightness
        brightness = int((BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        if (STATE != state):
            off(strip)
            break
        strip.show()
        time.sleep(wait_ms / 1000.0)

def breathingRainbow(strip, state, maxBrightness, wait_ms=50):
    """Draw rainbow that fades across all pixels at once."""
    global BRIGHTNESS
    direction = 1
    step = 1
    minBreath = 8
    maxBreath = maxBrightness
	
    if BRIGHTNESS < minBreath:
        BRIGHTNESS = minBreath
    for j in range(256):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
            if (STATE != state):
                break
        BRIGHTNESS = BRIGHTNESS + (direction * step)
        if BRIGHTNESS >= maxBreath or BRIGHTNESS < minBreath:
            direction = direction * -1
        strip.setBrightness(BRIGHTNESS)
        if (STATE != state):
            off(strip)
            break
        strip.show()
        time.sleep(wait_ms / 1000.0)

def clearStrip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
        
def off(strip):
    clearStrip(strip)
    strip.show()
    time.sleep(0.2)

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

@attrs (heat=[FirePixel(0) for i in range(FLAMELENGTH)])
def fire(strip, state, maxBrightness):
    #step 1 - cool down every piwel
    for i in range(len(fire.heat)):
        fire.heat[i].coolDown(COOLING, len(fire.heat))
        if (STATE != state):
            break
    
    #step 2 - average out colors
    for i in range(len(fire.heat) - 1, 2, -1):
        fire.heat[i].average(fire.heat[i - 1], fire.heat[i - 2])
        if (STATE != state):
            break
    
    #step 3 - ramdomly ignite new sparks near the bottom
    if random.randint(0, 256) < SPARKING:
        y = random.randint(0, 7)
        fire.heat[y].setColor(random.randint(100,255))
        
    #step 4 - convert heat to colors and send to string
    for j in range(len(fire.heat)):
        pixelColor = fire.heat[j].getHeatColor()
        strip.setPixelColor(j, pixelColor)
        strip.setPixelColor(strip.numPixels() - j, pixelColor)
        if LED_COUNT > 300:
            strip.setPixelColor(j + 300, pixelColor)
            strip.setPixelColor(strip.numPixels() - 300 - j, pixelColor)
        if LED_COUNT > 600:
            strip.setPixelColor(j + 600, pixelColor)
            strip.setPixelColor(strip.numPixels() - 600 - j, pixelColor)
        if (STATE != state):
            off(strip)
            break
    brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
    strip.setBrightness(brightness)
    strip.show()
    time.sleep(0.01)
    
def setBrightness(strip):
    strip.setBrightness(LED_BRIGHTNESS)

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

def frietjes(strip, state, maxBrightness):
    minWidth = 40
    maxWidth = 120
    minSpeed = 2
    maxSpeed = 30
    start = [random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16]
    width = [random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth),random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth)]
    speed = [random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed)]
    pos = [start[0], start[1], start[2], start[3], start[4], start[5], start[6], start[7]]
    randomRed = 20
    randomGreen = 10
    randomBlue = 5
    colorR = [0,0,0,0,0,0,0,0]
    colorG = [0,0,0,0,0,0,0,0]
    colorB = [0,0,0,0,0,0,0,0]
    for i in range(8):
        colorR[i] = 235 + random.randint(0 - randomRed, randomRed)
        colorG[i] = 130 + random.randint(0 - randomGreen, randomGreen)
        colorB[i] = 5 + random.randint(0 - randomBlue, randomBlue)
    
    brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
    strip.setBrightness(brightness)
    virtLED_COUNT = LED_COUNT * 16
    while True:
        clearStrip(strip)
        for i in range(8):
            pos[i] += speed[i]
            if pos[i] + (width[i] * 16) > virtLED_COUNT:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            if pos[i] < 0:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            drawFractionalBar(strip, pos[i], width[i], colorG[i], colorR[i], colorB[i])
            if (STATE != state):
                break
        if (STATE != state):
            off(strip)
            break
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.show()
        time.sleep(0.05)

def kerst1(strip, state, maxBrightness):
    minWidth = 40
    maxWidth = 120
    minSpeed = 2
    maxSpeed = 30
    start = [random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16, random.randint(maxWidth, LED_COUNT - maxWidth) * 16]
    width = [random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth),random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth), random.randint(minWidth, maxWidth)]
    speed = [random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed), random.randint(minSpeed, maxSpeed)]
    pos = [start[0], start[1], start[2], start[3], start[4], start[5], start[6], start[7]]
    randomRed = 20
    randomGreen = 5
    randomBlue = 5
    colorR = [0,0,0,0,0,0,0,0]
    colorG = [0,0,0,0,0,0,0,0]
    colorB = [0,0,0,0,0,0,0,0]
    for i in range(4):
        colorR[i] = 235 + random.randint(0 - randomRed, randomRed)
        colorG[i] = 5 + random.randint(0 - randomGreen, randomGreen)
        colorB[i] = 5 + random.randint(0 - randomBlue, randomBlue)
    randomRed = 5
    randomGreen = 20
    for i in range(4):
        colorR[i + 4] = 5 + random.randint(0 - randomRed, randomRed)
        colorG[i + 4] = 235 + random.randint(0 - randomGreen, randomGreen)
        colorB[i + 4] = 5 + random.randint(0 - randomBlue, randomBlue)
    
    brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
    strip.setBrightness(brightness)
    virtLED_COUNT = LED_COUNT * 16
    while True:
        clearStrip(strip)
        for i in range(8):
            pos[i] += speed[i]
            if pos[i] + (width[i] * 16) > virtLED_COUNT:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            if pos[i] < 0:
                speed[i] = speed[i] * -1
                pos[i] += 2 * speed[i]
            drawFractionalBar(strip, pos[i], width[i], colorG[i], colorR[i], colorB[i])
            if (STATE != state):
                break
        if (STATE != state):
            off(strip)
            break
        brightness = int((LED_BRIGHTNESS * maxBrightness) / 255)
        strip.setBrightness(brightness)
        strip.show()
        time.sleep(0.05)
        
def randomOn():
    global STATE
    if RANDOMON:
        newState = random.randint(1, MAXSTATE)
        while newState == STATE:
            newState = random.randint(1, MAXSTATE)
        STATE = newState
        message = 'random state=%d\n'%(STATE)
        print message
        threading.Timer(randomTimer, randomOn).start()

def flaskThread():
    app.run(host=hostIP,port=hostPort)
    
@app.route("/", methods=['GET','POST'])
def root():
    global TEMP
    buttonNr = request.args.get('button', default = 0, type = int)
    if buttonNr == 1:
        buttonStateUp(0)
    if buttonNr == 2:
        buttonStateDown(0)
    if buttonNr == 3:
        buttonBrightnessUp(0)
    if buttonNr == 4:
        buttonBrightnessDown(0)
    if buttonNr == 5:
        buttonSave(0)
    cpu = CPUTemperature()
    TEMP = cpu.temperature
    return render_template('index.html', title='LED Controller', temp=round(TEMP,2), state=STATE, stateDescr=states[STATE], brightness=LED_BRIGHTNESS, randomOn=RANDOMON)

@app.route('/_get_temp')
def get_temp():
    cpu = CPUTemperature()
    return jsonify(temp=round(cpu.temperature,2))

@app.route('/button1')
def set_stateUp():
    buttonStateUp(0)
    return jsonify(state=STATE, stateDescr=states[STATE])

@app.route('/button2')
def set_stateDown():
    buttonStateDown(0)
    return jsonify(state=STATE, stateDescr=states[STATE])

@app.route('/brightness')
def set_brightness():
    global LED_BRIGHTNESS
    b = request.args.get('brightness', LED_BRIGHTNESS, type=int)
    LED_BRIGHTNESS = b
    message = 'b=%d\n'%(LED_BRIGHTNESS)
    print message
    return jsonify(brightness=LED_BRIGHTNESS)

@app.route('/randomOn')
def set_randomOn():
    global RANDOMON
    r = request.args.get('randomOn', RANDOMON, type=int)
    if r == 1:
        RANDOMON = True
    else:
        RANDOMON = False
    message = "randomOn=%d\n"%(RANDOMON)
    print message
    return jsonify(randomOn=RANDOMON)

# Main program logic follows:
if __name__ == '__main__':
    thread = threading.Thread(target=flaskThread)
    thread.start()
     
    #Start neopixel setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    #App running indication
    GPIO.setup(4, GPIO.OUT)
    
    #light green LED to show the app has started
    GPIO.output(4,True)
    
    
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    loadConfig()
    
    try:
        print ('Press Ctrl-C to quit.')
        while True:
            while STATE == 0:
                off(strip)
            # Color wipe animations.
            while STATE == 1:
                colorWipe(strip, Color(255, 0, 0), STATE, 128)  # green wipe
                setBrightness(strip)
            while STATE == 2:
                colorWipe(strip, Color(0, 255, 0), STATE, 128)  # red wipe
                setBrightness(strip)
            while STATE == 3:
                colorWipe(strip, Color(0, 0, 255), STATE, 128)  # blue wipe
                setBrightness(strip)
            while STATE == 4:
                colorWipe(strip, Color(255, 255, 0), STATE, 60)  # yellow wipe
                setBrightness(strip)
            #breathing colors
            while STATE == 5:
                breathingColor(strip, Color(255, 0, 0), STATE, 255) #green
                setBrightness(strip)
            while STATE == 6:
                breathingColor(strip, Color(0, 255, 0), STATE, 255) #red
                setBrightness(strip)
            while STATE == 7:
                breathingColor(strip, Color(0, 0, 255), STATE, 255) #blue
                setBrightness(strip)
            while STATE == 8:
                breathingColor(strip, Color(180, 255, 10), STATE, 100) #yellow
                setBrightness(strip)
            # Theater chase animations.
            while STATE == 9:
                theaterChase(strip, Color(255,   0,   0), STATE, 255)  # Green theater chase
                setBrightness(strip)
            while STATE == 10:
                theaterChase(strip, Color(0,   255,   0), STATE, 255)  # Red theater chase
                setBrightness(strip)
            while STATE == 11:
                theaterChase(strip, Color(  0,   0, 255), STATE, 255)  # Blue theater chase
                setBrightness(strip)
            while STATE == 12:
                theaterChase(strip, Color(255, 255, 0), STATE, 255)  # yellow theater chase
                setBrightness(strip)
            # Rainbow animations.
            while STATE == 13:
                breathingRainbow(strip, STATE, 128, 20)
            while STATE == 14:
                rainbowCycle(strip, STATE, 128, 20, True)
                setBrightness(strip)
            while STATE == 15:
                theaterChaseRainbow(strip, STATE, 255, 50, True)
                setBrightness(strip)
            #other animations
            while STATE == 16:
                fire(strip, STATE, 180)
                setBrightness(strip)
            while STATE == 17:
                frietjes(strip, STATE, 150)
            #kerst
            while STATE == 18:
		kerst1(strip, STATE, 150)

    finally:
        print "cleaning up GPIO prior to exit"
        GPIO.cleanup()
        print "killing threads"
        thread.join()
