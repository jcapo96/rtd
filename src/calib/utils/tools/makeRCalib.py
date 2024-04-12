import json
import numpy as np
import pandas as pd

class ReadoutCalib():
    def __init__(self, readout="IFIC") -> None:
        self.readout = readout
        self.pathToData = "/eos/user/j/jcapotor/RTDdata"
        self.pathToSaveCalib = f"{self.pathToData}/calib/"
        self.outputFileName = f"{self.pathToSaveCalib}{self.readout.upper()}RCalib.json"
        self.results = None
        self.resultsErr = None
        self.channels = None

    def makeIFIC(self, date):
        tini = 30
        results, resultsErr, channels = [0], [0], [7]
        dates = ["20231114", "20231116"]
        if "14" in date or "16" in date:
            firstChannel, nChannles = 6, 12
        elif "17" in date:
            firstChannel, nChannles = 0, 6
        for channelNumber in range(2, nChannles+1):
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

    def save(self):
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
            print("Still not implemented!")
        else:
            print("Not a valid option: IFIC or CERN")
        with open(f"{self.outputFileName}", "w") as f:
            json.dump(self.container, f, indent=4)
        print(f"{self.readout.upper()} readout calibration has been written to {self.outputFileName}")

    def load(self):
        with open(f"{self.outputFileName}", "r") as f:
            self.data = pd.DataFrame.from_dict(json.load(f))
        return self
