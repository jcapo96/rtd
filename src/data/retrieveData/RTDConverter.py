from rtd.src.data.retrieveData import RTDConverterTools
from rtd.src.data.retrieveData import access
import ROOT, array, os
from tqdm import tqdm
import pandas as pd
import numpy as np

class RTDConverter():
    """
    RTDConverter class is responsible for converting data from an external source
    into a ROOT file format and storing it.

    Attributes:
        access (object): An object providing access to the data source.
        outputRootFileName (str): The path to the output ROOT file where the
            converted data will be stored.
        SlowControlWebMapping (DataFrame): DataFrame containing mapping information
            between slow control IDs and web IDs.
        treeNames (list): A list of slow control IDs extracted from SlowControlWebMapping.
        currentFillingTreeName (str): The current slow control ID being filled.

    Methods:
        loadSlowControlWebMapping(): Loads the mapping information from an external
            source into the SlowControlWebMapping attribute.
        fillRootFile(): Fills the ROOT file with converted data.
    """

    def __init__(self, detector, elementId, startDay=None, endDay=None, startTime=None, endTime=None, FROM_CERN=True, outputRootFileName=f"{os.path.dirname(os.path.abspath(__file__))}/test.root", clockTick=10):
        """
        Initialize an instance of RTDConverter.

        Args:
            access (object): An object providing access to the data source.
            outputRootFileName (str, optional): The path to the output ROOT file.
                Defaults to "/Users/jcapo/cernbox/DUNE-IFIC/Software/SlowControlNP04/retrieveData/test.root".
        """
        self.startDay, self.startTime, self.endDay, self.endTime = startDay, startTime, endDay, endTime
        self.access = access.Access(detector=detector, elementId=elementId, startDay=self.startDay, endDay=self.endDay, startTime=self.startTime, endTime=self.endTime, FROM_CERN=FROM_CERN)
        self.outputRootFileName = outputRootFileName
        self.clockTick = clockTick #units in seconds
        self.loadSlowControlWebMapping()
        self.access.startDay, self.access.endDay = RTDConverterTools.prepareTimeStamp(self.access.startDay, self.access.endDay)
        self.branchNames = list(self.slowControlWebMapping["CAL-ID"].values)
        self.currentFillingTreeName = "temp"
        self.currentFillingBranchName = self.slowControlWebMapping.loc[(self.slowControlWebMapping["DCS-ID"] == int(self.access.elementId))]["CAL-ID"].values[0]

    def loadSlowControlWebMapping(self):
        """
        Loads the mapping information from an external source into the SlowControlWebMapping attribute.

        Returns:
            self: The RTDConverter instance.
        """
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.slowControlWebMapping = pd.read_csv(f"{path}/mapping/pdhd_mapping.csv",
                           sep=";", header=0)
        return self

    def fillRootFile(self):
        """
        Fills the ROOT file with converted data.

        Returns:
            bool: True if successful, False otherwise.
        """
        if RTDConverterTools.checkFileExists(outputRootFileName=self.outputRootFileName) is False:
            # If the file does not exist, create and close it
            outputFile = ROOT.TFile(f"{self.outputRootFileName}", "RECREATE")
            outputFile.Close()
            print(f"Creating new file at: {self.outputRootFileName}")

        if RTDConverterTools.checkTreeExists(outputRootFileName=self.outputRootFileName,
                                             currentTreeName=self.currentFillingTreeName) is False:
            # If the trees are not in the rootfile, create them
            print(f"Tree: {self.currentFillingTreeName} not existing in the rootfile.")
            outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
            outputTree = ROOT.TTree(self.currentFillingTreeName, "Temperature measured by RTDs")
            #creates the variables
            epochTime = array.array("d", [0.0])
            temp = array.array("d", [0.0])
            tempError = array.array("d", [0.0])
            #creates the branches
            outputTree.Branch(f"t{self.currentFillingBranchName}", epochTime, f"t{self.currentFillingBranchName}/D")
            outputTree.Branch(f"T{self.currentFillingBranchName}", temp, f"T{self.currentFillingBranchName}/D")
            outputTree.Branch(f"err{self.currentFillingBranchName}", tempError, f"err{self.currentFillingBranchName}/D")

            outputFile.cd()
            outputTree.Write(self.currentFillingTreeName, ROOT.TObject.kWriteDelete)
            outputFile.Close()

        elif RTDConverterTools.checkTreeExists(outputRootFileName=self.outputRootFileName,
                                             currentTreeName=self.currentFillingTreeName) is True:

            if RTDConverterTools.checkBranchExists(outputRootFileName=self.outputRootFileName,
                                                treeName=self.currentFillingTreeName,
                                                branchName=self.currentFillingBranchName) is False:
                print(f"Creating branch {self.currentFillingBranchName} in {self.currentFillingTreeName}")
                outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
                outputTree = outputFile.Get(self.currentFillingTreeName)
                #creates the variables
                epochTime = array.array("d", [0.0])
                temp = array.array("d", [0.0])
                tempError = array.array("d", [0.0])
                #creates the branches
                outputTree.Branch(f"t{self.currentFillingBranchName}", epochTime, f"t{self.currentFillingBranchName}/D")
                outputTree.Branch(f"T{self.currentFillingBranchName}", temp, f"T{self.currentFillingBranchName}/D")
                outputTree.Branch(f"err{self.currentFillingBranchName}", tempError, f"err{self.currentFillingBranchName}/D")

                outputFile.cd()
                outputTree.Write(self.currentFillingTreeName, ROOT.TObject.kWriteDelete)
                outputFile.Close()

        print(f"Start filling 'T{self.currentFillingBranchName}' on '{self.outputRootFileName}'")
        outputFile = ROOT.TFile(f"{self.outputRootFileName}", "UPDATE")
        outputTree = outputFile.Get(self.currentFillingTreeName)
        outputTree.SetBranchStatus("*", 0)  # Deactivate all branches
        outputTree.SetBranchStatus(f"T{self.currentFillingBranchName}", 1)  # Activate only the desired branch
        outputTree.SetBranchStatus(f"err{self.currentFillingBranchName}", 1)
        outputTree.SetBranchStatus(f"t{self.currentFillingBranchName}", 1)

        epochTime = array.array("d", [0.0])
        temp = array.array("d", [0.0])
        tempError = array.array("d", [0.0])

        outputTree.SetBranchAddress(f"t{self.currentFillingBranchName}", epochTime)
        outputTree.SetBranchAddress(f"T{self.currentFillingBranchName}", temp)
        outputTree.SetBranchAddress(f"err{self.currentFillingBranchName}", tempError)

        print(f"{len(self.access.data)} entries in total.")
        startTimeStamp = RTDConverterTools.convertDDMMYYYY(self.startDay, self.startTime)
        endTimeStamp = RTDConverterTools.convertDDMMYYYY(self.endDay, self.endTime)
        self.ticks = np.arange(startTimeStamp, endTimeStamp+1, self.clockTick) #have to add +1 to endDate because of python syntax
        self.access.data["epochTime"] = (self.access.data["epochTime"])
        with tqdm(total=len(self.ticks)) as pbar:
            for tick in self.ticks:
                clockData = self.access.data.loc[(self.access.data["epochTime"] >= tick) & (self.access.data["epochTime"] < tick+self.clockTick)]
                if len(clockData) == 0:
                    temp[0] = -999
                    tempError[0] = -999
                    epochTime[0] = tick
                else:
                    temp[0] = clockData["temp"].mean()
                    tempError[0] = clockData["temp"].std()
                    epochTime[0] = tick

                outputTree.Fill()
                pbar.update(1)

        outputFile.cd()
        outputTree.SetBranchStatus("*", 1)  # Activate all branches
        outputTree.Write(self.currentFillingTreeName, ROOT.TObject.kWriteDelete)
        outputFile.Close()