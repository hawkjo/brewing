import sys
import time
import os

# Scheduling and emailing
# use pip install apscheduler==2.1.2
# see here: https://pythonadventures.wordpress.com/2013/08/06/apscheduler-examples/
from apscheduler.scheduler import Scheduler # for checking the temperature at regular intervals

# Control
import RPi.GPIO as GPIO  # for manipulating pins
import outputs
import thermometer
from flashingled import FlashingLED

# Record keeping
import logging
from emailing import send_email

#--------------------------------------------------
# Setup specific parameters
PIN_MODE = GPIO.BCM
FRIDGE_PIN = 17
LED_PIN = 18  # Set to None if no led desired
BREWING_TOP_DIR = '/home/pi/brewing'
#--------------------------------------------------

def print_and_log(s):
    print s
    logging.info(s)

def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d hours %d minutes %d seconds" % (h, m, s)


class Fermenter:
    def __init__(self, brew_dir='.'):
        os.chdir(brew_dir)
        self.name_of_brew = os.path.basename(os.getcwd())
        assert os.getcwd() == os.path.join(BREWING_TOP_DIR, self.name_of_brew)

        t_fname = 'temperature_profile.txt'
        self.times_and_temps = [map(float, line.strip().split()) for line in open(t_fname)
                                if not line.strip().startswith('#')]

        self.therm = thermometer.Thermometer()
        GPIO.setmode(PIN_MODE)
        self.fridge = outputs.OutputObject(FRIDGE_PIN)
        if LED_PIN is not None:
            self.flashingled = FlashingLED(outputs.OutputObject(LED_PIN))
            self.flashingled.start()

        logging.basicConfig(filename='brew.log',
                level=logging.DEBUG,
                format='%(asctime)s %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p')

        self.plot_fname = '%s_temp_history.pdf' % self.name_of_brew

    def __del__(self):
        self.fridge.turn_off()
        self.flashingled.stop()

    def send_email_with_graph(self, message):
        attachment_fpath = self.therm.plot_temp_history(self.name_of_brew, self.plot_fname)
        send_email(message, attachment_fpath)

    def run(self):
        # Print intentions
        print_and_log('Starting run "%s"' % self.name_of_brew)
        print
        print_and_log('Intended Schedule:')
        print_and_log('\t'.join(['Time(h)', 'Temp(F)']))
        for time, temp in self.times_and_temps:
            print_and_log('%g\t%g' % (time, temp))
        print_and_log('Total time: %g hours' % sum(tm for tm, temp in self.times_and_temps))
        print

        # start email scheduler
        email_sched = Scheduler()
        email_sched.start()
        text = "It's been twelve hours. Here are the latest temperature readings from your new brew"
        email_job = email_sched.add_interval_job(
                self.send_email_with_graph,
                hours=12,
                args=[text])

        # Starting main routing
        send_email('Starting job %s' % self.name_of_brew)

        for duration, temp in self.times_and_temps:
            text = "Changing temperature to %.2f for %.1f hours." % (temp, duration)
            send_email(text)
            print_and_log(text)
            self.recordAndRegulateTemp(duration, temp)

        print_and_log("Program done. Fermenter shutting down.")
        self.send_email_with_graph("Ending. Fermenter is shutting off. Final temp history figure attched.")
        email_sched.unschedule_job(email_job)
        self.fridge.turn_off()
        self.flashingled.stop()

    def recordAndRegulateTemp(self, number_of_hours, temp):
        sched = Scheduler()
        sched.start()
        self.my_job(temp)
        job = sched.add_interval_job(self.my_job, minutes=5, args=[temp])
    
        start_time = time.time()
        while True:
            time_left = (3600 * number_of_hours) - (time.time() - start_time)
            if time_left <= 0:
                break
            text = "time left: %s\n" % format_time(time_left)
            sys.stdout.write(text); sys.stdout.flush()
            time.sleep(60)
    
        sched.unschedule_job(job)

    def my_job(self, temp):
        try:
            # try grabbing to current temp and writing it to the csv file
            current_temp = self.therm.read_temp()
            print_and_log('temperature is %.2f (target %g)' % (current_temp, temp))
        except: # send an email if you can't
            send_email("can't read the temperature")
            time.sleep(2)
    
        # now to regulate the temperature:
        if current_temp > (temp + 1):
            if self.fridge.turn_on():
                print_and_log('turning on the fridge')
            else:
                print_and_log('fridge on and remaining on')
        else:
            if self.fridge.turn_off():
                print_and_log('turning off the fridge')
            else:
                print_and_log('fridge off and remaining off')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        brew_dir = '.'
    elif len(sys.argv) == 2:
        brew_dir = sys.argv[1]
    else:
        sys.exit('Usage: ferment.py [<directory>]')

    fermenter = Fermenter(brew_dir)
    fermenter.run()
