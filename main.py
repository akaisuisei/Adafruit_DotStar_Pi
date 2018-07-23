from concierge_python.concierge import Concierge
import RPi.GPIO as GPIO
from rotary import RotaryEncoder
from mpu import Mpu
from apds import Apds
import json
import signal
import sys
import time

MOVE_COUNTER = 5
VOLUME_COUNTER = 4
BROKER_ADDRESS = "raspi-mika.local"
siteId = 'default'
haveBeenMoved = -1
volumeBeenSet = -1
hotwordSended = False
bPressed = False
c =  Concierge(siteId)
asrStart = "hermes/asr/startListening"
asrStop = "hermes/asr/stopListening"
pub_payload = None
mpu = Mpu()
apds = Apds()

def lup():
    print("lup")
def ldown():
    print("ldown")

def near():
    print("near")
def far():
    print("far")

def main():
    global haveBeenMoved, volumeBeenSet
    rotary = RotaryEncoder()
    rotary.add_rotate_callback(volumeCallback)
    rotary.add_push_callback(buttonPushCallback)
    rotary.add_release_callback(buttonReleaseCallback)
    mpu.add_callback(objectMoveCallback)
    mpu.start()
    apds.add_dir_callback(moveFingerCallback)
    apds.add_light_up_callback(lup, 1000)
    apds.add_light_down_callback(ldown, 300)
    apds.add_near_callback(near, 40)
    apds.add_far_callback(far, 17)
    apds.start()
    signal.signal(signal.SIGINT, sig_handler)
    c.subscribe(asrStart, on_startListening)
    c.subscride(asrStop, on_stopListening)
    while(True):
        if(volumeBeenSet > 0):
            volumeBeenSet -= 1
            haveBeenMoved = -1
        if (bPressed or hotwordSended):
            haveBeenMoved = -1
        if (haveBeenMoved == 0):
            sendHotword()
            haveBeenMoved = -1
        if(haveBeenMoved > 0):
            haveBeenMoved -= 1
        time.sleep(0.2)

def sig_handler(sig, frame):
    c.disconnect()
    mpu.stop()
    Apds.run =False
    GPIO.cleanup()
    sys.exit(0)

def on_startListening(client, userdata, message):
    global sessionId
    if not hotwordSended:
        return
    msg = json.loads(message.payload.decode("utf-8","ignore"))
    if(msg['siteId'] != siteId):
        return
    sessionId = msg['sessionId']

def on_stopListening(client, userdata, message):
    global hotwordSended, sessionId
    if not hotwordSended:
        return
    msg = json.loads(message.payload.decode("utf-8","ignore"))
    if(msg['siteId'] != siteId):
        return
    hotwordSended = False
    sessionId = False

def sendHotword():
    global hotwordSended
    hotwordSended = True
    c.startHotword()

def sendStopHotword():
    global hotwordSended
    hotwordSended = False
    c.stopHotword()

def volumeCallback(degree):
    global volumeBeenSet
    if (bPressed):
        return
    volumeBeenSet = VOLUME_COUNTER
    c.publishRotary(degree)

def buttonPushCallback():
    global bPressed
    print("button press")
    bPressed =True
    sendHotword()

def buttonReleaseCallback():
    global bPressed, sessionId
    if(not bPressed or sessionId is None):
        return
    print("button release")
    sendStopHotword(sessionId)
    sessionId = None
    bPressed = False

def moveFingerCallback(direction):
    print("direction: {}".format(direction))
    c.publishSwipe(direction)

def objectMoveCallback():
    global haveBeenMoved
    if (not bPressed and volumeBeenSet <= 0):
        haveBeenMoved = MOVE_COUNTER
        print("haveBeenMoved")


if __name__ == "__main__":
    main()
