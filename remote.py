from concierge_python.concierge import Concierge
import RPi.GPIO as GPIO
from rotary import RotaryEncoder
from mpu import Mpu
from apds import Apds
import json
import signal
import sys
import threading
import time

class Remote():
    MOVE_COUNTER = 5
    ROTARY_COUNTER = 4
    asrStart = "hermes/asr/startListening"
    asrStop = "hermes/asr/stopListening"

    def _init_rotary(self):
        self.rotary = RotaryEncoder()
        self.rotary.add_rotate_callback(self.on_rotary)
        self.rotary.add_push_callback(self.on_press)
        self.rotary.add_release_callback(self.on_release)
    def _init_apds(self):
        self.apds = Apds()
        self.apds.add_dir_callback(self.on_swipe)
        self.apds.add_light_up_callback(self.on_lup, 1000)
        self.apds.add_light_down_callback(self.on_ldown, 300)
        self.apds.add_near_callback(self.on_near, 40)
        self.apds.add_far_callback(self.on_far, 17)
        self.apds.start()
    def _init_mpu(self):
        self.mpu = Mpu()
        self.mpu.add_callback(self.on_move)
        self.mpu.start()

    def __init__(self, siteId, concierge):
        self.siteId = siteId
        self.haveBeenMoved = -1
        self.rotarySet = -1
        self.hotwordSended = False
        self.bPressed = False
        self.sessionId = None
        self.c = concierge
        self.c.subscribe(Remote.asrStart, self.on_startListening)
        self.c.subscribe(Remote.asrStop, self.on_stopListening)
        self._init_mpu()
        self._init_apds()
        self._init_rotary()
        self.run = True

    def start(self):
        self.run = True
        self.t = threading.Thread(target=self.worker, args=())
        self.t.start()

    def worker(self):
        while(self.run):
            if(self.rotarySet > 0):
                self.rotarySet -= 1
                self.haveBeenMoved = -1
            if (self.bPressed or self.hotwordSended):
                self.haveBeenMoved = -1
            if (self.haveBeenMoved == 0):
                self.sendHotword()
                self.haveBeenMoved = -1
            if (self.haveBeenMoved > 0):
                self.haveBeenMoved -= 1
            time.sleep(0.2)

    def stop(self):
        self.run = False
        self.mpu.stop()
        Apds.run =False

    def on_startListening(self, client, userdata, message):
        if not self.hotwordSended:
            return
        msg = json.loads(message.payload.decode("utf-8","ignore"))
        if(msg['siteId'] != self.siteId):
            return
        self.sessionId = msg['sessionId']

    def on_stopListening(self, client, userdata, message):
        if not self.hotwordSended:
            return
        msg = json.loads(message.payload.decode("utf-8","ignore"))
        if(msg['siteId'] != self.siteId):
            return
        self.hotwordSended = False
        self.sessionId = None

    def sendHotword(self):
        self.hotwordSended = True
        self.c.startHotword()

    def sendStopHotword(self):
        self.hotwordSended = False
        self.c.stopHotword()

    def on_rotary(self, degree):
        if (self.bPressed):
            return
        self.rotarySet = Remote.ROTARY_COUNTER
        self.c.publishRotary(degree)

    def on_press(self):
        print("button press")
        self.bPressed =True
        self.sendHotword()

    def on_release(self):
        if(not self.bPressed or self.sessionId is None):
            return
        print("button release")
        self.sendStopHotword()
        self.sessionId = None
        self.bPressed = False

    def on_swipe(self, direction):
        print("direction: {}".format(direction))
        self.c.publishSwipe(direction)

    def on_move(self):
        if (not self.bPressed and self.rotarySet <= 0):
            self.haveBeenMoved = Remote.MOVE_COUNTER
            print("haveBeenMoved")

    def on_lup(self):
        print("lup")

    def on_ldown(self):
        print("ldown")

    def on_near(self):
        print("near")

    def on_far(self):
        print("far")

if __name__ == "__main__":
    def sig_handler(sig, frame):
        c.disconnect()
        a.stop()
        sys.exit(0)
    MQTT_IP_ADDR = "raspi-mika.local"
    signal.signal(signal.SIGINT, sig_handler)
    c = Concierge(MQTT_IP_ADDR, "default", False)
    a = Remote("default", c)
    a.start()
    c.loop_forever()
