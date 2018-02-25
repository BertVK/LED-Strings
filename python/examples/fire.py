# Fire class for neopixel string
# Author: Bert Van Kets (bert@vankets.com)

from neopixel import *

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

        