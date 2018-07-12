import RPi.GPIO as GPIO
from rotary import RotaryEncoder
from mpu import Mpu
from apds import Apds
import paho.mqtt.client as mqtt
import json
import signal
import sys
import time

BROKER_ADDRESS = "raspi-mika.local"
siteId = 'default'
haveBeenMoved = False
hotwordSended = False
volume = 0
client =  mqtt.Client()
asrStart = "hermes/asr/startListening"
asrStop = "hermes/asr/stopListening"

mpu = Mpu()
apds = Apds()

def main():
    rotary = RotaryEncoder()
    rotary.add_rotate_callback(volumeCallback)
    rotary.add_push_callback(buttonPushCallback)
    rotary.add_release_callback(buttonPushCallback)
    mpu.add_callback(objectMoveCallback)
    mpu.start()
    apds.add_dir_callback(moveFingerCallback)
    apds.start()
    signal.signal(signal.SIGINT, sig_handler)
    client.connect(BROKER_ADDRESS)
    client.on_connect = on_connect
    client.message_callback_add(asrStart, on_startListening)
    client.message_callback_add(asrStop, on_stopListening)
    client.loop_start()
    while(True):
        time.sleep(0.2)

def sig_handler(sig, frame):
    client.disconnect()
    mpu.stop()
    Apds.run =False
    GPIO.cleanup()
    sys.exit(0)

def on_connect(client, userdata, flags, rc):
    print('connected')
    client.subscribe("hermes/asr/stopListening")

def on_startListening(client, userdata, message):
    global pub_payload
    msg = json.loads(message.payload.decode("utf-8","ignore"))
    if(msg['siteId'] != siteId):
        return
    client.unsubscribe("hermes/asr/startListening")
    pub_payload = '{"siteId":"remote","sessionId":%s}' % msg['sessionId']

def on_stopListening(client, userdata, message):
    global hotwordSended
    msg = json.loads(message.payload.decode("utf-8","ignore"))
    if(msg['siteId'] != siteId):
        return
    hotwordSended = False

def sendHotword():
    global hotwordSended
    hotwordSended = True
    client.subscribe("hermes/asr/startListening")
    client.publish("hermes/hotword/default/detected",
                   '{"siteId":"%s","modelId":"default"}' % siteId)

def sendStopHotword():
    global hotwordSended
    hotwordSended = False
    client.publish("hermes/asr/stopListening",  pub_payload)

def volumeCallback(degree):
    global volume
    volume += degree
    print("volume: {}".format(volume))
    client.publish("concierge/commands/volume", volume)

def buttonPushCallback():
    print("button press")
    sendHotword()

def buttonReleaseCallback():
    print("button release")
    sendStopHotword()

def moveFingerCallback(direction):
    print("direction: {}".format(direction))

def objectMoveCallback():
    global haveBeenMoved
    haveBeenMoved = True
    print("haveBeenMoved")


if __name__ == "__main__":
    main()
