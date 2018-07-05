#!/usr/bin/env python2
# -*-: coding utf-8 -*-

from hermes_python.hermes import Hermes
import hermes_python
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

MQTT_IP_ADDR = "ledtest.local"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
client = None
pingTopic = 'concierge/apps/live/ping'

def dialogue_open(hermes, intent_message):
    hermes.skill.hotword_detected()

def dialogue_close(hermes, intent_message):
    hermes.skill.stop()

def on_connect(client, userdata, flags, rc):
        client.subscribe(pingTopic)

def on_message(client, userdata, msg):
    client.publish('concierge/apps/live/pong', '{"result":"snips-skill-matrix"}')

if __name__ == "__main__":
    skill = SnipsMatrix()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_IP_ADDR)
    client.loop_start()
    with Hermes(MQTT_ADDR) as h:
        h.skill = skill
        h.subscribe_session_started(self.action_session_started) \
        .subscribe_session_ended(self.action_session_ended) \
        .loop_forever()
