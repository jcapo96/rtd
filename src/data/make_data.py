import ROOT
import os, array, tqdm, json
from datetime import datetime, timedelta
from src.data.retrieveData import access
import pandas as pd
import numpy as np

class MakeData():
    def __init__(self, detector=None, system=None, sensors=None, sensorIds=None, all=False,
                 startDay=None, endDay=None, startTime=None, endTime=None,
                 clockTick=60,
                 FROM_CERN=True, ref="40525", configuation="precision",
                 pathToSaveData="/eos/user/j/jcapotor/PDHDdata/") -> None:

        self.pathToSaveData = pathToSaveData
        self.pathToCalibData = "/eos/user/j/jcapotor/RTDdata/calib/"

        self.detector = detector
        self.system = system
        self.sensors = sensors
        self.sensorIds = sensorIds
        self.all = all
        self.startDay = startDay
        self.endDay = endDay
        self.startTime = startTime
        self.endTime = endTime
        self.clockTick = clockTick

        self.FROM_CERN = FROM_CERN

        self.ref = ref
        self.configuration = configuation
    def loadSlowControlWebMapping(self):
        """
        Loads the mapping information from an external source into the SlowControlWebMapping attribute.

        Returns:
            self: The RTDConverter instance.
        """
        path = os.path.dirname(os.path.abspath(__file__))
        if int(self.startDay.split("-")[0]) > 2023:
            self.mapping = pd.read_csv(f"{path}/mapping/{self.configuration}_pdhd_mapping.csv",
                            sep=",", decimal=".", header=0)
        elif int(self.startDay.split("-")[0]) < 2023:
            self.mapping = pd.read_csv(f"{path}/mapping/pdsp_mapping.csv",
                                       sep=";", decimal=".", header=0)
        return self

    def makeClock(self):
        changeDate = datetime.strptime(f"{self.startDay.split('-')[0]}-03-31 02:00:00", "%Y-%m-%d %H:%M:%S").timestamp()
        if (self.startDay is not None) and (self.endDay is not None):
            startDatetime = datetime.strptime(f"{self.startDay} {self.startTime}", "%Y-%m-%d %H:%M:%S").timestamp() + 60*60
            endDatetime = datetime.strptime(f"{self.endDay} {self.endTime}", "%Y-%m-%d %H:%M:%S").timestamp() + 60*60
        elif (self.startDay is not None) and (self.startTime is None) and (self.endDay is None):
            self.startTime = "00:00:00"
            startDatetime = datetime.strptime(f"{self.startDay} {self.startTime}", "%Y-%m-%d %H:%M:%S").timestamp() + 60*60
            endDatetime = datetime.strptime(f"{self.startDay} {self.startTime}", "%Y-%m-%d %H:%M:%S").timestamp() + 60*60 + 60*60*24
        if startDatetime > changeDate:
            startDatetime += 60*60
        if endDatetime > changeDate:
            endDatetime += 60*60
        self.ticks = np.arange(startDatetime, endDatetime+1, self.clockTick) #have to add +1 to endDate because of python syntax
        return self

    def selectSensors(self):
        if self.all == False:
            if (self.system is not None) and (self.sensors is None):
                self.selection = self.mapping.loc[(self.mapping["SYSTEM"] == self.system.upper())]
            elif (self.system is None) and (self.sensors is not None):
                self.selection = self.mapping[self.mapping["SC-ID"].isin(self.sensors)]
            elif (self.system is None) and (self.sensors is None):
                if (self.sensorIds is not None):
                    self.selection = self.mapping.loc[(self.mapping["CAL-ID"].isin(self.sensorIds))]
            else:
                self.selection = self.mapping.loc[(self.mapping["SYSTEM"] == self.system.upper())]
                self.selection = self.selection[self.selection["SC-ID"].isin(self.sensors)]
        elif self.all == True:
            self.selection = self.mapping
        return self.selection.reset_index(drop=True)

    def makeFileName(self):
        self.outputRootFileName = f"{self.pathToSaveData}"
        if self.detector is not None:
            self.outputRootFileName += f"{self.detector}_"

        if self.system is not None and self.all is False:
            self.outputRootFileName += f"{self.system}_"
            if self.sensors is not None:
                self.outputRootFileName += f"{self.sensors}_"

        elif (self.system is not None and self.all is True) or (self.system is None and self.all is True):
            self.outputRootFileName += f"all_"

        if self.startDay is not None:
            self.outputRootFileName += f"{self.startDay}_"

        if self.startTime is not None:
            self.outputRootFileName += f"{self.startTime}_"

        if self.endDay is not None:
            self.outputRootFileName += f"{self.endDay}_"

        if self.endTime is not None:
            self.outputRootFileName += f"{self.endTime}_"

        self.outputRootFileName += f"ctick{self.clockTick}_"

        if self.CALIB is True:
            self.outputRootFileName += f"calib_"
            self.outputRootFileName += f"R{self.ref}"

        if self.FROM_CERN is True:
            self.outputRootFileName += "cache"
        elif self.FROM_CERN is False:
            self.outputRootFileName += "web"

        self.outputRootFileName += ".root"

    def makeCalibFileName(self):
        if self.all is False:
            if self.system is not None:
                if "TGRAD" in self.system.upper():
                    self.CALIB, self.RCALIB = True, True
                    self.calibFileName = ["LARTGRAD_TREE", "LN22TGRAD_TREE", "LN23TGRAD_TREE"]
                else:
                    self.CALIB, self.RCALIB = False, False
            elif self.system is None:
                self.CALIB, self.RCALIB = False, False
        elif self.all is True:
            self.CALIB, self.RCALIB = True, True
            self.calibFileName = ["LARTGRAD_TREE", "LN22TGRAD_TREE", "LN23TGRAD_TREE"]

        return self

    def getData(self):
        self.loadSlowControlWebMapping()
        self.selectSensors()
        self.container = {}
        for index, row in self.selection.iterrows():
            try:
                self.container[row["SC-ID"]] = {
                                            "access":access.Access(detector=self.detector, elementId=row["DCS-ID"],
                                                            startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime,
                                                            FROM_CERN=self.FROM_CERN),
                                            "Y":float(row["Y"]),
                                            "X":float(row["X"]),
                                            "Z":float(row["Z"]),
                                            "name":int(row["SC-ID"].split("TE")[1]),
                                            "id":int(row["CAL-ID"]),
                                            "SYSTEM":str(row["SYSTEM"]),
                                            "type":str(row["NAME"])
                                        }
            except:
                self.container[row["SC-ID"]] = {
                                            "access":access.Access(detector=self.detector, elementId=row["DCS-ID"],
                                                            startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime,
                                                            FROM_CERN=self.FROM_CERN),
                                            "Y":-999,
                                            "X":-999,
                                            "Z":-999,
                                            "name":int(999),
                                            "id":int(999),
                                            "SYSTEM":str(row["SYSTEM"]),
                                            "type":str(row["NAME"])
                                        }
        return self

    def make(self):
        self.loadSlowControlWebMapping()
        self.selectSensors()
        self.makeCalibFileName()
        self.makeFileName()
        self.makeClock()
        tempTreeName = "temp"
        infoTreeName = "info"
        outputFile = ROOT.TFile(f"{self.outputRootFileName}", "RECREATE")
        outputTree = ROOT.TTree(tempTreeName, "Temperature measured by RTDs")
        nsensors = len(self.selection)
        epochTime = np.array([0.0 for _ in range(nsensors)])
        eepochTime = np.array([0.0 for _ in range(nsensors)])
        temp = np.array([0.0 for _ in range(nsensors)])
        etemp = np.array([0.0 for _ in range(nsensors)])

        y = array.array("d", [0.0]*nsensors)
        name = array.array("i", [0]*nsensors)
        id = array.array("i", [0]*nsensors)

        outputTree.Branch("t", epochTime, f"t[{nsensors}]/D")
        outputTree.Branch("et", eepochTime, f"et[{nsensors}]/D")
        outputTree.Branch("temp", temp, f"temp[{nsensors}]/D")
        outputTree.Branch("etemp", etemp, f"etemp[{nsensors}]/D")

        outputTree.Branch("y", y, f"y[{nsensors}]/D")
        outputTree.Branch("name", name, f"name[{nsensors}]/I")
        outputTree.Branch("id", id, f"id[{nsensors}]/I")

        container = {}
        for index, row in self.selection.iterrows():
            try:
                container[row["SC-ID"]] = {
                                            "access":access.Access(detector=self.detector, elementId=row["DCS-ID"],
                                                            startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime,
                                                            FROM_CERN=self.FROM_CERN),
                                            "Y":float(row["Y"]),
                                            "name":int(row["SC-ID"].split("TE")[1]),
                                            "id":int(row["CAL-ID"])
                                        }
            except:
                container[row["SC-ID"]] = {
                                            "access":access.Access(detector=self.detector, elementId=row["DCS-ID"],
                                                            startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime,
                                                            FROM_CERN=self.FROM_CERN),
                                            "Y":-999,
                                            "name":int(999),
                                            "id":int(999)
                                        }

        with tqdm.tqdm(total=len(self.selection)*len(self.ticks)) as pbar:
            for ntick, tick in enumerate(self.ticks):
                for idx, key in enumerate(container.keys()):
                    # index = int(key.split("TE")[1]) - 1
                    index = idx
                    clockData = container[key]["access"].data.loc[(container[key]["access"].data["epochTime"] >= tick) & (container[key]["access"].data["epochTime"] < tick+self.clockTick)]
                    y[index] = container[key]["Y"]
                    name[index] = container[key]["name"]
                    id[index] = container[key]["id"]

                    if len(clockData) == 0:
                        epochTime[index] = tick
                        eepochTime[index] = -999
                        temp[index] = -999
                        etemp[index] = -999
                    else:
                        epochTime[index] = tick
                        eepochTime[index] = self.clockTick/2
                        temp[index] = clockData["temp"].mean()
                        etemp[index] = clockData["temp"].std()
                    pbar.update(1)

                outputTree.Fill()

        outputTree.Write()
        outputFile.Close()

        if self.CALIB is True:
            for calibFileName in self.calibFileName:
                with open(f"{self.pathToCalibData}{calibFileName}.json") as f:
                    data = json.load(f)[self.ref]

                outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
                outputTree = ROOT.TTree(f"{calibFileName}", f"Calibration constants from {calibFileName.split('.')[0]}")

                values_to_fill, branches_to_fill = {}, {}
                for id, values in data.items():
                    try:
                        name = int(self.mapping.loc[(self.mapping["CAL-ID"] == int(id))]["SC-ID"].values[0].split("TE")[1])
                    except:
                        name = int(id)
                    values_to_fill[name] = array.array("d", [0.0])
                    branches_to_fill[name] = outputTree.Branch(f"cal{name}", values_to_fill[name], f"cal{name}/D")

                for i in range(9): #this is not general enough
                    for id, values in data.items():
                        try:
                            name = int(self.mapping.loc[(self.mapping["CAL-ID"] == int(id))]["SC-ID"].values[0].split("TE")[1])
                        except:
                            name = int(id)
                        if len(values) > 1:
                            values_to_fill[name][0] = values[i]
                        else:
                            values_to_fill[name][0] = values[0]
                    outputTree.Fill()

                outputFile.cd()
                outputTree.Write()
                outputFile.Close()

        if self.RCALIB is True:
            for calibFileName in self.calibFileName:
                with open(f"{self.pathToCalibData}{calibFileName}_rcal.json") as f:
                    data = json.load(f)[self.ref]

                outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
                outputTree = ROOT.TTree(f"r{calibFileName}", f"Calibration constants from {calibFileName.split('.')[0]}_rcal")

                values_to_fill, branches_to_fill = {}, {}
                for id, values in data.items():
                    try:
                        name = int(self.mapping.loc[(self.mapping["CAL-ID"] == int(id))]["SC-ID"].values[0].split("TE")[1])
                    except:
                        name = int(id)
                    values_to_fill[name] = array.array("d", [0.0])
                    branches_to_fill[name] = outputTree.Branch(f"cal{name}", values_to_fill[name], f"cal{name}/D")

                for i in range(9): #this is not general enough
                    for id, values in data.items():
                        try:
                            name = int(self.mapping.loc[(self.mapping["CAL-ID"] == int(id))]["SC-ID"].values[0].split("TE")[1])
                        except:
                            name = int(id)
                        if len(values) > 1:
                            values_to_fill[name][0] = values[i]
                        else:
                            values_to_fill[name][0] = values[0]
                    outputTree.Fill()

                outputFile.cd()
                outputTree.Write()
                outputFile.Close()

        calibFileName = "CERNRCalib"
        with open(f"{self.pathToCalibData}{calibFileName}.json") as f:
            data = json.load(f)

        outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
        outputTree = ROOT.TTree(f"r{calibFileName}", f"Calibration constants from {calibFileName.split('.')[0]}_rcal")

        values_to_fill, branches_to_fill = {}, {}
        for id, values in data.items():
            name = f"{id.split('s')[1]}"
            values_to_fill[name] = array.array("d", [0.0])
            branches_to_fill[name] = outputTree.Branch(f"cal{name}", values_to_fill[name], f"cal{name}/D")

        for id, values in data.items():
            name = f"{id.split('s')[1]}"
            values_to_fill[name][0] = np.mean(values)
        outputTree.Fill()

        outputFile.cd()
        outputTree.Write()
        outputFile.Close()

        if self.CALIB is True:
            calibFileName = "LAR2018TGRAD"
            data = pd.read_csv(f"{self.pathToCalibData}{calibFileName}.csv",
                                        sep=";", decimal=".", header=0, na_values=[None, "", "NA", "NaN", "N/A"])

            outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
            outputTreeRef = ROOT.TTree(f"{calibFileName}_REF", f"Calibration constants from {calibFileName} reference")
            outputTreeTree = ROOT.TTree(f"{calibFileName}_TREE", f"Calibration constants from {calibFileName} tree method")
            outputTreePoff = ROOT.TTree(f"{calibFileName}_POFF", f"Calibration constants from {calibFileName} pumps off method")

            values_to_fill_ref, branches_to_fill_ref = {}, {}
            values_to_fill_tree, branches_to_fill_tree = {}, {}
            values_to_fill_poff, branches_to_fill_poff = {}, {}
            for index, row in data.iterrows():
                if pd.isna(row["OFF"]):
                    continue
                name = f'{int(row["SC-ID"].split("TE")[1])}'
                values_to_fill_tree[name] = array.array("d", [0.0])
                branches_to_fill_tree[name] = outputTreeTree.Branch(f"cal{name}", values_to_fill_tree[name], f"cal{name}/D")

                values_to_fill_ref[name] = array.array("d", [0.0])
                branches_to_fill_ref[name] = outputTreeRef.Branch(f"cal{name}", values_to_fill_ref[name], f"cal{name}/D")

                values_to_fill_poff[name] = array.array("d", [0.0])
                branches_to_fill_poff[name] = outputTreePoff.Branch(f"cal{name}", values_to_fill_poff[name], f"cal{name}/D")

            for index, row in data.iterrows():
                if pd.isna(row["OFF"]):
                    continue
                name = f'{int(row["SC-ID"].split("TE")[1])}'
                values_to_fill_ref[name][0] = float(row["OFF"])*1e3
                values_to_fill_tree[name][0] = float(row["OFF_TREE"])*1e3
                values_to_fill_poff[name][0] = float(row["POFF"])*1e3

            outputTreeRef.Fill()
            outputTreeTree.Fill()
            outputTreePoff.Fill()

            outputFile.cd()
            outputTreeRef.Write()
            outputTreeTree.Write()
            outputTreePoff.Write()
            outputFile.Close()