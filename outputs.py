import sys
import RPi.GPIO as GPIO
import threading
import time


class OutputObject(object):
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)

    def is_on(self):
        return GPIO.input(self.pin)

    def turn_on(self):
        if not self.is_on():
            GPIO.output(self.pin, True)
            return 1  # True if changed
        else:
            return 0

    def turn_off(self):
        if self.is_on():
            GPIO.output(self.pin, False)
            return 1  # True if changed
        else:
            return 0

    def loop(self, wait_time=1):
        self.turn_off()
        while True:
          assert self.turn_on()
          time.sleep(wait_time)
          assert self.turn_off()
          time.sleep(wait_time)

        
class FlashingLED(OutputObject):
    """ Flashing LED class
        The run() method will be started and it will run in the background
        until the application exits.
        """
    def __init__(self, pin, interval=1):
        """ Constructor
                :type interval: int
                :param interval: Check interval, in seconds
                """
        super(FlashingLED, self).__init__(pin)
        self.interval = interval

    def start(self):
        self.event = threading.Event()
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
        
    def run(self):
        """ Method that runs forever """
        while not self.event.isSet():
            self.turn_on()
            time.sleep(self.interval)
            self.turn_off()
            time.sleep(self.interval)

    def stop(self):
        self.event.set()
        self.turn_off()


if __name__ == '__main__':
    from ferment import FRIDGE_PIN, LED_PIN, PIN_MODE
    GPIO.setmode(PIN_MODE)
    for pin in [LED_PIN, FRIDGE_PIN]:
        thing = OutputObject(pin)
        thing.turn_off()
