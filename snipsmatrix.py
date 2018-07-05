from dotstar import Adafruit_DotStar
import glob
from PIL import Image
import Queue
import subprocess
import sys
import threading
import time
import os

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
        for x in range(Animation.width):
            for y in range(Animation.height):
                p = self.pixels[self.item][x, y]
                self.strip.setPixelColor(y, Animation.gamma[p[0]], 
                                         Animation.gamma[p[1]],
                                         Animation.gamma[p[2]])
            self.strip.show()
        self.item += 1
        self.item %= self.num_image
        time.sleep(0.5)

class SnipsMatrix:
    queue = Queue.Queue()
    state_hotword = None
    state_waiting = None

    @staticmethod
    def worker():
        item = ""
        while True:
            if (not SnipsMatrix.queue.empty()):
                item = SnipsMatrix.queue.get_nowait()
                SnipsMatrix.queue.task_done()
            if (item == "hotword"):
                if (SnipsMatrix.state_hotword is not None):
                    SnipsMatrix.state_hotword.show()
            if (item == "waiting"):
                if (SnipsMatrix.state_waiting is not None):
                    SnipsMatrix.state_waiting.show()

    def __init__(self):
        numpixels = 128
        datapin   = 10
        clockpin  = 11
        strip     = Adafruit_DotStar(numpixels, datapin, clockpin, 1000000)
        strip.begin()           # Initialize pins for output
        SnipsMatrix.state_hotword = Animation('hotword', strip)
        SnipsMatrix.queue.put("hotword")
        SnipsMatrix.queue.put("waiting")
        t = threading.Thread(target=SnipsMatrix.worker, args=())
        t.start()

    def hotword_detected(self):
        SnipsMatrix.queue.put("hotword")

    def stop(self):
        SnipsMatrix.queue.put("waiting")
