#!/usr/bin/env python2
# -*-: coding utf-8 -*-

import calendar
import json
import os
import time
import threading
from datetime import datetime
from snipsmatrix import SnipsMatrix
import socket
import signal
import sys
from concierge_python.concierge import Concierge

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "raspi-mika.local"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))
print(MQTT_IP_ADDR)
DIR = os.path.dirname(os.path.realpath(__file__)) + '/alarm/'

alive = 0;
lang = "EN"
site_id = "default"
_id= "snips-skill-matrix"
dial_open = 'hermes/asr/startListening'
dial_close = 'hermes/asr/stopListening'
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

def on_dialogue_open(client, userdata, msg):
    global last_session
    print(msg.topic)
    print(msg.payload)
    data = json.loads(msg.payload)
    if data['siteId'] == site_id:
        skill.hotword_detected()
        last_session = data['sessionId']

def on_dialogue_close(client, userdata, msg):
    print(msg.topic)
    print(msg.payload)
    data = json.loads(msg.payload)
    if (data['siteId'] != site_id):
        return
    if last_session and data['sessionId'] and data['sessionId'] == last_session:
        skill.stop_hotword()

def on_stop(client, userdata, msg):
    print(msg.topic)
    skill.stop()

def on_image(client, userdata, msg):
    print(msg.topic)
    tmp = msg.topic.split('/')
    name = tmp [-1]
    directory = tmp[-2]
    if (tmp[-3] != 'add'):
        return
    image = msg.payload
    skill.save_image(name, directory, image)

def on_time(client, userdata, msg):
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

def on_animation(client, userdata, msg):
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

def on_timer(client, userdata, msg):
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

def on_rotary(client, userdata, msg):
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

def on_swipe(client, userdata, msg):
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

def on_weather(client, userdata, msg):
    try:
        tmp = json.loads(msg.payload)
    except:
        print('weather not a json')
        return
    if ('temp' not in tmp or 'weather' not in tmp):
        return
    skill.show_weather(tmp['temp'], tmp['weather'])

def on_ping(client, userdata, msg):
        concierge.publishPong(_id)

def sig_handler(sig, frame):
    c.disconnect()
    skill.exit()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sig_handler)
    concierge = Concierge(MQTT_IP_ADDR, site_id, False)
    json_dir = load_json_dir()
    c = concierge
    c.subscribePing(on_ping)
    c.subscribe(dial_open, on_dialogue_open)
    c.subscribe(dial_close, on_dialogue_close)
    c.subscribeTime(on_time)
    c.subscribeTimer(on_timer)
    c.subscribeAnimation(on_animation)
    c.subscribeStop(on_stop)
    c.subscribeImage(on_image)
    c.subscribeRotary(on_rotary)
    c.subscribeSwipe(on_swipe)
    c.subscribeWeather(on_weather)
    c.loop_forever()
