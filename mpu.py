import threading
from mpu6050 import mpu6050
import RPi.GPIO as GPIO
from time import sleep
import events

class Mpu:
    run = False
    def __init__(self):
        self.event = events.Events()
        self.max_counter = 2

    def add_callback(self, func, max_counter = 51):
        self.event.on_change += func
        self.max_counter = max_counter

    def start(self):
        Mpu.run = True
        self.t = threading.Thread(target=self.worker, args=())
        self.t.start()

    def stop(self):
        Mpu.run = False

    def worker(self):
        try:
            self.sensor = mpu6050(0x68)
        except:
            return None
        sensibility = 3
        self.sensor.set_value_at_address(0x07,0x68)
        self.sensor.set_value_at_address(0x20,0x37)
        self.sensor.set_value_at_address(0x01,0x1C)
        self.sensor.set_value_at_address(sensibility,0x1F)
        self.sensor.set_value_at_address(20,0x20)
        self.sensor.set_value_at_address(0x15,0x69)
        self.sensor.set_value_at_address(0x40,0x38)
        counter = 0
        while(Mpu.run):
            sensorStatus = self.sensor.read_int()
            #accel = self.sensor.get_accel_data()
            #gyro = self.sensor.get_accel_data()
            if sensorStatus == 65:
                #if counter >= self.max_counter:
                self.event.on_change()
                counter = -1
            counter += 1
            sleep(0.1)
