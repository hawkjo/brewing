import time
import os
import glob
import logging

# Plotting
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Thermometer:
    def __init__(self, log=True):
        # Set up the temperature probe
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        self.device_file = device_folder + '/w1_slave'

        self.temp_history = []
        self.log = log
        if self.log:
	    logging.basicConfig(
                    filename='temperature.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

    def read_temp_raw(self):
        """Read the raw temperatures"""
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines
    
    def read_temp(self):
        """Process raw temps"""
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            self.temp_history.append((time.time(), temp_f))
            if self.log:
                logging.info('%.2f F' % temp_f)
            return temp_f

    def plot_temp_history(self, annotation=None, fpath=None):
        times = np.asarray([(tm-self.temp_history[0][0])/3600.0 for tm, temp in self.temp_history])
        temps = np.asarray([temp for tm, temp in self.temp_history])
    
        window_size = int(0.06*temps.shape[0])
        if window_size % 2 != 0:
            window_size = window_size + 1
    
        average_times, average_temps = [], []
        for i in range(window_size/2, (temps.shape[0] - window_size/2)):
            average_times.append(np.mean(times[i-(window_size/2):i+(window_size/2)]))
            average_temps.append(np.mean(temps[i-(window_size/2):i+(window_size/2)]))
    
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.plot(times, temps,
                color='#3E4A89', alpha=0.6, linewidth = 0.60,label="raw temperature data")
        ax.plot(average_times, average_temps,
                color='#3E4A89', linewidth = 2.0,
                label="sliding window average. window size of "+str(window_size))
        
        ax.set_xlabel("time (h)")
        ax.set_ylabel("temperature (f)")
        ax.legend(loc='best', fancybox=True,prop={'size':10})
        title = "raw and smoothed temperature data"
        if annotation:
            title = '\n'.join([annotation, title])
        ax.set_title(title)
    
        if fpath is None:
            fpath = 'temp_history.pdf'
        fig.savefig(fpath, bbox_inches='tight')

        txt_fpath = fpath.replace('.pdf', '.txt')
        with open(txt_fpath, 'w') as out:
            out.write('\n'.join(['%g\t%g' % (tm, temp) for tm, temp in self.temp_history]))
            
        return fpath


if __name__ == "__main__":
    therm = Thermometer()
    while True:
        print therm.read_temp()
        time.sleep(1)
