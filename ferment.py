import sys
import time
import os

# Control
import RPi.GPIO as GPIO
import local_config
import outputs
import thermometer
from apscheduler.scheduler import Scheduler # for emailing and checking temp at regular intervals

# Record keeping
import logging
from emailing import send_email

def print_and_log(s):
    print s
    logging.info(s)

def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return "%d days %d hours %d minutes %d seconds" % (d, h, m, s)


class Fermenter:
    def __init__(self:
        self.target_temp = self.get_target_temp()
        self.therm = thermometer.Thermometer()
        GPIO.setmode(local_config.pin_mode)
        self.fridge = outputs.OutputObject(local_config.fridge_pin)
        if local_config.led_pin is not None:
            self.flashingled = outputs.FlashingLED(local_config.led_pin)
            self.flashingled.start()

        logging.basicConfig(filename='brew.log',
                level=logging.DEBUG,
                format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p')

    def __del__(self):
        self.fridge.turn_off()
        self.flashingled.stop()

    def get_target_temp(self):
        """ Reads target temp from file.
        
            Target temp file must contain either a single scalar or the word 'off'.
            """
        for line in open(local_config.target_temp_fpath):
            temp = line.strip()
            if temp == 'off':
                return temp
            return float(temp)

    def send_email_with_graph(self, message, title=''):
        attachment_fpath = self.therm.plot_temp_history(title, 'email.pdf')
        send_email(message, attachment_fpath)

    def run(self):
        print_and_log('Starting fermenter')

        # start email scheduler
        email_sched = Scheduler()
        email_sched.start()
        text = "It's been twelve hours. Here are the latest temperature readings from your new brew"
        email_job = email_sched.add_interval_job(
                self.send_email_with_graph,
                hours=12,
                args=[text])

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
            # try grabbing to current temp and writing it to the csv file
            current_temp = self.therm.read_temp()
            print_and_log('temperature is %.2f (target %g)' % (current_temp, self.target_temp))
            self.temp_history.add_temp(time.time(), current_temp, self.target_temp)
        except: # send an email if you can't
            send_email("can't read the temperature")
            time.sleep(2)
    
        # now to regulate the temperature:
        if current_temp > (self.target_temp + 1.0):
            if self.fridge.turn_on():
                print_and_log('turning on the fridge')
            else:
                print_and_log('fridge on and remaining on')
        elif current_temp < (self.target_temp) - 0.25:
            if self.fridge.turn_off():
                print_and_log('turning off the fridge')
            else:
                print_and_log('fridge off and remaining off')
        else:
            if self.fridge.is_on():
                print_and_log('fridge on and remaining on')
            else:
                print_and_log('fridge off and remaining off')


if __name__ == '__main__':
    if len(sys.argv) != 1, 
        sys.exit('Usage: ferment.py')

    fermenter = Fermenter()
    fermenter.run()
