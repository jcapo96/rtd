from src import baseClasses, muxClasses
import pandas as pd
import pickle, json

class Sensor():
    def __init__(self, dataset, id):
        self.dataset = dataset
        try:
            self.id = int(id)
        except:
            self.id = id
        self.is_calib_corrected = False
        self.is_mux_corrected = {}
        self.is_mux_equalized = {}
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
        sensorCoordinates = sensorCoordinates[["SYSTEM", "NAME", "BOARD", "CAL-ID", "W-CABLE", "FLANGE", "X", "Y", "Z"]]
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
        self.err = pd.Series()
        for index, info in self.info.items():
            config = info["configInfo"]
            sensor = info["sensorInfo"]
            channel = baseClasses.Channel(self.dataset, sensor["SC-ID"].values[0])
            if channel.data is None or channel.err is None:
                continue
            else:
                if "Start" in config and "End" in config:
                    dataConfig = channel.data.loc[(channel.data.index >= config["Start"]) & (channel.data.index <= config["End"])]
                    dataErrConfig = channel.err.loc[(channel.err.index >= config["Start"]) & (channel.err.index <= config["End"])]

                    if not dataConfig.empty:
                        self.data = pd.concat([self.data, dataConfig])
                    if not dataErrConfig.empty:
                        self.err = pd.concat([self.err, dataErrConfig])
                else:
                    print(f"ERROR: Missing 'Start' or 'End' in config for SensorID ({self.id})")

        if self.data.empty:
            self.data = None
            print(f"ERROR: Data for SensorID ({self.id}) not found")

        if self.err.empty:
            self.err = None
            print(f"ERROR: Error data for SensorID ({self.id}) not found")
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

    def muxCorrection(self, manual_correction=False):
        self.data = pd.Series()
        for index, info in self.info.items():
            config = info["configInfo"]
            sensor = info["sensorInfo"]
            channel = baseClasses.Channel(self.dataset, sensor["SC-ID"].values[0])
            if manual_correction:
                mux = muxClasses.MUX(self.dataset, sensor["BOARD"].values[0]).correct()
            else:
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

    def muxEqualization(self, equalizationName="LAST_SUM", equalizationSumName="HP-OFFSETS"):
        self.data = pd.Series()
        indexOfCorrections = pd.read_excel(f"/eos/user/j/jcapotor/RTDdata/corrections/index_of_corrections.xlsx", header=0)
        if equalizationName not in indexOfCorrections["Name"].values:
            print(f"ERROR: Equalization ({equalizationName}) not found")
        else:
            correctionInfo = indexOfCorrections.loc[indexOfCorrections["Name"]==equalizationName].reset_index(drop=True)
            correctionSumInfo = indexOfCorrections.loc[indexOfCorrections["Name"]==equalizationSumName].reset_index(drop=True)
            with open(correctionInfo["Path"].values[0], "rb") as file:
                correction = pickle.load(file)
            self.equalizationInfo = correction
            with open(correctionSumInfo["Path"].values[0], "rb") as file:
                correctionSum = pickle.load(file)
            self.equalizationSumInfo = correctionSum
        for index, info in self.info.items():
            config = info["configInfo"]
            sensor = info["sensorInfo"]
            boardNumber = sensor["BOARD"].values[0]
            channel = baseClasses.Channel(self.dataset, sensor["SC-ID"].values[0])
            mux = muxClasses.MUX(self.dataset, sensor["BOARD"].values[0])
            if channel.data is None:
                self.is_mux_equalized[index] = {"config":config, "is_corrected":False}
                continue
            else:
                dataConfig = channel.data.loc[(channel.data.index >= config["Start"]) & (channel.data.index <= config["End"])]
                try:
                    boardNumber = int(boardNumber)
                    if boardNumber not in correction.keys():
                        self.is_mux_equalized[index] = {"config":config, "is_corrected":False}
                        self.data = pd.concat([df for df in [self.data, dataConfig] if not df.empty])
                        # print(f"ERROR: Board ({boardNumber}) not found in equalization ({equalizationName})")
                        continue
                    equalizationFactor = correction[f"B{boardNumber}"]["mean"]
                    equalizationSumFactor = correctionSum[boardNumber]
                    # dataConfig = dataConfig/(mux.data*equalizationFactor) - equalizationSumFactor*1e-3 #older version
                    if boardNumber == 4:
                        # dataConfig = dataConfig*(mux.data*equalizationFactor)
                        dataConfig = dataConfig*(mux.data/4) + equalizationFactor
                    else:
                        # dataConfig = dataConfig/(mux.data*equalizationFactor)
                        dataConfig = dataConfig/(mux.data) + equalizationFactor
                    self.data = pd.concat([df for df in [self.data, dataConfig] if not df.empty])
                    self.is_mux_equalized[index] = {"config":config, "is_corrected":True, "equalizationFactor":equalizationFactor, "equalizationSumFactor":equalizationSumFactor}
                except:
                    self.is_mux_equalized[index] = {"config":config, "is_corrected":False}
                    continue
        if len(self.data) == 0:
            self.data = None
            print(f"ERROR: SensorID ({self.id}) data not found")
        return self