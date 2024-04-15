import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class ReadoutCalib():
    def __init__(self, readout="IFIC") -> None:
        self.readout = readout
        self.pathToData = "/eos/user/j/jcapotor/RTDdata"
        self.pathToSaveCalib = f"{self.pathToData}/calib/"
        self.outputFileName = f"{self.pathToSaveCalib}{self.readout.upper()}RCalib.json"
        self.results = None
        self.resultsErr = None
        self.channels = None
        self.container = {}

    def makeIFIC(self, date):
        tini = 30
        results, resultsErr, channels = [0], [0], [7]
        if "14" in date or "16" in date:
            firstChannel, nChannels = 6, 12
        elif "17" in date:
            firstChannel, nChannels = 0, 6
        for channelNumber in range(2, nChannels+1):
            fileName1 = f"{self.pathToData}/Data/IFIC_Readout_Calib/{date}/{date}_CH1HP1_CH{channelNumber}_HP2.txt"
            fileName2 = f"{self.pathToData}/Data/IFIC_Readout_Calib/{date}/{date}_CH1HP2_CH{channelNumber}_HP1.txt"
            data1 = pd.read_csv(fileName1, sep="\t", header=None)
            data2 = pd.read_csv(fileName2, sep="\t", header=None)

            value1 = (data1[2][tini:] - data1[1+channelNumber][tini:]).mean()*1e3
            value1Err = (data1[2][tini:] - data1[1+channelNumber][tini:]).std()*1e3
            value2 = (data2[2][tini:] - data2[1+channelNumber][tini:]).mean()*1e3
            value2Err = (data2[2][tini:] - data2[1+channelNumber][tini:]).std()*1e3

            results.append((value1 + value2)/2)
            resultsErr.append(np.sqrt(value1Err**2 + value2Err**2))
            channels.append(channelNumber+firstChannel)

            self.results = np.array(results)
            self.resultsErr = np.array(resultsErr)
            self.channels = np.array(channels)
        return self

    def makeCERN(self, date):
        tini = 5
        results, resultsErr, channels = [], [], []
        for board in ["BOARD1", "BOARD2"]:
            nChannels = 24
            if board == "BOARD1":
                firstChannel = 0
                results.append(0)
                resultsErr.append(0)
                channels.append(1)
            elif board == "BOARD2":
                firstChannel = 24
                results.append(0)
                resultsErr.append(0)
                channels.append(25)
            for channelNumber in range(2+firstChannel, firstChannel+nChannels+1):
                try:
                    fileName1 = f"{self.pathToData}/Data/CERN_Readout_Calib/{date}/{board}/CH{firstChannel+1}_CH{firstChannel+1}HP1_CH{channelNumber}HP2.csv"
                    fileName2 = f"{self.pathToData}/Data/CERN_Readout_Calib/{date}/{board}/CH{firstChannel+1}_CH{firstChannel+1}HP2_CH{channelNumber}HP1.csv"

                    fileName3 = f"{self.pathToData}/Data/CERN_Readout_Calib/{date}/{board}/CH{channelNumber}_CH{firstChannel+1}HP1_CH{channelNumber}HP2.csv"
                    fileName4 = f"{self.pathToData}/Data/CERN_Readout_Calib/{date}/{board}/CH{channelNumber}_CH{firstChannel+1}HP2_CH{channelNumber}HP1.csv"

                    data1 = pd.read_csv(fileName1, sep=",", header=None, skiprows=1)
                    data2 = pd.read_csv(fileName2, sep=",", header=None, skiprows=1)

                    data3 = pd.read_csv(fileName3, sep=",", header=None, skiprows=1)
                    data4 = pd.read_csv(fileName4, sep=",", header=None, skiprows=1)

                    value1 = (data1[1][tini:] - data3[1][tini:]).mean()*1e3
                    value1Err = (data1[1][tini:] - data3[1][tini:]).std()*1e3

                    value2 = (data2[1][tini:] - data4[1][tini:]).mean()*1e3
                    value2Err = (data2[1][tini:] - data4[1][tini:]).std()*1e3

                    results.append((value1 + value2)/2)
                    resultsErr.append(np.sqrt(value1Err**2 + value2Err**2))
                    channels.append(channelNumber)
                except:
                    continue

        self.results = np.array(results)
        self.resultsErr = np.array(resultsErr)
        self.channels = np.array(channels)
        return self

    def make(self):
        self.container = {}
        if self.readout.upper() == "IFIC":
            self.dates = ["20231114", "20231116"]
            for date in self.dates:
                self.makeIFIC(date=date)
                for nchan, chan in enumerate(self.channels):
                    if f"s{chan}" not in self.container.keys():
                        self.container[f"s{int(chan)}"] = [self.results[nchan]]
                    else:
                        self.container[f"s{int(chan)}"].append(self.results[nchan])
        elif self.readout.upper() == "CERN":
            self.dates = ["20231907", "20232307", "20232507"]
            for date in self.dates:
                self.makeCERN(date=date)
                for nchan, chan in enumerate(self.channels):
                    if f"s{chan}" not in self.container.keys():
                        self.container[f"s{int(chan)}"] = [self.results[nchan]]
                    else:
                        self.container[f"s{int(chan)}"].append(self.results[nchan])
        else:
            print("Not a valid option: IFIC or CERN")
        return self

    def save(self):
        if len(self.container) == 0:
            self.make()
        with open(f"{self.outputFileName}", "w") as f:
            json.dump(self.container, f, indent=4)
        print(f"{self.readout.upper()} readout calibration has been written to {self.outputFileName}")

    def load(self):
        with open(f"{self.outputFileName}", "r") as f:
            self.data = pd.DataFrame.from_dict(json.load(f))
        return self