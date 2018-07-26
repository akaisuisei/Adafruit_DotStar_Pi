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
        c.subscribeAsrStart(self.on_dialogue_open)
        c.subscribeAsrStop(self.on_dialogue_close)
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

    def on_stop(self):
        self.skill.stop()

    def on_image(self, name, directory, image):
        self.skill.save_image(name, directory, image)

    def on_time(self, duration, value):
        self.skill.show_time(duration)

    def on_animation(self, animation, duration):
        if not animation:
            return
        self.skill.show_animation(animation, duration)

    def on_timer(self, duration):
        print(duration)
        self.skill.show_timer(duration)

    def on_rotary(self, value):
        #simulate concierge
        self.rotate_count[self.active_app] += value
        volume = self.rotate_count[self.active_app]
        tmp = "inc_"
        if (value <= 0):
            tmp = 'dec_'
        data = self.json_dir[tmp + self.active_app]
        print(data)
        self.c.publish(data[0], data[1])
        self.skill.show_rotate(volume)

    def on_swipe(self, value):
        apps = ['music', 'light']
        if value == 'right' or value == 'left':
            self.swipe_num += 1
        else:
            self.swipe_num -= 1
        if self.swipe_num < 0:
            self.swipe_num = len(apps) - 1
        if self.swipe_num >= len(apps):
            self.swipe_num = 0
        self.active_app = apps[self.swipe_num]
        self.skill.show_animation(apps[self.swipe_num], None)

    def on_weather(self, temperature, condition):
        if  temperature is None or condition is None:
            return
        self.skill.show_weather(temperature, condition)

    def on_ping(self):
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
