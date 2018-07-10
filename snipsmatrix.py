from dotstar import Adafruit_DotStar
import glob
from os.path import expanduser
import Queue
import subprocess
import sys
import threading
import time
import os
from animation import AnimationTime, AnimationImage, AnimationWeather
from animation import AnimationVolume

TIMER = 30
CONFIG_INI_DIR =  expanduser("~/.matrix/")

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
        SnipsMatrix.state_hotword = AnimationImage('hotword', strip)
        SnipsMatrix.state_time = AnimationTime(strip)
        SnipsMatrix.state_volume = AnimationVolume(strip, 0)
        SnipsMatrix.state_weather = AnimationWeather(strip)
        SnipsMatrix.custom_anim = SnipsMatrix.load_custom_animation(strip)
        SnipsMatrix.queue.put("hotword")
        SnipsMatrix.queue.put("waiting")
        t = threading.Thread(target=SnipsMatrix.worker, args=())
        t.start()

    def hotword_detected(self):
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
        SnipsMatrix.custom_anim[directory] = AnimationImage(CONFIG_INI_DIR +
                                                       directory,
                                                       self.strip,
                                                    True)

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
            res[k[0]] = AnimationImage(k[1], strip, True)
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
                SnipsMatrix.state_hotword.reset(0)
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
