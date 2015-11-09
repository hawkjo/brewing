import sys
import time
import os
import shutil

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
        self.state = 'normal'
        self.last_state_change_time = time.time()

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

    def run(self):
        # Starting main routing
        send_email('Starting fermenter at %gF' % self.target_temp)

        while True:
            self.regulate_and_record_temp()
            time.sleep(60)

    def regulate_and_record_temp(self):
        target_temp = self.get_target_temp()
        if target_temp != self.target_temp:
            temps = tuple(['off' if t == 'off' else '%gF' for t in (self.target_temp, target_temp)])
            send_email('Changing temperature from %s to %s' % temps)
            self.target_temp = target_temp

        try:        # try grabbing the current temp
            current_temp = self.therm.read_temp()
            stat_str = '%.2f (%g)' % (current_temp, self.target_temp)
        except:     # send an email if you can't
            send_email("can't read the temperature")
            time.sleep(2)

        # deal with target_temp=off
        if self.target_temp == 'off':
            self.set_state('normal')
            if self.fridge.turn_off():
                stat_str += ' on->off'
            else:
                stat_str += ' off'
            print stat_str
            self.temp_history.add_temp(time.time(), current_temp, -1, self.fridge.is_on())
            return

        # regulate the temperature:
        if current_temp > self.target_temp + 1.0:
            if self.fridge.turn_on():
                stat_str += ' off->on'
                self.set_state('normal')
            else:
                stat_str += ' on'
                if current_temp > self.target_temp + 2.0:
                    stat_str += '\tWarning: High Temperatures'
                    self.set_state('high_temp')

        elif current_temp < self.target_temp - 0.25:
            if self.fridge.turn_off():
                stat_str += ' on->off'
                self.set_state('normal')
            else:
                stat_str += ' off'
                if current_temp < self.target_temp - 2.0:
                    stat_str += '\tWarning: Low Temperatures'
                    self.set_state('low_temp')

        else:
            if self.fridge.is_on():
                stat_str += ' on'
            else:
                stat_str += ' off'

        print stat_str
        self.temp_history.add_temp(time.time(), current_temp, self.target_temp, self.fridge.is_on())

    def set_state(self, state):
        assert state in ['high_temp', 'low_temp', 'normal'], state
        if self.state == state == 'normal':
            return
        elif self.state != state:
            self.last_state_change_time = time.time()
        self.state = state

        if state == 'normal':
            subject = 'Returned to Normal Operation'
            title = 'State: Normal Operation'
            event_times = None
            event_labels = None
        elif state == 'high_temp':
            subject = 'Warning: High Temp'
            title = 'State: High Temp'
            event_times = [self.last_state_change_time],
            event_labels = ['High Temp Begun']
        else:
            subject = 'Warning: Low Temp'
            title = 'State: Low Temp'
            event_times = [self.last_state_change_time],
            event_labels = ['Low Temp Begun']

        # Send updates roughly logarithmically in time for the first day, then once a day
        min_since_last_change = int(time.time() - self.last_state_change_time) / 60
        times_to_contact = [0, 5, 10, 20] + range(30, 6*60, 30) + range(6*60, 24*60, 60)
        if min_since_last_change in times_to_contact or min_since_last_change % 24 * 60 == 0:
            # Send email with temp graph since state change and previous 12 hours
            start = self.last_state_change_time - 12 * 60 * 60 
            self.temp_history.plot_temp_history(
                    start=start,
                    stop=None,
                    subject=subject,
                    title=title,
                    event_times=event_times,
                    event_labels=event_labels,
                    email=True)

def set_target_temp(temp):
    if temp != 'off':
        assert 45 <= temp <= 80, 'Target temp out of range [45, 80]: %g' % temp
    with open('.tmp', 'w') as out:
        out.write(str(temp))
    shutil.move('.tmp', '.target_temp')
    print 'Temperature successfully set to', temp


if __name__ == '__main__':
    usage = """
fermenter.py action [args]

Actions:
    start
    set_target_temp <temp_F/off>
"""
    assert len(sys.argv) > 1, usage
    action = sys.argv[1]

    if action == 'start':
        assert len(sys.argv) == 2, usage
        fermenter = Fermenter()
        fermenter.run()
    elif action == 'set_target_temp':
        assert len(sys.argv) == 3, usage
        if sys.argv[1].lower() == 'off':
            temp = 'off'
        else:
            temp = float(sys.argv[1])
        set_target_temp(temp)
