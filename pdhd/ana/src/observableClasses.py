from . import systemClasses
import pandas as pd

class Bulk:
    def __init__(self, dataset, system_name="TGRAD", calibName="SECOND_POFF_TGRAD_HAWAI_APA_CE_OFF_REC_OFF_HV_OFF_20241203_134500_20241203_141500"):
        self.calibName = calibName
        self.dataset = dataset
        self.system_name = system_name
        self.system = systemClasses.System(self.dataset, self.system_name)
        self._calibrate()

    def _calibrate(self):
        self.system.calibrate(calibName=self.calibName)
        return self

    def define_bottom(self, h0=0, hf=1000):
        self.bottom_sensors = {}
        for id, sensor in self.system.sensors.items():
            # if (self.system_name == "APA") and ("F" in sensor.name) and (("APA3" not in sensor.name) or ("APA4" not in sensor.name)):
            #     continue
            if sensor.Y > h0 and sensor.Y < hf:
                self.bottom_sensors[sensor.id] = sensor
        return self

    def define_middle(self, h0=1000, hf=5000):
        self.middle_sensors = {}
        for id, sensor in self.system.sensors.items():
            # if (self.system_name == "APA") and ("F" in sensor.name):
            #     continue
            if sensor.Y >= h0 and sensor.Y < hf:
                self.middle_sensors[sensor.id] = sensor
        return self

    def define_top(self, h0=5000, hf=8000):
        self.top_sensors = {}
        for id, sensor in self.system.sensors.items():
            # if (self.system_name == "APA") and ("F" in sensor.name):
            #     continue
            if sensor.Y >= h0 and sensor.Y < hf:
                self.top_sensors[sensor.id] = sensor
        return self

    def define(self):
        if len(self.system.sensors) == 0:
            raise ValueError("No sensors defined in the system.")
        if not hasattr(self, 'bottom_sensors'):
            self.define_bottom()
        if not hasattr(self, 'middle_sensors'):
            self.define_middle()
        if not hasattr(self, 'top_sensors'):
            self.define_top()
        # Merge sensor data into self.bottom, adding each as a new column
        self.bottom = pd.DataFrame()
        for id, sensor in self.bottom_sensors.items():
            sensor_df = sensor.data.squeeze()
            self.bottom[id] = sensor_df
        # Keep only the mean and std columns in self.bottom
        self.bottom['mean'] = self.bottom.mean(axis=1)
        self.bottom['std'] = self.bottom.std(axis=1)
        self.bottom = self.bottom[['mean', 'std']]

        self.middle = pd.DataFrame()
        for id, sensor in self.middle_sensors.items():
            sensor_df = sensor.data.squeeze()
            self.middle[id] = sensor_df
        self.middle['mean'] = self.middle.mean(axis=1)
        self.middle['std'] = self.middle.std(axis=1)
        self.middle = self.middle[['mean', 'std']]

        self.top = pd.DataFrame()
        for id, sensor in self.top_sensors.items():
            sensor_df = sensor.data.squeeze()
            self.top[id] = sensor_df
        self.top['mean'] = self.top.mean(axis=1)
        self.top['std'] = self.top.std(axis=1)
        self.top = self.top[['mean', 'std']]
        return self
