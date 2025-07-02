from src import systemClasses, baseClasses
import pandas as pd
from tqdm import tqdm
import datetime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class Calibration():
    def __init__(self, dataset, tini, tend):
        self.dataset = dataset
        self.tini = tini
        self.tend = tend
        self._info()
        self._data()

    def _info(self):
        logFile = baseClasses.LogFile().configurations
        logFile["Start"] = pd.to_datetime(logFile["Start"])
        logFile["End"] = pd.to_datetime(logFile["End"])
        logFile = logFile.loc[(logFile["Start"] <= self.tend) & (logFile["End"] >= self.tini)]
        if len(logFile) == 0:
            self.configurations = None
            print(f"ERROR: No configurations found for the selected time range")
        else:
            self.configurations = logFile
            self.systems = {}
            for index, configurationRow in self.configurations.iterrows():
                mapping = baseClasses.Configuration(configurationRow["Configuration"]).mapping
                hp_systems = mapping.loc[(mapping["BOARD"]<=4)]["SYSTEM"].unique()
                self.systems[configurationRow["Configuration"]] = {"tini": configurationRow["Start"], "tend": configurationRow["End"], "systems": hp_systems}
            if len(self.systems) == 0:
                self.systems = None
                print(f"ERROR: No systems found for the selected time range")
        return self

    def _data(self):
        if self.systems is not None:
            self.sensors = {}
            cnt = 0
            for configuration, info in self.systems.items():
                print(f"Collecting data for configuration '{configuration}' between {info['tini']} and {info['tend']}")
                self.sensors[cnt] = {"configuration": configuration, "tini": max([info["tini"], self.tini]), "tend": min([info["tend"], self.tend]), "sensors": {}}
                for systemName in info["systems"]:
                    if systemName == "EMPTY":
                        continue
                    system = systemClasses.System(self.dataset, systemName)
                    system.muxEqualization()
                    for id, sensor in system.sensors.items():
                        if sensor not in self.sensors[cnt]["sensors"]:
                            self.sensors[cnt]["sensors"][id] = sensor
                        else:
                            self.sensors[cnt]["sensors"][id] = sensor
                            print(f"WARNING: Sensor {sensor} already exists in the configuration {configuration} between {info['tini']} and {info['tend']}")
                cnt += 1
        return self

    def calibrate(self, ref=40525):
        if self.sensors is not None:
            self.calib = {}
            for cnt, sensors in self.sensors.items():
                self.calib[cnt] = {"configuration": sensors["configuration"], "tini": sensors["tini"], "tend": sensors["tend"], "ref":ref, "calib": {}}
                if ref not in sensors["sensors"].keys():
                    print(f"ERROR: Reference sensor {ref} not found in the configuration {sensors['configuration']} between {sensors['tini']} and {sensors['tend']}")
                    continue
                if sensors["sensors"][ref] is None:
                    print(f"ERROR: Reference sensor {ref} is None in the configuration {sensors['configuration']} between {sensors['tini']} and {sensors['tend']}")
                    continue
                ref_sensor = sensors["sensors"][ref]
                for id, sensor in sensors["sensors"].items():
                    if sensor is not None:
                        cc = (
                            sensor.data.loc[(sensor.data.index >= sensors["tini"]) & (sensor.data.index <= sensors["tend"]) & (sensor.data>0) & (sensor.data<90)] -
                            ref_sensor.data.loc[(ref_sensor.data.index >= sensors["tini"]) & (ref_sensor.data.index <= sensors["tend"]) & (ref_sensor.data>0) & (ref_sensor.data<90)]
                            ).mean()
                        err = (
                            sensor.data.loc[(sensor.data.index >= sensors["tini"]) & (sensor.data.index <= sensors["tend"]) & (sensor.data>0) & (sensor.data<90)] -
                            ref_sensor.data.loc[(ref_sensor.data.index >= sensors["tini"]) & (ref_sensor.data.index <= sensors["tend"]) & (ref_sensor.data>0) & (ref_sensor.data<90)]
                            ).std()
                        self.calib[cnt]["calib"][id] = {"cc": cc, "err": err}
                self.calib[cnt]["calib"] = pd.DataFrame(self.calib[cnt]["calib"]).T
        return self