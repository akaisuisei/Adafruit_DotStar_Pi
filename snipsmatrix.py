from dotstar import Adafruit_DotStar
import glob
from os.path import expanduser
from PIL import Image
import Queue
import subprocess
import sys
import threading
import time
import os

import util

TIMER = 30
CONFIG_INI_DIR =  expanduser("~/.matrix/")

class Animation:
    gamma = bytearray(256)
    for i in range(256):
        gamma[i] = int(pow(float(i) / 255.0, 2.7) * 255.0 + 0.5)
    width = 8
    height = 16

    def __init__(self, images, strip):
        f = glob.glob(images + "/*.png")
        imgs = [Image.open(x).convert("RGB") for x in f]
        self.num_image = len(f)
        self.pixels = [img.load() for img in imgs]
        self.item = 0;
        self.strip = strip

    def show(self):
        for y in range(Animation.height):
            for x in range(Animation.width):
                p = self.pixels[self.item][x, y]
                self.strip.setPixelColor(x+(y*Animation.width),
                        Animation.gamma[p[0]],
                        Animation.gamma[p[1]],
                        Animation.gamma[p[2]])
            self.strip.show()
        self.item += 1
        self.item %= self.num_image
        time.sleep(0.1)

    def clear(self, color):
        for y in range(128):
            self.strip.setPixelColor(y, color)
        self.strip.show()

class AnimationVolume:
    def __init__(self, strip):
        self.strip = strip
        vol = 0;

    def show(self, new_vol):
        def draw_rect(x_start, y_start, w, h, color):
            for x in range(w):
                for y in range(h):
                    pos = 7 - x + x_start + (y + y_start) * Animation.width
                    print(pos)
                    self.strip.setPixelColor(pos, color)
        if (new_vol >= 16):
            return
        self.clear(0)
        if (new_vol <= 0):
            return
        self.vol = new_vol
        draw_rect(5, 15 - self.vol, 2, self.vol, 0xFFFFFF)
        self.strip.show()

    def clear(self, color):
        for y in range(128):
            self.strip.setPixelColor(y, color)
        self.strip.show()

class AnimationWeather:
    width = 8
    height = 8
    def __init__(self, strip):
        dirs = glob.glob("image/weather/*/")
        names = [(x.split('/')[-2], x) for x in dirs]
        res = {}
        for k in names:
            f =  glob.glob(k[1] + "*.png")
            imgs = [Image.open(x).convert("RGB").load() for x in f]
            res[k[0]] = imgs
            self.strip = strip
        self.pixels = res

    def show(self, dic):
        def draw_number(arr, x_start, y_start, color):
            for x in range(3):
                for y in range(5):
                    if arr[y][x] == 1:
                        pos = 2 - x + x_start + (y + y_start) * Animation.width
                        self.strip.setPixelColor(pos, color)
        def draw_line(x, y, l, color):
            for tmp in range(l):
                pos = x + tmp + y * Animation.width
                self.strip.setPixelColor(pos, color)
        if dic['weather'] not in self.pixels:
            return
        for y in range(AnimationWeather.height):
            for x in range(AnimationWeather.width):
                p = self.pixels[dic['weather']][0][x, y]
                self.strip.setPixelColor(x+(y*AnimationWeather.width),
                        Animation.gamma[p[0]],
                        Animation.gamma[p[1]],
                        Animation.gamma[p[2]])
        color = 0xFFFFFF
        c3 = util.number_bit[dic['temp'] / 10]
        c4 = util.number_bit[dic['temp'] % 10]
        draw_number(c3, 4, 9, color)
        draw_number(c4, 0, 9, color)
        self.strip.show()

