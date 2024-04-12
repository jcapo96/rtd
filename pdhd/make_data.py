from rtd.src.data.retrieveData.RTDConverter import RTDConverter
from rtd.src.calib.utils.tools.makeRCalib import ReadoutCalib
import pandas as pd
import ROOT, os, json, array

pathToSaveData = "/eos/user/j/jcapotor/PDHDdata/"
pathToCalibData = "/eos/user/j/jcapotor/RTDdata/calib/"
calibFileName = "LARTGRAD_TREE"
ref = "40525"
detector = "np04"
system = "apa"
startDay = "2024-03-05"
endDay = "2024-04-12"
startTime = "00:00:00"
endTime = "09:00:00"
FROM_CERN = True
CALIB = False
clockTick = 60

slowControlWebMapping = pd.read_csv(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/src/data/mapping/pdhd_mapping.csv",
                           sep=";", header=0).astype("str")
if CALIB is True:
    if FROM_CERN is True:
        outputRootFileName = f"{pathToSaveData}{detector}_{system}_{startDay}T{startTime}_{endDay}T{endTime}_ctick{clockTick}_{calibFileName.split('.')[0]}R{ref}cache.root"
    elif FROM_CERN is False:
        outputRootFileName = f"{pathToSaveData}{detector}_{system}_{startDay}T{startTime}_{endDay}T{endTime}_ctick{clockTick}_{calibFileName.split('.')[0]}R{ref}web.root"
elif CALIB is False:
    if FROM_CERN is True:
        outputRootFileName = f"{pathToSaveData}{detector}_{system}_{startDay}T{startTime}_{endDay}T{endTime}_ctick{clockTick}s_cache.root"
    elif FROM_CERN is False:
        outputRootFileName = f"{pathToSaveData}{detector}_{system}_{startDay}T{startTime}_{endDay}T{endTime}_ctick{clockTick}s_web.root"

for index, row in slowControlWebMapping.iterrows():
    if system not in row["SYSTEM"].lower():
        continue
    print(row["DCS-ID"], row["SC-ID"])
    RTDConverter(detector=detector, elementId=row["DCS-ID"], startDay=startDay, endDay=endDay, startTime=startTime, endTime=endTime, outputRootFileName=outputRootFileName, FROM_CERN=FROM_CERN, clockTick=clockTick).fillRootFile()

with open(f"{pathToCalibData}{calibFileName}.json") as f:
    data = json.load(f)[ref]

outputFile = ROOT.TFile(f"{outputRootFileName}", "UPDATE")
outputTree = ROOT.TTree(f"calib", f"Calibration constants from {calibFileName.split('.')[0]}")

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

with open(f"{pathToCalibData}{calibFileName}_rcal.json") as f:
    data = json.load(f)[ref]

outputFile = ROOT.TFile(f"{outputRootFileName}", "UPDATE")
outputTree = ROOT.TTree(f"rcalib", f"Calibration constants from {calibFileName.split('.')[0]}")

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