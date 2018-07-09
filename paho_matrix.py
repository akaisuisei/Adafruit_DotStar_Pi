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
import socket

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "ledtest.local"
if socket.gethostname() == "raspi-mika":
    MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
client = None
site_id = "default"
skill_name = "snips-skill-matrix"
pingTopic = 'concierge/apps/live/ping'
dial_open = 'hermes/dialogueManager/sessionStarted'
dial_close = 'hermes/dialogueManager/sessionEnded'
m_topic = 'concierge/feedback/led'
show_hour = '{}/{}/time'.format(m_topic, site_id)
show_animation = '{}/{}/animation'.format(m_topic, site_id)
show_timer = '{}/{}/timer'.format(m_topic, site_id)
stop_display = '{}/{}/stop'.format(m_topic, site_id)
add_image = '{}/{}/add/#'.format(m_topic, site_id)
skill = SnipsMatrix()
def dialogue_open(client, userdata, msg):
    print(msg.topic)
    skill.hotword_detected()

def dialogue_close(client, userdata, msg):
    print(msg.topic)
    skill.stop()

def display_stop(client, userdata, msg):
    print(msg.topic)
    skill.stop()

def save_image(client, userdata, msg):
    print(msg.topic)
    tmp = msg.topic.split('/')
    name = tmp [-1]
    directory = tmp[-2]
    if (tmp[-3] != 'add'):
        return
    image = msg.payload
    skill.save_image(name, directory, image)

def display_time(client, userdata, msg):
    print('time')
    data = json.loads(msg.payload)
    duration = None
    if ('duration' in data):
        duration = data['duration']
    skill.show_time(duration)

def display_animation(client, userdata, msg):
    print(msg.topic)
    data = json.loads(msg.payload)
    if ('animation' not in data):
        return
    animation = data['animation']
    duration = None
    if ('duration' in data):
        duration = data['duration']
    skill.show_animation(animation, duration)

def display_timer(client, userdata, msg):
    print(msg.topic)
    data = json.loads(msg.payload)
    duration = None
    if ('duration' in data):
        duration = data['duration']
    skill.show_timer(duration)

def on_connect(client, userdata, flags, rc):
        print('connected')
        client.subscribe(pingTopic)
        client.subscribe("{}/#".format('concierge'))

def on_message(client, userdata, msg):
    client.publish('concierge/apps/live/pong', '{"result":"{}"}'.format(skill_name))

def on_message_def(client, userdata, msg):
    print(msg.topic)

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message_def
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
