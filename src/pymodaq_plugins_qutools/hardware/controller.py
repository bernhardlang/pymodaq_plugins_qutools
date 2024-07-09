import time
import numpy as np
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG


class QutagController:

    def __init__(self):
        self.device = None

    def connect(self):
        if self.device is not None:
            raise RuntimeError("qutag device already initialised")
        self.device = QuTAG()
        self.qutag.enableChannels(True)
        self.qutag.setExposureTime(100)

    def disconnect(self):
        if self.device is not None:
            self.device.deInitialize()
            self.device = None

    def controller.update_hist(self):
        self.hist_step = (self.hist_end - self.hist_start) / self.n_bins

    def grab_hist(self, seconds):
        end = time.time() + seconds
        diffs = []
        self.start = None
        while time.time() < end:
            tags = qutag.getLastTimestamps(reset=True)
            if self.process_tags(tags):
                diffs.append(ps - fs)

        hist = np.zeros(self.n_bins)
        for item in diffs:
            idx = min(item - self.hist_start) / self.hist_step, self.hist_end)
            hist[max(idx, 0)] += 1

        return hist

    def tagger_loop(self):
        self.start = None
        self.stop = False
        # << clear tagger buffer
        while not self.stop:
            tags = qutag.getLastTimestamps(reset=True)
            if self.process_tags(tags):
                self.callback(ps - fs)

    def process_tags(self, tags):
        for i,channel in enumerate(tags[1]):
            if self.start is None:
                if channel == 0:
                    self.start = tags[0][i]
                    self.fs = None
                    self.ps = None
            elif channel == 1:
                if self.ps is None: # should never be other then None
                    self.ps = int(results[0][i])
            elif channel == 2:
                if self.fs is None:
                    self.fs = int(results[0][i])
            if self.fs is None or self.ps is None:
                return False
            self.start = None
            return True


class QutagControllerSimu:

    def connect(self):
        pass

    def disconnect(self):
        pass

    def grab_hist(self, seconds):
        diffs = np.random.normal(self.delay, self.jitter,
                                 int(self.rep_rate * seconds))
        hist = np.zeros(self.n_bins)
        for item in diffs:
            idx = min(item - self.hist_start) / self.hist_step, self.hist_end)
            hist[max(idx, 0)] += 1

    def tagger_loop(self):
        self.stop = False
        while not self.stop:
            diff = self.data_queue.get()
            self.callback(diff)
