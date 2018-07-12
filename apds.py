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
        self.apds.enableGestureSensor()
        self.event_dir = Events()

    def add_dir_callback(self, func):
        self.event_dir.on_change += func
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
        while Apds.run:
            sleep(0.5)
            if self.apds.isGestureAvailable():
                motion = self.apds.readGesture()
                if motion in Apds.apd_to_str:
                    self.event_dir.on_change(Apds.apd_to_str[motion])
