import glob
from PIL import Image
import time
import util

class Animation:
    gamma = bytearray(256)
    for i in range(256):
        gamma[i] = int(pow(float(i) / 255.0, 2.7) * 255.0 + 0.5)
    width = 8
    height = 16

    _current = [0] * (width * height)
    _next = [0] * (width * height)

    def __init__(self, strip):
        self.strip = strip
    @staticmethod
    def getPos(x, y):
        return (Animation.width - x - 1) + y * Animation.width

    def prepare(self, x, y, color):
        pos = Animation.getPos(x, y)
        if (pos < len(Animation._next) and pos >= 0):
            Animation._next[pos] = color

    def write(self,flip = False):
        Animation.s_write(self.strip, flip)

    def show(self):
        print('not implemented')
        pass

    def clear(self, color):
        Animation.s_clear(color)
    def clear_canvas(self, color, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                self.prepare(i, j, color)

    def reset(self, color):
        Animation.s_reset(self.strip, color)

    def draw_hline(self, x, y, l, color):
        for tmp in range(l):
            self.prepare(x + tmp, y, color)

    def draw_vline(self, x, y, l, color):
        for tmp in range(l):
            self.prepare(x , y + tmp, color)

    def draw_rect(self, x_start, y_start, w, h, color):
        for i in range(x_start, x_start + w):
            self.draw_vline(i, y_start, h, color)

    def draw_image(self, x_s, y_s, w, h, img):
        for y in range(h):
            for x in range(w):
                p = img[x, y]
                self.prepare(x + x_s, y + y_s, Animation.pix_to_hex(p))

    def draw_number(self, num, x_start, y_start, color):
        arr = util.number_bit[num]
        for x in range(3):
            for y in range(5):
                c = 0
                if arr[y][x] == 1:
                    c = color
                self.prepare(x + x_start, y + y_start, c)
    @staticmethod
    def flip():
        rotate = [0] * Animation.width * Animation.height
        for x in range (8):
            for y in range (8):
                rotate[8*8 +Animation.getPos(y, 7 - x)] = Animation._next[Animation.getPos(x, y)]
        for x in range (8):
            for y in range (8):
                rotate[Animation.getPos(y, 7 - x)] = Animation._next[8*8 +Animation.getPos(x, y)]
        return rotate

    @staticmethod
    def s_write(strip, flip = False):
        if(flip):
            Animation._next = Animation.flip()
        for i in range(len(Animation._next)):
            if Animation._next[i] != Animation._current[i]:
                strip.setPixelColor(i, Animation._next[i])
                Animation._current[i] = Animation._next[i]
        strip.show()

    @staticmethod
    def s_reset(strip, color):
        Animation.s_clear(color)
        Animation.s_write(strip)

    @staticmethod
    def s_clear(color):
        Animation._next = [color] * (len(Animation._next))

    @staticmethod
    def rgb_to_hex(r, g, b):
        return b + (r << 8) + (g << 16)

    @staticmethod
    def pix_to_hex(p):
        return Animation.rgb_to_hex(Animation.gamma[p[0]],
                                    Animation.gamma[p[1]],
                                    Animation.gamma[p[2]])

class AnimationImage(Animation):
    def __init__(self, images, strip, custom = False):
        Animation.__init__(self, strip)
        if (custom):
            f = glob.glob("{}/*.png".format(images))
        else:
            f = glob.glob("image/{}/*.png".format(images))
        print(f)
        imgs = [Image.open(x).convert("RGB") for x in f]
        self.num_image = len(f)
        self.pixels = [img.load() for img in imgs]
        self.item = 0;

    def show(self):
        self.draw_image(0, 0,Animation.width, Animation.height, self.pixels[self.item])
        self.write()
        self.item += 1
        self.item %= self.num_image
        time.sleep(0.1)

class AnimationRotate(Animation):

    def __init__(self, strip, vol):
        Animation.__init__(self, strip)
        self.vol = vol

    def show(self, new_vol):
        if (new_vol.value > 16):
            return
        if (new_vol.value <= 0):
            new_vol.value = 1
        self.clear(0)
        self.vol = new_vol.value
        self.draw_rect(3, 16 - self.vol, 2, self.vol, 0xFFFFFF)
        self.write()

class AnimationWeather(Animation):
    width = 8
    height = 8

    def __init__(self, strip):
        Animation.__init__(self, strip)
        dirs = glob.glob("image/weather/*/")
        names = [(x.split('/')[-2], x) for x in dirs]
        res = {}
        for k in names:
            f =  glob.glob(k[1] + "*.png")
            imgs = [Image.open(x).convert("RGB").load() for x in f]
            res[k[0]] = imgs
        self.pixels = res

    def show(self, dic, flip = False):
        if dic.condition not in self.pixels:
            return
        self.draw_image(0, 0, AnimationWeather.width, AnimationWeather.height,
                       self.pixels[dic.condition][0])
        color = 0xFFFFFF
        self.draw_number(dic.temperature % 10, 5, 9, color)
        self.draw_number(dic.temperature / 10, 1, 9, color)
        self.write(flip)

class AnimationTime(Animation):

    def show(self, second, flip = False):
        second = int(second)
        second %= (60 * 60 * 24)
        if second > 60 * 60:
            t1 = second / (60 * 60)
            t2 = (second % (60 * 60)) / 60
        else:
            t1 = second / 60
            t2 = second % 60
        color = 0xFFFFFF
        self.clear(0)
        self.draw_number(t1 % 10, 5, 1, color)
        self.draw_number(t1 / 10, 1, 1, color)
        self.draw_hline(5, 7, 3, color)
        self.draw_number(t2 % 10, 5, 9, color)
        self.draw_number(t2 / 10, 1, 9, color)
        self.write(flip)
