import RPi.GPIO as GPIO
import os

#--------------------------------------------------
# Setup-specific parameters
pin_mode = GPIO.BCM
fridge_pin = 17
led_pin = 18  # Set to None if no led desired
brewing_top_dir = '/home/pi/brewing'
#--------------------------------------------------

data_dir = os.path.join(brewing_top_dir, 'data')
src_dir = os.path.join(brewing_top_dir, 'src')

target_temp_fpath = os.path.join(src_dir, 'target_temp.txt')
temp_history_fpath = os.path.join(data_dir, 'temp_history.h5')

