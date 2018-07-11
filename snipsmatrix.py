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

class DisplayPriority:
    #animation due to hardware component
    hardware = 0
    #animation due to hotword
    hotword = 1
    # short animation from app
    short_apps = 2
    #animation that is trigger every second- minute (timer, show time)
    schedule_apps = 3

    @staticmethod
    def can_I_do_it(priority):
        if priority == DisplayPriority.hardware:
            print("prio Hardware")
            return True
        if priority == DisplayPriority.hotword:
            print("prio hotword: {}".format(SnipsMatrix.timer_hardware is None))
            return SnipsMatrix.timer_hardware is None
        if priority == DisplayPriority.short_apps:
            print("prio short_app: {}".format(SnipsMatrix.timer_hardware is None
                                              and not SnipsMatrix.hotword_status))
            return (SnipsMatrix.timer_hardware is None  and
                not SnipsMatrix.hotword_status)
        if priority == DisplayPriority.schedule_apps:
            print("prio schedule_app: {}".format(SnipsMatrix.timer_hardware is None
                                              and not SnipsMatrix.hotword_status) and not SnipsMatrix.timer_short_app)
            return (SnipsMatrix.timer_hardware is None and
                    not SnipsMatrix.hotword_status and
                   not SnipsMatrix.timer_short_app)
        return False

class SnipsMatrix:
    queue = Queue.Queue()
    state_hotword = None
    state_waiting = None
    state_volume = None
    state_time = None
    state_weather = None
    timerstop = None
    timer_hardware = None
    timer_short_app = None
    timer = None
    hotword_status = False
    custom_anim = False

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
        SnipsMatrix.hotword_status = True
        SnipsMatrix.queue.put("hotword")

    def stop(self):
        print('stop all animation')
        self.stop_all_timer()
        SnipsMatrix.queue.put("waiting")

    def exit(self):
        print('exit snipsmatrix')
        self.stop_all_timer()
        SnipsMatrix.queue.put("__exit__")

    def stop_hotword(self):
        print('stop hotword')
        SnipsMatrix.hotword_status =  False
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
        SnipsMatrix.create_timer_time(duration)

    def show_animation(self, name, duration):
        SnipsMatrix.queue.put(name)
        if duration is not None:
            SnipsMatrix.create_short_app_timer(duration)

    def show_timer(self, duration):
        if duration is None:
            return
        SnipsMatrix.create_timer(duration)

    def show_volume(self, vol):
        if vol is None:
            return
        SnipsMatrix.queue.put([vol])
        SnipsMatrix.create_hardware_timer(10)

    def show_weather(self, tmp, weather):
        SnipsMatrix.queue.put({"weather": weather, "temp": tmp})
        SnipsMatrix.create_short_app_timer(20)

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
            if isinstance(item, (int, long)):
                if DisplayPriority.can_I_do_it(DisplayPriority.schedule_apps):
                    SnipsMatrix.state_time.show(item)
                item =""
            if isinstance(item, (float)):
                if DisplayPriority.can_I_do_it(DisplayPriority.short_apps):
                    SnipsMatrix.state_time.show(item)
                item =""
            elif isinstance(item, list):
                if DisplayPriority.can_I_do_it(DisplayPriority.hardware):
                    SnipsMatrix.state_volume.show(item[0])
                    item =""
            elif isinstance(item, dict):
                if DisplayPriority.can_I_do_it(DisplayPriority.short_apps):
                    SnipsMatrix.state_weather.show(item)
                    item =""
            elif (item == "hotword"):
                if DisplayPriority.can_I_do_it(DisplayPriority.hotword):
                    SnipsMatrix.state_hotword.show()
            elif (item == "waiting"):
                SnipsMatrix.state_hotword.reset(0)
                item =""
            elif (item == "__exit__"):
                return
            elif (item in SnipsMatrix.custom_anim):
                if DisplayPriority.can_I_do_it(DisplayPriority.short_apps):
                    SnipsMatrix.custom_anim[item].show()

    @staticmethod
    def create_timer(duration, stop_time = None):
        if stop_time is None:
            stop_time = int(time.time()) + duration
        duration = stop_time - int(time.time())
        if SnipsMatrix.timer:
            SnipsMatrix.timer.cancel()
            del SnipsMatrix.timer
            SnipsMatrix.timer = None
        if duration >= 0 :
            SnipsMatrix.queue.put(int(duration))
        elif duration >= -2:
            SnipsMatrix.queue.put(int(0))
        else:
            SnipsMatrix.queue.put("waiting")
            return
        SnipsMatrix.timer = threading.Timer(1,
                                            SnipsMatrix.create_timer,
                                           args=[duration, stop_time])
        SnipsMatrix.timer.start()

    @staticmethod
    def create_hardware_timer(duration):
        if SnipsMatrix.timer_hardware:
            SnipsMatrix.timer_hardware.cancel()
            del SnipsMatrix.timer_hardware
            SnipsMatrix.timer_hardware = None
        SnipsMatrix.timer_hardware = threading.Timer(duration,
                SnipsMatrix.stop_show_hardware)
        SnipsMatrix.timer_hardware.start()

    @staticmethod
    def create_short_app_timer(duration):
        if SnipsMatrix.timer_short_app:
            SnipsMatrix.timer_short_app.cancel()
            del SnipsMatrix.timer_short_app
            SnipsMatrix.timer_short_app = None
        SnipsMatrix.timer_short_app = threading.Timer(duration,
                SnipsMatrix.stop_show_short_app)
        SnipsMatrix.timer_short_app.start()

    @staticmethod
    def create_timer_time(duration):
        SnipsMatrix.queue.put(time.time())
        if SnipsMatrix.timer_short_app:
            SnipsMatrix.timer_short_app.cancel()
            del SnipsMatrix.timer_short_app
            SnipsMatrix.timer_short_app = None
        if duration < 0:
            SnipsMatrix.queue.put("waiting")
            return
        SnipsMatrix.timer_short_app = threading.Timer(1,
                                            SnipsMatrix.create_timer_time,
                                            args = [duration - 1])
        SnipsMatrix.timer_short_app.start()

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
        if SnipsMatrix.timer_hardware:
            SnipsMatrix.timer_hardware.cancel()
            del SnipsMatrix.timer_hardware
            SnipsMatrix.timer_hardware = None
        if SnipsMatrix.timer_short_app:
            SnipsMatrix.timer_short_app.cancel()
            del SnipsMatrix.timer_short_app
            SnipsMatrix.timer_short_app = None

    @staticmethod
    def stop_show_hardware():
        if SnipsMatrix.timer_hardware:
            SnipsMatrix.timer_hardware.cancel()
            del SnipsMatrix.timer_hardware
        SnipsMatrix.timer_hardware = None
        SnipsMatrix.queue.put("waiting")

    @staticmethod
    def stop_show_short_app():
        if SnipsMatrix.timer_short_app:
            SnipsMatrix.timer_short_app.cancel()
            del SnipsMatrix.timer_short_app
        SnipsMatrix.timer_short_app = None
        SnipsMatrix.queue.put("waiting")
