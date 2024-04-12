import ROOT
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
pathToSaveData = "/eos/user/j/jcapotor/PDHDdata/"
# fileName = "np04_apa_2024-03-05T00:00:00_2024-04-11T22:30:00_ctick60s_cache.root"
fileName = "np04_tgrad_2024-04-10T00:00:00_2024-04-11T22:30:00_ctick5s_cache.root"

outputRootFileName = f"{pathToSaveData}{fileName}"

outputFile = ROOT.TFile(f"{outputRootFileName}", "READ")
# print(outputFile.Map())
data = outputFile.Get("data")
cal = outputFile.Get("calib")
rcal = outputFile.Get("rcalib")

cc = {}
for branch in cal.GetListOfBranches():
    branchName = branch.GetName()
    for entry in cal:
        if branchName not in cc.keys():
            cc[branchName.split("cal")[1]] = [getattr(entry, branchName)]
        elif branchName in cc.keys():
            cc[branchName.split("cal")[1]].append(getattr(entry, branchName))

rcc = {}
for branch in rcal.GetListOfBranches():
    branchName = branch.GetName()
    for entry in rcal:
        if branchName not in rcc.keys():
            rcc[branchName.split("cal")[1]] = [getattr(entry, branchName)]
        elif branchName in rcal.keys():
            rcc[branchName.split("cal")[1]].append(getattr(entry, branchName))

t, temp = {}, {}
for branch in data.GetListOfBranches():
    branchName = branch.GetName()
    if "T" not in branchName:
        continue
    id = branchName.split("T")[1]
    if id not in cc.keys():
        continue
    c = cc[id][0]*1e-3
    rc = rcc[id][0]*1e-3
    for entry in data:
        if getattr(entry, branchName) < 0:
            continue
        if branchName not in temp.keys():
            temp[branchName] = [getattr(entry, branchName) - c - rc]
            t[branchName] = [getattr(entry, f"t{branchName.split('T')[1]}")]
        elif branchName in temp.keys():
            temp[branchName].append(getattr(entry, branchName) - c - rc)
            t[branchName].append(getattr(entry, f"t{branchName.split('T')[1]}"))

plt.figure(figsize=(10,6))
results, heights, errors = {}, {}, {}
mapping = pd.read_csv("/afs/cern.ch/user/j/jcapotor/software/rtd/src/data/mapping/pdhd_mapping.csv", sep=";", decimal=",", header=0).astype("str")
for key, values in temp.items():
    if np.mean(values) > 88:
        continue
    height = mapping.loc[(mapping["CAL-ID"]==key.split("T")[1])]["Y"]
    results[key] = np.mean(values[-10000:])
    heights[key] = float(height)
    errors[key] = np.std(values[-10000:])

plt.errorbar(results.values(), heights.values(), xerr=3e-3, fmt=".", capsize=6)
plt.title("TGrad temperatures")
plt.ylabel("Height (m)")
plt.xlabel("Temperature (K)")
plt.legend(ncol=4)
plt.savefig("test.png")
outputFile.Close()