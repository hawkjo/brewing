import os
import numpy as np
import math
import time
import h5py
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from emailing import send_email


class TempHistory(object):
    """ Records temperature history: time, temp, target temp, fridge state.
        
        The time storage is implicit, where each row represents one minute.
        Temperatures are recorded with 2 sig figs.
        Fridge state is 0 or 1.
        """
    def __init__(self, fname, seconds_per_dset=10000000):
        self.filename = fname
        if not os.path.isfile(self.filename):
            with h5py.File(self.filename, 'w') as f:
                f.attrs['seconds_per_dset'] = seconds_per_dset

        with h5py.File(self.filename, 'r') as f:
            self.seconds_per_dset = f.attrs['seconds_per_dset']
        self.entries_per_chunk = math.ceil(self.seconds_per_dset/60.0)

    def dset_name_and_entry(self, tme):
        if tme < 0:
            with h5py.File(self.filename, 'r') as f:
                dset_name, entry = self.get_last_entry()
            tme = int(dset_name)*self.seconds_per_dset + entry * 60 + 1 + tme
        d, r = divmod(tme, self.seconds_per_dset)
        return str(int(d)), int(r/60)

    def set_first_entry(self):
        with h5py.File(self.filename, 'r+') as f:
            dset_name = min(f.keys(), key=int)
            dset = f[dset_name]
            target_temps = dset[:, 2]
            entry = next(i for i, tt in enumerate(target_temps) if tt != 0)
            f.attrs['first_dset_name'] = dset_name
            f.attrs['first_entry'] = entry

    def get_first_entry(self):
        with h5py.File(self.filename, 'r') as f:
            return f.attrs['first_dset_name'], f.attrs['first_entry']

    def set_last_entry(self, dset_name, entry):
        with h5py.File(self.filename, 'r+') as f:
            f.attrs['last_dset_name'] = dset_name
            f.attrs['last_entry'] = entry

    def get_last_entry(self):
        with h5py.File(self.filename, 'r') as f:
            return f.attrs['last_dset_name'], f.attrs['last_entry']

    def add_temp(self, tme, temp, target, fridge_state):
        dset_name, entry = self.dset_name_and_entry(tme)
        temp = int(round(100*temp))
        target = int(round(100*target))
        fridge_state = int(fridge_state)

        with h5py.File(self.filename, 'r+') as f:
            if dset_name not in f:
                f.create_dataset(dset_name, (self.entries_per_chunk, 3), dtype='i')
            f[dset_name][entry] = [temp, target, fridge_state]
        self.set_last_entry(dset_name, entry)

    def __getitem__(self, val):
        with h5py.File(self.filename, 'r') as f:
            if isinstance(val, int) or isinstance(val, float):
                dset_name, entry = self.dset_name_and_entry(val)
                res = np.zeros((4,), dtype=np.float)
                res[1:] = f[dset_name][entry]
                res[1:3] /= 100.0
                return res

            elif isinstance(val, slice):
                dset_name, entry = {}, {}
                if val.start is None:
                    if 'first_entry' not in f.attrs:
                        self.set_first_entry()
                    dset_name['start'], entry['start'] = self.get_first_entry()
                    val = slice(int(dset_name['start']) * self.seconds_per_dset + entry['start'] * 60,
                            val.stop,
                            val.step)
                else:
                    dset_name['start'], entry['start'] = self.dset_name_and_entry(val.start)

                if val.stop is None:
                    dset_name['stop'], entry['stop'] = self.get_last_entry()
                    val = slice(val.start,
                            int(dset_name['stop']) * self.seconds_per_dset + entry['stop'] * 60,
                            val.step)
                else:
                    dset_name['stop'], entry['stop'] = self.dset_name_and_entry(val.stop)

                if int(dset_name['start']) > int(dset_name['stop']):
                    return None
                elif dset_name['start'] == dset_name['stop']:
                    res = f[dset_name['start']][entry['start'] : entry['stop'] + 1]
                else:
                    # Collect all entries from disparate data sets
                    res = f[dset_name['start']][entry['start']:]
                    for dsname in map(str,
                            range(int(dset_name['start']) + 1, int(dset_name['stop']))):
                        res = np.r_[res, f[dsname][:]]
                    res = np.r_[res, f[dset_name['stop']][:entry['stop'] + 1]]
            else:
                raise ValueError('__getitem__ only support scalars and slices at the moment')

        # Add times and return temps to float values
        start = int(val.start)
        stop = start + 60 * res.shape[0]
        res = np.c_[np.arange(start, stop, 60), res][::val.step]
        res = res.astype(np.float)
        res[:, 1:3] /= 100
        return res

    def plot_temp_history(self,
            start=None,
            stop=None,
            step=1,
            title=None,
            landmarks=None,
            landmark_labels=None,
            fpath=None,
            email=False):
        history = self[start:stop:step]
        target_temps = history[:, 2]
        bad_idxs = [i for i, tt in enumerate(target_temps) if tt == 0]
        history = np.delete(history, bad_idxs, axis=0)

        times = history[:, 0]
        if landmarks is not None:
            landmarks = [(lm - times[0]) / 3600.0 for lm in landmarks]
            if landmark_labels is None:
                landmark_labels = [None for lm in landmarks]
            else:
                assert len(landmarks) == len(landmark_labels)
        times = (times - times[0]) / 3600.0

        temps = history[:, 1]
        target_temps = history[:, 2]
        fridge_states = history[:, 3]

        state = fridge_states[0]
        on_temps, off_temps = [], []
        for t, fs in zip(temps, fridge_states):
            if fs != state:
                state = fs
                on_temps.append(t)
                off_temps.append(t)
            elif fs:
                on_temps.append(t)
                off_temps.append(None)
            else:
                off_temps.append(t)
                on_temps.append(None)

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.plot(times, on_temps,
                color='b', linewidth = 1.60,label='fridge on')
        ax.plot(times, off_temps,
                color='b', linewidth = 0.60,label='fridge off')
        ax.plot(times, target_temps, '-.',
                color='k', alpha=0.3, linewidth = 0.40, label='target')
        for lm, lm_label in zip(landmarks, landmark_labels):
            ax.plot([lm, lm], ax.get_ylim(), ':',
                    color='r', alpha=0.3, linewidth=2, label=lm_label)
        
        ax.set_xlabel("time (h)")
        ax.set_ylabel("temperature (f)")
        ax.legend(loc='best', fancybox=True,prop={'size':10})
        if title:
            ax.set_title(title)
    
        if fpath is None:
            fpath = os.path.splitext(self.filename)[0] + '.pdf'
        fig.savefig(fpath, bbox_inches='tight')

        if email:
            send_email('Temperature history.', attachment_fpath=fpath)

        return fpath