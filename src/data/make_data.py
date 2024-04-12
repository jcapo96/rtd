import ROOT, os, array, tqdm, json
from rtd.src.data.retrieveData import RTDConverterTools
from rtd.src.data.retrieveData import access
import pandas as pd
import numpy as np

class MakeData():
    def __init__(self, detector=None, system=None, sensors=None,
                 startDay=None, endDay=None, startTime=None, endTime=None,
                 clockTick=60,
                 FROM_CERN=True, ref="40525") -> None:

        self.pathToSaveData = "/eos/user/j/jcapotor/PDHDdata/"
        self.pathToCalibData = "/eos/user/j/jcapotor/RTDdata/calib/"

        self.detector = detector
        self.system = system
        self.sensors = sensors
        self.startDay = startDay
        self.endDay = endDay
        self.startTime = startTime
        self.endTime = endTime
        self.clockTick = clockTick
        self.makeClock()

        self.FROM_CERN = FROM_CERN

        self.ref = ref
        self.loadSlowControlWebMapping()
        self.selectSensors()
        self.makeCalibFileName()
        self.makeFileName()

    def loadSlowControlWebMapping(self):
        """
        Loads the mapping information from an external source into the SlowControlWebMapping attribute.

        Returns:
            self: The RTDConverter instance.
        """
        path = os.path.dirname(os.path.abspath(__file__))
        self.mapping = pd.read_csv(f"{path}/mapping/pdhd_mapping.csv",
                           sep=";", decimal=",", header=0)
        return self

    def makeClock(self):
        startTimeStamp = RTDConverterTools.convertDDMMYYYY(self.startDay, self.startTime)
        endTimeStamp = RTDConverterTools.convertDDMMYYYY(self.endDay, self.endTime)
        self.ticks = np.arange(startTimeStamp, endTimeStamp+1, self.clockTick) #have to add +1 to endDate because of python syntax
        return self

    def selectSensors(self):
        if (self.system is not None) and (self.sensors is None):
            self.selection = self.mapping.loc[(self.mapping["SYSTEM"] == self.system.upper())]
        elif (self.system is None) and (self.sensors is not None):
            self.selection = self.mapping[self.mapping["SC-ID"].isin(self.sensors)]
        else:
            self.selection = self.mapping.loc[(self.mapping["SYSTEM"] == self.system.upper())]
            self.selection = self.selection[self.selection["SC-ID"].isin(self.sensors)]
        return self.selection.reset_index(drop=True)

    def makeFileName(self):
        if self.CALIB is True:
            if self.FROM_CERN is True:
                self.outputRootFileName = f"{self.pathToSaveData}{self.detector}_{self.system}_{self.startDay}T{self.startTime}_{self.endDay}T{self.endTime}_ctick{self.clockTick}_{self.calibFileName.split('.')[0]}R{self.ref}cache.root"
            elif self.FROM_CERN is False:
                self.outputRootFileName = f"{self.pathToSaveData}{self.detector}_{self.system}_{self.startDay}T{self.startTime}_{self.endDay}T{self.endTime}_ctick{self.clockTick}_{self.calibFileName.split('.')[0]}R{self.ref}web.root"
        elif self.CALIB is False:
            if self.FROM_CERN is True:
                self.outputRootFileName = f"{self.pathToSaveData}{self.detector}_{self.system}_{self.startDay}T{self.startTime}_{self.endDay}T{self.endTime}_ctick{self.clockTick}s_cache.root"
            elif self.FROM_CERN is False:
                self.outputRootFileName = f"{self.pathToSaveData}{self.detector}_{self.system}_{self.startDay}T{self.startTime}_{self.endDay}T{self.endTime}_ctick{self.clockTick}s_web.root"
        return self

    def makeCalibFileName(self):
        if self.system is not None:
            if "TGRAD" in self.system.upper():
                self.CALIB, self.RCALIB = True, True
                self.calibFileName = ["LARTGRAD_TREE"]
            else:
                self.CALIB, self.RCALIB = False, False
        elif self.system is None:
            systems = self.selection["SYSTEM"].unique()
            for system in systems:
                if "TGRAD" in system:
                    self.CALIB, self.RCALIB = True, True
                    self.calibFileName.append("LARTGRAD_TREE")
                else:
                    self.CALIB, self.RCALIB = False, False
        return self
    def make(self):
        tempTreeName = "temp"
        outputFile = ROOT.TFile(f"{self.outputRootFileName}", "RECREATE")
        outputTree = ROOT.TTree(tempTreeName, "Temperature measured by RTDs")
        length = len(self.ticks)
        epochTime = array.array("d", [0.0] * length)
        eepochTime = array.array("d", [0.0] * length)
        temp = array.array("d", [0.0] * length)
        etemp = array.array("d", [0.0] * length)
        y = array.array("d", [0.0])

        name = array.array("i", [0])
        id = array.array("i", [0])

        outputTree.Branch("t", epochTime, f"t[{length}]/D")
        outputTree.Branch("et", eepochTime, f"et[{length}]/D")
        outputTree.Branch("temp", temp, f"temp[{length}]/D")
        outputTree.Branch("etemp", etemp, f"etemp[{length}]/D")
        outputTree.Branch("y", y, "y/D")
        outputTree.Branch("name", name, "name/I")
        outputTree.Branch("id", id, "id/I")

        with tqdm.tqdm(total=len(self.selection)*len(self.ticks)) as pbar:
            for nrow, row in self.selection.iterrows():
                acc = access.Access(detector=self.detector, elementId=row["DCS-ID"], startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime, FROM_CERN=self.FROM_CERN)
                try:
                    y[0] = float(row["Y"])
                    name[0] = int(row["SC-ID"].split("TE")[1])
                    id[0] = int(row["CAL-ID"])
                except:
                    y[0] = float(-999)
                    name[0] = int(999)
                    id[0] = int(999)
                for ntick, tick in enumerate(self.ticks):
                    clockData = acc.data.loc[(acc.data["epochTime"] >= tick) & (acc.data["epochTime"] < tick+self.clockTick)]
                    # print(clockData)
                    if len(clockData) == 0:
                        epochTime[ntick] = tick
                        eepochTime[ntick] = -999
                        temp[ntick] = -999
                        etemp[ntick] = -999
                    else:
                        epochTime[ntick] = tick
                        eepochTime[ntick] = self.clockTick/2
                        temp[ntick] = clockData["temp"].mean()
                        etemp[ntick] = clockData["temp"].std()
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
                    values_to_fill[id] = array.array("d", [0.0])
                    branches_to_fill[id] = outputTree.Branch(f"cal{id}", values_to_fill[id], f"cal{id}/D")

                for i in range(9): #this is not general enough
                    for id, values in data.items():
                        if len(values) > 1:
                            values_to_fill[id][0] = values[i]
                        else:
                            values_to_fill[id][0] = values[0]
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
                    values_to_fill[id] = array.array("d", [0.0])
                    branches_to_fill[id] = outputTree.Branch(f"cal{id}", values_to_fill[id], f"cal{id}/D")

                for i in range(9): #this is not general enough
                    for id, values in data.items():
                        if len(values) > 1:
                            values_to_fill[id][0] = values[i]
                        else:
                            values_to_fill[id][0] = values[0]
                    outputTree.Fill()

                outputFile.cd()
                outputTree.Write()
                outputFile.Close()

m = MakeData(detector="np04", system="apa", startDay="2024-03-05", endDay="2024-04-12", startTime="00:00:00", endTime="15:30:00", clockTick=60)
m.make()