import RPi.GPIO as GPIO
from events import Events
import threading

class RotaryEncoder:
    def __init__(self):
        self.sw = 15
        self.clk = 16
        self.dt = 18
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.clk, GPIO.BOTH,
                              callback = self.wheelTurned,
                              bouncetime = 100)
        GPIO.add_event_detect(self.sw, GPIO.BOTH,
                              callback = self.buttonPress,
                              bouncetime = 100)
        self.event = Events(('rotate', 'release', 'press'))

    def add_rotate_callback(self, func):
        self.event.rotate += func

    def add_push_callback(self, func):
        self.event.press += func

    def add_release_callback(self, func):
        self.event.release += func

    def wheelTurned(self, channel):
        clkState = GPIO.input(self.clk)
        dtState = GPIO.input(self.dt)
        if clkState != dtState :
            counter = 1 if clkState >= dtState else -1
        else :
            counter = 1
        self.event.rotate(counter)

    def buttonPress(self, channel):
        print(channel)
        if  GPIO.input(channel):
            self.event.release()
        else:
            self.event.press()
