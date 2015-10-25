import sys
import RPi.GPIO as GPIO
import time


class OutputObject:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def is_on(self):
        return GPIO.input(self.pin)

    def turn_on(self):
        if not self.is_on():
            GPIO.output(self.pin, True)
            return 1
        else:
            return 0

    def turn_off(self):
        if self.is_on():
            GPIO.output(self.pin, False)
            return 1
        else:
            return 0

    def loop(self, wait_time=1):
        self.turn_off()
        while True:
          assert self.turn_on()
          time.sleep(wait_time)
          assert self.turn_off()
          time.sleep(wait_time)


if __name__ == '__main__':
    from ferment import FRIDGE_PIN, LED_PIN, PIN_MODE
    GPIO.setmode(PIN_MODE)
    for pin in [LED_PIN, FRIDGE_PIN]:
        thing = OutputObject(pin)
        thing.turn_off()
