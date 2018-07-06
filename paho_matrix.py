#!/usr/bin/env python2
# -*-: coding utf-8 -*-

import calendar
import json
import os
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from snipsmatrix import SnipsMatrix
import json

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "ledtest.local"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
client = None
siteid = "default"
skill_name = "snips-skill-matrix"
pingTopic = 'concierge/apps/live/ping'
dial_open = 'hermes/dialogueManager/sessionStarted'
dial_close = 'hermes/dialogueManager/sessionEnded'
show_hour = 'concierge/feedback/led/{}/hour'.format(site_id)
show_animation = 'concierge/feedback/led/{}/animation'.format(site_id)
show_timer = 'concierge/feedback/led/{}/timer'.format(site_id)
stop_display = 'concierge/feedback/led/{}/stop'.format(site_id)
add_image = 'concierge/feedback/led/{}/add/#'.format(site_id)
skill = SnipsMatrix()

def dialogue_open(client, userdata, msg):
    skill.hotword_detected()

def dialogue_close(client, userdata, msg):
    skill.stop()

def display_stop(client, userdata, msg):
    skill.stop()

def save_image(client, userdata, msg):
    tmp = msg.slit('/')
    name = tmp [-1]
    directory = tmp[-2]
    image = msg.payload
    skill.save(name, directory, image)

def display_time(client, userdata, msg):
    data = json.loads(msg.payload)
    duration = data['duration']
    skill.show_time(duration)

def display_animation(client, userdata, msg):
    data = json.loads(msg.payload)
    animation = data['animation']
    duration = data['duration']
    skill.show_animation(animation, duration)

def display_timer(client, userdata, msg):
    data = json.loads(msg.payload)
    duration = data['duration']
    skill.show_timer(duration)

def on_connect(client, userdata, flags, rc):
        client.subscribe(pingTopic)
        client.subscribe(dial_open)
        client.subscribe(dial_close)
        client.subscribe(show_hour)
        client.subscribe(show_timer)
        client.subscribe(show_animation)
        client.subscribe(stop_display)
        client.subscribe(add_image)

def on_message(client, userdata, msg):
    client.publish('concierge/apps/live/pong', '{"result":"{}"}'.format(skill_name))

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_IP_ADDR)
    client.message_callback_add(pingTopic, on_message)
    client.message_callback_add(dial_open, dialogue_open)
    client.message_callback_add(dial_close, dialogue_close)
    client.message_callback_add(show_hour, display_time)
    client.message_callback_add(show_timer, display_timer)
    client.message_callback_add(show_animation, display_animation)
    client.message_callback_add(stop_display, display_stop)
    client.message_callback_add(add_image, save_image)
    client.loop_forever()
