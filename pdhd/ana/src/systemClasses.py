from src import sensorClasses
import pandas as pd

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
            for index, row in self.system.iterrows():
                self.sensors[int(row["CAL-ID"])] = sensorClasses.Sensor(self.dataset, row["CAL-ID"])
        if len(self.sensors) > 0:
            self.ids = self.sesnors.keys()
        return self

    def tempCalibration(self, calibName="LAR2023_TREE_AVG", ref="40525"):
        if len(self.sensors)>0:
            for index, value in self.sensors.items():
                self.sensors[index] = value.tempCalibration(calibName=calibName, ref=ref)
        return self