class AnimationTime():
    def __init__(self, strip):
        self.strip = strip

    def show(self, second):
        def draw_number(arr, x_start, y_start, color):
            for x in range(3):
                for y in range(5):
                    if arr[y][x] == 1:
                        pos = 2 - x + x_start + (y + y_start) * Animation.width
                        self.strip.setPixelColor(pos, color)
        def draw_line(x, y, l, color):
            for tmp in range(l):
                pos = x + tmp + y * Animation.width
                self.strip.setPixelColor(pos, color)
        self.clear(0)
        second = int(second)
        second %= (60 * 60 * 24)
        if second > 60 * 60:
            t1 = second / (60 * 60)
            t2 = (second % (60 * 60)) / 60
        else:
            t1 = second / 60
            t2 = second % 60
        c1 = util.number_bit[t1 / 10]
        c2 = util.number_bit[t1 % 10]
        c3 = util.number_bit[t2 / 10]
        c4 = util.number_bit[t2 % 10]
        color = 0xFFFFFF
        draw_number(c1, 4, 1, color)
        draw_number(c2, 0, 1, color)
        draw_line(0, 7, 3, color)
        draw_number(c3, 4, 9, color)
        draw_number(c4, 0, 9, color)
        print(second)
        self.strip.show()

    def clear(self, color):
        for y in range(128):
            self.strip.setPixelColor(y, color)
        self.strip.show()

