import os
import numpy as np
import math
import h5py


class TempHistory(object):
    """ Records temperature history: time, temp, target temp, fridge state.
        
        The time storage is implicit, where each row represents one minute.
        Temperatures are recorded with 2 sig figs.
        Fridge state is 0 or 1.
        """
    def __init__(self, fname, seconds_per_dset=10000000):
        self.filename = fname
        if not os.isfile(self.filename):
            with h5py.File(self.filename, 'w') as f:
                f.attrs['seconds_per_dset'] = seconds_per_dset

        with h5py.File(self.filename, 'r') as f:
            self.seconds_per_dset = f.attrs['seconds_per_dset']
        self.entries_per_chunk = math.ceil(self.seconds_per_dset/60.0)

    def dset_name_and_entry(self, tme):
        if tme < 0:
            dset_name, entry = self.last_entry
            tme = int(dset_name) + entry * 60 + 1 + tme
        d, r = divmod(tme, self.seconds_per_dset)
        return str(int(d)), int(r/60)

    def add_temp(self, tme, temp, target, fridge_state):
        dset_name, entry = self.dset_name_and_entry(tme)
        temp = int(100*temp)
        target = int(100*temp)
        fridge_state = int(fridge_state)

        with h4py.File(self.filename, 'r+') as f:
            if dset_name not in f:
                f.create_dataset(dset_name, (entries_per_chunk, 3), dtype='i')
            f[dset_name][entry] = [temp, target, fridge_state]
        self.last_entry = (dset_name, entry)

    def __getitem__(self, val):
        with h5py.File(self.filename, 'r') as f:
            if isinstance(val, int) or isinstance(val, float):
                dset_name, entry = self.dset_name_and_entry(val)
                res = np.zeros((4,), dtype=np.float)
                res[1:] = f[dset_name][entry]
                res[1:3] = res[1:3]/100.0
                return res

            elif isinstance(val, slice):
                # Deal with None starts and stops
                if val.start is None:
                    val = slice(min(map(int, f.keys())), val.stop, val.step)
                if val.stop is None:
                    val = slice(val.start,
                                max(map(int, f.keys())) + self.seconds_per_dset - 1,
                                val.step)

                dset_name, entry = {}, {}
                for pos in ['start', 'stop']:
                    dset_name[pos], entry[pos] = self.dset_name_and_entry(getattr(val, pos))

                if int(dset_name['start']) > int(dset_name['stop']):
                    return None
                elif dset_name['start'] == dset_name['stop']:
                    res = f[dset_name['start']][entry['start'] : entry['stop']]
                else:
                    # Collect all entries from disparate data sets
                    res = f[dset_name['start']][entry['start']:]
                    for dsname in map(str,
                            range(int(dset_name['start']) + 1, int(dset_name['stop']))):
                        res = np.r_[res, f[dsname][:]]
                    res = np.r_[res, f[dset_name['stop']][:entry['stop']]]
            else:
                raise ValueError('__getitem__ only support scalars and slices at the moment')

        # Add times and return temps to float values
        res = np.c_[np.arange(val.start, val.stop, 60), res][::val.step]
        res = res.astype(np.float)
        res[:, 1:3] /= 100
        return res
