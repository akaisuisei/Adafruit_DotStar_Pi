import threading
from mpu6050 import mpu6050
import RPi.GPIO as GPIO
from time import sleep
import events

class Mpu:
    run = False
    def __init__(self):
        self.sensor = mpu6050(0x68)
        sensibility = 3
        self.sensor.set_value_at_address(0x07,0x68)
        self.sensor.set_value_at_address(0x20,0x37)
        self.sensor.set_value_at_address(0x01,0x1C)
        self.sensor.set_value_at_address(sensibility,0x1F)
        self.sensor.set_value_at_address(20,0x20)
        self.sensor.set_value_at_address(0x15,0x69)
        self.sensor.set_value_at_address(0x40,0x38)
        self.event = events.Events()

    def add_callback(self, func):
        self.event.on_change += func

    def start(self):
        Mpu.run = True
        self.t = threading.Thread(target=self.worker, args=())
        self.t.start()

    def stop(self):
        Mpu.run = False

    def worker(self):
        counter = 0
        max_counter = 51
        while(Mpu.run):
            sensorStatus = self.sensor.read_int()
            if sensorStatus == 65:
                if counter >= max_counter:
                    self.event.on_change()
                counter = -1
            counter += 1
            sleep(0.1)
