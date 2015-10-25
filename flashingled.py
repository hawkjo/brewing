import threading
import time

class FlashingLED:
    """ Flashing LED class
        The run() method will be started and it will run in the background
        until the application exits.
        """
    def __init__(self, led, interval=1):
        """ Constructor
                :type interval: int
                :param interval: Check interval, in seconds
                """
        self.led = led
        self.interval = interval

    def start(self):
        self.event = threading.Event()
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
        
    def run(self):
        """ Method that runs forever """
        while not self.event.isSet():
            self.led.turn_on()
            time.sleep(self.interval)
            self.led.turn_off()
            time.sleep(self.interval)

    def stop(self):
        self.event.set()
        self.led.turn_off()
