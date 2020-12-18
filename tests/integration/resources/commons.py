import json
import os
from statistics import mean
import time


class Measurer:
    def __init__(self, measurements_path):
        self.measurements_path = measurements_path

    def time_that(self, f, json_keyword, n_times=1, **kwargs):
        times = []
        for i in range(n_times):
            start = time.time()
            try:
                output = f(**kwargs)
            except Exception:
                output = None
            finally:
                stop = time.time()
            times.append(stop - start)
        self.dump(keyword=json_keyword, value=mean(times))
        return output

    def dump(self, keyword, value):
        measurements = self.get_measurements()
        measurements[keyword] = value
        with open(self.measurements_path, 'w+') as f:
            json.dump(measurements, f, indent=2, sort_keys=True)

    def get_measurements(self):
        if os.path.isfile(self.measurements_path):
            with open(self.measurements_path) as f:
                measurements = json.load(f)
        else:
            measurements = {}
        return measurements


def read_configs(path):
    with open(path, 'r') as f:
        configs = json.load(f)
    return configs
