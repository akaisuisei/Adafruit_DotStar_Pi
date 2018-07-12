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
import signal
import sys


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "raspi-mika.local"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))
print(MQTT_IP_ADDR)
DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
client = None
site_id = "default"
skill_name = "snips-skill-matrix"
pingTopic = 'concierge/apps/live/ping'
dial_open = 'hermes/asr/startListening'
dial_close = 'hermes/asr/stopListening'
m_topic = 'concierge/feedback/led'
show_hour = '{}/{}/time'.format(m_topic, site_id)
show_animation = '{}/{}/animation'.format(m_topic, site_id)
show_timer = '{}/{}/timer'.format(m_topic, site_id)
show_weather = '{}/{}/weather'.format(m_topic, site_id)
stop_display = '{}/{}/stop'.format(m_topic, site_id)
add_image = '{}/{}/add/#'.format(m_topic, site_id)
show_volume = 'concierge/commands/volume'
skill = SnipsMatrix()
last_session = None

def dialogue_open(client, userdata, msg):
    global last_session
    print(msg.topic)
    print(msg.payload)
    data = json.loads(msg.payload)
    if data['siteId'] == site_id:
        skill.hotword_detected()
        last_session = data['sessionId']

def dialogue_close(client, userdata, msg):
    print(msg.topic)
    print(msg.payload)
    data = json.loads(msg.payload)
    if (data['siteId'] != site_id):
        return
    if last_session and data['sessionId'] and data['sessionId'] == last_session:
        skill.stop_hotword()

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
    try:
        data = json.loads(msg.payload)
    except:
        print('time not a json')
        return
    duration = None
    if ('duration' in data):
        duration = data['duration']
    skill.show_time(duration)

def display_animation(client, userdata, msg):
    print(msg.topic)
    try:
        data = json.loads(msg.payload)
    except:
        print('animation not a json')
        return
    if ('animation' not in data):
        return
    animation = data['animation']
    duration = None
    if ('duration' in data):
        duration = data['duration']
    skill.show_animation(animation, duration)

def display_timer(client, userdata, msg):
    print(msg.topic)
    try:
        data = json.loads(msg.payload)
    except:
        print('timer not a json')
        return
    duration = None
    if (not isinstance(data, dict)):
        return
    if ('duration' in data):
        duration = data['duration']
    skill.show_timer(duration)

def display_volume(client, userdata, msg):
    print(msg.topic)
    skill.show_volume(int(msg.payload))

def display_weather(client, userdata, msg):
    print(msg.topic)
    try:
        tmp = json.loads(msg.payload)
    except:
        print('weather not a json')
        return
    if ('temp' not in tmp or 'weather' not in tmp):
        return
    skill.show_weather(tmp['temp'], tmp['weather'])

def on_connect(client, userdata, flags, rc):
    print('connected')
    client.subscribe(pingTopic)
    client.subscribe(dial_open)
    client.subscribe(dial_close)
    client.subscribe("{}/#".format('concierge'))

def on_message(client, userdata, msg):
    client.publish('concierge/apps/live/pong', '{"result":"{}"}'.format(skill_name))

def on_message_def(client, userdata, msg):
    print(msg.topic)

def sig_handler(sig, frame):
    client.disconnect()
    skill.exit()
    sys.exit(0)

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
    client.message_callback_add(show_volume, display_volume)
    client.message_callback_add(show_weather, display_weather)
    signal.signal(signal.SIGINT, sig_handler)
    client.loop_forever()
