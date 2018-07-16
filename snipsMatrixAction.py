class Action(object):
    def __init__(self, value = 0):
        self.value = value

    def __trunc__(self):
        return int(self.value)
    def __str__(self):
        return "snipsMatrixAction.{} val: {}".format(self.__class__.__name__, str(self.value))

class Timer(Action):
    pass

class Time(Action):
    pass

class Rotate(Action):
    pass

class Weather(Action):
    def __init__(self, cond, temp):
        self.condition = cond
        self.temperature = temp

    def __trunc__(self):
        return int(self.temperature)

    def __str__(self):
        return "snipsMatrixAction.{} cond: {}, temp: {}".format(self.__class__.__name__,
                                                            str(self.condition),
                                                           self.temperature)

class Hotword(Action):
    pass

class Clear(Action):
    def __trunc__(self):
        return -1

class Exit(Action):
    pass

class CustomAnimation(Action):
    def __trunc__(self):
        return -1
