import sys
import time
import os

# Control
import RPi.GPIO as GPIO
import local_config
import outputs
import thermometer
from temp_history import TempHistory

# Record keeping
from emailing import send_email


class Fermenter:
    def __init__(self):
        # Setup temperature input, control, and history
        self.target_temp = self.get_target_temp()
        self.therm = thermometer.Thermometer()
        self.temp_history = TempHistory(local_config.temp_history_fpath)

        # Setup outputs
        GPIO.setmode(local_config.pin_mode)
        self.fridge = outputs.OutputObject(local_config.fridge_pin)
        if local_config.led_pin is not None:
            self.flashingled = outputs.FlashingLED(local_config.led_pin)
            self.flashingled.start()

    def __del__(self):
        self.fridge.turn_off()
        self.flashingled.stop()

    def get_target_temp(self):
        """ Reads target temp from file.
        
            Target temp file must contain either a single scalar or the word 'off'.
            """
        for line in open('.target_temp'):
            temp = line.strip()
            if temp == 'off':
                return temp
            return float(temp)

    def send_email_with_graph(self, title=''):
        start = -12 * 60 * 60
        self.temp_history.plot_temp_history(
            start=start,
            title=title,
            email=True)

    def run(self):
        # Starting main routing
        send_email('Starting fermenter at %gF' % self.target_temp)

        while True:
            self.regulate_and_record_temp()
            time.sleep(60)

    def regulate_and_record_temp(self):
        target_temp = self.get_target_temp()
        if target_temp != self.target_temp:
            send_email('Changing temperature from %gF to %gF' % (self.target_temp, target_temp))
            self.target_temp = target_temp
        try:
            # try grabbing to current temp
            current_temp = self.therm.read_temp()
            stat_str = '%.2f (%g)' % (current_temp, self.target_temp)
        except: # send an email if you can't
            send_email("can't read the temperature")
            time.sleep(2)
    
        # now to regulate the temperature:
        if current_temp > (self.target_temp + 1.0):
            if self.fridge.turn_on():
                stat_str += ' off->on'
            else:
                stat_str += ' on'
                if current_temp > (self.target_temp + 2.0):
                    self.send_email_with_graph('Warning: High Temperatures')
                    stat_str += '\tWarning: High Temperatures'
        elif current_temp < (self.target_temp) - 0.25:
            if self.fridge.turn_off():
                stat_str += ' on->off'
            else:
                stat_str += ' off'
        else:
            if self.fridge.is_on():
                stat_str += ' on'
            else:
                stat_str += ' off'

        print stat_str
        self.temp_history.add_temp(time.time(), current_temp, self.target_temp, self.fridge.is_on())

if __name__ == '__main__':
    if len(sys.argv) != 1:
        sys.exit('Usage: ferment.py')

    fermenter = Fermenter()
    fermenter.run()
