from dotstar import Adafruit_DotStar
import glob
from PIL import Image
import Queue
import subprocess
import sys
import threading
import time
import os

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

    def clear(self,color):
        for y in range(128):
            self.strip.setPixelColor(y, color)
        self.strip.show()

class AnimationTime():
    def __init__(self, strip):
        self.strip = strip

    def show(second):
        self.clear(0)

    def clear(self,color):
        for y in range(128):
            self.strip.setPixelColor(y, color)
        self.strip.show()

class SnipsMatrix:
    queue = Queue.Queue()
    state_hotword = None
    state_waiting = None
    state_time = None
    timerstop = None
    timer = None

    def __init__(self):
        numpixels = 128
        datapin   = 10
        clockpin  = 11
        strip = Adafruit_DotStar(numpixels, datapin, clockpin, 2000000)
        strip.begin()
        strip.setBrightness(64)
        SnipsMatrix.state_hotword = Animation('hotword', strip)
        SnipsMatrix.state_time = AnimationTime(strip)
        SnipsMatrix.queue.put("hotword")
        SnipsMatrix.queue.put("waiting")
        t = threading.Thread(target=SnipsMatrix.worker, args=())
        t.start()

    def hotword_detected(self):
        self.stop_all_timer()
        SnipsMatrix.queue.put("hotword")

    def stop(self):
        self.stop_all_timer()
        SnipsMatrix.queue.put("waiting")

    def save_image(self, name, directory, image):
        if not os.path.exists(CONFIG_INI_DIR):
                os.makedirs(CONFIG_INI_DIR)
        f_name = "{}/{}/{}".format(CONFIG_INI_DIR, directory, name)
        try:
            with open(f_name, 'w') as f:
                f.write(image)
        except IOError as e:
            print(e)

    def show_time(self, duration):
        if duration is None:
            duration = 70
        SnipsMatrix.stop_all_timer()
        SnipsMatrix.create_stop_timer(duration)

    def show_animation(self, name, duration):
        SnipsMatrix.queue.put(name)
        if duration is not None:
            self.stop_all_timer()

    def show_timer(self, duration):
        if duration is None:
            return
        self.stop_all_timer()

    @staticmethod
    def worker():
        item = ""
        while True:
            time.sleep(0.01)
            if (not SnipsMatrix.queue.empty()):
                item = SnipsMatrix.queue.get_nowait()
                SnipsMatrix.queue.task_done()
            if isinstance(item, (int, long)):
                pass
            elif (item == "hotword"):
                SnipsMatrix.state_hotword.show()
            elif (item == "waiting"):
                SnipsMatrix.state_hotword.clear(0x000000)
                item =""

    @staticmethod
    def create_timer(duration):
        SnipsMatrix.timerstop = threading.Timer(duration, stop_animation)
        SnipsMatrix.timerstop.start()
        SnipsMatrix.timer = threading.Timer(1,
                                            SnipsMatrix.worker_timer,
                                           args=(duration))
        SnipsMatrix.timer.start()

    @staticmethod
    def worker_timer(duration):
        duration -= 1
        SnipsMatrix.timer = threading.Timer(1,
                                            SnipsMatrix.worker_timer,
                                           args=(duration))
        SnipsMatrix.queue.put(duration)
        SnipsMatrix.timer.start()

    @staticmethod
    def create_timer_time(duration):
        SnipsMatrix.timerstop = threading.Timer(duration, stop_animation)
        SnipsMatrix.timerstop.start()
        SnipsMatrix.timer = threading.Timer(30,SnipsMatrix.worker_timer_time)
        SnipsMatrix.timer.start()

    @staticmethod
    def worker_timer_time():
        SnipsMatrix.timer = threading.Timer(30,SnipsMatrix.worker_timer_time)
        SnipsMatrix.timer.start()
        SnipsMatrix.queue.put(time.time())
        SnipsMatrix.timer.start()

    @staticmethod
    def create_stop_timer(duration):
        SnipsMatrix.timerstop = threading.Timer(duration, SnipsMatrix.stop_animation)
        SnipsMatrix.timerstop.start()

    @staticmethod
    def stop_all_timer():
        if SnipsMatrix.timerstop:
            SnipsMatrix.timerstop.cancel()
            SnipsMatrix.timerstop = None
        if SnipsMatrix.timer:
            SnipsMatrix.timer.cancel()
            SnipsMatrix.timer = None

    @staticmethod
    def stop_animation():
        SnipsMatrix.queue.put("waiting")