class SnipsMatrix:
    queue = Queue.Queue()
    state_hotword = None
    state_waiting = None
    state_volume = None
    state_time = None
    state_weather = None
    timerstop = None
    timer_volume = None
    timer = None
    custom_anim = None


    def __init__(self):
        numpixels = 128
        datapin   = 10
        clockpin  = 11
        strip = Adafruit_DotStar(numpixels, datapin, clockpin, 1000000)
        strip.begin()
        strip.setBrightness(64)
        self.strip = strip
        SnipsMatrix.state_hotword = Animation('hotword', strip)
        SnipsMatrix.state_time = AnimationTime(strip)
        SnipsMatrix.state_volume = AnimationVolume(strip)
        SnipsMatrix.state_weather = AnimationWeather(strip)
        SnipsMatrix.custom_anim = SnipsMatrix.load_custom_animation(strip)
        SnipsMatrix.queue.put("hotword")
        SnipsMatrix.queue.put("waiting")
        t = threading.Thread(target=SnipsMatrix.worker, args=())
        t.start()

    def hotword_detected(self):
        self.stop_all_timer()
        SnipsMatrix.queue.put("hotword")

    def stop(self):
        print('stop')
        self.stop_all_timer()
        SnipsMatrix.queue.put("waiting")

    def save_image(self, name, directory, image):
        already_exist = True
        if (image is None):
            return
        if not os.path.exists(CONFIG_INI_DIR):
                os.makedirs(CONFIG_INI_DIR)
        if not os.path.exists(CONFIG_INI_DIR + directory):
                os.makedirs(CONFIG_INI_DIR + directory)
                already_exist = False
        f_name = "{}{}/{}".format(CONFIG_INI_DIR, directory, name)
        try:
            with open(f_name, 'w') as f:
                f.write(image)
        except IOError as e:
            print(e)
            return
        if already_exist:
            del SnipsMatrix.custom_anim[directory]
        SnipsMatrix.custom_anim[directory] = Animation(CONFIG_INI_DIR +
                                                       directory,
                                                       self.strip)

    def show_time(self, duration):
        if duration is None:
            duration = 70
        SnipsMatrix.stop_all_timer()
        SnipsMatrix.create_timer_time(duration)

    def show_animation(self, name, duration):
        SnipsMatrix.queue.put(name)
        self.stop_all_timer()
        if duration is not None:
            SnipsMatrix.create_stop_timer(duration)

    def show_timer(self, duration):
        if duration is None:
            return
        self.stop_all_timer()
        SnipsMatrix.create_timer(duration)

    def show_volume(self, vol):
        if vol is None:
            return
        SnipsMatrix.queue.put([vol])
        SnipsMatrix.create_volume_timer(10)

    def show_weather(self, tmp, weather):
        SnipsMatrix.queue.put({"weather": weather, "temp": tmp})
        SnipsMatrix.create_volume_timer(30)

    @staticmethod
    def load_custom_animation(strip):
        dirs = glob.glob("{}*/".format(CONFIG_INI_DIR))
        names = [(x.split('/')[-2], x) for x in dirs]
        res = {}
        for k in names:
            res[k[0]] = Animation(k[1], strip)
        return res

    @staticmethod
    def worker():
        item = ""
        while True:
            time.sleep(0.01)
            if (not SnipsMatrix.queue.empty()):
                item = SnipsMatrix.queue.get_nowait()
                SnipsMatrix.queue.task_done()
                print(item)
            if isinstance(item, (int, long, float)):
                if SnipsMatrix.timer_volume is None:
                    SnipsMatrix.state_time.show(item)
                item =""
            elif isinstance(item, list):
                SnipsMatrix.state_volume.show(item[0])
                item =""
            elif isinstance(item, dict):
                SnipsMatrix.state_weather.show(item)
                item =""
            elif (item == "hotword"):
                SnipsMatrix.state_hotword.show()
            elif (item == "waiting"):
                SnipsMatrix.state_hotword.clear(0x000000)
                item =""
            elif (item in SnipsMatrix.custom_anim):
                SnipsMatrix.custom_anim[item].show()

    @staticmethod
    def create_timer(duration):
        SnipsMatrix.create_stop_timer(duration + 1)
        SnipsMatrix.queue.put(duration)
        SnipsMatrix.timer = threading.Timer(1,
                                            SnipsMatrix.worker_timer,
                                           args=[duration])
        SnipsMatrix.timer.start()

    @staticmethod
    def worker_timer(duration):
        duration -= 1
        SnipsMatrix.queue.put(duration)
        SnipsMatrix.timer = threading.Timer(1,
                                            SnipsMatrix.worker_timer,
                                           args=[duration])
        SnipsMatrix.timer.start()

    @staticmethod
    def create_timer_time(duration):
        SnipsMatrix.create_stop_timer(duration)
        SnipsMatrix.queue.put(time.time())
        SnipsMatrix.timer = threading.Timer(TIMER,
                                            SnipsMatrix.worker_timer_time)
        SnipsMatrix.timer.start()

    @staticmethod
    def worker_timer_time():
        SnipsMatrix.queue.put(time.time())
        SnipsMatrix.timer = threading.Timer(TIMER,
                                            SnipsMatrix.worker_timer_time)
        SnipsMatrix.timer.start()

    @staticmethod
    def create_stop_timer(duration):
        SnipsMatrix.timerstop = threading.Timer(duration, SnipsMatrix.stop_animation)
        SnipsMatrix.timerstop.start()

    @staticmethod
    def create_volume_timer(duration):
        if SnipsMatrix.timer_volume:
            SnipsMatrix.timer_volume.cancel()
            del SnipsMatrix.timer_volume
            SnipsMatrix.timer_volume = None
        SnipsMatrix.timer_volume = threading.Timer(duration,
                SnipsMatrix.stop_show_volume)
        SnipsMatrix.timer_volume.start()

    @staticmethod
    def stop_all_timer():
        if SnipsMatrix.timerstop:
            SnipsMatrix.timerstop.cancel()
            del SnipsMatrix.timerstop
            SnipsMatrix.timerstop = None
        if SnipsMatrix.timer:
            SnipsMatrix.timer.cancel()
            del SnipsMatrix.timer
            SnipsMatrix.timer = None
        if SnipsMatrix.timer_volume:
            SnipsMatrix.timer_volume.cancel()
            del SnipsMatrix.timer_volume
            SnipsMatrix.timer_volume = None

    @staticmethod
    def stop_animation():
        SnipsMatrix.stop_all_timer()
        SnipsMatrix.queue.put("waiting")

    @staticmethod
    def stop_show_volume():
        if SnipsMatrix.timer_volume:
            SnipsMatrix.timer_volume.cancel()
            del SnipsMatrix.timer_volume
        SnipsMatrix.timer_volume = None
        SnipsMatrix.queue.put("waiting")
