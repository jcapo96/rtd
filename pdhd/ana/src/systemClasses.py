from src import sensorClasses
import pandas as pd
from tqdm import tqdm

class System():
    def __init__(self, dataset, name):
        self.dataset = dataset
        self.name = name
        self._info()
        self._data()

    def _info(self):
        self.system = pd.read_csv(f"/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/baseline.csv", header=0)
        self.system = self.system.loc[self.system["SYSTEM"]==self.name].reset_index(drop=True)
        if len(self.system) == 0:
            self.system = None
            print(f"ERROR: System ({self.name}) not found")
        return self

    def _data(self):
        self.sensors = {}
        if self.system is not None:
            for index, row in tqdm(self.system.iterrows(), desc="Initializing Sensors", total=len(self.system), unit="sensor"):
                self.sensors[int(row["CAL-ID"])] = sensorClasses.Sensor(self.dataset, row["CAL-ID"])
        if len(self.sensors) > 0:
            self.ids = self.sensors.keys()
        return self


    def muxEqualization(self, equalizationName="FIRST_POFF_39644_39619_39614_40200_39607_39669", equalizationSumName="HP-OFFSETS"):
        if len(self.sensors) > 0:
            for index, value in tqdm(self.sensors.items(), desc="Equalizing Sensors", unit="sensor"):
                self.sensors[index] = value.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        return self

    def tempCalibration(self, calibName="LAR2023_TREE_AVG", ref="40525"):
        if len(self.sensors)>0:
            for index, value in tqdm(self.sensors.items(), desc=f"Calibrating Sensors - Calibration Name: {calibName}", unit="sensor"):
                self.sensors[index] = value.tempCalibration(calibName=calibName, ref=ref)
        return self

    def calibrate(self, calibName="LAR2023_TREE_AVG", ref="40525", equalizationName="FIRST_POFF_39644_39619_39614_40200_39607_39669", equalizationSumName="HP-OFFSETS"):
        self.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        self.tempCalibration(calibName=calibName, ref=ref)
        return self
