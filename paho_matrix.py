#!/usr/bin/env python2
# -*-: coding utf-8 -*-

import calendar
import json
import os
import time
import threading
from crontab import CronTab
from datetime import datetime
import requests
import paho.mqtt.client as mqtt
from snipsmatrix import SnipsMatrix

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
client = None
pingTopic = 'concierge/apps/live/ping'
dial_open = 'hermes/dialogueManager/sessionStarted'
dial_close = 'hermes/dialogueManager/sessionEnded'
skill = SnipsMatrix()
def dialogue_open(client, userdata, msg):
    print("toto")
    skill.hotword_detected()

def dialogue_close(client, userdata, msg):

    skill.stop()

def on_connect(client, userdata, flags, rc):
        client.subscribe(pingTopic)
        client.subscribe(dial_open)
        client.subscribe(dial_close)

def on_message(client, userdata, msg):
    client.publish('concierge/apps/live/pong', '{"result":"snips-skill-matrix"}')

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_IP_ADDR)
    client.message_callback_add(pingTopic, on_message)
    client.message_callback_add(dial_open, dialogue_open)
    client.message_callback_add(dial_close, dialogue_close)
    client.loop_forever()
