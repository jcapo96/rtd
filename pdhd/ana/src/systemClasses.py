from src import sensorClasses
import pandas as pd
from tqdm import tqdm
import datetime

class System():
    def __init__(self, dataset, name):
        self.dataset = dataset
        self.name = name
        self.is_single_profile = False
        self.is_multiple_profiles = False
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
            for index, row in tqdm(self.system.iterrows(), desc=f"Initializing {self.name} Sensors", total=len(self.system), unit="sensor"):
                self.sensors[int(row["CAL-ID"])] = sensorClasses.Sensor(self.dataset, row["CAL-ID"])
        if len(self.sensors) > 0:
            self.ids = self.sensors.keys()
        return self

    def muxEqualization(self, equalizationName="FIRST_POFF_39644_39619_39614_40200_39607_39669", equalizationSumName="HP-OFFSETS"):
        if len(self.sensors) > 0:
            for index, value in tqdm(self.sensors.items(), desc=f"Equalizing {self.name} Sensors", unit="sensor"):
                self.sensors[index] = value.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        return self

    def muxContinuity(self, equalizationName="FIRST_POFF_39644_39619_39614_40200_39607_39669", equalizationSumName="HP-OFFSETS"):
        if len(self.sensors) > 0:
            for index, value in tqdm(self.sensors.items(), desc=f"Continuity {self.name} Sensors", unit="sensor"):
                self.sensors[index] = value.muxContinuity(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        return self

    def tempCalibration(self, calibName="LAR2023_TREE_AVG", ref="40525"):
        if len(self.sensors)>0:
            for index, value in tqdm(self.sensors.items(), desc=f"Calibrating {self.name} Sensors - Calibration Name: {calibName}", unit="sensor"):
                self.sensors[index] = value.tempCalibration(calibName=calibName, ref=ref)
        return self

    def calibrate(self, calibName="LAR2023_TREE_AVG", ref="40525", equalizationName="LAST_SUM", equalizationSumName="HP-OFFSETS"):
        self.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        self.tempCalibration(calibName=calibName, ref=ref)
        return self

    def makeProfiles(self, tini=None, tend=None, deltat=30):
        if tini is not None and tend is not None and len(self.sensors) > 0:
            profiles_data = []
            for index, sensor in self.sensors.items():
                temperature = sensor.data.loc[(sensor.data.index >= tini) & (sensor.data.index <= tend)]
                if not temperature.empty:
                    profiles_data.append({
                        "X": sensor.X,
                        "Y": sensor.Y,
                        "Z": sensor.Z,
                        "name": sensor.name,
                        "temp": temperature.mean(),
                        "err": temperature.std()
                    })
            self.profiles = pd.DataFrame.from_records(profiles_data)
            self.is_single_profile = True

        elif tini is None or tend is None:
            profiles_data = {}
            t = min(sensor.data.index.min() for sensor in self.sensors.values())
            max_t = max(sensor.data.index.max() for sensor in self.sensors.values())

            num_steps = (max_t - t).total_seconds() // (deltat * 60)
            progress = tqdm(total=int(num_steps), desc=f"Calculating {self.name} temperature profiles every {deltat} minutes: ", unit="step")

            while t < max_t:
                profiles_data[t] = []
                for index, sensor in self.sensors.items():
                    temperature = sensor.data.loc[
                        (sensor.data.index >= t) & (sensor.data.index < t + datetime.timedelta(minutes=deltat))
                    ]
                    if not temperature.empty:
                        profiles_data[t].append({
                            "X": sensor.X,
                            "Y": sensor.Y,
                            "Z": sensor.Z,
                            "temp": temperature.mean(),
                            "err": temperature.std()
                        })

                profiles_data[t] = pd.DataFrame.from_records(profiles_data[t])
                t += datetime.timedelta(minutes=deltat)
                progress.update(1)

            progress.close()
            self.profiles = profiles_data
            self.is_multiple_profiles = True

        return self

