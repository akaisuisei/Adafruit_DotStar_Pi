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

class ConciergeMatrix():
    _id= "snips-skill-matrix"
    dial_open = 'hermes/asr/startListening'
    dial_close = 'hermes/asr/stopListening'

    def __init__(self, siteId, c):
        self.json_dir = ConciergeMatrix.load_json_dir()
        self.skill = SnipsMatrix()
        self.current_session = None
        self.swipe_num = 0
        self.active_app = 'music'
        self.site_id = siteId
        self.swipe_num = 0
        self.rotate_count = {'music': 0, 'light':0}
        c.subscribePing(self.on_ping)
        c.subscribe(ConciergeMatrix.dial_open, self.on_dialogue_open)
        c.subscribe(ConciergeMatrix.dial_close, self.on_dialogue_close)
        c.subscribeTime(self.on_time)
        c.subscribeTimer(self.on_timer)
        c.subscribeAnimation(self.on_animation)
        c.subscribeStop(self.on_stop)
        c.subscribeImage(self.on_image)
        c.subscribeRotary(self.on_rotary)
        c.subscribeSwipe(self.on_swipe)
        c.subscribeWeather(self.on_weather)
        self.c = c

    @staticmethod
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

    def on_dialogue_open(self, client, userdata, msg):
        print(msg.topic)
        data = json.loads(msg.payload)
        if data['siteId'] == self.site_id:
            self.skill.hotword_detected()
            self.current_session = data['sessionId']

    def on_dialogue_close(self, client, userdata, msg):
        print(msg.topic)
        data = json.loads(msg.payload)
        if (data['siteId'] != self.site_id):
            return
        if (self.current_session and
            data['sessionId'] and
            data['sessionId'] == self.current_session):
            self.skill.stop_hotword()

    def on_stop(self, client, userdata, msg):
        print(msg.topic)
        self.skill.stop()

    def on_image(self, client, userdata, msg):
        print(msg.topic)
        tmp = msg.topic.split('/')
        name = tmp [-1]
        directory = tmp[-2]
        if (tmp[-3] != 'add'):
            return
        image = msg.payload
        self.skill.save_image(name, directory, image)

    def on_time(self, client, userdata, msg):
        print('time')
        try:
            data = json.loads(msg.payload)
        except:
            print('time not a json')
            return
        duration = None
        if ('duration' in data):
            duration = data['duration']
        self.skill.show_time(duration)

    def on_animation(self, client, userdata, msg):
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
        self.skill.show_animation(animation, duration)

    def on_timer(self, client, userdata, msg):
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
        self.skill.show_timer(duration)

    def on_rotary(self, client, userdata, msg):
        print(msg.topic)
        #simulate concierge
        self.rotate_count[self.active_app] += int(msg.payload)
        volume = self.rotate_count[self.active_app]
        tmp = "inc_"
        if (int(msg.payload) <= 0):
            tmp = 'dec_'
        data = self.json_dir[tmp + self.active_app]
        print(data)
        self.c.publish(data[0], data[1])
        self.skill.show_rotate(volume)

    def on_swipe(self, client, userdata, msg):
        apps = ['music', 'light']
        if msg.payload == 'right' or msg.payload == 'left':
            self.swipe_num += 1
        else:
            self.swipe_num -= 1
        if self.swipe_num < 0:
            self.swipe_num = len(apps) - 1
        if self.swipe_num >= len(apps):
            self.swipe_num = 0
        print(msg.topic)
        self.active_app = apps[self.swipe_num]
        self.skill.show_animation(apps[self.swipe_num], None)

    def on_weather(self, client, userdata, msg):
        try:
            tmp = json.loads(msg.payload)
        except:
            print('weather not a json')
            return
        if ('temp' not in tmp or 'weather' not in tmp):
            return
        self.skill.show_weather(tmp['temp'], tmp['weather'])

    def on_ping(self, client, userdata, msg):
        self.c.publishPong(_id)

    def stop(self):
        self.skill.exit()

if __name__ == "__main__":
    def sig_handler(sig, frame):
        c.disconnect()
        a.stop()
        sys.exit(0)
    MQTT_IP_ADDR = "raspi-mika.local"
    signal.signal(signal.SIGINT, sig_handler)
    c = Concierge(MQTT_IP_ADDR, "default", False)
    a = ConciergeMatrix("default", c)
    c.loop_forever()
