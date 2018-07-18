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
m_topic = 'concierge/feedback/led/{}'.format(site_id)
show_hour = '{}/time'.format(m_topic)
show_animation = '{}/animation'.format(m_topic)
show_timer = '{}/timer'.format(m_topic)
show_weather = '{}/weather'.format(m_topic)
stop_display = '{}/stop'.format(m_topic)
add_image = '{}/add/#'.format(m_topic)
show_rotate = '{}/rotary'.format(m_topic)
show_swipe = '{}/swipe'.format(m_topic)
show_rotate = 'concierge/commands/remote/rotary'
show_swipe = 'concierge/commands/remote/swipe'
skill = SnipsMatrix()
last_session = None
swipe_num = 0
active_app = 'music'
rotate_count = {'music': 0, 'light':0}
json_dir = None
def load_json_dir():
    def load_json(path):
        data = None
        with open(path, 'r') as f:
            data = json.load(f)
        data['siteId'] = 'default'
        data['customData'] = None
        data['sessionId'] = '317r637fhnfcl3u2ej9ienj'
        return json.dumps(data)
    data = {}
    data['inc_light'] = ['hermes/intent/lightsShift', load_json('inc_light.json')]
    data['dec_light'] = ['hermes/intent/lightsShift', load_json('dec_light.json')]
    data['inc_music'] = ['hermes/intent/VolumeUp', load_json('inc_music.json')]
    data['dec_music'] = ['hermes/intent/VolumeDown', load_json('dec_music.json')]
    return data

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

def display_rotate(client, userdata, msg):
    print(msg.topic)
    print("toto")
    #simulate concierge
    rotate_count[active_app] += int(msg.payload)
    volume = rotate_count[active_app]
    tmp = "inc_"
    if (int(msg.payload) <= 0):
        tmp = 'dec_'
    data = json_dir[tmp + active_app]
    print(data)
    client.publish(data[0], data[1])
    skill.show_rotate(volume)

def display_swipe(client, userdata, msg):
    global swipe_num, active_app
    apps = ['music', 'light']
    if msg.payload == 'right' or msg.payload == 'left':
        swipe_num += 1
    else:
        swipe_num -= 1
    if swipe_num < 0:
        swipe_num = len(apps) - 1
    if swipe_num >= len(apps):
        swipe_num = 0
    print(msg.topic)
    active_app = apps[swipe_num]
    skill.show_animation(apps[swipe_num], None)

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
    json_dir = load_json_dir()
    client.message_callback_add(pingTopic, on_message)
    client.message_callback_add(dial_open, dialogue_open)
    client.message_callback_add(dial_close, dialogue_close)
    client.message_callback_add(show_hour, display_time)
    client.message_callback_add(show_timer, display_timer)
    client.message_callback_add(show_animation, display_animation)
    client.message_callback_add(stop_display, display_stop)
    client.message_callback_add(add_image, save_image)
    client.message_callback_add(show_rotate, display_rotate)
    client.message_callback_add(show_swipe, display_swipe)
    client.message_callback_add(show_weather, display_weather)
    signal.signal(signal.SIGINT, sig_handler)
    client.loop_forever()
