from src import baseClasses, muxClasses
import pandas as pd
import pickle

class Sensor():
    def __init__(self, dataset, id):
        self.dataset = dataset
        self.id = id
        self.is_calib_corrected = False
        self.is_mux_corrected = {}
        self._info()
        self._data()
        self._coordinates()

    def _info(self):
        self.info = {}
        for index, configurationRow in baseClasses.LogFile().configurations.iterrows():
            mapping = baseClasses.Configuration(configurationRow["Configuration"]).mapping
            sensorConfig = mapping[mapping["CAL-ID"] == self.id]
            if len(sensorConfig) == 0:
                continue
            self.info[index] = {"sensorInfo":sensorConfig, "configInfo":configurationRow.T}
        if len(self.info) == 0:
            self.info = None
            print(f"ERROR: SensorID ({self.id}) not found")
        return self.info

    def _coordinates(self):
        sensorCoordinates = pd.read_csv(f"/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/baseline.csv", header=0)
        sensorCoordinates = sensorCoordinates[["SYSTEM", "NAME", "CAL-ID", "W-CABLE", "FLANGE", "X", "Y", "Z"]]
        sensorCoordinates = sensorCoordinates.loc[sensorCoordinates["CAL-ID"]==self.id].reset_index(drop=True)
        if len(sensorCoordinates) == 0:
            sensorCoordinates = None
            print(f"ERROR: SensorID ({self.id}) coordinates not found")
        if sensorCoordinates is not None:
            self.X = sensorCoordinates["X"].values[0]
            self.Y = sensorCoordinates["Y"].values[0]
            self.Z = sensorCoordinates["Z"].values[0]

            self.system = sensorCoordinates["SYSTEM"].values[0]
            self.name = sensorCoordinates["NAME"].values[0]
            self.wcable = sensorCoordinates["W-CABLE"].values[0]
            self.flange = sensorCoordinates["FLANGE"].values[0]
        return self

    def _data(self):
        self.data = pd.Series()
        for index, info in self.info.items():
            config = info["configInfo"]
            sensor = info["sensorInfo"]
            channel = baseClasses.Channel(self.dataset, sensor["SC-ID"].values[0])
            if channel.data is None:
                continue
            else:
                dataConfig = channel.data.loc[(channel.data.index >= config["Start"]) & (channel.data.index <= config["End"])]
                self.data = pd.concat([df for df in [self.data, dataConfig] if not df.empty])
        if len(self.data) == 0:
            self.data = None
            print(f"ERROR: SensorID ({self.id}) data not found")
        return self

    def tempCalibration(self, calibName="LAR2023_TREE_AVG", ref="40525"):
        indexOfCalibs = pd.read_excel(f"/eos/user/j/jcapotor/RTDdata/calib/index_of_calibs.xlsx", header=0)
        if calibName not in indexOfCalibs["Name"].values:
            print(f"ERROR: Calibration ({calibName}) not found")
            self.cc = None
            self.cc_err = None
            self.cc_ref = None
            self.cc_name = None
            self.cc_type = None
            self.cc_system = None
            self.cc_help = None
            self.cc_path = None
            self.cc_macro = None
            self.is_calib_corrected = False
        else:
            calibInfo = indexOfCalibs.loc[indexOfCalibs["Name"]==calibName].reset_index(drop=True)
            with open(calibInfo["Path"].values[0], "rb") as file:
                calib = pickle.load(file)
            self.calib = calib
            if ref not in calib.keys():
                print(f"ERROR: Reference ({ref}) not found in calibration ({calibName})")
                self.cc = None
                self.cc_err = None
                self.cc_ref = None
                self.cc_name = None
                self.cc_type = None
                self.cc_system = None
                self.cc_help = None
                self.cc_path = None
                self.cc_macro = None
                self.is_calib_corrected = False
            else:
                if str(int(self.id)) not in calib[ref].index:
                    print(f"ERROR: SensorID ({str(int(self.id))}) not found in calibration ({calibName})")
                    self.cc = None
                    self.cc_err = None
                    self.cc_ref = None
                    self.cc_name = None
                    self.cc_type = None
                    self.cc_system = None
                    self.cc_help = None
                    self.cc_path = None
                    self.cc_macro = None
                    self.is_calib_corrected = False
                else:
                    calib = calib[ref].loc[str(int(self.id))]
                    self.cc = calib["cc"]
                    self.cc_err = calib["cc_err"]
                    self.cc_ref = int(ref)
                    self.cc_name = calibName
                    self.cc_type = calibInfo["Type"].values[0]
                    self.cc_system = calibInfo["System"].values[0]
                    self.cc_help = calibInfo["Description"].values[0]
                    self.cc_path = calibInfo["Path"].values[0]
                    self.cc_macro = calibInfo["Macro"].values[0]
                    self.data = self.data - 1e-3*self.cc
                    self.is_calib_corrected = True
        return self

    def muxCorrection(self):
        self.data = pd.Series()
        for index, info in self.info.items():
            config = info["configInfo"]
            sensor = info["sensorInfo"]
            channel = baseClasses.Channel(self.dataset, sensor["SC-ID"].values[0])
            mux = muxClasses.MUX(self.dataset, sensor["BOARD"].values[0])
            if channel.data is None:
                self.is_mux_corrected[index] = {"config":config, "is_corrected":False}
                continue
            else:
                dataConfig = channel.data.loc[(channel.data.index >= config["Start"]) & (channel.data.index <= config["End"])]
                if mux.data is not None:
                    dataConfig = dataConfig/mux.data
                    self.data = pd.concat([df for df in [self.data, dataConfig] if not df.empty])
                    self.is_mux_corrected[index] = {"config":config, "is_corrected":True}
                else:
                    self.data = pd.concat([df for df in [self.data, dataConfig] if not df.empty])
                    self.is_mux_corrected[index] = {"config":config, "is_corrected":False}
        if len(self.data) == 0:
            self.data = None
            print(f"ERROR: SensorID ({self.id}) data not found")
        return self
