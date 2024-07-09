import time
import numpy as np
from threading import Thread
from queue import Queue
from pymodaq_plugins_qutools.hardware.QuTAG_HR import QuTAG


class QutagController:

    def __init__(self):
        self.device = None
        self.report_queue_size = False
        self.data_queue = Queue()

    def connect(self):
        if self.device is not None:
            raise RuntimeError("qutag device already initialised")
        self.device = QuTAG()
        self.device.enableChannels(True)

    def disconnect(self):
        if self.device is not None:
            self.device.deInitialize()
            self.device = None

    def update_hist(self):
        self.hist_step = (self.hist_end - self.hist_start) / self.n_bins

    def init_tagging(self):
        self.fs = [None, None]
        self.ps = None

    def grab_hist(self, seconds):

        def add_to_hist(diff):
            diffs.append(diff)

        end = time.time() + seconds
        diffs = []
        self.init_tagging()
        while time.time() < end:
            tags = self.device.getLastTimestamps(reset=True)
            self.process_tags(tags, add_to_hist)

        hist = np.zeros(self.n_bins)
        for item in diffs:
            idx = min(int((item - self.hist_start) / self.hist_step),
                      self.n_bins - 1)
            hist[max(idx, 0)] += 1

        return hist

    def grab_item(self): # dummy for now
        # << clear tagger buffer
        print("grabbing item")

        def get_tag(tag):
            self.diff = tag

        self.diff = None
        self.init_tagging()
        while self.diff is None:
            tags = self.device.getLastTimestamps(reset=True)
            self.process_tags(tags, get_tag)
        return self.diff

    def start_tagging(self, callback):
        if hasattr(self, 'thread') and self.thread.is_alive():
            return
        self.callback = callback
        self.stop = False
        self.thread = Thread(target=self.tagger_loop)
        self.thread.start()

    def stop_tagging(self):
        self.stop = True
        if self.thread.is_alive():
            self.thread.join()

    def tagger_loop(self):
        # << clear tagger buffer
        def store_tag(tag):
            self.data_queue.put(tag)
        self.init_tagging()
        while not self.stop:
            tags = self.device.getLastTimestamps(reset=True)
            self.process_tags(tags, store_tag)
            rc = self.device.getDataLost()
            if rc:
                print("Data loss", rc)
            qs = self.data_queue.qsize()
            if qs:
                if self.report_queue_size:
                    self.callback(self.data_queue.get(), qs)
                else:
                    self.callback(self.data_queue.get())

    def process_tags(self, tags, callback):
        for i in range(tags[2]):
            value = int(tags[0][i])
            channel = tags[1][i]
            if channel == 0:
                if self.fs[0] is None:
                    self.fs[0] = value
                elif self.fs[1] is None:
                    self.fs[1] = value
            elif channel == 1:
                if self.ps is None:
                    self.ps = value
            else: # glitch
                continue

            if self.fs[0] is None or self.fs[1] is None or self.ps is None:
                continue

            callback((self.ps - min(self.fs)) * 1e-12)
            self.init_tagging()


class QutagControllerSimu(QutagController):

    def grab_hist(self, seconds):
        diffs = np.random.normal(self.delay, self.jitter,
                                 int(self.rep_rate * seconds))
        hist = np.zeros(self.n_bins)
        for item in diffs:
            idx = min((item - self.hist_start) / self.hist_step, self.hist_end)
            hist[max(idx, 0)] += 1

    def tagger_loop(self):
        self.stop = False
        while not self.stop:
            diff = self.data_queue.get()
            self.callback(diff)
