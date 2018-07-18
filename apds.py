import operator
import threading
from apds9960.const import *
from apds9960 import APDS9960
import smbus
from time import sleep
from events import Events
import sys

class Apds():
    run = False
    apd_to_str = {
        APDS9960_DIR_NONE: "none",
        APDS9960_DIR_LEFT: "left",
        APDS9960_DIR_RIGHT: "right",
        APDS9960_DIR_UP: "up",
        APDS9960_DIR_DOWN: "down",
        APDS9960_DIR_NEAR: "near",
        APDS9960_DIR_FAR: "far",
    }
    str_to_apd = {
        "none" : APDS9960_DIR_NONE,
        "left" : APDS9960_DIR_LEFT,
        "right" : APDS9960_DIR_RIGHT,
        "up" : APDS9960_DIR_UP,
        "down" : APDS9960_DIR_DOWN,
        "near" : APDS9960_DIR_NEAR,
        "far" : APDS9960_DIR_FAR,
    }

    def __init__(self):
        bus = smbus.SMBus(1)
        self.apds = APDS9960(bus)
        self.apds.setProximityIntLowThreshold(50)
        self.apds.enableLightSensor()
        self.apds.enableGestureSensor()
        self.event = Events(('on_change', 'on_light_up', 'on_light_down', 'on_near', 'on_far'))
        maxInt = sys.maxsize
        minInt =- maxInt - 1
        self.light_up = maxInt
        self.light_down =  minInt
        self.far = maxInt
        self.near =  minInt

    def add_dir_callback(self, func):
        self.event.on_change += func
        return True

    def add_light_up_callback(self, func, value):
        self.event.on_light_up += func
        self.light_up = value
        return True

    def add_light_down_callback(self, func, value):
        self.event.on_light_down += func
        self.light_down = value
        return True

    def add_near_callback(self, func, value):
        self.event.on_near += func
        self.near = value
        return True

    def add_far_callback(self, func, value):
        self.event.on_far += func
        self.far = value
        return True

    def start(self):
        Apds.run = True
        self.t = threading.Thread(target=self.worker, args=())
        self.t.start()

    def getLight(self):
        return self.apds.readAmbientLight()

    def getProximity(self):
        return self.apds.readProximity()

    def worker(self):
        def test(v1, v2, beenSet,func,op):
            if op(v1, v2):
                if not beenSet:
                    func()
                return True
            return False
        b_light_up = False
        b_light_down = False
        b_far = False
        b_near =  False
        while Apds.run:
            sleep(0.5)
            light = self.getLight()
            proxi = self.getProximity()
            b_light_up = test(self.light_up, light, b_light_up, self.event.on_light_up, operator.lt)
            b_light_down = test(self.light_down, light, b_light_down, self.event.on_light_down, operator.gt)
            b_far = test(self.far, proxi, b_far, self.event.on_far, operator.gt)
            b_near = test(self.near, proxi, b_near, self.event.on_near, operator.lt)
            if self.apds.isGestureAvailable():
                motion = self.apds.readGesture()
                if motion in Apds.apd_to_str:
                    self.event.on_change(Apds.apd_to_str[motion])
