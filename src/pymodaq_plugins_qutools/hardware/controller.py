import time
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

    def grab(self, seconds):
        end = time.time() + seconds
        diffs = []
        while time.time() < end:
            no, result may contain multiple items ...
            while True:
                result = qutag.getLastTimestamps(reset=True)
                if result[1] == 0:
                    start = result[0]
                    continue
                break
            # result[0] tags, result[1] channel in which tag occured
